"""Obsidian notes: a small YAML-subset frontmatter reader/writer, plus helpers for the tables and bullet trees
that live under a '## ' heading in the note body. Standard library only."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

_FM = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)(.*)\Z", re.S)
_NUM = re.compile(r"-?\d+(\.\d+)?\Z")
_KEY = re.compile(r"^([A-Za-z_][\w-]*):(?:[ \t]+(.*)|[ \t]*)$")


def _split(inner: str) -> list[str]:
    """Splits an inline list on commas that are outside quotes."""
    out, cur, quote, prev = [], [], None, ""
    for ch in inner:
        if quote:
            cur.append(ch)
            if ch == quote and prev != "\\":
                quote = None
        elif ch in "\"'":
            quote = ch
            cur.append(ch)
        elif ch == ",":
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
        prev = ch
    out.append("".join(cur))
    return [x for x in out if x.strip()]


def _scalar(raw: str):
    s = raw.strip()
    if s in ("", "null", "~"):
        return None
    if len(s) >= 2 and s[0] in "\"'" and s[-1] == s[0]:
        inner = s[1:-1]
        return inner.replace('\\"', '"').replace("\\\\", "\\") if s[0] == '"' else inner.replace("''", "'")
    if s in ("true", "false"):
        return s == "true"
    if _NUM.match(s):
        return float(s) if "." in s else int(s)
    if s.startswith("[") and s.endswith("]") and not s.startswith("[["):
        return [_scalar(x) for x in _split(s[1:-1])]
    return s


def _fmt(v, in_list: bool = False) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() else repr(v)
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_fmt(x, True) for x in v) + "]"
    s = " ".join(str(v).split())
    risky = (in_list and any(c in s for c in ",[]\"'")) or (not s or s[0] in "[]{}#&*!|>'\"%@`-?:," or s.endswith(":") or ": " in s or " #" in s or "[[" in s
             or s in ("true", "false", "null", "~") or bool(_NUM.match(s)))
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"' if risky else s


@dataclass
class Note:
    path: Path
    fields: dict = field(default_factory=dict)
    body: str = ""
    entity: str = ""

    @property
    def id(self) -> str:
        return self.path.stem


def parse(text: str) -> tuple[dict, str]:
    text = text.lstrip("\ufeff").replace("\r\n", "\n")
    m = _FM.match(text)
    if not m:
        return {}, text
    fields, key = {}, None
    for line in m.group(1).split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        km = None if line[0] in " \t" else _KEY.match(line)
        if km:
            key = km.group(1)
            fields[key] = _scalar(km.group(2)) if km.group(2) is not None else None
        elif key is not None and re.match(r"^\s+-\s+", line):
            if not isinstance(fields[key], list):
                fields[key] = []
            fields[key].append(_scalar(re.sub(r"^\s+-\s+", "", line)))
        else:
            raise ValueError(f"Frontmatter yang tidak didukung: {line.strip()!r} (hanya 'kunci: nilai' dan daftar)")
    return fields, m.group(2).lstrip("\n")


def dump(fields: dict, body: str) -> str:
    lines = [f"{k}: {_fmt(v)}".rstrip() for k, v in fields.items()]
    return "---\n" + "\n".join(lines) + "\n---\n\n" + body.strip("\n") + "\n"


def read_note(path: Path, entity: str = "") -> Note:
    fields, body = parse(Path(path).read_text(encoding="utf-8"))
    return Note(Path(path), fields, body, entity)


def write_note(note: Note) -> None:
    note.path.parent.mkdir(parents=True, exist_ok=True)
    tmp = note.path.with_suffix(".md.tmp")
    tmp.write_text(dump(note.fields, note.body), encoding="utf-8", newline="\n")
    os.replace(tmp, note.path)


# ---- body sections -------------------------------------------------------------------------------------------

def _sec_re(title: str) -> re.Pattern:
    return re.compile(rf"^##[ \t]+{re.escape(title)}[ \t]*\n(.*?)(?=^##[ \t]|\Z)", re.S | re.M)


def get_section(body: str, title: str) -> str:
    m = _sec_re(title).search(body)
    return m.group(1).strip("\n") if m else ""


def set_section(body: str, title: str, content: str) -> str:
    block = f"## {title}\n\n{content.strip(chr(10))}\n\n"
    if _sec_re(title).search(body):
        return _sec_re(title).sub(lambda _m: block, body, count=1).rstrip("\n") + "\n"
    return body.rstrip("\n") + ("\n\n" if body.strip() else "") + block.rstrip("\n") + "\n"


def table_rows(text: str) -> list[dict]:
    rows = [ln.strip() for ln in text.split("\n") if ln.strip().startswith("|")]
    if len(rows) < 2:
        return []
    cut = lambda ln: [c.strip() for c in ln.strip().strip("|").split("|")]
    head = [h.lower() for h in cut(rows[0])]
    body = [r for r in rows[1:] if not re.fullmatch(r"[|\s:\-]+", r)]
    return [dict(zip(head, cut(r))) for r in body]


def make_table(headers: list[str], rows: list[list]) -> str:
    clean = lambda v: "" if v is None else str(v).replace("|", "/").replace("\n", " ")
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(clean(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


_BULLET = re.compile(r"^(\s*)-\s+(.*?)(?:\s+\[([^\[\]]+)\])?\s*$")


def bullet_tree(text: str) -> list[dict]:
    """'- text [Category]' lines, two spaces per level -> [{text, category, children}]."""
    root: list[dict] = []
    stack: list[tuple[int, list[dict]]] = [(-1, root)]
    for line in text.split("\n"):
        m = _BULLET.match(line.rstrip())
        if not m:
            continue
        depth = len(m.group(1).replace("\t", "  ")) // 2
        node = {"text": m.group(2).strip(), "category": m.group(3), "children": []}
        while stack and stack[-1][0] >= depth:
            stack.pop()
        stack[-1][1].append(node)
        stack.append((depth, node["children"]))
    return root


def make_bullet_tree(nodes: list[dict], depth: int = 0) -> str:
    out = []
    for n in nodes:
        tag = f" [{n['category']}]" if n.get("category") else ""
        out.append("  " * depth + f"- {n['text']}{tag}")
        if n.get("children"):
            out.append(make_bullet_tree(n["children"], depth + 1))
    return "\n".join(out)
