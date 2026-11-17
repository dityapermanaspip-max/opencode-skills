"""The three figures of the report as inline SVG/HTML: risk heat map, score-versus-appetite bars, KRI line chart.
One series per chart, thin marks, direct labels on the points that matter, thresholds drawn and named."""

from __future__ import annotations

import math

from gv_kri import readings, status_of
from gv_notes import get_section, table_rows
from gv_pdf_util import ZONE_COLORS, ZONE_ORDER, ZONE_TEXT, date_short, e, num

SERIES = "#2a78d6"
CRIT = "#d03b3b"


def labels_of(matrix, section: str) -> dict:
    return {int(r["level"]): r.get("label", "") for r in table_rows(get_section(matrix.note.body, section)) if r.get("level", "").isdigit()}


def _ticks(lo: float, hi: float, n: int = 4) -> list[float]:
    """Round tick values (1, 2, 2.5, 5 x 10^k) inside the range."""
    raw = (hi - lo) / n
    mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
    t, out = math.ceil(lo / step) * step, []
    while t <= hi + 1e-9:
        out.append(round(t, 6))
        t += step
    return out


def zone_legend(matrix) -> str:
    spans: dict[str, list[int]] = {}
    for l in range(1, matrix.max_l + 1):
        for i in range(1, matrix.max_i + 1):
            spans.setdefault(matrix.zone(f"{l}x{i}"), []).append(matrix.score(f"{l}x{i}"))
    items = [f"<span><i style='background:{ZONE_COLORS[z]}'></i>{e(z)} (skor {min(spans[z])}-{max(spans[z])})</span>" for z in ZONE_ORDER if z in spans]
    return f"<div class='legend'>{''.join(items)}</div>"


def heatmap(matrix, counts: dict) -> str:
    lk, im = labels_of(matrix, "Label kemungkinan"), labels_of(matrix, "Label dampak")
    head = "<tr><th></th>" + "".join(f"<th>{i}<small>{e(im.get(i, ''))}</small></th>" for i in range(1, matrix.max_i + 1)) + "</tr>"
    rows = []
    for l in range(matrix.max_l, 0, -1):
        cells = []
        for i in range(1, matrix.max_i + 1):
            cell = f"{l}x{i}"
            z, n = matrix.zone(cell), counts.get(cell, 0)
            body = f"<span class='sc'>{matrix.score(cell)}</span>" + (f"<b class='n'>{n}</b>" if n else "")
            cells.append(f"<td style='background:{ZONE_COLORS.get(z, '#d9d8d3')};color:{ZONE_TEXT.get(z, '#0b0b0b')}'>{body}</td>")
        rows.append(f"<tr><th>{l}<small>{e(lk.get(l, ''))}</small></th>{''.join(cells)}</tr>")
    cap = "<p><small>Baris: kemungkinan. Kolom: dampak. Angka kecil di sudut: skor sel. Angka besar: jumlah risiko dengan nilai aktif di sel itu.</small></p>"
    return f"<table class='heat'>{head}{''.join(rows)}</table>{zone_legend(matrix)}{cap}"


def score_bars(rows: list, matrix) -> str:
    """Active score per risk, sorted high to low, with the appetite line."""
    data = sorted((r for r in rows if r["score"] is not None), key=lambda r: -r["score"])
    if not data:
        return ""
    top, thr = matrix.max_l * matrix.max_i, matrix.appetite(rows[0]["eva"].fields["fiscal_year"])
    x0, wbar, rh = 265, 300, 21
    h = 34 + rh * len(data)
    out = [f"<svg viewBox='0 0 720 {h}' role='img' aria-label='Skor aktif per risiko dibanding batas appetite'>"]
    for tick in range(0, top + 1, 5):
        x = x0 + wbar * tick / top
        out.append(f"<line x1='{x:.1f}' y1='22' x2='{x:.1f}' y2='{h - 6}' stroke='#e6e5e0' stroke-width='1'/>"
                   f"<text x='{x:.1f}' y='14' font-size='8.5' text-anchor='middle' class='mut'>{tick}</text>")
    for k, r in enumerate(data):
        y = 28 + rh * k
        zone, w = r["zone"], wbar * r["score"] / top
        title = r["risk"].fields["title"]
        title = title if len(title) <= 44 else title[:43].rstrip() + "..."
        out.append(f"<text x='0' y='{y + 10}' font-size='8.6'>{e(r['risk'].id)} {e(title)}</text>"
                   f"<rect x='{x0}' y='{y}' width='{w:.1f}' height='12' rx='3' fill='{ZONE_COLORS.get(zone, '#d9d8d3')}'/>"
                   f"<text x='{x0 + wbar + 12}' y='{y + 10}' font-size='8.6'>{r['score']} - {e(r['active_cell'])} - {e(zone)}</text>")
    if thr is not None:
        x = x0 + wbar * thr / top
        out.append(f"<line x1='{x:.1f}' y1='20' x2='{x:.1f}' y2='{h - 6}' stroke='#0b0b0b' stroke-width='1.6' stroke-dasharray='5 3'/>"
                   f"<text x='{x + 4:.1f}' y='{h - 8}' font-size='8.6' font-weight='600'>Batas appetite {thr}</text>")
    out.append("</svg>")
    return f"<div class='chart'>{''.join(out)}</div>"


def kri_chart(note) -> str:
    """Readings over time (equal spacing), the amber and red thresholds as dashed lines, labels on the extremes and every red reading."""
    pts = sorted(readings(note))
    if len(pts) < 2:
        return ""
    f = note.fields
    amber, red, direction = f.get("amber"), f.get("red"), f["direction"]
    vals = [v for _d, v in pts] + [t for t in (amber, red) if t is not None]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.12 or 1.0
    lo, hi = lo - pad, hi + pad
    x0, x1, y0, y1 = 52, 700, 16, 168
    X = lambda k: x0 + (x1 - x0) * k / (len(pts) - 1)
    Y = lambda v: y1 - (y1 - y0) * (v - lo) / (hi - lo)
    out = ["<svg viewBox='0 0 720 205' role='img' aria-label='Pembacaan KRI dari waktu ke waktu'>"]
    for v in _ticks(lo, hi):
        out.append(f"<line x1='{x0}' y1='{Y(v):.1f}' x2='{x1}' y2='{Y(v):.1f}' stroke='#e6e5e0'/>"
                   f"<text x='{x0 - 6}' y='{Y(v) + 3:.1f}' font-size='8.5' text-anchor='end' class='mut'>{num(v, 1)}</text>")
    for value, name, colour in ((amber, "Kuning", "#52514e"), (red, "Merah", CRIT)):
        if value is not None:
            out.append(f"<line x1='{x0}' y1='{Y(value):.1f}' x2='{x1}' y2='{Y(value):.1f}' stroke='{colour}' stroke-width='1.4' stroke-dasharray='5 3'/>"
                       f"<text x='{x1}' y='{Y(value) - 4:.1f}' font-size='8.5' text-anchor='end' font-weight='600' fill='{colour}' style='fill:{colour}'>{name} {num(value)}</text>")
    line = " ".join(f"{X(k):.1f},{Y(v):.1f}" for k, (_d, v) in enumerate(pts))
    out.append(f"<polyline points='{line}' fill='none' stroke='{SERIES}' stroke-width='2'/>")
    show = {min(range(len(pts)), key=lambda k: pts[k][1]), max(range(len(pts)), key=lambda k: pts[k][1])}
    show |= {k for k, (_d, v) in enumerate(pts) if status_of(v, amber, red, direction) == "red"}
    step = max(1, len(pts) // 12)
    for k, (d, v) in enumerate(pts):
        out.append(f"<circle cx='{X(k):.1f}' cy='{Y(v):.1f}' r='4' fill='{SERIES}' stroke='#fff' stroke-width='2'/>")
        if k % step == 0 or k == len(pts) - 1:
            out.append(f"<text x='{X(k):.1f}' y='{y1 + 15}' font-size='8.2' text-anchor='middle' class='mut'>{e(date_short(d))}</text>")
        if k in show:
            above = (v >= (lo + hi) / 2)
            out.append(f"<text x='{X(k):.1f}' y='{Y(v) + (-9 if above else 17):.1f}' font-size='8.6' text-anchor='middle' font-weight='600'>{num(v)}</text>")
    out.append("</svg>")
    return f"<div class='chart'>{''.join(out)}</div>"
