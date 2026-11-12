"""The template catalog the skill ships (a generated copy of the HILDA pack) and what to say about it.

``assets/manifest.json`` and ``assets/templates/*.docx`` are written by ``sync_templates.py`` from the HILDA
pack ``pbj-pengadaan-langsung-2026``; never edit them by hand. The pack builders in the hilda-be1
repository are the single source of the wording.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from pbj_derived import parse_derived_key

SKILL_DIR = Path(__file__).resolve().parent.parent
ASSETS = SKILL_DIR / "assets"
MANIFEST_PATH = ASSETS / "manifest.json"

OFFICIAL = "formulir resmi LKPP"
OWNER = "formulir pemilik (BPKP) atau model LKPP"
AUTHORED = "disusun dari SSUK dan peraturan; perlu reviu pemilik/hukum sebelum dipakai"
# Everything not listed here is AUTHORED. The SPMK and the four sanction documents reproduce official
# formats (SPMK: Lampiran Peraturan LKPP 12/2021; sanctions: Peraturan LKPP 4/2021 Bagian VIII a-d).
ASAL = {
    "spmk": OFFICIAL,
    "usulan_sanksi": OFFICIAL + " (LKPP 4/2021; mendahului Perpres 46/2025, periksa)",
    "pemberitahuan_sanksi": OFFICIAL + " (LKPP 4/2021; mendahului Perpres 46/2025, periksa)",
    "sk_sanksi": OFFICIAL + " (LKPP 4/2021; mendahului Perpres 46/2025, periksa)",
    "sk_sanksi_temuan": OFFICIAL + " (LKPP 4/2021; mendahului Perpres 46/2025, periksa)",
    **{k: OWNER for k in ("nota_dinas", "kak", "dokumen_pemilihan", "ba_reviu", "sppbj", "spk")},
}

WHEN = {
    "pengadaan_langsung": "Kontrak baru dengan metode Pengadaan Langsung (konstruksi sampai Rp400 juta, Perpres 46/2025 Pasal 38): dari nota dinas sampai serah terima.",
    "kontrak_kritis": "Deviasi melewati batas kritis (periode I lebih dari 10%, periode II lebih dari 5%): SCM tahap I-III dan Surat Peringatan I-III.",
    "perubahan_kontrak": "Perubahan harga, waktu atau lingkup: addendum (penambahan nilai paling banyak 10%, Perpres Pasal 54).",
    "keadaan_kahar": "Keadaan kahar: penghentian kontrak, lalu addendum (perpanjangan) atau pengakhiran.",
    "pemutusan_kontrak": "Pemutusan kontrak oleh PPK: tiga surat peringatan, pemberitahuan rencana (14 hari kalender), pemutusan, pencairan jaminan, permintaan penunjukan langsung lanjutan.",
    "sanksi_daftar_hitam": "Usulan dan penetapan sanksi daftar hitam setelah pemutusan karena kesalahan penyedia (rincian sanksi di tangan LKPP).",
    "pembatalan_sppbj": "SPPBJ dibatalkan sebelum kontrak ditandatangani (penyedia gagal atau anggaran tidak cukup), lalu SPPBJ ke pemenang cadangan.",
}

_manifest: dict | None = None


def manifest() -> dict:
    global _manifest
    if _manifest is None:
        if not MANIFEST_PATH.is_file():
            raise SystemExit(f"{MANIFEST_PATH} is missing: run scripts/sync_templates.py first")
        _manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return _manifest


def templates() -> dict[str, dict]:
    return {t["key"]: t for t in manifest()["templates"]}


def template(key: str) -> dict:
    found = templates().get(key)
    if not found:
        raise SystemExit(f"unknown template '{key}'. Known: {', '.join(sorted(templates()))}")
    return found


def template_path(key: str) -> Path:
    return ASSETS / "templates" / template(key)["file"]


FORM_SUFFIX = re.compile(r"\s*\((Rp|Rp, terbilang|terbilang|hari|tanggal, huruf|bulan|tahun|tahun, huruf|HURUF KAPITAL)\)\s*$")
FAMILY_KIND = {"number": "number", "date": "date", "text": "text"}
_vocabulary: dict[str, tuple[str, str]] | None = None


def vocabulary() -> dict[str, tuple[str, str]]:
    """Every typed (base) key with its label and kind. A key used only through derived forms
    (nilai_hps__rupiah) is a base key too: the person types the number once."""
    global _vocabulary
    if _vocabulary is None:
        labels, kinds = manifest()["placeholder_labels"], manifest()["placeholder_kinds"]
        vocab: dict[str, tuple[str, str]] = {}
        for key, text in labels.items():
            derived = parse_derived_key(key)
            if derived and derived[0] not in vocab:
                vocab[derived[0]] = (FORM_SUFFIX.sub("", text), FAMILY_KIND[derived[2]])
        for key, text in labels.items():
            if not parse_derived_key(key):
                vocab[key] = (text, kinds.get(key, "text"))
        _vocabulary = vocab
    return _vocabulary


def label(key: str) -> str:
    return manifest()["placeholder_labels"].get(key) or vocabulary().get(key, (key, "text"))[0]


def kind(key: str) -> str:
    return vocabulary().get(key, (key, "text"))[1]


def known_key(key: str) -> bool:
    return key in vocabulary()


def asal(key: str) -> str:
    return ASAL.get(key, AUTHORED)


def packages() -> dict[str, dict]:
    return {p["key"]: p for p in manifest()["package_templates"]}


def steps(package_key: str) -> list[dict]:
    """Ordered steps of a package with the template key each one uses."""
    package = packages().get(package_key)
    if not package:
        raise SystemExit(f"unknown package '{package_key}'. Known: {', '.join(packages())}")
    by_doc_type = {t["doc_type"]: t["key"] for t in manifest()["templates"] if t.get("default")}
    out = []
    for number, step in enumerate(package["steps"], 1):
        out.append(
            {
                "no": number,
                "name": step["name"],
                "template": by_doc_type.get(step["doc_type"]),
                "depends_on": step.get("depends_on"),
                "optional": bool(step.get("optional")),
            }
        )
    return out
