"""Builds examples/demo-diskompen from the facts in demo_diskompen_data.py (a fictional LKjIP 2025 of a district communications office).
Usage: python -P scripts/make_demo_diskompen.py <folder> [--force]. Context, risks, bowtie and KRI go in as drafts a person accepts;
the ratings are illustrative proposals and say so in the vault. Everything goes through the engine, so the result passes `check`."""

from __future__ import annotations

import calendar
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import demo_diskompen_data as D  # noqa: E402
import gv_check  # noqa: E402
import gv_cmds as C  # noqa: E402
import gv_cycle  # noqa: E402
import gv_draft  # noqa: E402
import gv_kri  # noqa: E402
import gv_pdf  # noqa: E402
import gv_report  # noqa: E402
import gv_sim  # noqa: E402
from gv_notes import make_table, set_section  # noqa: E402
from gv_vault import Vault  # noqa: E402

NOTE = """
## Catatan demo (baca dahulu)

Vault ini dibangun dari dokumen fiktif "Laporan Kinerja Instansi Pemerintah (LKjIP) 2025 Dinas Komunikasi dan Penerangan Kabupaten Tirta
Sembada". Dokumennya tidak disertakan di repositori. Yang berasal dari dokumen dan yang bukan:

- **Fakta dari dokumen**: sasaran, indikator, target, realisasi, kejadian, bulan, angka ketersediaan layanan per bulan, rencana perbaikan
  pada Bab IV. Nomor halaman ada pada deskripsi risiko.
- **Usulan penyusun demo (contoh, bukan penilaian Dinas)**: nilai inheren, residual dan ekspektasi, efektivitas kontrol, level dampak
  insiden menurut kriteria contoh, batas appetite 14 (batas atas zona MODERATE), ambang KRI (kuning 99,50 mengikuti target PK; merah 98,00 dipakai dokumen untuk
  menyebut bulan terburuk) dan alasan penilaian pada tiap evaluasi.
- **Tanggal**: rencana yang tanggalnya tidak disebut dokumen diberi 2026-12-31 sementara (tertulis pada catatan rencana). Insiden
  ketersediaan bertanggal akhir bulan karena dokumen hanya menyebut bulan.
- **Tidak dimasukkan**: 14 insiden keamanan informasi (5 phishing, 4 malware, 3 pengubahan tampilan, 2 akses tidak sah) karena dokumen
  hanya memberi jumlah, tanpa tanggal dan dampak per kejadian. Tambahkan dengan `new insiden` bila datanya ada.
- **Belum dikerjakan**: ACTUAL, periode tutup buku dan tren. Coba `open-period`, isi ACTUAL, lalu `close`.

Alur yang dipakai: konteks, risiko, bowtie dan KRI masuk sebagai draf (`_Draft/`) yang diterima atau ditolak seseorang; nilai dan
status dihitung mesin (`check` dan `status` bisa dijalankan kapan saja).
"""


def reset(folder: Path) -> None:
    for child in folder.iterdir():  # clear the contents, not the folder (it may be open in Obsidian or a shell)
        shutil.rmtree(child) if child.is_dir() else child.unlink()


def ind_id(code: str) -> str:
    return f"IND-{[i[0] for i in D.INDICATORS].index(code) + 1:03d}"


def context_items() -> list[dict]:
    items = [{"level": "mandat", "title": t, "source": s, "ref": r} for r, t, s in D.MANDATES]
    items += [{"level": "sasaran", "title": t, "parent": "m2", "ref": f"s{n}"} for n, t in enumerate(D.OBJECTIVES)]
    items += [{"level": "indikator", "title": f"{c} {t}", "parent": f"s{o}", "unit": u, "target": tg, "ref": f"i{c}"}
              for c, o, t, u, tg in D.INDICATORS]
    items += [{"level": "proses", "title": t, "owner": ow, "indicators": [f"i{c}" for c in ind], "ref": k} for k, t, ow, ind in D.PROCESSES]
    return items


def matrix(v: Vault) -> None:
    C.new(v, "matriks", ["title=Matriks risiko 5x5 Dinas Komunikasi dan Penerangan (contoh)", "max_likelihood=5", "max_impact=5"])
    C.matrix(v, "activate", "MTX-001")
    C.appetite(v, "MTX-001", 2025, 14)
    m = v.get("MTX-001")
    lab = lambda names: make_table(["Level", "Label"], [[i, n] for i, n in enumerate(names, 1)])
    m.body = set_section(m.body, "Label kemungkinan", lab(["Sangat jarang", "Jarang", "Mungkin", "Sering", "Hampir pasti"]))
    m.body = set_section(m.body, "Label dampak", lab(["Tidak signifikan", "Kecil", "Sedang", "Besar", "Sangat besar"]))
    rows = [["Gangguan Layanan", lvl, f"{text} (contoh)"] for lvl, text in D.DOWNTIME_CRITERIA]
    rows += [["Reputasi", 3, "Diberitakan media daring lokal (contoh)"], ["Reputasi", 5, "Diberitakan media nasional (contoh)"]]
    m.body = set_section(m.body, "Kriteria dampak", make_table(["Kategori", "Level", "Uraian"], rows))
    v.save(m)


def build(folder: Path) -> Vault:
    C.init(str(folder), D.ORG, D.YEAR)
    v = Vault(folder)
    matrix(v)
    gv_draft.accept(v, gv_draft.create(v, "konteks", None, context_items(), "Draf konteks dari LKjIP 2025 (Bab I, II dan Tabel 2.1).").id)
    ctl = {}
    for key, (title, kind) in D.CONTROLS.items():
        C.new(v, "kontrol", [f"title={title}", f"control_type={kind}"])
        ctl[key] = v.all("kontrol")[-1].id
    pre, rsk = {}, {}
    risks_by_process = {k: [r for r in D.RISKS if r[1] == k] for k, *_ in D.PROCESSES}
    for n, (pkey, ptitle, owner, _ind) in enumerate(D.PROCESSES, 1):
        items = [{"title": r[3], "description": r[4], "indicator": ind_id(r[2])} for r in risks_by_process[pkey]]
        if pkey == "ppid":  # a proposal the person rejects: it stays in the process note as 'Saran ditolak'
            items.append({"title": "Sengketa informasi publik diajukan ke Komisi Informasi", "indicator": ind_id("1.2"),
                          "description": "Usulan AI tanpa dasar di dokumen."})
        drf = gv_draft.create(v, "risiko", f"PRS-{n:03d}", items, "Usulan risiko dari LKjIP 2025; nomor halaman ada pada deskripsi.")
        made = gv_draft.accept(v, drf.id, list(range(1, len(risks_by_process[pkey]) + 1)))
        assert not any("GAGAL" in m for m in made), made
        if pkey == "ppid":
            gv_draft.reject(v, drf.id, [len(items)], "Dokumen tidak mencatat sengketa informasi; 5 permohonan ditolak karena dikecualikan.")
        for r, (rid, pid) in zip(risks_by_process[pkey], zip(made[0::2], made[1::2])):
            rsk[r[0]], pre[r[0]] = rid, pid
    owner_of = {k: o for k, _t, o, _i in D.PROCESSES}
    eva = {}
    for key, pkey, code, title, desc, inh, res, exp, ctls, why, plan in D.RISKS:
        C.new(v, "evaluasi", [f"pre={pre[key]}"])
        eva[key] = f"EVA-{D.YEAR}-{pre[key].split('-')[1]}"
        if res == "sim":  # the residual of this risk is the simulation's suggestion, which needs the incidents first
            availability_incidents(v, pre[key])
            gv_sim.simulate(v, eva[key], 10000, 75, seed=D.YEAR)
        C.rate(v, eva[key], inherent=inh)
        for ck, eff in ctls:
            gv_cycle.add_control(v, eva[key], ctl[ck], eff)
        levels = {k: x for k, x in (("residual", res), ("expected", exp)) if x}
        if levels:
            C.rate(v, eva[key], **levels)
        note = v.get(eva[key])
        note.body = set_section(note.body, "Dasar penilaian (ilustrasi)", f"{why}\n\nNilai ini usulan penyusun demo, bukan penilaian Dinas.")
        v.save(note)
        if plan:
            action, target, pcode, ptitle2, kind, pnote = plan
            C.new(v, "rencana", [f"evaluation={eva[key]}", f"action={action}", f"pic={owner_of[pkey]}", f"target_date={target}",
                                 f"new_control_code={pcode}", f"new_control_title={ptitle2}", f"new_control_type={kind}", f"notes={pnote}"])
    kri(v, rsk)
    bowtie(v, rsk)
    v.cfg_note.body += NOTE
    v.save_config()
    gv_report.write_dashboard(v, gv_report.status(v))
    gv_report.report(v, D.YEAR)
    print(gv_pdf.write_pdf(v, D.YEAR)[2])  # the formatted report; the HTML stays when no browser is installed
    return v


def availability_incidents(v: Vault, pre: str) -> None:
    """One incident per month that missed the 99,50% target; the impact level comes from the example downtime criteria."""
    for name, _days, pct, hours in D.AVAIL:
        mo = D.MONTH_NO[name]
        C.new(v, "insiden", [f"pre={pre}", f"date={D.YEAR}-{mo}-{calendar.monthrange(D.YEAR, int(mo))[1]:02d}",
                             f"title=Ketersediaan {name} {pct}% ({str(hours).replace('.', ',')} jam henti)", f"impact={D.downtime_level(hours)}"])


def kri(v: Vault, rsk: dict) -> None:
    C.new(v, "kri", [f"risk={rsk['avail']}", "title=Ketersediaan layanan jaringan dan pusat data", "unit=%", "kri_type=LAGGING",
                     "direction=lower_is_worse", "frequency=monthly", "what_measured=Rata-rata ketersediaan layanan per bulan menurut log pemantauan"])
    gv_kri.change_threshold(v, "KRI-001", 99.5, 98.0, "Contoh demo: kuning = target PK 2025 (99,50%); merah = 98,00%, batas yang dipakai LKjIP hal. 12")
    for mo, pct in D.AVAIL_ALL:
        gv_kri.add_reading(v, "KRI-001", pct, f"{D.YEAR}-{mo}-{calendar.monthrange(D.YEAR, int(mo))[1]:02d}")
    both = {"kri_type": "LEADING", "direction": "lower_is_worse", "frequency": "monthly"}
    ppid = {"title": "Informasi berkala pada portal PPID yang mutakhir", "unit": "%", **both,
            "what_measured": "Persentase jenis informasi berkala yang diperbarui pada triwulan berjalan",
            "watch": "PD tidak menyampaikan pembaruan berkala", "rationale": "Laporan menyebut informasi berkala belum memadai (hal. 10). Belum ada data pembacaan."}
    data = {"title": "Dataset statistik sektoral pada portal Satu Data", "unit": "dataset", **both,
            "what_measured": "Jumlah dataset yang tersedia pada portal", "watch": "PD produsen data terlambat menyampaikan data",
            "rationale": "Hanya dua pembacaan tahunan dari dokumen (62 pada 2024, 74 pada 2025, target 120). Ambang sengaja kosong.", "amber": 100, "red": 90}
    spend = {"title": "Serapan anggaran kegiatan per triwulan", "unit": "%", **both, "what_measured": "Realisasi dibanding pagu kegiatan",
             "watch": "Pengadaan tidak menghasilkan penyedia", "rationale": "Usulan AI belum ditinjau; ambang sengaja kosong."}
    gv_draft.accept(v, gv_draft.create(v, "kri", rsk["ppid"], [ppid], "Usulan KRI: ambang kosong.").id)
    gv_draft.accept(v, gv_draft.create(v, "kri", rsk["dataset"], [data], "Usulan KRI: ambang dalam draf diabaikan.").id)
    gv_draft.create(v, "kri", rsk["anggaran"], [spend], "Usulan AI untuk ditinjau: belum ada yang diterima.")
    k = v.all("kri")[-1].id
    gv_kri.add_reading(v, k, 62, f"{D.YEAR - 1}-12-31")
    gv_kri.add_reading(v, k, 74, f"{D.YEAR}-12-31")


def bowtie(v: Vault, rsk: dict) -> None:
    for key in ("ppid", "avail", "dataset"):
        items = [{"type": t, "description": d, "category": c} for t, d, c in D.BOWTIE[key]]
        gv_draft.accept(v, gv_draft.create(v, "bowtie", rsk[key], items, "Usulan penyebab dan dampak dari LKjIP 2025.").id)
    items = [{"type": t, "description": d, "category": c} for t, d, c in D.BOWTIE["server"]]
    drf = gv_draft.create(v, "bowtie", rsk["server"], items, "Usulan; butir ke-3 tidak punya dasar di dokumen.")
    gv_draft.accept(v, drf.id, [1, 2])
    gv_draft.reject(v, drf.id, [3], "Tidak ada dasar di dokumen: kehilangan data tidak disebut.")
    items = [{"type": t, "description": d, "category": c} for t, d, c in D.BOWTIE["insiden"]]
    drf = gv_draft.create(v, "bowtie", rsk["insiden"], items, "Usulan; butir 2 dan 4 belum ditinjau.")
    gv_draft.accept(v, drf.id, [1, 3])


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    folder = Path(sys.argv[1])
    if folder.exists() and any(folder.iterdir()):
        if "--force" not in sys.argv:
            print(f"{folder} sudah ada; pakai --force untuk membuat ulang")
            return 1
        reset(folder)
    v = build(folder)
    bad = [f for f in gv_check.check(Vault(folder)) if f[0] == "ERROR"]
    print(f"Vault demo dibuat di {folder}: {len(v.notes)} catatan, {len(bad)} error pada check")
    for f in bad:
        print(" ", f)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
