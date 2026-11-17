"""Key Risk Indicators: readings, the traffic-light status, thresholds that change only with a logged reason,
and retiring. Adoption model: a KRI is active as soon as it exists (no approval step), at most three active per risk."""

from __future__ import annotations

from datetime import date

from gv_notes import get_section, make_table, set_section, table_rows
from gv_rules import VaultError, _check_order


def status_of(value, amber, red, direction: str) -> str:
    if amber is None or red is None or value is None:
        return "grey"
    if direction == "higher_is_worse":
        return "red" if value >= red else "amber" if value >= amber else "green"
    return "red" if value <= red else "amber" if value <= amber else "green"


def readings(note) -> list[tuple[str, float]]:
    out = []
    for r in table_rows(get_section(note.body, "Pembacaan")):
        try:
            out.append((r["tanggal"], float(r["nilai"].replace(",", "."))))
        except (KeyError, ValueError):
            continue
    return out


def latest(note):
    """The newest reading by date; on the same date the one entered last."""
    rows = readings(note)
    best = None
    for idx, (d, v) in enumerate(rows):
        if best is None or (d, idx) >= (best[0], best[2]):
            best = (d, v, idx)
    return (best[0], best[1]) if best else None


def current_status(note) -> tuple[str, tuple | None]:
    last = latest(note)
    f = note.fields
    return status_of(last[1] if last else None, f.get("amber"), f.get("red"), f["direction"]), last


def add_reading(vault, kri_id: str, value: float, when: str | None = None) -> str:
    note = vault.get(kri_id)
    if note.fields.get("status") != "ACTIVE":
        raise VaultError(f"{kri_id} sudah RETIRED: tidak menerima pembacaan baru")
    when = date.fromisoformat(when).isoformat() if when else date.today().isoformat()
    rows = [[d, v] for d, v in readings(note)] + [[when, value]]
    note.body = set_section(note.body, "Pembacaan", make_table(["Tanggal", "Nilai"], rows))
    vault.save(note)
    status = current_status(note)[0]
    vault.log("kri read", kri_id, f"{value} pada {when} -> {status}")
    return status


def change_threshold(vault, kri_id: str, amber, red, reason: str) -> None:
    if not (reason or "").strip():
        raise VaultError("Perubahan ambang wajib beralasan (--reason)")
    note = vault.get(kri_id)
    if note.fields.get("status") != "ACTIVE":
        raise VaultError(f"{kri_id} sudah RETIRED")
    f = note.fields
    old = (f.get("amber"), f.get("red"))
    new = (float(amber) if amber is not None else old[0], float(red) if red is not None else old[1])
    probe = dict(f, amber=new[0], red=new[1])
    _check_order(probe)
    f["amber"], f["red"] = new
    hist = [[r.get("tanggal"), r.get("kuning lama"), r.get("merah lama"), r.get("kuning baru"), r.get("merah baru"), r.get("alasan")]
            for r in table_rows(get_section(note.body, "Riwayat ambang"))]
    hist.append([date.today().isoformat(), old[0], old[1], new[0], new[1], reason.strip()])
    note.body = set_section(note.body, "Riwayat ambang",
                            make_table(["Tanggal", "Kuning lama", "Merah lama", "Kuning baru", "Merah baru", "Alasan"], hist))
    vault.save(note)
    vault.log("kri threshold", kri_id, f"{old} -> {new}: {reason.strip()}")


def retire(vault, kri_id: str) -> None:
    note = vault.get(kri_id)
    if note.fields.get("status") == "RETIRED":
        raise VaultError(f"{kri_id} sudah RETIRED")
    note.fields["status"] = "RETIRED"
    vault.save(note)
    vault.log("kri retire", kri_id, "ACTIVE -> RETIRED (riwayat disimpan)")
