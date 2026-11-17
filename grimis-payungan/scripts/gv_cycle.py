"""The risk value cycle of one evaluation: four values, which one is active, existing controls and mitigation plans.
The rules: no control -> INHERENT; control and not every plan DONE (or no plan)
-> RESIDUAL; every plan DONE -> EXPECTED. ACTUAL is never active, it is only the input of the annual close."""

from __future__ import annotations

from datetime import date

from gv_matrix import load as load_matrix
from gv_notes import get_section, make_table, set_section, table_rows
from gv_rules import VaultError
from gv_schema import EFFECTIVENESS, strip_link

ECM_HEAD = ["Kontrol", "Efektivitas", "Sumber rencana", "Catatan"]
LEVELS = ("inherent", "residual", "expected", "actual")


def ecm_rows(note) -> list[dict]:
    rows = []
    for r in table_rows(get_section(note.body, "Kontrol yang ada")):
        if r.get("kontrol"):
            rows.append({"control": strip_link(r["kontrol"]), "status": r.get("efektivitas") or "EFFECTIVE",
                         "plan": strip_link(r.get("sumber rencana")), "notes": r.get("catatan", "")})
    return rows


def set_ecm(note, rows: list[dict]) -> None:
    table = make_table(ECM_HEAD, [[f"[[{r['control']}]]", r["status"], f"[[{r['plan']}]]" if r.get("plan") else "", r.get("notes", "")]
                                  for r in rows])
    note.body = set_section(note.body, "Kontrol yang ada", table)


def plans_of(vault, eva_id: str) -> list:
    return [p for p in vault.all("rencana") if p.fields["evaluation"] == eva_id]


def active_of(vault, ev) -> tuple[str, str | None]:
    f = ev.fields
    plans = plans_of(vault, ev.id)
    if not ecm_rows(ev):
        kind = "INHERENT"
    elif plans and all(p.fields["status"] == "DONE" for p in plans):
        kind = "EXPECTED"
    else:
        kind = "RESIDUAL"
    return kind, f.get(kind.lower())


def refresh_active(vault, ev) -> None:
    ev.fields["active_type"], ev.fields["active_cell"] = active_of(vault, ev)
    vault.save(ev)


def _open_eval(vault, eva_id: str):
    ev = vault.get(eva_id)
    if ev.entity != "evaluasi":
        raise VaultError(f"{eva_id} bukan evaluasi")
    if ev.fields.get("closed"):
        raise VaultError(f"{eva_id} sudah ditutup (tutup buku) dan tidak dapat diubah")
    return ev


def rate(vault, eva_id: str, **levels) -> dict:
    """levels: inherent/residual/expected/actual = 'KxD', 'sim' (use the saved Monte Carlo suggestion) or '-' (clear)."""
    ev = _open_eval(vault, eva_id)
    matrix = load_matrix(vault, ev.fields["matrix"])
    changed, from_sim = {}, []
    for name in LEVELS:
        value = levels.get(name)
        if value is None:
            continue
        if name == "actual" and not (vault.cfg["period_open"] and ev.fields["fiscal_year"] == vault.cfg["fiscal_year"]):
            raise VaultError("ACTUAL hanya boleh diisi selama periode tutup buku tahun itu dibuka (perintah: open-period)")
        if value == "-":
            cell = None
        elif value == "sim":
            cell = ev.fields.get("sim_suggestion")
            if not cell:
                raise VaultError(f"{eva_id} belum punya saran simulasi: jalankan 'simulate {eva_id}' dulu")
            from_sim.append(name)
        else:
            cell = f"{matrix.check(value)[0]}x{matrix.check(value)[1]}"
        ev.fields[name] = cell
        changed[name] = cell
    if not changed:
        raise VaultError("Tidak ada nilai yang diberikan (--inherent, --residual, --expected, --actual)")
    if from_sim:  # the simulation section says 'not used yet' when written; record the decision next to it
        sim = get_section(ev.body, "Simulasi Monte Carlo")
        used = f"Saran ini dipakai sebagai {', '.join(from_sim)} pada {date.today().isoformat()}."
        ev.body = set_section(ev.body, "Simulasi Monte Carlo", f"{sim}\n\n{used}")
    refresh_active(vault, ev)
    vault.log("rate", eva_id, ", ".join(f"{k}={v}" for k, v in changed.items()) + f" | aktif {ev.fields['active_type']}")
    return changed


def add_control(vault, eva_id: str, ctl_id: str, status: str = "EFFECTIVE", notes: str = "", plan: str | None = None) -> None:
    ev = _open_eval(vault, eva_id)
    if ctl_id not in vault.notes or vault.notes[ctl_id].entity != "kontrol":
        raise VaultError(f"Kontrol tidak ditemukan di kamus: {ctl_id}")
    status = next((s for s in EFFECTIVENESS if s.lower() == status.lower()), None)
    if not status:
        raise VaultError(f"Efektivitas harus salah satu dari {', '.join(EFFECTIVENESS)}")
    rows = ecm_rows(ev)
    if any(r["control"] == ctl_id for r in rows):
        raise VaultError(f"{ctl_id} sudah terpasang pada {eva_id}")
    rows.append({"control": ctl_id, "status": status, "plan": plan, "notes": notes})
    set_ecm(ev, rows)
    refresh_active(vault, ev)
    vault.log("control add", eva_id, f"{ctl_id} {status} | aktif {ev.fields['active_type']}")


def remove_control(vault, eva_id: str, ctl_id: str) -> None:
    ev = _open_eval(vault, eva_id)
    rows = ecm_rows(ev)
    hit = [r for r in rows if r["control"] == ctl_id]
    if not hit:
        raise VaultError(f"{ctl_id} tidak terpasang pada {eva_id}")
    if hit[0]["plan"]:
        raise VaultError(f"{ctl_id} berasal dari rencana {hit[0]['plan']}: tidak dihapus dari evaluasi")
    set_ecm(ev, [r for r in rows if r["control"] != ctl_id])
    refresh_active(vault, ev)
    vault.log("control remove", eva_id, f"{ctl_id} | aktif {ev.fields['active_type']}")


def new_plan(vault, raw: dict):
    plan = vault.create("rencana", raw, who="plan new")
    refresh_active(vault, vault.get(plan.fields["evaluation"]))
    return plan


def start_plan(vault, plan_id: str):
    plan = vault.get(plan_id)
    if plan.fields["status"] != "PLANNED":
        raise VaultError(f"{plan_id} berstatus {plan.fields['status']}: hanya PLANNED yang dapat dimulai")
    plan.fields["status"] = "IN_PROGRESS"
    vault.save(plan)
    vault.log("plan start", plan_id, "IN_PROGRESS")
    return plan


def complete_plan(vault, plan_id: str, evidence: str | None = None, notes: str | None = None):
    """DONE: creates or reuses the control named by new_control_code and attaches it to the evaluation (source = this plan)."""
    plan = vault.get(plan_id)
    f = plan.fields
    if f["status"] not in ("PLANNED", "IN_PROGRESS"):
        raise VaultError(f"{plan_id} berstatus {f['status']}: tidak dapat diselesaikan")
    ev = _open_eval(vault, f["evaluation"])
    code = f.get("new_control_code")
    if not code:
        raise VaultError(f"{plan_id} belum punya new_control_code: isi kode (dan judul/jenis) kontrol yang dihasilkan rencana ini")
    ctl = vault.notes.get(code) if code in vault.notes else next((c for c in vault.all("kontrol") if c.fields.get("code") == code), None)
    if ctl is None or ctl.entity != "kontrol":
        ctl = vault.create("kontrol", {"title": f.get("new_control_title") or code, "code": code,
                                       "control_type": f.get("new_control_type") or "preventif"}, who="plan done")
    rows = ecm_rows(ev)
    if any(r["control"] == ctl.id for r in rows):
        raise VaultError(f"{ctl.id} sudah terpasang pada {ev.id}")
    rows.append({"control": ctl.id, "status": "EFFECTIVE", "plan": plan_id, "notes": ""})
    set_ecm(ev, rows)
    f["status"] = "DONE"
    f["evidence"] = evidence or f.get("evidence")
    f["notes"] = notes or f.get("notes")
    vault.save(plan)
    refresh_active(vault, ev)
    vault.log("plan done", plan_id, f"kontrol {ctl.id} | {ev.id} aktif {ev.fields['active_type']}")
    return plan, ctl
