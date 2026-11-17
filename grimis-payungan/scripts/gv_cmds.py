"""Command handlers: each takes a Vault and plain arguments and returns the text to print (Indonesian)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import gv_cycle
import gv_kri
import gv_sim
from gv_matrix import load as load_matrix
from gv_matrix import matrix_body
from gv_notes import write_note, Note
from gv_rules import VaultError
from gv_schema import ENTITIES, entity_name, entity_of_id

FOLDERS = sorted({e.folder for e in ENTITIES.values()}) + ["99-Laporan"]

GRIMIS_BODY = """# Vault manajemen risiko

Vault ini dikelola oleh skill `grimis-payungan`. Siklusnya: mandat -> sasaran -> indikator -> proses
-> identifikasi risiko -> evaluasi (inheren, residual, ekspektasi, aktual) -> mitigasi -> insiden -> tutup buku tahunan.

- Satu catatan = satu objek. ID dan nama berkas sama (mis. `RSK-001.md`). Tautan memakai `[[ID]]`.
- Nilai dan status yang beraturan diubah lewat perintah `grimis.py` (rate, plan, kri, close), bukan diketik manual.
- Teks bebas (deskripsi, penyebab, dampak, catatan) boleh diedit langsung.
- `LOG.md` mencatat setiap perubahan dan hanya bertambah. `00-Dashboard.md` dan `99-Laporan/` dibuat otomatis.
- Kolom di atas (org, fiscal_year, period_open, active_matrix) adalah pengaturan akar: tahun kerja, apakah periode tutup buku
  dibuka (ACTUAL baru boleh diisi saat dibuka), dan matriks aktif untuk tahun depan.
"""


def init(path: str, org: str, year: int) -> str:
    root = Path(path)
    if root.exists() and any(root.iterdir()):
        raise VaultError(f"Folder {root} sudah berisi sesuatu: pilih folder kosong atau yang belum ada")
    for folder in FOLDERS:
        (root / folder).mkdir(parents=True, exist_ok=True)
    write_note(Note(root / "GRIMIS.md", {"org": org, "fiscal_year": year, "period_open": False, "active_matrix": None}, GRIMIS_BODY))
    return f"Vault dibuat di {root.resolve()} untuk {org}, tahun kerja {year}. Langkah berikut: matriks, lalu konteks."


def _kv(pairs: list[str]) -> dict:
    out = {}
    for p in pairs:
        if "=" not in p:
            raise VaultError(f"Gunakan bentuk kolom=nilai, bukan {p!r}")
        k, v = p.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def new(v, entity: str, pairs: list[str]) -> str:
    ent = entity_name(entity)
    raw = _kv(pairs)
    if ent == "matriks":
        body = matrix_body(int(raw.get("max_likelihood", 5)), int(raw.get("max_impact", 5)))
        note = v.create(ent, raw, body=body)
    elif ent == "rencana":
        note = gv_cycle.new_plan(v, raw)
    else:
        note = v.create(ent, raw)
        if ent == "evaluasi":
            gv_cycle.refresh_active(v, note)
    return f"Dibuat {note.id}"


def set_fields(v, note_id: str, pairs: list[str]) -> str:
    v.update(note_id, _kv(pairs))
    return f"{note_id} diperbarui"


def show(v, note_id: str) -> str:
    n = v.get(note_id)
    lines = [f"{n.id} ({n.entity})"] + [f"  {k}: {val}" for k, val in n.fields.items() if val not in (None, "", [])]
    if n.entity == "evaluasi":
        lines += [f"  kontrol: {', '.join(r['control'] + '/' + r['status'] for r in gv_cycle.ecm_rows(n)) or '-'}",
                  f"  rencana: {', '.join(p.id + '/' + p.fields['status'] for p in gv_cycle.plans_of(v, n.id)) or '-'}"]
    if n.entity == "kri":
        st, last = gv_kri.current_status(n)
        lines.append(f"  status: {st}, pembacaan terakhir: {last or '-'}")
    return "\n".join(lines)


def list_(v, entity: str) -> str:
    rows = v.all(entity)
    return "\n".join(f"{n.id}  {n.fields.get('title') or n.fields.get('action') or n.fields.get('pre') or ''}" for n in rows) or "(kosong)"


def rate(v, eva: str, **levels) -> str:
    changed = gv_cycle.rate(v, eva, **levels)
    ev = v.get(eva)
    m = load_matrix(v, ev.fields["matrix"])
    cell = ev.fields.get("active_cell")
    shown = f"{ev.fields['active_type']} {cell} (skor {m.score(cell)}, {m.zone(cell)})" if cell else f"{ev.fields['active_type']} (belum dinilai)"
    return f"{eva}: " + ", ".join(f"{k}={val or 'kosong'}" for k, val in changed.items()) + f". Nilai aktif sekarang: {shown}"


def control(v, action: str, eva: str, ctl: str, status: str = "EFFECTIVE", notes: str = "") -> str:
    (gv_cycle.add_control(v, eva, ctl, status, notes) if action == "add" else gv_cycle.remove_control(v, eva, ctl))
    return f"{ctl} {'dipasang pada' if action == 'add' else 'dilepas dari'} {eva}; nilai aktif: {v.get(eva).fields['active_type']}"


def plan(v, action: str, plan_id: str, evidence=None, notes=None) -> str:
    if action == "start":
        gv_cycle.start_plan(v, plan_id)
        return f"{plan_id} IN_PROGRESS"
    _, ctl = gv_cycle.complete_plan(v, plan_id, evidence, notes)
    ev = v.get(v.get(plan_id).fields["evaluation"])
    return f"{plan_id} DONE; kontrol {ctl.id} terpasang pada {ev.id}; nilai aktif: {ev.fields['active_type']}"


def kri(v, action: str, kri_id: str, value=None, when=None, amber=None, red=None, reason=None) -> str:
    if action == "read":
        return f"{kri_id}: pembacaan dicatat, status {gv_kri.add_reading(v, kri_id, float(value.replace(',', '.')), when)}"
    if action == "threshold":
        gv_kri.change_threshold(v, kri_id, amber, red, reason)
        return f"{kri_id}: ambang diubah dan dicatat di riwayat"
    gv_kri.retire(v, kri_id)
    return f"{kri_id} RETIRED"


def simulate(v, eva: str, iterations: int, pct: int, seed) -> str:
    s = gv_sim.simulate(v, eva, iterations, pct, seed)
    base = "tanpa data insiden" if s["no_incident_data"] else f"{s['incident_count']} insiden"
    return (f"{eva}: simulasi {s['iterations']} iterasi ({base}); saran sel {s['suggested_cell']}. "
            f"Belum dipakai: pakai 'rate {eva} --residual sim' bila setuju.")


def appetite(v, matrix_id: str, year: int, score: int) -> str:
    m = load_matrix(v, matrix_id)
    m.set_appetite(year, score)
    v.save(m.note)
    v.log("appetite", matrix_id, f"tahun {year}: batas skor {score}")
    return f"Appetite {matrix_id} tahun {year} = {score}"


def matrix(v, action: str, matrix_id: str) -> str:
    m = load_matrix(v, matrix_id)
    if action == "activate":
        v.cfg["active_matrix"] = matrix_id
        v.save_config()
        v.log("matrix activate", matrix_id, "dipakai untuk tahun depan dan evaluasi baru")
        return f"{matrix_id} sekarang matriks aktif"
    zones = {m.zone(f"{l}x{i}") for l in range(1, m.max_l + 1) for i in range(1, m.max_i + 1)}
    return f"{m.id} {m.max_l}x{m.max_i}, zona: {', '.join(sorted(zones))}\nSkor sel:\n{m.grid()}"


def new_year_hint(v) -> str:
    return f"Tahun kerja {v.cfg['fiscal_year']}, periode {'dibuka' if v.cfg['period_open'] else 'belum dibuka'}, hari ini {date.today()}"
