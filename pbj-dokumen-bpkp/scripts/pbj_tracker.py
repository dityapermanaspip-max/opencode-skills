"""The project tracker: one Markdown note (``proyek.md``) per contract, readable and editable in Obsidian.

Layout of the note:
  front matter  flat ``key: "value"`` lines; the keys are the SAME vocabulary the HILDA templates use
                (nama_paket, nomor_spk, nilai_kontrak, tanggal_mulai ...), so one fact is typed once.
  ## Progres fisik   weekly plan/actual table (deviation and the critical test are recomputed on save)
  ## Dokumen         one row per generated or registered document
  ## Catatan         dated log lines
Sections the person adds by hand are kept as they are. Values are JSON-quoted strings, which is valid
YAML, so Obsidian shows them as properties.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from pbj_derived import parse_amount
from pbj_progress import evaluate, row_label

FILE = "proyek.md"
META = ("tipe", "metode", "status_kontrak", "jenis_pengadaan")
JENIS = ("konstruksi", "barang", "jasa_lainnya", "konsultansi")
PROGRESS_COLS = ["Pekan", "Mulai", "Selesai", "Rencana (%)", "Realisasi (%)", "Deviasi (%)", "Kriteria kritis"]
DOC_COLS = ["Template", "Naskah", "Nomor", "Tanggal", "Status", "Berkas"]
STATUSES = ("draf", "ditandatangani", "dikirim", "selesai", "batal")
KNOWN = ("Progres fisik", "Dokumen", "Catatan")


def _cell(value) -> str:
    return str(value).replace("|", "/").replace("\n", " ").strip()


def _table(cols: list[str], rows: list[list[str]]) -> list[str]:
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    return lines + ["| " + " | ".join(_cell(c) for c in row) + " |" for row in rows]


def _rows(lines: list[str]) -> list[list[str]]:
    out = []
    for line in lines:
        line = line.strip()
        if line.startswith("|") and not re.fullmatch(r"\|[\s:|-]+\|", line):
            out.append([c.strip() for c in line.strip("|").split("|")])
    return out[1:]  # first row is the header


def _num(text: str, where: str) -> float:
    """A number from a hand-editable table cell: 85, 85,5 and 85% all mean the same."""
    value = parse_amount(str(text).strip().rstrip("%").strip())
    if value is None:
        raise SystemExit(f"proyek.md: {where} '{text}' bukan angka (tulis 85 atau 85,5)")
    return value


class Project:
    def __init__(self, path: Path):
        self.path = path
        self.data: dict[str, str] = {"tipe": "proyek-pbj"}
        self.progress: list[dict] = []
        self.docs: list[dict] = []
        self.notes: list[str] = []
        self.sections: list[tuple[str | None, list[str]]] = []  # body in order, for hand-written sections

    # ------------------------------------------------------------------ io
    @classmethod
    def find(cls, folder: Path) -> Project:
        path = folder / FILE
        if not path.is_file():
            raise SystemExit(f"{path} not found. Run `pbj.py init` in the project folder first.")
        return cls.load(path)

    @classmethod
    def load(cls, path: Path) -> Project:
        project = cls(path)
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        body = text
        if text.startswith("---\n"):
            head, _, body = text[4:].partition("\n---\n")
            for line in head.split("\n"):
                key, sep, value = line.partition(":")
                if not sep or not key.strip():
                    continue
                value = value.strip()
                project.data[key.strip()] = json.loads(value) if value.startswith('"') else value.strip("'")
        heading, chunk = None, []
        for line in body.split("\n"):
            if line.startswith("## "):
                project.sections.append((heading, chunk))
                heading, chunk = line[3:].strip(), []
            else:
                chunk.append(line)
        project.sections.append((heading, chunk))
        for name, lines in project.sections:
            if name == "Progres fisik":
                for r in _rows(lines):
                    if len(r) >= 5:
                        week = _num(r[0], f"pekan '{r[0]}'")
                        if week != int(week) or week < 1:
                            raise SystemExit(f"proyek.md: pekan '{r[0]}' harus bilangan bulat mulai 1")
                        project.progress.append({"pekan": int(week), "mulai": r[1], "selesai": r[2], "rencana": _num(r[3], f"pekan {r[0]}: Rencana (%)"), "realisasi": _num(r[4], f"pekan {r[0]}: Realisasi (%)")})
            elif name == "Dokumen":
                for r in _rows(lines):
                    if len(r) >= 6:
                        link = re.search(r"\[\[(.+?)\]\]", r[5])
                        project.docs.append({"template": r[0], "naskah": r[1], "nomor": r[2], "tanggal": r[3], "status": r[4], "berkas": link.group(1) if link else r[5]})
            elif name == "Catatan":
                project.notes = [ln.rstrip() for ln in lines if ln.strip()]
        return project

    def save(self) -> None:
        front = ["---"] + [f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in self.data.items()] + ["---"]
        generated = {
            "Progres fisik": _table(PROGRESS_COLS, [[r["pekan"], r["mulai"], r["selesai"], f"{r['rencana']:g}", f"{r['realisasi']:g}", f"{evaluate(r['rencana'], r['realisasi'])['deviasi']:g}", row_label(r)] for r in self.progress]),
            "Dokumen": _table(DOC_COLS, [[d["template"], d["naskah"], d["nomor"], d["tanggal"], d["status"], f"[[{d['berkas']}]]" if d["berkas"] else ""] for d in self.docs]),
            "Catatan": self.notes,
        }
        body: list[str] = []
        seen = set()
        for name, lines in self.sections or [(None, [f"# {self.data.get('nama_paket', 'Proyek')}", "", "Dicatat dengan skill pbj-dokumen-bpkp. Nilai turunan (deviasi, status kritis) dihitung ulang oleh `pbj.py`; sisanya boleh disunting langsung.", ""])]:
            if name in generated:
                seen.add(name)
                body += [f"## {name}", ""] + generated[name] + [""]
            else:
                body += ([f"## {name}"] if name else []) + [ln for ln in lines]
        for name in KNOWN:
            if name not in seen:
                body += [f"## {name}", ""] + generated[name] + [""]
        text = "\n".join(front) + "\n" + "\n".join(body).rstrip("\n") + "\n"
        self.path.write_text(text, encoding="utf-8")

    # --------------------------------------------------------------- edits
    def set(self, key: str, value: str) -> None:
        self.data[key] = value

    def add_progress(self, row: dict) -> bool:
        """Insert or replace the row of that week; True when it replaced one."""
        for i, existing in enumerate(self.progress):
            if existing["pekan"] == row["pekan"]:
                self.progress[i] = row
                return True
        self.progress.append(row)
        self.progress.sort(key=lambda r: r["pekan"])
        return False

    def add_doc(self, doc: dict) -> None:
        self.docs.append(doc)

    def note(self, text: str) -> None:
        self.notes.append(f"- {date.today().isoformat()}: {text}")
