"""Progress arithmetic for a running contract: deviation, the critical-contract test, pace, projection.

The test is the one in the SSUK of the Peraturan LKPP 12/2021 contract models (Pasal "Peringatan Dini
Keterlambatan Pelaksanaan Pekerjaan dan Kontrak Kritis"):
  period I  (planned progress 0% to 70%)   : late by MORE than 10%        -> critical
  period II (planned progress 70% to 100%) : late by MORE than 5%         -> critical
  period II, late by less than 5% but the work will run past the fiscal year -> critical
This module only says that the criteria are MET. Declaring a contract critical, the warning letter and
the show cause meeting (SCM) are acts of the Pejabat Penandatangan Kontrak, never of this script.
"""

from __future__ import annotations

from datetime import date, timedelta

from pbj_derived import parse_amount

PERIOD_SPLIT = 70.0
LIMIT = {"I": 10.0, "II": 5.0}
SCM_TEMPLATES = {"ba_scm", "sp"}


def iso(value) -> date | None:
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError:
        return None


def number(value) -> float | None:
    """A figure from proyek.md: 150, 150,5 and Rp150 all parse; anything else is None."""
    return parse_amount(value)


def evaluate(rencana: float, realisasi: float) -> dict:
    deviasi = round(realisasi - rencana, 2)
    periode = "I" if rencana <= PERIOD_SPLIT else "II"
    return {"deviasi": deviasi, "periode": periode, "ambang": LIMIT[periode], "kritis": deviasi < -LIMIT[periode]}


def row_label(row: dict) -> str:
    ev = evaluate(row["rencana"], row["realisasi"])
    if ev["kritis"]:
        return f"memenuhi kriteria kritis (periode {ev['periode']}, terlambat {abs(ev['deviasi']):.2f} > {ev['ambang']:.0f})"
    return "terlambat" if ev["deviasi"] < 0 else "sesuai/lebih"


def id_num(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")


def analyse(data: dict, rows: list[dict], docs: list[dict]) -> dict:
    """Facts and checks derived from the typed data; nothing here is typed by a person."""
    out: dict = {"checks": [], "advice": [], "lines": []}
    mulai, selesai_kontrak = iso(data.get("tanggal_mulai")), iso(data.get("tanggal_selesai"))
    jangka = number(data.get("jangka_waktu_hari"))
    if mulai and jangka and selesai_kontrak:
        expected = mulai + timedelta(days=int(jangka) - 1)
        if expected != selesai_kontrak:
            out["checks"].append(f"tanggal_selesai {selesai_kontrak.isoformat()} tidak sama dengan tanggal_mulai + jangka waktu - 1 ({expected.isoformat()}); samakan dengan kontrak/SPMK")
    for before, after in zip(rows, rows[1:]):
        b_end, a_start = iso(before["selesai"]), iso(after["mulai"])
        if b_end and a_start and a_start != b_end + timedelta(days=1):
            out["checks"].append(f"pekan {after['pekan']} tidak bersambung dengan pekan {before['pekan']} ({before['selesai']} -> {after['mulai']})")
        if after["realisasi"] < before["realisasi"]:
            out["checks"].append(f"realisasi turun dari pekan {before['pekan']} ke pekan {after['pekan']}: periksa data")
    if not rows:
        out["advice"].append("Belum ada data progres: tambahkan per pekan dengan `progress add` (rencana dan realisasi kumulatif dari laporan pengawas).")
        return out

    last = rows[-1]
    ev = evaluate(last["rencana"], last["realisasi"])
    out["last"] = ev
    first_critical = next((r for r in rows if evaluate(r["rencana"], r["realisasi"])["kritis"]), None)
    out["first_critical"] = first_critical
    last_end = iso(last["selesai"])
    lines = out["lines"]
    lines.append(f"Pekan {last['pekan']} ({last['mulai']} s/d {last['selesai']}): rencana {id_num(last['rencana'])}%, realisasi {id_num(last['realisasi'])}%, deviasi {id_num(ev['deviasi'])}% -> {row_label(last)}")

    remaining = None
    if mulai and last_end:
        elapsed = (last_end - mulai).days + 1
        remaining = int(jangka) - elapsed if jangka else ((selesai_kontrak - last_end).days if selesai_kontrak else None)
        lines.append(f"Waktu terpakai {elapsed} hari" + (f", sisa {remaining} hari" + (f" ({elapsed / jangka * 100:.0f}% waktu)" if jangka else "") if remaining is not None else ""))
        out["elapsed"], out["remaining"] = elapsed, remaining

    pace_day = None
    window = rows[-4:]
    if len(window) >= 2 and iso(window[0]["selesai"]) and last_end:
        days = (last_end - iso(window[0]["selesai"])).days
        if days > 0:
            pace_day = (last["realisasi"] - window[0]["realisasi"]) / days
            lines.append(f"Laju realisasi {len(window) - 1} pekan terakhir: {id_num(pace_day * 7)}% per pekan")
    out["pace_day"] = pace_day
    if remaining and remaining > 0:
        needed = (100 - last["realisasi"]) / remaining
        lines.append(f"Laju yang dibutuhkan agar selesai tepat waktu: {id_num(needed * 7)}% per pekan" + (f" ({needed / pace_day:.0f} kali laju terakhir)" if pace_day and pace_day > 0 else ""))
        if pace_day is not None:
            reach = min(100.0, last["realisasi"] + max(pace_day, 0) * remaining)
            lines.append(f"Proyeksi realisasi pada akhir masa pelaksanaan dengan laju terakhir: {id_num(reach)}% (indikatif)")
            if pace_day > 0 and last_end:
                finish = last_end + timedelta(days=int((100 - last["realisasi"]) / pace_day))
                fallback = selesai_kontrak.year if selesai_kontrak else last_end.year
                raw_year = number(data.get("tahun_anggaran"))
                year = int(raw_year) if raw_year is not None else fallback
                out["finish"] = finish
                if not 1000 <= year <= 9999:
                    out["checks"].append(f"tahun_anggaran '{data.get('tahun_anggaran')}' tidak masuk akal; proyeksi memakai tahun {fallback}")
                    year = fallback
                if finish > date(year, 12, 31):
                    lines.append(f"Dengan laju terakhir pekerjaan baru selesai sekitar {finish.isoformat()}, melewati tahun anggaran {year}: kesempatan yang melewati tahun anggaran butuh DIPA tahun berikutnya (SSUK 32.3)")

    done = {d["template"] for d in docs if d["status"] != "batal"}
    advice = out["advice"]
    if ev["kritis"]:
        since = f"pekan {first_critical['pekan']} ({first_critical['selesai']})" if first_critical else "pekan ini"
        advice.append(f"Kriteria kontrak kritis terpenuhi sejak {since}. SSUK: Pejabat Penandatangan Kontrak memberi peringatan tertulis lalu menyelenggarakan SCM tahap I (`route kontrak_kritis`).")
        if not (SCM_TEMPLATES & done):
            advice.append("Belum ada BA SCM atau surat peringatan yang tercatat di tabel Dokumen.")
    if remaining is not None and remaining <= 0 and last["realisasi"] < 100:
        advice.append("Masa pelaksanaan habis sebelum pekerjaan selesai: kesempatan menyelesaikan (addendum, sampai 50 hari kalender, dengan denda dan perpanjangan jaminan) atau pemutusan (`route perubahan_kontrak`, `route pemutusan_kontrak`).")
    if "pemutusan" in done:
        advice.append("Kontrak sudah diputus: lanjutkan dengan `route sanksi_daftar_hitam` dan `replacement` (kontrak pengganti).")
    return out
