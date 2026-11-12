"""Offline self-test of the skill: python selftest.py  (exit code 0 = everything passed).

Uses synthetic data only. Run it after sync_templates.py or after changing any script."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from docx import Document  # noqa: E402

import pbj_catalog as catalog  # noqa: E402
import pbj_derived as d  # noqa: E402
import pbj_docx as docx  # noqa: E402
from pbj_fill import _base_keys  # noqa: E402
from pbj_progress import analyse, evaluate  # noqa: E402
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


def main() -> int:
    for test in (test_derived, test_templates, test_split_runs, test_progress_and_tracker):
        test()
    print("FAILED: " + ", ".join(failures) if failures else "all passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
