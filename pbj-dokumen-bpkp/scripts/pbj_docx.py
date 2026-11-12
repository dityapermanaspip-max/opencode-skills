"""Editing a .docx at the level of text nodes, so a marker or a blank that Word split over several runs
is still found and the formatting of the surrounding text survives.

Three uses:
* ``fill_markers``  - replace ``{{key}}`` markers of a HILDA template with typed values.
* ``list_blanks`` / ``fill_blanks`` - find and fill the blanks of the owner's own forms (``_____``,
  ``.....``, ``------Nama Unit Kerja------``, ``[petunjuk]``) by index.
* ``literal_replace`` - exact text substitution inside a form.
"""

from __future__ import annotations

import re
from bisect import bisect_right

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

W_P, W_T, W_TC = qn("w:p"), qn("w:t"), qn("w:tc")
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
MARKER = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")
BLANKS = (
    ("garis bawah", re.compile(r"_{3,}")),
    ("titik", re.compile(r"\.{4,}|…{2,}")),
    ("strip", re.compile(r"-{3,}(?:[^-\n]|-(?!-)){2,70}?-{3,}")),
    ("petunjuk", re.compile(r"\[[^\]\n]{3,160}\]")),
)
BLANK_ANY = re.compile("|".join(f"(?P<k{i}>{rx.pattern})" for i, (_, rx) in enumerate(BLANKS)))


def paragraphs(doc):
    """Every w:p of the body, headers and footers, nested tables and text boxes included."""
    for part in doc.part.package.iter_parts():
        name = str(part.partname)
        if name == "/word/document.xml" or re.fullmatch(r"/word/(header|footer)\d*\.xml", name):
            for p in part.element.iter(W_P):
                yield name, p


def _nodes(p):
    return [t for t in p.iter(W_T) if next(t.iterancestors(W_P)) is p]


def _write(node, text: str) -> None:
    """Set a w:t; a newline becomes a line break inside the same run."""
    lines = text.replace("\r\n", "\n").split("\n")
    node.text = lines[0]
    node.set(XML_SPACE, "preserve")
    anchor = node
    for line in lines[1:]:
        br = OxmlElement("w:br")
        anchor.addnext(br)
        t = OxmlElement("w:t")
        t.text = line
        t.set(XML_SPACE, "preserve")
        br.addnext(t)
        anchor = t


def substitute(doc, regex: re.Pattern, fn, *, after: bool = False, limit: int | None = None) -> int:
    """Replace every match for which ``fn(match, where)`` returns a string; None leaves it alone.

    ``after=True`` keeps the matched text and inserts the value right behind it (inside the node where
    the match ends, so tabs and runs between a label and its colon stay where they are)."""
    done = 0
    for where, p in paragraphs(doc):
        nodes = _nodes(p)
        texts = [t.text or "" for t in nodes]
        starts, pos = [], 0
        for tx in texts:
            starts.append(pos)
            pos += len(tx)
        edits = []
        for m in regex.finditer("".join(texts)):
            if limit is not None and done + len(edits) >= limit:
                break
            value = fn(m, where)
            if value is not None:
                edits.append((m.start(), m.end(), value))
        for s, e, value in reversed(edits):
            i = bisect_right(starts, s) - 1
            j = bisect_right(starts, max(e - 1, s)) - 1
            if after:
                cut = e - starts[j]
                texts[j] = texts[j][:cut] + value + texts[j][cut:]
                done += 1
                continue
            head, tail = texts[i][: s - starts[i]], texts[j][e - starts[j]:]
            if i == j:
                texts[i] = head + value + tail
            else:
                texts[i] = head + value
                for k in range(i + 1, j):
                    texts[k] = ""
                texts[j] = tail
            done += 1
        if edits:
            for node, tx in zip(nodes, texts):
                if tx != (node.text or ""):
                    _write(node, tx)
    return done


def fill_markers(doc, resolve) -> tuple[int, set[str]]:
    """``resolve(key)`` returns the text for a marker key (None = unknown key, left in place).

    Returns the number of replacements and the keys that were unknown."""
    unknown: set[str] = set()

    def fn(m, _where):
        value = resolve(m.group(1))
        if value is None:
            unknown.add(m.group(1))
        return value

    return substitute(doc, MARKER, fn), unknown


def marker_keys(doc) -> set[str]:
    keys: set[str] = set()
    substitute(doc, MARKER, lambda m, _w: keys.add(m.group(1)) and None)
    return keys


def _context(full_text: str, start: int, end: int, span: int = 38) -> str:
    return (full_text[max(0, start - span): start] + "<<" + full_text[start:end] + ">>" + full_text[end: end + span]).replace("\n", " ")


def list_blanks(doc) -> list[dict]:
    """Blanks of an owner form in document order; ``index`` is what ``fill_blanks`` takes."""
    found: list[dict] = []
    for where, p in paragraphs(doc):
        full = "".join(t.text or "" for t in _nodes(p))
        for m in BLANK_ANY.finditer(full):
            kind = next(BLANKS[int(name[1:])][0] for name, val in m.groupdict().items() if val is not None)
            place = "tabel" if next(p.iterancestors(W_TC), None) is not None else "teks"
            found.append({"index": len(found), "jenis": kind, "bagian": where.rsplit("/", 1)[-1] + "/" + place, "konteks": _context(full, m.start(), m.end())})
    return found


def fill_blanks(doc, values: dict[int, str]) -> int:
    counter = {"i": 0}

    def fn(m, _where):
        index = counter["i"]
        counter["i"] += 1
        return values.get(index)

    return substitute(doc, BLANK_ANY, fn)


def literal_replace(doc, old: str, new: str) -> int:
    return substitute(doc, re.compile(re.escape(old)), lambda m, _w: new)


def insert_after(doc, anchor: str, value: str) -> int:
    """Put ``value`` right behind the FIRST occurrence of ``anchor`` (a label such as 'Nama Paket:')."""
    return substitute(doc, re.compile(re.escape(anchor)), lambda m, _w: value, after=True, limit=1)


def _tables(container):
    for table in container.tables:
        yield table
        for row in table.rows:
            for cell in row.cells:
                yield from _tables(cell)


def fill_cell(doc, label: str, value: str) -> int:
    """In a table row whose first cell reads ``label`` (a trailing colon is ignored), write ``value``
    into the first empty cell to its right. Returns how many rows were filled."""
    want = label.strip().rstrip(":").strip().lower()
    done = 0
    for table in _tables(doc):
        for row in table.rows:
            cells, seen = [], set()
            for cell in row.cells:  # merged cells repeat
                if id(cell._tc) not in seen:
                    seen.add(id(cell._tc))
                    cells.append(cell)
            if not cells or cells[0].text.strip().rstrip(":").strip().lower() != want:
                continue
            target = next((c for c in cells[1:] if c.text.strip() == ""), None)
            if target is not None:
                target.paragraphs[0].add_run(value)
                done += 1
    return done


def paragraph_texts(doc):
    """(where, text) for every non-empty paragraph, exactly as the matchers see it (tabs are not text)."""
    for where, p in paragraphs(doc):
        text = "".join(t.text or "" for t in _nodes(p))
        if text.strip():
            yield where.rsplit("/", 1)[-1] + ("/tabel" if next(p.iterancestors(W_TC), None) is not None else ""), text


def open_docx(path):
    return Document(str(path))
