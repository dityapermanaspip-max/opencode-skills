"""Bowtie data: branch keys, which controls a person picked for which branch, and the checks on them.
Controls are picked only from the controls installed on an evaluation of the risk (working year), as in the web app.
The pick is stored in the risk note, section `## Kontrol bowtie` (table Cabang | Kontrol), by branch text so it survives
re-ordering. Standard library only."""

from __future__ import annotations

import re

import gv_evidence
from gv_cycle import ecm_rows
from gv_draft import norm
from gv_notes import bullet_tree, get_section, make_table, set_section, table_rows
from gv_rules import VaultError
from gv_schema import strip_link

SECTION = "Kontrol bowtie"
_KEY = re.compile(r"[ci]\d+(\.\d+)*\Z")


def branches(risk) -> list[tuple[str, str]]:
    """Every branch as (key, text). Keys are `c0`, `c4.1`, `i2`: the scheme the renderer and KRI matching use."""
    out: list[tuple[str, str]] = []

    def walk(nodes, prefix: str) -> None:
        for idx, node in enumerate(nodes):
            key = f"{prefix}{idx}"
            out.append((key, node["text"]))
            walk(node["children"], key + ".")

    walk(bullet_tree(get_section(risk.body, "Penyebab")), "c")
    walk(bullet_tree(get_section(risk.body, "Dampak")), "i")
    return out


def attachments(risk) -> list[tuple[str, str]]:
    """(branch text, control id) rows of the risk note."""
    return [(r["cabang"], strip_link(r["kontrol"])) for r in table_rows(get_section(risk.body, SECTION))
            if r.get("cabang") and r.get("kontrol")]


def _evaluations(vault, risk_id: str) -> list:
    year = vault.cfg["fiscal_year"]
    return [ev for ev in vault.all("evaluasi")
            if ev.fields["fiscal_year"] == year and vault.notes[ev.fields["pre"]].fields["risk"] == risk_id]


def installed(vault, risk_id: str) -> dict[str, list[dict]]:
    """control id -> [{eva, status, plan, notes, files, proven}] over the working year's evaluations of the risk.
    `files` are the names in 08-Bukti/<EVA>/<CTL>/; `proven` = has files or came from a plan."""
    out: dict[str, list[dict]] = {}
    for ev in _evaluations(vault, risk_id):
        for r in ecm_rows(ev):
            names = [p.name for p in gv_evidence.files(vault, ev.id, r["control"])]
            out.setdefault(r["control"], []).append({"eva": ev.id, **r, "files": names, "proven": bool(r["plan"]) or bool(names)})
    return out


def _risk(vault, risk_id: str):
    note = vault.get(risk_id)
    if note.entity != "risiko":
        raise VaultError(f"{risk_id} bukan risiko")
    return note


def _resolve(risk, ref: str) -> str:
    """A branch key (c1, i0, c4.1) or its text (exact, else a unique part of it) -> the branch text."""
    tree, ref = branches(risk), ref.strip()
    if _KEY.match(ref.lower()):
        hit = [b for b in tree if b[0] == ref.lower()]
    else:
        want = norm(ref)
        hit = [b for b in tree if norm(b[1]) == want] or [b for b in tree if want and want in norm(b[1])]
    if len(hit) != 1:
        listing = "; ".join(f"{k} = {t}" for k, t in tree) or "belum ada cabang"
        raise VaultError(f"Cabang '{ref}' {'tidak ditemukan' if not hit else 'ambigu'} pada {risk.id}. Cabang: {listing}")
    return hit[0][1]


def _write(vault, risk, rows: list[tuple[str, str]]) -> None:
    risk.body = set_section(risk.body, SECTION, make_table(["Cabang", "Kontrol"], [[t, f"[[{c}]]"] for t, c in rows]))
    vault.save(risk)


def attach(vault, risk_id: str, refs: list[str], controls: list[str]) -> list[str]:
    risk = _risk(vault, risk_id)
    evas = _evaluations(vault, risk_id)
    if not evas:
        raise VaultError(f"{risk_id} belum punya evaluasi tahun {vault.cfg['fiscal_year']}")
    pool = installed(vault, risk_id)
    for ctl in controls:
        if ctl not in pool:
            raise VaultError(f"{ctl} belum terpasang pada evaluasi {', '.join(e.id for e in evas)}. Kontrol bowtie hanya dipilih dari kontrol "
                             f"yang terpasang pada evaluasi; terpasang: {', '.join(sorted(pool)) or 'belum ada'}. "
                             f"Pasang dulu: control add {evas[0].id} {ctl}")
    loose = [c for c in controls if not any(x["proven"] for x in pool[c])]
    if loose:
        raise VaultError(f"{', '.join(loose)} belum punya bukti. Kontrol pada bowtie harus terbukti ada: taruh berkas (SOP, tangkapan layar "
                         f"aplikasi, foto atau CCTV, dsb.) di {gv_evidence.ROOT}/{pool[loose[0]][0]['eva']}/{loose[0]}/ lalu ulangi")
    rows, said = attachments(risk), []
    for ref in refs:
        text = _resolve(risk, ref)
        for ctl in controls:
            if any(norm(t) == norm(text) and c == ctl for t, c in rows):
                said.append(f"{ctl} sudah terpasang pada '{text}'")
                continue
            rows.append((text, ctl))
            said.append(f"{ctl} dipasang pada '{text}'")
            vault.log("bowtie attach", risk_id, f"{ctl} -> {text}")
    _write(vault, risk, rows)
    return said


def detach(vault, risk_id: str, refs: list[str], controls: list[str]) -> list[str]:
    risk = _risk(vault, risk_id)
    rows = attachments(risk)
    gone = {norm(_resolve(risk, ref)) for ref in refs}
    keep = [(t, c) for t, c in rows if not (norm(t) in gone and (not controls or c in controls))]
    if len(keep) == len(rows):
        raise VaultError(f"Tidak ada kontrol bowtie yang cocok pada {risk_id}")
    _write(vault, risk, keep)
    removed = [f"{c} dilepas dari '{t}'" for t, c in rows if (t, c) not in keep]
    for line in removed:
        vault.log("bowtie detach", risk_id, line)
    return removed


def describe(vault, risk_id: str) -> str:
    """`bowtie show`: the branch keys, the picks so far, and the controls a person may still pick."""
    risk = _risk(vault, risk_id)
    picks, pool = attachments(risk), installed(vault, risk_id)
    out = [f"{risk.id}: {risk.fields.get('title')}", "Cabang (kunci, teks, kontrol yang sudah dipilih):"]
    for key, text in branches(risk):
        mine = [c for t, c in picks if norm(t) == norm(text)]
        out.append(f"  {key:<6} {text}" + (f"  <- {', '.join(mine)}" if mine else ""))
    if not branches(risk):
        out.append("  (belum ada cabang: buat draft bowtie dan accept dulu)")
    year = vault.cfg["fiscal_year"]
    out.append(f"Kontrol pada evaluasi {year} (hanya yang punya bukti yang boleh dipilih):")
    for cid, evals in sorted(pool.items()):
        out.append(f"  {cid}  {vault.notes[cid].fields.get('control_type')}  " + "; ".join(f"{x['status']} ({x['eva']})" for x in evals)
                   + ("" if any(x["proven"] for x in evals) else "  [TANPA BUKTI: belum bisa dipilih]")
                   + f"  {vault.notes[cid].fields.get('title')}")
    if not pool:
        out.append("  (belum ada: pasang dulu dengan control add)")
    return chr(10).join(out)


def problems(vault) -> list[tuple[str, str, str]]:
    """For `check`: picks whose branch or control no longer exists (WARN), or whose control is not in the dictionary (ERROR)."""
    out = []
    for risk in vault.all("risiko"):
        rows = attachments(risk)
        if not rows:
            continue
        texts = {norm(t) for _k, t in branches(risk)}
        pool = installed(vault, risk.id)
        for text, ctl in rows:
            if ctl not in vault.notes or vault.notes[ctl].entity != "kontrol":
                out.append(("ERROR", risk.id, f"Kontrol bowtie: {ctl} tidak ada di kamus"))
            elif ctl not in pool:
                out.append(("WARN", risk.id, f"Kontrol bowtie: {ctl} tidak lagi terpasang pada evaluasi {vault.cfg['fiscal_year']}"))
            if norm(text) not in texts:
                out.append(("WARN", risk.id, f"Kontrol bowtie: cabang '{text}' tidak ada lagi (teks diubah atau dihapus)"))
    return out
