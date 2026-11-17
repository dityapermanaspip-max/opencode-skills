"""Bowtie SVG: a tree on each side of the risk. Sub-causes grow outward (left) from their parent, sub-impacts outward (right),
every branch is joined to its parent, both sides are centred on the risk event. KRI badges and picked controls sit on their
branch; each opens a detail panel (see gv_bowtie_pop). Standard library only.

`view` (built by gv_bowtie): {"kri": {branch key: [(kri, status)]}, "ctl": {branch key: [control id]},
"info": {control id: {"note", "evals", "branches"}}, "unattached": [control id]}."""

from __future__ import annotations

from gv_bowtie_pop import (CSS, CTL_INK, EFF_COLOUR, KRI_COLOUR, KRI_LABEL, control_panel, kri_panel, lines, wrap, worst)
from gv_pdf_util import ZONE_COLORS, ZONE_TEXT, e as _e

FONT = "Segoe UI, Helvetica, Arial, sans-serif"
LEFT_X, TOP = 30, 76
CW, GAPX, ROWGAP, WRAP = 250, 46, 10, 31  # branch box width, gap between columns, gap between rows, characters per line
CENTRE_W = 230
MIN_W = 900
CHIP_W, CHIP_PER_ROW = 66, 3
LEGEND = ("Lencana bulat = KRI (warna = status) · kotak bertitik = kontrol (titik = efektivitas). "
          "Garis putus-putus = tanpa bukti. Buka berkas .svg di peramban lalu klik lencana untuk rincian.")


def _place(nodes, prefix: str, depth: int, y: float, flat: list, view: dict) -> tuple[list, float]:
    """Tidy tree: leaves stack top to bottom, a parent sits at the middle of its children.
    Keys follow the KRI matching (`c0`, `c4.1`, `i2`). Returns (placed nodes, next free y); cy is relative to y=0."""
    placed = []
    for idx, node in enumerate(nodes):
        key = f"{prefix}{idx}"
        rows = wrap(node.get("text"), WRAP)
        chips = -(-len(view["ctl"].get(key, [])) // CHIP_PER_ROW)
        h = 25 + 16 * len(rows) + (21 * chips + 1 if chips else 0)
        start = y
        kids, y = _place(node.get("children", []), key + ".", depth + 1, y, flat, view)
        cy = max((kids[0]["cy"] + kids[-1]["cy"]) / 2 if kids else 0, start + h / 2)
        item = {"key": key, "depth": depth, "cy": cy, "h": h, "lines": rows, "kids": kids,
                "cat": node.get("category") or ("Penyebab" if prefix[0] == "c" else "Dampak")}
        flat.append(item)
        placed.append(item)
        y = max(y, cy + h / 2 + ROWGAP)
    return placed, y


def _edge(x1, y1, x2, y2) -> str:
    xm = (x1 + x2) / 2
    return (f"<path d='M {x1:.1f} {y1:.1f} C {xm:.1f} {y1:.1f} {xm:.1f} {y2:.1f} {x2:.1f} {y2:.1f}' "
            f"fill='none' stroke='#b8b6ae' stroke-width='1.3'/>")


def _kri_chip(kri, status: str, x: float, y: float) -> str:
    tip = f"{kri.id} · {KRI_LABEL.get(status, status)}. Klik untuk rincian"
    return (f"<a href='#p-{kri.id}' class='chip'><title>{_e(tip)}</title>"
            f"<rect class='box' x='{x}' y='{y:.1f}' width='68' height='15' rx='7.5' fill='{KRI_COLOUR.get(status, KRI_COLOUR['grey'])}'/>"
            f"<text x='{x + 34}' y='{y + 11:.1f}' font-size='9' fill='#fff' text-anchor='middle' font-weight='600'>{_e(kri.id)}</text></a>")


def _ctl_chip(cid: str, info: dict, x: float, y: float) -> str:
    kind = (info["note"].fields.get("control_type") or "-").capitalize()
    status = worst(info["evals"])
    unproven = not any(e["proven"] for e in info["evals"])
    tip = f"{cid} · {kind} · {status}" + (" · TANPA BUKTI" if unproven else "") + ". Klik untuk rincian"
    dash = " stroke-dasharray='3 2'" if unproven else ""
    return (f"<a href='#p-{cid}' class='chip'><title>{_e(tip)}</title>"
            f"<rect class='box' x='{x}' y='{y:.1f}' width='{CHIP_W}' height='16' rx='3' fill='#fff' stroke='{CTL_INK}' stroke-width='1.1'{dash}/>"
            f"<circle cx='{x + 9}' cy='{y + 8:.1f}' r='3.5' fill='{EFF_COLOUR.get(status, '#6b6b6b')}'/>"
            f"<text x='{x + 16}' y='{y + 11.5:.1f}' font-size='9' font-weight='600' fill='{CTL_INK}'>{_e(cid)}</text></a>")


def _draw(items, tag: str, x_of, view: dict, anchor: tuple, dy: float, edges: list, boxes: list) -> None:
    """Causes: a box links from its right edge to its parent's left edge (the centre for the first level).
    Impacts: from the parent's right edge to the box's left edge."""
    fill, edge, ink = ("#fff6e8", "#d9b877", "#7a6144") if tag == "c" else ("#fdeeee", "#d9a0a0", "#8a4a4a")
    for it in items:
        x, cy = x_of(it["depth"]), it["cy"] + dy
        y = cy - it["h"] / 2
        edges.append(_edge(x + CW, cy, *anchor) if tag == "c" else _edge(*anchor, x, cy))
        boxes.append(f"<rect x='{x}' y='{y:.1f}' width='{CW}' height='{it['h']}' rx='8' fill='{fill}' stroke='{edge}' stroke-width='1'/>"
                     f"<text x='{x + 10}' y='{y + 15:.1f}' font-size='10' font-weight='600' fill='{ink}'>{_e(it['cat'])}</text>"
                     + lines(x + 10, round(y + 32, 1), it["lines"], 12, weight="600"))
        for j, (kri, status) in enumerate(view["kri"].get(it["key"], [])):
            boxes.append(_kri_chip(kri, status, x + CW - 74 - j * 72, y + 5))
        for j, cid in enumerate(view["ctl"].get(it["key"], [])):
            boxes.append(_ctl_chip(cid, view["info"][cid], x + 10 + (j % CHIP_PER_ROW) * (CHIP_W + 6),
                                   y + 24 + 16 * len(it["lines"]) + (j // CHIP_PER_ROW) * 21))
        _draw(it["kids"], tag, x_of, view, (x, cy) if tag == "c" else (x + CW, cy), dy, edges, boxes)


def _centre_svg(risk, row, view: dict, cx: float) -> tuple[str, float]:
    f = risk.fields
    title = wrap(f.get("title"), 22)
    active = f"{row['active_type']} {row['active_cell']} · skor {row['score']} · {row['zone']}" if row else "belum dievaluasi"
    appetite = f"Appetite {row['threshold']} · {row['appetite']}" if row else "-"
    fill = ZONE_COLORS.get(row["zone"] if row else None, "#e8edf3")
    ink = ZONE_TEXT.get(row["zone"] if row else None, "#0b0b0b")
    y = 44 + len(title) * 21
    body = [lines(cx + 14, 32, title, 15, ink, "700"),
            f"<text x='{cx + 14}' y='{y}' font-size='10.5' fill='{ink}'>{_e(active)}</text>",
            f"<text x='{cx + 14}' y='{y + 16}' font-size='10' fill='{ink}'>{_e(appetite)}</text>"]
    y += 38
    for kri, status in view["kri"].get("centre", []):
        rows = wrap(f"{kri.id} · {kri.fields.get('title', '')}", 34)
        body.append(f"<a href='#p-{kri.id}' class='chip'><title>{_e(kri.id)} · {KRI_LABEL.get(status, status)}. Klik untuk rincian</title>"
                    f"<circle class='box' cx='{cx + 18}' cy='{y - 3}' r='4.5' fill='{KRI_COLOUR.get(status, KRI_COLOUR['grey'])}' "
                    f"stroke='#fff'/>" + lines(cx + 29, y, rows, 9.5, ink) + "</a>")
        y += len(rows) * 12.5 + 6
    h = max(150, y + 8)
    rect = f"<rect x='{cx}' y='0' width='{CENTRE_W}' height='{h}' rx='12' fill='{fill}' stroke='#5c5b57' stroke-width='1.4'/>"
    return rect + "".join(body), h


def _strip(view: dict, y: float, width: float) -> tuple[str, float]:
    """Controls installed on the evaluation but not picked for a branch: still clickable."""
    ids = view["unattached"]
    if not ids:
        return "", 0
    per = max(1, int((width - 2 * LEFT_X + 6) // (CHIP_W + 6)))
    out = [f"<text x='{LEFT_X}' y='{y + 10}' font-size='10' font-weight='600' fill='#66645f'>"
           f"Kontrol pada evaluasi yang belum dipasang ke cabang (klik untuk rincian)</text>"]
    for j, cid in enumerate(ids):
        out.append(_ctl_chip(cid, view["info"][cid], LEFT_X + (j % per) * (CHIP_W + 6), y + 18 + (j // per) * 21))
    return "".join(out), 18 + (-(-len(ids) // per)) * 21 + 6


def svg_of(risk, row, causes: list, impacts: list, view: dict) -> str:
    cflat: list = []
    iflat: list = []
    cplaced, cend = _place(causes, "c", 0, 0, cflat, view)
    iplaced, iend = _place(impacts, "i", 0, 0, iflat, view)
    c_h, i_h = (cend - ROWGAP if causes else 0), (iend - ROWGAP if impacts else 0)
    nc = max((n["depth"] for n in cflat), default=0) + 1
    ni = max((n["depth"] for n in iflat), default=0) + 1
    cx = LEFT_X + nc * (CW + GAPX)
    ix0 = cx + CENTRE_W + GAPX
    width = max(MIN_W, ix0 + ni * (CW + GAPX) - GAPX + LEFT_X)
    centre_svg, centre_h = _centre_svg(risk, row, view, cx)
    span = max(c_h, i_h, centre_h)
    mid = TOP + span / 2
    edges: list = []
    boxes: list = []
    _draw(cplaced, "c", lambda d: LEFT_X + (nc - 1 - d) * (CW + GAPX), view, (cx, mid), TOP + (span - c_h) / 2, edges, boxes)
    _draw(iplaced, "i", lambda d: ix0 + d * (CW + GAPX), view, (cx + CENTRE_W, mid), TOP + (span - i_h) / 2, edges, boxes)
    for present, x in ((causes, LEFT_X), (impacts, ix0)):
        if not present:
            boxes.append(f"<text x='{x}' y='{mid:.1f}' font-size='11' fill='#66645f'>Belum ada cabang pada catatan risiko.</text>")
    strip, strip_h = _strip(view, TOP + span + 14, width)
    legend_y = TOP + span + 14 + strip_h + 16
    kris = {k.id: (k, s) for pairs in view["kri"].values() for k, s in pairs}

    def panels_for(h: float) -> list[tuple[str, float]]:
        return ([control_panel(i["note"], i["evals"], i["branches"], width, h, mid) for _c, i in sorted(view["info"].items())]
                + [kri_panel(k, s, width, h, mid) for _k, (k, s) in sorted(kris.items())])

    height = round(legend_y + 14)
    height = max(height, round(max((ph for _svg, ph in panels_for(height)), default=0)) + 24)  # a panel must fit on the canvas
    panels = [svg for svg, _ph in panels_for(height)]
    meta = (f"{row['active_type']} {row['active_cell']} (skor {row['score']}, {row['zone']}) · "
            f"appetite {row['threshold']}: {row['appetite']}") if row else "Belum dievaluasi"
    head = (f"<title>Bowtie {_e(risk.id)} - {_e(risk.fields.get('title'))}</title>"
            f"<desc>Penyebab di kiri, peristiwa risiko di tengah, dampak di kanan. Lencana menandai KRI dan kontrol; klik untuk rincian.</desc>"
            f"<style>{CSS}</style>")
    header = (f"<text x='{LEFT_X}' y='26' font-size='15' font-weight='700'>Bowtie {_e(risk.id)} — {_e(risk.fields.get('title'))}</text>"
              f"<text x='{LEFT_X}' y='45' font-size='10.5' fill='#66645f'>{_e(meta)}</text>"
              f"<text x='{LEFT_X}' y='{TOP - 12}' font-size='11' font-weight='700' fill='#8a5a00'>PENYEBAB</text>"
              f"<text x='{ix0}' y='{TOP - 12}' font-size='11' font-weight='700' fill='#9d4040'>DAMPAK</text>")
    parts = [f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {width} {height}' width='{width}' height='{height}' "
             f"font-family='{FONT}' role='img' aria-label='Bowtie risiko {_e(risk.id)}'>", head,
             f"<rect width='{width}' height='{height}' fill='#fbfaf7'/>", header,
             *edges, *boxes, f"<g transform='translate(0,{mid - centre_h / 2:.1f})'>", centre_svg, "</g>", strip,
             f"<text x='{LEFT_X}' y='{legend_y}' font-size='9.5' fill='#66645f'>{_e(LEGEND)}</text>", *panels, "</svg>"]
    return "\n".join(parts) + "\n"
