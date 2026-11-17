"""Builds examples/demo-vault: a fictional organisation over 2024-2026 (two real annual closes, the working year 2026 left open).
Usage: python -P scripts/make_demo.py <folder> [--force]. Everything goes through the engine, so the result passes `check`."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gv_check  # noqa: E402
import gv_close  # noqa: E402
import gv_cmds as C  # noqa: E402
import gv_cycle  # noqa: E402
import gv_draft  # noqa: E402
import gv_kri  # noqa: E402
import gv_report  # noqa: E402
import gv_sim  # noqa: E402
from gv_vault import Vault  # noqa: E402

# (inherent, residual, expected, actual) per anchor and year; the residual of a year after the first starts as last year's actual
VALUES = {
    2024: {1: ("4x4", "3x4", "2x3", "3x4"), 2: ("4x3", "3x3", "2x3", "3x3"), 3: ("3x5", "2x4", "2x3", "2x4"), 4: ("4x3", "3x3", "2x2", "3x3"), 5: ("3x3", "2x3", "1x3", "2x3")},
    2025: {1: (None, "3x3", "2x3", "3x3"), 2: (None, "3x3", "2x3", "3x3"), 3: (None, "3x4", "2x3", "3x4"), 4: (None, "3x3", "2x2", "3x3"), 5: (None, "2x3", "1x3", "2x3")},
}
CTL_OF = {1: "CTL-001", 2: "CTL-001", 3: "CTL-002", 4: "CTL-003", 5: "CTL-003"}


def plan(v, eva, action, target, code, title, kind="preventif", budget=0):
    C.new(v, "rencana", [f"evaluation={eva}", f"action={action}", "pic=Kepala Bagian Umum", f"target_date={target}", f"budget={budget}",
                         f"new_control_code={code}", f"new_control_title={title}", f"new_control_type={kind}"])


def year_cycle(v, year):
    """Rates one year in full, plans included, opens the period, enters ACTUAL and closes."""
    for n, (inh, res, exp, act) in VALUES[year].items():
        eva = f"EVA-{year}-{n:03d}"
        if inh:
            C.rate(v, eva, inherent=inh)
        if f"CTL-{CTL_OF[n][-3:]}" not in [r["control"] for r in gv_cycle.ecm_rows(v.get(eva))]:
            gv_cycle.add_control(v, eva, CTL_OF[n])
        C.rate(v, eva, residual=res, expected=exp)
    if year == 2024:
        plan(v, "EVA-2024-001", "Pemindaian berkas masuk di loket", "2024-09-30", "SCAN-01", "Pemindaian berkas masuk", budget=15000000)
        C.plan(v, "done", "PLN-001", evidence="BA serah terima pemindai")
    else:
        plan(v, "EVA-2025-003", "Verifikasi ganda otomatis di aplikasi pembayaran", "2025-10-31", "VER-02", "Verifikasi ganda otomatis", budget=40000000)
        C.plan(v, "done", "PLN-002", evidence="Laporan uji aplikasi")
        plan(v, "EVA-2025-004", "Pelatihan penyusunan bukti belanja", "2025-11-30", "LAT-04", "Pelatihan bukti belanja", "korektif", 8000000)
    gv_close.open_period(v)
    for n, vals in VALUES[year].items():
        C.rate(v, f"EVA-{year}-{n:03d}", actual=vals[3])
    return gv_close.close_year(v, year)


def build(folder: Path) -> Vault:
    C.init(str(folder), "Instansi Demo", 2024)
    v = Vault(folder)
    new = lambda ent, *pairs: C.new(v, ent, list(pairs))
    new("matriks", "title=Matriks risiko 5x5 Instansi Demo", "max_likelihood=5", "max_impact=5")
    C.matrix(v, "activate", "MTX-001")
    for y in (2024, 2025, 2026):
        C.appetite(v, "MTX-001", y, 9)
    m = v.get("MTX-001")
    from gv_notes import make_table, set_section
    m.body = set_section(m.body, "Label kemungkinan", make_table(["Level", "Label"], [[1, "Sangat jarang"], [2, "Jarang"], [3, "Mungkin"], [4, "Sering"], [5, "Hampir pasti"]]))
    m.body = set_section(m.body, "Label dampak", make_table(["Level", "Label"], [[1, "Tidak signifikan"], [2, "Kecil"], [3, "Sedang"], [4, "Besar"], [5, "Sangat besar"]]))
    m.body = set_section(m.body, "Kriteria dampak", make_table(["Kategori", "Level", "Uraian"], [
        ["Finansial", 3, "Kerugian Rp50 juta sampai Rp200 juta (contoh)"], ["Finansial", 5, "Kerugian di atas Rp1 miliar (contoh)"],
        ["Gangguan Layanan", 3, "Layanan terhenti 1 sampai 3 hari kerja (contoh)"], ["Reputasi", 4, "Diberitakan media regional (contoh)"]]))
    v.save(m)

    new("mandat", "title=Peraturan Instansi Demo tentang Pelayanan Perizinan (fiktif)", "source=Contoh untuk demonstrasi")
    new("sasaran", "title=Layanan perizinan selesai tepat waktu", "mandate=MND-001")
    new("sasaran", "title=Pengelolaan keuangan yang akuntabel", "mandate=MND-001")
    new("indikator", "title=Persentase izin selesai sesuai standar waktu", "objective=SAS-001", "unit=%", "target=95")
    new("indikator", "title=Jumlah temuan pemeriksaan keuangan yang berulang", "objective=SAS-002", "unit=temuan", "target=0")
    new("proses", "title=Pelayanan perizinan", "owner=Bagian Pelayanan", "indicators=IND-001")
    new("proses", "title=Pembayaran dan pertanggungjawaban belanja", "owner=Bagian Keuangan", "indicators=IND-002")
    new("proses", "title=Pengelolaan arsip dokumen", "owner=Bagian Umum", "indicators=IND-001")
    risks = [("Berkas permohonan izin hilang saat berpindah antarbagian", 1, 1), ("Izin terbit melewati batas waktu standar", 1, 1),
             ("Tagihan penyedia dibayar dua kali", 2, 2), ("Bukti pertanggungjawaban belanja tidak lengkap saat diperiksa", 2, 2),
             ("Dokumen arsip rusak di ruang penyimpanan", 3, 1)]
    for n, (title, proc, ind) in enumerate(risks, 1):
        new("risiko", f"title={title}")
        new("pasang", f"risk=RSK-{n:03d}", f"process=PRS-{proc:03d}", f"indicator=IND-{ind:03d}")
    new("kontrol", "title=Buku register berkas masuk dan keluar", "control_type=detektif")
    new("kontrol", "title=Verifikasi ganda sebelum pembayaran", "control_type=preventif")
    new("kontrol", "title=Daftar periksa kelengkapan bukti", "control_type=preventif")
    for n in range(1, 6):
        new("evaluasi", f"pre=PRE-{n:03d}")
    for n, d, i in ((1, "2024-03-12", 3), (1, "2024-08-02", 4)):
        new("insiden", f"pre=PRE-{n:03d}", f"date={d}", "title=Berkas hilang di loket", f"impact={i}")
    year_cycle(v, 2024)
    new("insiden", "pre=PRE-001", "date=2025-05-06", "title=Berkas hilang di loket", "impact=3")
    new("insiden", "pre=PRE-003", "date=2025-09-17", "title=Tagihan terbayar ganda", "impact=4")
    year_cycle(v, 2025)

    # 2026, the working year, left open: controls that did not come from a DONE plan are installed again, values re-rated
    v = Vault(folder)
    for n in range(1, 6):
        eva = f"EVA-2026-{n:03d}"
        if CTL_OF[n] not in [r["control"] for r in gv_cycle.ecm_rows(v.get(eva))]:
            gv_cycle.add_control(v, eva, CTL_OF[n])
    C.rate(v, "EVA-2026-001", residual="2x4", expected="1x4")
    C.rate(v, "EVA-2026-002", residual="3x3")
    C.rate(v, "EVA-2026-003", residual="3x5")
    C.rate(v, "EVA-2026-004", residual="2x3")
    C.rate(v, "EVA-2026-005", residual="2x3", expected="1x3")
    plan(v, "EVA-2026-001", "Perluasan pemindaian ke semua loket", "2026-12-15", "SCAN-05", "Pemindaian semua loket", budget=22000000)
    C.plan(v, "start", "PLN-004")
    plan(v, "EVA-2026-003", "Rekonsiliasi harian tagihan sebelum pembayaran", "2026-12-20", "REK-06", "Rekonsiliasi harian tagihan", "detektif", 5000000)
    plan(v, "EVA-2026-005", "Perbaikan ruang arsip dan pengatur kelembapan", "2026-08-31", "RUANG-03", "Ruang arsip standar", budget=30000000)
    C.plan(v, "done", "PLN-006", evidence="Foto dan BA pekerjaan")
    for pre, d, t, i in ((1, "2026-02-12", "Berkas hilang di loket 2", 3), (1, "2026-05-20", "Berkas tertukar antarbagian", 2),
                         (1, "2026-09-03", "Berkas hilang saat dipindah", 3), (3, "2026-04-14", "Tagihan terbayar ganda", 4),
                         (3, "2026-08-30", "Tagihan terbayar ganda lagi", 5), (2, "2026-06-01", "Izin terlambat 9 hari", 2)):
        new("insiden", f"pre=PRE-{pre:03d}", f"date={d}", f"title={t}", f"impact={i}")

    kri_rows = [("RSK-001", "Berkas hilang per bulan", "kasus/bulan", "LEADING", "higher_is_worse", "monthly", 2, 4, [1, 2, 2, 3]),
                ("RSK-002", "Izin melewati batas waktu", "%", "LEADING", "higher_is_worse", "monthly", 15, 25, [8, 12, 22, 22]),
                ("RSK-003", "Tagihan dibayar tanpa verifikasi ganda", "kasus/bulan", "LEADING", "higher_is_worse", "monthly", 1, 3, [0, 1, 0, 0]),
                ("RSK-005", "Arsip tersimpan sesuai standar", "%", "LEADING", "lower_is_worse", "monthly", 85, 70, [90, 88, 82, 82])]
    for n, (risk, title, unit, typ, direction, freq, amber, red, vals) in enumerate(kri_rows, 1):
        new("kri", f"risk={risk}", f"title={title}", f"unit={unit}", f"kri_type={typ}", f"direction={direction}", f"frequency={freq}")
        gv_kri.change_threshold(v, f"KRI-{n:03d}", amber, red, "Penetapan awal oleh pemilik risiko")
        for k, val in enumerate(vals):
            gv_kri.add_reading(v, f"KRI-{n:03d}", val, f"2026-{7 + k:02d}-28")
    gv_kri.change_threshold(v, "KRI-002", 10, 20, "Standar waktu layanan diperketat pada semester kedua")

    bow = [{"type": "cause", "description": "Berkas dipindah tanpa tanda terima", "category": "Kebijakan", "children": [
              {"description": "Tidak ada prosedur serah terima berkas antarbagian", "category": "Kebijakan"}]},
           {"type": "cause", "description": "Petugas menumpuk berkas di meja", "category": "Kelalaian Manusia"},
           {"type": "impact", "description": "Pemohon harus mengajukan ulang", "category": "Gangguan Layanan"},
           {"type": "impact", "description": "Keluhan pemohon di media sosial", "category": "Reputasi"}]
    gv_draft.accept(v, gv_draft.create(v, "bowtie", "RSK-001", bow).id)
    gv_draft.accept(v, gv_draft.create(v, "bowtie", "RSK-003", [
        {"type": "cause", "description": "Faktur yang sama diinput dua kali", "category": "Kelalaian Manusia"},
        {"type": "impact", "description": "Kelebihan pembayaran kepada penyedia", "category": "Finansial"}]).id)
    gv_draft.create(v, "bowtie", "RSK-002", [{"type": "cause", "description": "Antrean berkas menumpuk di meja verifikator", "category": "Kelalaian Manusia"},
                                             {"type": "impact", "description": "Pemohon kehilangan peluang usaha", "category": "Finansial"}],
                    "Usulan AI untuk ditinjau: belum ada yang diterima.")
    gv_draft.create(v, "kri", "RSK-004", [{"title": "Belanja tanpa bukti lengkap", "what_measured": "Jumlah dokumen belanja bulan ini yang ditolak verifikator",
                                          "unit": "dokumen/bulan", "kri_type": "LEADING", "direction": "higher_is_worse", "frequency": "monthly",
                                          "watch": "Pelaksana kegiatan tidak memakai daftar periksa", "rationale": "Penolakan dokumen adalah tanda awal bukti tidak lengkap"}],
                    "Usulan AI untuk ditinjau: ambang sengaja kosong.")
    new("laporan", "title=Pengunjung melapor berkas izinnya tidak ditemukan di loket 2", "reporter=Warga (anonim)", "date=2026-11-10")
    new("laporan", "title=Berkas hilang di loket 2 pada bulan September", "reporter=Petugas loket", "date=2026-09-04", "status=APPROVED", "risk=RSK-001")
    gv_sim.simulate(v, "EVA-2026-001", 10000, 75, seed=2026)
    gv_sim.simulate(v, "EVA-2026-003", 10000, 75, seed=2026)
    gv_report.write_dashboard(v, gv_report.status(v))
    for y in (2025, 2026):
        gv_report.report(v, y)
    return v


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    folder = Path(sys.argv[1])
    if folder.exists() and any(folder.iterdir()):
        if "--force" not in sys.argv:
            print(f"{folder} sudah ada; pakai --force untuk membuat ulang")
            return 1
        for child in folder.iterdir():  # clear the contents, not the folder (it may be open in Obsidian or a shell)
            shutil.rmtree(child) if child.is_dir() else child.unlink()
    v = build(folder)
    bad = [f for f in gv_check.check(Vault(folder)) if f[0] == "ERROR"]
    print(f"Vault demo dibuat di {folder}: {len(v.notes)} catatan, {len(bad)} error pada check")
    for f in bad:
        print(" ", f)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
