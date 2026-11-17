"""Small helpers for the HTML/PDF report: escaping, inline Markdown, Indonesian number and date formats, zone colours."""

from __future__ import annotations

import html
import re

MONTHS = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]

# One ordinal scale for the five default zones; the zone NAME is always printed next to a colour, never colour alone.
ZONE_COLORS = {"LOW": "#0ca30c", "MODERATE_LOW": "#83aa13", "MODERATE": "#fab219", "HIGH": "#ec835a", "EXTREME": "#d03b3b"}
ZONE_TEXT = {"LOW": "#ffffff", "MODERATE_LOW": "#0b0b0b", "MODERATE": "#0b0b0b", "HIGH": "#0b0b0b", "EXTREME": "#ffffff"}
ZONE_ORDER = ["LOW", "MODERATE_LOW", "MODERATE", "HIGH", "EXTREME"]
APPETITE_TEXT = {"DI_BAWAH_APPETITE": "Dalam appetite", "DI_ATAS_APPETITE": "Di atas appetite", "BELUM_ADA_APPETITE": "Appetite belum ditetapkan",
                 "BELUM_DIEVALUASI": "Belum dievaluasi"}


def e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def inline(text) -> str:
    """Escapes, then turns **bold** and `code` into tags and [[ID]] links into plain ids."""
    s = e(text)
    s = re.sub(r"\[\[(.+?)(?:\|.*?)?\]\]", r"\1", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", s)


def num(value, digits: int = 2) -> str:
    """12.5 -> '12,5', 14.0 -> '14', None -> '-' (decimal comma)."""
    if value in (None, ""):
        return "-"
    try:
        x = float(str(value).replace(",", "."))
    except ValueError:
        return str(value)
    return f"{x:.{digits}f}".rstrip("0").rstrip(".").replace(".", ",")


def date_long(iso) -> str:
    try:
        y, m, d = (int(p) for p in str(iso)[:10].split("-"))
        return f"{d} {MONTHS[m - 1]} {y}"
    except (ValueError, IndexError):
        return str(iso or "-")


def date_short(iso) -> str:
    try:
        y, m, _d = (int(p) for p in str(iso)[:10].split("-"))
        return f"{MONTHS[m - 1][:3]} {str(y)[2:]}"
    except (ValueError, IndexError):
        return str(iso)


def cell_text(matrix, cell) -> str:
    """'5x4' -> '5x4 (skor 20, EXTREME)'; None -> '-'."""
    return f"{cell} (skor {matrix.score(cell)}, {matrix.zone(cell)})" if cell else "-"


def chip(zone: str, text: str) -> str:
    return f"<span class='chip' style='background:{ZONE_COLORS.get(zone, '#d9d8d3')};color:{ZONE_TEXT.get(zone, '#0b0b0b')}'>{e(text)}</span>"
