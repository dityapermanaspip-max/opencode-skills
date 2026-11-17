"""The fiscal period and the annual close (annual closing of the books).
Close = every evaluation of the year gets its ACTUAL, then: ACTUAL becomes next year's RESIDUAL (only on the same
matrix), plans left open become NOT_REALISED, plans that are DONE carry their control into next year, and the trend
compares this year's RESIDUAL with last year's on the same matrix."""

from __future__ import annotations

from datetime import date

from gv_cycle import ecm_rows, plans_of, refresh_active, set_ecm
from gv_matrix import load as load_matrix
from gv_rules import VaultError


def open_period(vault) -> int:
    year = vault.cfg["fiscal_year"]
    if vault.cfg["period_open"]:
        raise VaultError(f"Periode tutup buku {year} sudah dibuka")
    vault.cfg["period_open"] = True
    vault.save_config()
    vault.log("open-period", "sistem", f"periode {year} dibuka: ACTUAL boleh diisi, tutup buku boleh dijalankan")
    return year


def compute_trend(vault, ev) -> str:
    """IMPROVING / WORSENING / STABLE; only meaningful against last year's RESIDUAL on the SAME matrix."""
    cur = ev.fields.get("residual")
    if not cur:
        return "STABLE"
    prev = vault.notes.get(f"EVA-{ev.fields['fiscal_year'] - 1}-{ev.fields['pre'].split('-', 1)[1]}")
    if not prev or prev.fields["matrix"] != ev.fields["matrix"] or not prev.fields.get("residual"):
        return "STABLE"
    matrix = load_matrix(vault, ev.fields["matrix"])
    a, b = matrix.score(cur), matrix.score(prev.fields["residual"])
    return "STABLE" if a == b else "IMPROVING" if a < b else "WORSENING"


def close_year(vault, year: int) -> dict:
    if not (vault.cfg["period_open"] and vault.cfg["fiscal_year"] == year):
        raise VaultError(f"Periode tutup buku {year} belum dibuka (perintah: open-period)")
    new_matrix = vault.cfg.get("active_matrix")
    if not new_matrix:
        raise VaultError("Belum ada matriks aktif untuk tahun depan: isi 'active_matrix' di GRIMIS.md (perintah: matrix activate)")
    evs = [e for e in vault.all("evaluasi") if e.fields["fiscal_year"] == year and not e.fields.get("closed")
           and vault.notes[e.fields["pre"]].fields.get("active", True)]
    if not evs:
        raise VaultError(f"Tidak ada evaluasi tahun {year} yang perlu ditutup")
    missing = [e.id for e in evs if not e.fields.get("actual")]
    if missing:
        raise VaultError(f"{len(missing)} evaluasi belum diisi ACTUAL, tutup buku ditolak: {', '.join(missing)}")
    clash = [f"EVA-{year + 1}-{e.fields['pre'].split('-', 1)[1]}" for e in evs
             if f"EVA-{year + 1}-{e.fields['pre'].split('-', 1)[1]}" in vault.notes]
    if clash:
        raise VaultError(f"Sebagian evaluasi tahun depan sudah ada: {', '.join(clash)}")
    load_matrix(vault, new_matrix)
    summary = {"closed": 0, "carried": 0, "not_realised": 0, "blank_new": 0, "needs_controls": [], "trends": {}}
    for ev in evs:
        f = ev.fields
        same = f["matrix"] == new_matrix
        trend = compute_trend(vault, ev)
        raw = {"pre": f["pre"], "fiscal_year": year + 1, "matrix": new_matrix, "trend": trend}
        if same:
            raw.update(inherent=f.get("inherent"), residual=f["actual"])
        else:
            summary["blank_new"] += 1
        new_ev = vault.create("evaluasi", raw, who="close")
        for plan in plans_of(vault, ev.id):
            if plan.fields["status"] not in ("DONE", "NOT_REALISED"):
                plan.fields["status"] = "NOT_REALISED"
                vault.save(plan)
                summary["not_realised"] += 1
        carried = [dict(r, status="EFFECTIVE", notes=f"Carry-over dari tutup buku tahun {year}")
                   for r in ecm_rows(ev) if r["plan"] and vault.notes[r["plan"]].fields["status"] == "DONE"]
        if carried:
            set_ecm(new_ev, carried)
            summary["carried"] += len(carried)
        refresh_active(vault, new_ev)
        if new_ev.fields.get("residual") and not carried:
            summary["needs_controls"].append(new_ev.id)
        f["closed"] = date.today().isoformat()
        f["trend"] = trend
        vault.save(ev)
        summary["closed"] += 1
        summary["trends"][trend] = summary["trends"].get(trend, 0) + 1
    vault.cfg["fiscal_year"], vault.cfg["period_open"] = year + 1, False
    vault.save_config()
    vault.log("close", "sistem", f"tutup buku {year}: {summary['closed']} evaluasi, {summary['carried']} kontrol dibawa, "
              f"{summary['not_realised']} rencana NOT_REALISED, {summary['blank_new']} evaluasi baru kosong (matriks berganti), "
              f"{len(summary['needs_controls'])} evaluasi baru terisi RESIDUAL tetapi belum punya kontrol")
    return summary
