"""The vault model: which kinds of note exist, where they live, and what their frontmatter fields mean.
Plain values live in memory (a link is just an id); the stored form wraps links as "[[ID]]" for Obsidian."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

CELL = re.compile(r"^\s*(\d+)\s*[xX]\s*(\d+)\s*$")
LINK = re.compile(r"^\s*\[\[(.+?)(?:\|.*)?\]\]\s*$")


@dataclass(frozen=True)
class F:
    name: str
    kind: str = "str"      # str int float bool date cell link:<entity> links:<entity> enum:A|B|C
    req: bool = False
    default: object = None


@dataclass(frozen=True)
class Entity:
    name: str
    prefix: str
    folder: str
    fields: tuple


def _enum(*vals) -> str:
    return "enum:" + "|".join(vals)


CONTROL_TYPES = ("preventif", "detektif", "korektif")
PLAN_STATUS = ("PLANNED", "IN_PROGRESS", "DONE", "NOT_REALISED")
CAUSE_CATEGORIES = ("Kebijakan", "Kelalaian Manusia", "Bencana", "Fraud", "Stakeholders")
IMPACT_CATEGORIES = ("Finansial", "Reputasi", "Hukum", "Gangguan Layanan")
EFFECTIVENESS = ("EFFECTIVE", "PARTIAL", "INEFFECTIVE")

_ENTITIES = [
    Entity("mandat", "MND", "00-Konteks/Mandat", (F("title", req=True), F("source"))),
    Entity("sasaran", "SAS", "00-Konteks/Sasaran", (F("title", req=True), F("mandate", "link:mandat", True))),
    Entity("indikator", "IND", "00-Konteks/Indikator",
           (F("title", req=True), F("objective", "link:sasaran", True), F("unit"), F("target"))),
    Entity("proses", "PRS", "00-Konteks/Proses",
           (F("title", req=True), F("owner"), F("indicators", "links:indikator", default=[]))),
    Entity("matriks", "MTX", "01-Matriks",
           (F("title", req=True), F("max_likelihood", "int", True), F("max_impact", "int", True))),
    Entity("risiko", "RSK", "02-Kamus/Risiko", (F("title", req=True), F("description"), F("active", "bool", default=True))),
    Entity("kontrol", "CTL", "02-Kamus/Kontrol",
           (F("title", req=True), F("control_type", _enum(*CONTROL_TYPES), True), F("code"))),
    Entity("pasang", "PRE", "03-Register",
           (F("risk", "link:risiko", True), F("process", "link:proses", True),
            F("indicator", "link:indikator", True), F("active", "bool", default=True))),
    Entity("evaluasi", "EVA", "04-Evaluasi",
           (F("pre", "link:pasang", True), F("fiscal_year", "int", True), F("matrix", "link:matriks", True),
            F("inherent", "cell"), F("residual", "cell"), F("expected", "cell"), F("actual", "cell"),
            F("active_type", _enum("INHERENT", "RESIDUAL", "EXPECTED")), F("active_cell", "cell"),
            F("trend", _enum("IMPROVING", "WORSENING", "STABLE")), F("closed", "date"),
            F("sim_suggestion", "cell"), F("sim_date", "date"))),
    Entity("rencana", "PLN", "05-Rencana",
           (F("evaluation", "link:evaluasi", True), F("action", req=True), F("pic", req=True),
            F("target_date", "date", True), F("budget", "float", default=0),
            F("status", _enum(*PLAN_STATUS), default="PLANNED"), F("new_control_code"), F("new_control_title"),
            F("new_control_type", _enum(*CONTROL_TYPES)), F("evidence"), F("notes"))),
    Entity("kri", "KRI", "06-KRI",
           (F("risk", "link:risiko", True), F("title", req=True), F("what_measured"), F("unit"),
            F("kri_type", _enum("LEADING", "LAGGING"), True), F("direction", _enum("higher_is_worse", "lower_is_worse"), True),
            F("frequency", _enum("daily", "weekly", "monthly"), True), F("watch"), F("amber", "float"), F("red", "float"),
            F("status", _enum("ACTIVE", "RETIRED"), default="ACTIVE"))),
    Entity("insiden", "INS", "07-Insiden",
           (F("pre", "link:pasang", True), F("date", "date", True), F("title", req=True), F("impact", "int", True),
            F("use_in_simulation", "bool", default=True), F("report", "link:laporan"))),
    Entity("laporan", "LAP", "07-Insiden/Laporan",
           (F("title", req=True), F("reporter"), F("date", "date", True),
            F("status", _enum("PENDING", "APPROVED", "IGNORED"), default="PENDING"), F("risk", "link:risiko"))),
    Entity("draft", "DRF", "_Draft",
           (F("kind", _enum("konteks", "risiko", "bowtie", "kri"), True), F("target"),
            F("status", _enum("DRAFT", "ACCEPTED", "PARTIAL", "REJECTED"), default="DRAFT"))),
]
ENTITIES = {e.name: e for e in _ENTITIES}
BY_PREFIX = {e.prefix: e for e in _ENTITIES}
ALIASES = {"matrix": "matriks", "risk": "risiko", "control": "kontrol", "plan": "rencana", "incident": "insiden",
           "evaluation": "evaluasi", "anchor": "pasang", "process": "proses", "objective": "sasaran",
           "indicator": "indikator", "mandate": "mandat", "report": "laporan"}


def entity_name(name: str) -> str:
    n = ALIASES.get(name.lower(), name.lower())
    if n not in ENTITIES:
        raise ValueError(f"Jenis catatan tidak dikenal: {name!r}. Pilihan: {', '.join(ENTITIES)}")
    return n


def entity_of_id(note_id: str) -> Entity:
    prefix = note_id.split("-", 1)[0]
    if prefix not in BY_PREFIX:
        raise ValueError(f"ID tidak dikenal: {note_id!r}")
    return BY_PREFIX[prefix]


def parse_cell(value) -> tuple[int, int]:
    m = CELL.match(str(value))
    if not m:
        raise ValueError(f"Sel risiko harus berbentuk KxD (kemungkinan x dampak), misalnya 3x4, bukan {value!r}")
    return int(m.group(1)), int(m.group(2))


def fmt_cell(likelihood: int, impact: int) -> str:
    return f"{likelihood}x{impact}"


def strip_link(value) -> str | None:
    if value in (None, ""):
        return None
    m = LINK.match(str(value))
    return (m.group(1) if m else str(value)).strip()


def coerce(f: F, value):
    """A CLI string (or stored value) -> the plain value of the field. None or '' clears an optional field."""
    if value is None or value == "" or value == []:
        if f.req:
            raise ValueError(f"'{f.name}' wajib diisi")
        return [] if f.kind.startswith("links") else None
    k = f.kind
    try:
        if k == "str":
            return " ".join(str(value).split())
        if k == "int":
            return int(value)
        if k == "float":
            return float(str(value).replace(",", "."))
        if k == "bool":
            if isinstance(value, bool):
                return value
            return str(value).strip().lower() in ("1", "true", "ya", "y", "yes")
        if k == "date":
            return date.fromisoformat(str(value)).isoformat()
        if k == "cell":
            return fmt_cell(*parse_cell(value))
        if k.startswith("link:"):
            return strip_link(value)
        if k.startswith("links:"):
            items = value if isinstance(value, list) else str(value).replace(";", ",").split(",")
            return [strip_link(x) for x in items if strip_link(x)]
        if k.startswith("enum:"):
            allowed = k[5:].split("|")
            hit = [a for a in allowed if a.lower() == str(value).strip().lower()]
            if not hit:
                raise ValueError(f"nilai harus salah satu dari {', '.join(allowed)}")
            return hit[0]
    except ValueError as exc:
        raise ValueError(f"'{f.name}': {exc}") from None
    raise ValueError(f"jenis kolom tidak dikenal: {k}")


def to_store(f: F | None, value):
    if f is None or value is None:
        return value
    if f.kind.startswith("link:"):
        return f"[[{value}]]"
    if f.kind.startswith("links:"):
        return [f"[[{v}]]" for v in value]
    return value


def from_store(f: F | None, value):
    if f is None:
        return value
    if f.kind.startswith("link:"):
        return strip_link(value)
    if f.kind.startswith("links:"):
        items = value if isinstance(value, list) else ([] if value in (None, "") else [value])
        return [strip_link(v) for v in items if strip_link(v)]
    if f.kind in ("cell", "date") and value is not None:
        return str(value)
    return value


def link_target(f: F) -> str | None:
    return f.kind.split(":", 1)[1] if ":" in f.kind and f.kind.split(":", 1)[0] in ("link", "links") else None
