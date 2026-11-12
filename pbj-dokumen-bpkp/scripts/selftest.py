"""Offline self-test of the skill: python selftest.py  (exit code 0 = everything passed).

Uses synthetic data only. Run it after sync_templates.py or after changing any script."""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))

from docx import Document  # noqa: E402

import pbj_catalog as catalog  # noqa: E402
import pbj_cmds as cmds  # noqa: E402
import pbj_derived as d  # noqa: E402
import pbj_docx as docx  # noqa: E402
from pbj_fill import _base_keys  # noqa: E402
from pbj_progress import analyse, evaluate, number  # noqa: E402
from pbj_tracker import Project  # noqa: E402

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"  {detail}"))
    if not ok:
        failures.append(name)


def test_derived() -> None:
    check("terbilang", d.terbilang(155373000) == "seratus lima puluh lima juta tiga ratus tujuh puluh tiga ribu")
    check("seribu / satu juta", d.terbilang(1000) == "seribu" and d.terbilang(1_000_000) == "satu juta")
    check("rupiah", d.format_rupiah(155159568.32) == "Rp155.159.568,32")
    check("rupiah terbilang", d.rupiah_terbilang(155159568.32).endswith("rupiah dan tiga puluh dua sen"))
    check("parse amount", d.parse_amount("Rp155.373.000") == 155373000 and d.parse_amount("12.34.56") is None)
    check("date words", d.derive_value("2026-09-17", "hari", "date") == "Kamis" and d.derive_value("2026-09-17", "tahun_kata", "date") == "Dua Ribu Dua Puluh Enam")
    check("invalid date is empty", d.derive_value("2026-02-29", "hari", "date") == "")


def sample_value(key: str) -> str:
    return {"date": "2026-03-16", "number": "1500000"}.get(catalog.kind(key), f"Teks {key}")


def test_templates() -> None:
    bad = []
    for key in catalog.templates():
        keys = _base_keys(key)
        values = {k: sample_value(k) for k in keys}
        document = docx.open_docx(catalog.template_path(key))
        _, unknown = docx.fill_markers(document, lambda k: d.resolve(k, catalog.kind(k), values) or f"[{k}]")
        left = docx.marker_keys(document)
        text = "\n".join(t for _, t in docx.paragraph_texts(document))
        if unknown or left or any(f"[{k}]" in text for k in keys):  # the LKPP model itself has [..] prompts
            bad.append(key)
    check(f"all {len(catalog.templates())} templates fill without leftover markers", not bad, str(bad))


def test_split_runs() -> None:
    document = Document()
    p = document.add_paragraph()
    for chunk in ("Nomor ", "{{no", "mor_spk}}", " tanggal {{tanggal_spk__ha", "ri}}."):
        p.add_run(chunk)
    docx.fill_markers(document, lambda k: {"nomor_spk": "12/2026", "tanggal_spk__hari": "Senin"}.get(k))
    check("marker split over runs", document.paragraphs[0].text == "Nomor 12/2026 tanggal Senin.", document.paragraphs[0].text)
    p = document.add_paragraph("Nama: ______ dan ....... selesai")
    blanks = docx.list_blanks(document)
    docx.fill_blanks(document, {0: "A", 1: "B"})
    check("blanks by index", len(blanks) == 2 and document.paragraphs[1].text == "Nama: A dan B selesai", document.paragraphs[1].text)
    q = document.add_paragraph("Nama Paket:")
    check("insert after label", docx.insert_after(document, "Nama Paket:", " X") == 1 and q.text == "Nama Paket: X")


def test_progress_and_tracker() -> None:
    series = [(9, 15.54, 5.70), (10, 20.15, 6.26)]
    check("kritis threshold period I", [evaluate(r, a)["kritis"] for _, r, a in series] == [False, True])
    check("period II uses 5%", evaluate(80, 74)["kritis"] and not evaluate(80, 76)["kritis"])
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "proyek.md"
        project = Project(path)
        project.set("nama_paket", "Uji | paket")
        project.set("tanggal_mulai", "2026-08-04")
        project.set("jangka_waktu_hari", "150")
        project.add_progress({"pekan": 1, "mulai": "2026-08-04", "selesai": "2026-08-10", "rencana": 1.0, "realisasi": 1.0})
        project.add_progress({"pekan": 2, "mulai": "2026-08-11", "selesai": "2026-08-17", "rencana": 30.0, "realisasi": 2.0})
        project.add_doc({"template": "ba_scm", "naskah": "BA SCM", "nomor": "1", "tanggal": "2026-08-18", "status": "draf", "berkas": "dokumen/01_BA_SCM.docx"})
        project.note("uji")
        project.save()
        path.write_text(path.read_text(encoding="utf-8") + "\n## Ringkasan saya\n\nCatatan tulisan tangan.\n", encoding="utf-8")
        again = Project.load(path)
        again.save()
        reloaded = Project.load(path)
        check("tracker round trip", reloaded.data["nama_paket"] == "Uji | paket" and len(reloaded.progress) == 2 and reloaded.docs[0]["berkas"] == "dokumen/01_BA_SCM.docx")
        check("hand-written section kept", "Catatan tulisan tangan." in path.read_text(encoding="utf-8"))
        result = analyse(reloaded.data, reloaded.progress, reloaded.docs)
        check("analysis flags critical contract", result["last"]["kritis"] and result["first_critical"]["pekan"] == 2)
        check("SCM already recorded, no 'belum ada' advice", not any("Belum ada BA SCM" in a for a in result["advice"]))


def test_hand_edits() -> None:
    """A note edited in Obsidian is read as a person writes it: 8,5, 85%, free text under Catatan."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "proyek.md"
        path.write_text(
            '---\ntipe: "proyek-pbj"\nnama_paket: "Uji"\n---\n\n# Uji\n\n'
            "## Progres fisik\n\n"
            "| Pekan | Mulai | Selesai | Rencana (%) | Realisasi (%) | Deviasi (%) | Kriteria kritis |\n"
            "|---|---|---|---|---|---|---|\n"
            "| 1 | 2026-08-04 | 2026-08-10 | 10,5 | 8,25% | -2,25 | terlambat |\n\n"
            "## Dokumen\n\n| Template | Naskah | Nomor | Tanggal | Status | Berkas |\n|---|---|---|---|---|---|\n\n"
            "## Catatan\n\n- 2026-11-12: uji\n\nCatatan bebas yang ditulis tangan.\n",
            encoding="utf-8",
        )
        project = Project.load(path)
        row = project.progress[0]
        check("comma decimal and % parse", row["rencana"] == 10.5 and row["realisasi"] == 8.25, str(row))
        project.save()
        text = path.read_text(encoding="utf-8")
        check("free text under Catatan kept", "Catatan bebas yang ditulis tangan." in text)
        check("dated note kept once", text.count("- 2026-11-12: uji") == 1)
        check("number('1.500') reads 1500", number("1.500") == 1500 and d.parse_amount("1500.5") == 1500.5)
        check("number('nan') is None", number("nan") is None)

        bad = path.read_text(encoding="utf-8").replace("10.5", "10,x")
        path.write_text(bad, encoding="utf-8")
        try:
            Project.load(path)
            check("bad cell gives a readable error", False, "no exception")
        except SystemExit as exc:
            check("bad cell gives a readable error", "10,x" in str(exc) and "bukan angka" in str(exc), str(exc))


def test_progress_guards() -> None:
    rows = [
        {"pekan": 1, "mulai": "2026-01-01", "selesai": "2026-01-07", "rencana": 10, "realisasi": 8},
        {"pekan": 2, "mulai": "2026-01-08", "selesai": "2026-01-14", "rencana": 20, "realisasi": 15},
        {"pekan": 3, "mulai": "2026-01-15", "selesai": "2026-01-21", "rencana": 30, "realisasi": 22},
        {"pekan": 4, "mulai": "2026-01-22", "selesai": "2026-01-28", "rencana": 40, "realisasi": 28},
    ]
    data = {"tanggal_mulai": "2026-01-01", "tanggal_selesai": "2026-06-30", "jangka_waktu_hari": "181", "tahun_anggaran": "99999"}
    result = analyse(data, rows, [])
    check("absurd tahun_anggaran falls back", any("tidak masuk akal" in c for c in result["checks"]) and result.get("finish") is not None)


def test_cli_ceiling_and_doc_set() -> None:
    check("ceiling barang", cmds.pl_ceiling("barang") == (200_000_000, "Rp200.000.000 untuk barang"))
    check("ceiling konstruksi", cmds.pl_ceiling("konstruksi") == (400_000_000, "Rp400.000.000 untuk pekerjaan konstruksi"))
    check("ceiling unset", cmds.pl_ceiling(None) is None and cmds.pl_ceiling("") is None)

    def run(func, args) -> str:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            func(args)
        return out.getvalue()

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "proyek.md"
        project = Project(path)
        project.set("nama_paket", "Uji")
        project.set("metode", "Pengadaan Langsung")
        project.set("nilai_kontrak", "300000000")
        project.save()

        out = run(cmds.cmd_status, SimpleNamespace(folder=tmp))
        check("300 juta without jenis asks for both limits", "Rp400 juta untuk konstruksi" in out and "Rp200 juta untuk barang/jasa lainnya" in out, out)

        project.set("jenis_pengadaan", "barang")
        project.save()
        out = run(cmds.cmd_status, SimpleNamespace(folder=tmp))
        check("300 juta barang is flagged", "melebihi batas Pengadaan Langsung Rp200.000.000 untuk barang" in out, out)

        project.set("jenis_pengadaan", "konstruksi")
        project.save()
        out = run(cmds.cmd_status, SimpleNamespace(folder=tmp))
        check("300 juta konstruksi not flagged", "[periksa metode]" not in out, out)
        project.set("nilai_kontrak", "1000000000")
        project.save()
        out = run(cmds.cmd_replacement, SimpleNamespace(folder=tmp, realisasi=75.0))
        check("250 juta remainder konstruksi allowed", "Di bawah batas Pengadaan Langsung Rp400.000.000" in out, out)

        project.set("jenis_pengadaan", "barang")
        project.save()
        out = run(cmds.cmd_replacement, SimpleNamespace(folder=tmp, realisasi=75.0))
        check("250 juta remainder barang blocked", "Di atas batas Pengadaan Langsung Rp200.000.000 untuk barang" in out, out)

        project.set("jenis_pengadaan", "")
        project.save()
        out = run(cmds.cmd_replacement, SimpleNamespace(folder=tmp, realisasi=75.0))
        check("remainder unset states both limits", "Rp400 juta untuk konstruksi, Rp200 juta untuk barang/jasa lainnya" in out, out)

        project.add_doc({"template": "spk", "naskah": "SPK", "nomor": "01/2026", "tanggal": "", "status": "draf", "berkas": ""})
        project.save()
        run(cmds.cmd_doc, SimpleNamespace(folder=tmp, action="set", index=1, nomor="", tanggal=None, status=None, berkas=None, template=None, naskah=None))
        check("doc set clears a field", Project.load(path).docs[0]["nomor"] == "")
        run(cmds.cmd_doc, SimpleNamespace(folder=tmp, action="set", index=1, nomor=None, tanggal=None, status="selesai", berkas=None, template=None, naskah=None))
        reloaded = Project.load(path).docs[0]
        check("doc set keeps omitted fields", reloaded["nomor"] == "" and reloaded["status"] == "selesai")
        try:
            run(cmds.cmd_doc, SimpleNamespace(folder=tmp, action="set", index=1, nomor=None, tanggal="4 Agustus 2026", status=None, berkas=None, template=None, naskah=None))
            check("doc set rejects a non-ISO date", False, "no exception")
        except SystemExit as exc:
            check("doc set rejects a non-ISO date", "yyyy-mm-dd" in str(exc), str(exc))


def main() -> int:
    for test in (test_derived, test_templates, test_split_runs, test_progress_and_tracker, test_hand_edits, test_progress_guards, test_cli_ceiling_and_doc_set):
        test()
    print("FAILED: " + ", ".join(failures) if failures else "all passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
