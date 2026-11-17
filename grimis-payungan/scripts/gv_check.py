"""`check`: validates the whole vault against the model and the rules. Reports, never repairs.
Each finding is (level, id, message); level is ERROR (breaks a rule) or WARN (suspicious but allowed)."""

from __future__ import annotations

import gv_evidence
from gv_bowtie_data import problems as bowtie_problems
from gv_cycle import active_of, ecm_rows
from gv_matrix import Matrix
from gv_rules import MAX_KRI_PER_RISK, VaultError, validate
from gv_schema import ENTITIES


def check(vault) -> list[tuple[str, str, str]]:
    out = [("ERROR", "-", p) for p in vault.problems]
    for n in vault.notes.values():
        ent = ENTITIES[n.entity]
        for f in ent.fields:
            if f.req and n.fields.get(f.name) in (None, "", []):
                out.append(("ERROR", n.id, f"kolom wajib '{f.name}' kosong"))
        try:
            validate(vault, n, creating=False, audit=True)
        except VaultError as exc:
            out.append(("ERROR", n.id, str(exc)))
        except KeyError as exc:
            out.append(("ERROR", n.id, f"kolom hilang: {exc}"))
    for ev in vault.all("evaluasi"):
        out += _evaluation(vault, ev)
    for risk in vault.all("risiko"):
        active = [k for k in vault.all("kri") if k.fields["risk"] == risk.id and k.fields.get("status") == "ACTIVE"]
        if len(active) > MAX_KRI_PER_RISK:
            out.append(("ERROR", risk.id, f"{len(active)} KRI aktif, maksimum {MAX_KRI_PER_RISK}"))
    for pls in vault.all("rencana"):
        if pls.fields["status"] == "DONE" and not any(r["plan"] == pls.id for r in ecm_rows(vault.notes[pls.fields["evaluation"]])):
            out.append(("ERROR", pls.id, "rencana DONE tetapi kontrolnya tidak terpasang pada evaluasi"))
    out += bowtie_problems(vault)
    for ev in vault.all("evaluasi"):
        gap = gv_evidence.missing(vault, ev) if ev.fields["fiscal_year"] == vault.cfg["fiscal_year"] else []
        if gap:
            out.append(("WARN", ev.id, f"kontrol tanpa bukti (belum ada berkas di {gv_evidence.ROOT}/{ev.id}/<CTL>/): {', '.join(gap)}"))
    stray = gv_evidence.plan_sort(vault)
    if stray:
        out.append(("WARN", "VAULT", f"{len(stray)} berkas bukti belum di folder yang benar ({sum(s['dest'] is not None for s in stray)} bisa "
                    f"dipindah otomatis): jalankan 'evidence sort'"))
    cfg = vault.cfg
    if cfg.get("active_matrix") and cfg["active_matrix"] not in vault.notes:
        out.append(("ERROR", "VAULT", f"active_matrix menunjuk {cfg['active_matrix']} yang tidak ada"))
    return out


def _evaluation(vault, ev) -> list:
    out, f = [], ev.fields
    m = vault.notes.get(f.get("matrix"))
    if m is None or m.entity != "matriks":
        return out
    mx = Matrix(m)
    for name in ("inherent", "residual", "expected", "actual", "active_cell", "sim_suggestion"):
        if f.get(name):
            try:
                mx.check(f[name])
            except (VaultError, ValueError) as exc:
                out.append(("ERROR", ev.id, f"{name}: {exc}"))
    kind, cell = active_of(vault, ev)
    if (f.get("active_type"), f.get("active_cell")) != (kind, cell):
        out.append(("ERROR", ev.id, f"nilai aktif tersimpan ({f.get('active_type')}/{f.get('active_cell')}) tidak sama dengan hitungan "
                    f"({kind}/{cell}); jalankan 'rate' atau 'status --refresh'"))
    if f.get("residual") and not ecm_rows(ev):
        out.append(("WARN", ev.id, "RESIDUAL terisi tetapi belum ada kontrol yang ada"))
    if ecm_rows(ev) and not f.get("residual"):
        out.append(("WARN", ev.id, "ada kontrol yang ada tetapi RESIDUAL belum dinilai"))
    if f.get("closed") and not f.get("actual"):
        out.append(("ERROR", ev.id, "evaluasi ditutup tanpa ACTUAL"))
    year = f["fiscal_year"]
    if not ev.id.startswith(f"EVA-{year}-"):
        out.append(("ERROR", ev.id, f"ID tidak cocok dengan fiscal_year {year}"))
    return out
