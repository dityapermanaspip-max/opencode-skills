"""Bowtie SVG: text helpers, colours, and the click-to-open detail panels for controls and KRI.
The panels are plain SVG + CSS `:target`: a chip is a link to `#p-<ID>` and the panel is shown while that fragment is the
target. It works when the .svg is opened in a browser. An SVG embedded in an Obsidian note is drawn as an image, so it
stays static there (the Markdown note repeats the same details as tables). Standard library only."""

from __future__ import annotations

from gv_kri import readings
from gv_pdf_util import e as esc

KRI_COLOUR = {"green": "#2e7d32", "amber": "#b8860b", "red": "#c62828", "grey": "#6b6b6b"}
KRI_LABEL = {"green": "Hijau", "amber": "Kuning", "red": "Merah", "grey": "Abu-abu"}
EFF_COLOUR = {"EFFECTIVE": "#2e7d32", "PARTIAL": "#b8860b", "INEFFECTIVE": "#c62828"}
INK, CTL_INK = "#1c1c1a", "#3d4f6b"
PANEL_W = 470
CSS = "a{cursor:pointer}.chip:hover .box{stroke:#1c1c1a;stroke-width:1.6}.pop{display:none}.pop:target{display:inline}"


def wrap(text, width: int) -> list[str]:
    words = str(text or "").split()
    lines, cur = [], ""
    for word in words:
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= width:
            cur += " " + word
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines or ["-"]


def lines(x, y, rows, size: float, colour: str = INK, weight: str = "") -> str:
    step = size * 1.32
    attrs = f' font-weight="{weight}"' if weight else ""
    return "".join(f"<text x='{x}' y='{y + i * step:.1f}' font-size='{size}' fill='{colour}'{attrs}>{esc(line)}</text>"
                   for i, line in enumerate(rows))


def worst(evals: list[dict]) -> str:
    """The weakest effectiveness among the evaluations a control sits on."""
    order = ("INEFFECTIVE", "PARTIAL", "EFFECTIVE")
    return min((x["status"] for x in evals), key=lambda s: order.index(s) if s in order else 9, default="EFFECTIVE")


def num(value) -> str:
    return f"{value:g}" if isinstance(value, (int, float)) else str(value)


def limits(kri) -> str:
    f = kri.fields
    if f.get("amber") is None or f.get("red") is None:
        return "belum ditetapkan"
    sign = "≥" if f.get("direction") == "higher_is_worse" else "≤"
    return f"kuning {sign} {num(f['amber'])}, merah {sign} {num(f['red'])}"


def panel(pid: str, tag: str, colour: str, title: str, rows: list[tuple], w: float, h: float, mid: float) -> tuple[str, float]:
    """rows: (label, text or list of texts); an empty value is skipped. Returns (svg, panel height)."""
    head = wrap(title, 56)
    body = []
    for label, value in rows:
        items = value if isinstance(value, list) else [value]
        text = [ln for i, item in enumerate(items) if item not in (None, "")
                for ln in wrap(("• " if isinstance(value, list) else "") + str(item), 64)]
        if text:
            body.append((label, text))
    ph = 50 + 17.2 * len(head) + sum(14 + 14.6 * len(t) + 9 for _l, t in body)
    x = (w - PANEL_W) / 2
    y = max(10, min(mid - ph / 2, h - ph - 10))
    out = [f"<g id='{pid}' class='pop'>",
           f"<a href='#'><rect width='{w}' height='{h}' fill='{INK}' fill-opacity='.38'/></a>",
           f"<rect x='{x}' y='{y:.1f}' width='{PANEL_W}' height='{ph:.1f}' rx='10' fill='#fff' stroke='#8c8a82'/>",
           f"<rect x='{x}' y='{y:.1f}' width='{PANEL_W}' height='28' rx='10' fill='{colour}'/>"
           f"<rect x='{x}' y='{y + 14:.1f}' width='{PANEL_W}' height='14' fill='{colour}'/>",
           f"<text x='{x + 16}' y='{y + 19:.1f}' font-size='11' font-weight='700' fill='#fff'>{esc(tag)}</text>",
           f"<a href='#'><text x='{x + PANEL_W - 16}' y='{y + 19:.1f}' font-size='11' font-weight='700' fill='#fff' "
           f"text-anchor='end'>Tutup ×</text></a>",
           lines(x + 16, round(y + 50, 1), head, 13, INK, "700")]
    cy = y + 50 + 17.2 * len(head) + 6
    for label, text in body:
        out.append(f"<text x='{x + 16}' y='{cy:.1f}' font-size='10' font-weight='700' fill='#66645f'>{esc(label)}</text>")
        out.append(lines(x + 16, round(cy + 15, 1), text, 11))
        cy += 14 + 14.6 * len(text) + 9
    out.append("</g>")
    return "".join(out), ph


def control_panel(ctl, evals: list[dict], on: list[str], w: float, h: float, mid: float) -> tuple[str, float]:
    f = ctl.fields
    status = [f"{x['status']} (pada {x['eva']})" for x in evals]
    plans = [f"{x['plan']} (pada {x['eva']})" for x in evals if x.get("plan")]
    notes = [f"{x['notes']} ({x['eva']})" for x in evals if x.get("notes")]
    kinds = f"{(f.get('control_type') or '-').capitalize()}"
    more = [f"dan {len(on) - 6} cabang lainnya"] if len(on) > 6 else []
    rows = [("Efektivitas", status), ("Kode", f.get("code")), ("Sumber rencana", plans or None),
            ("Catatan", notes or None), ("Dipasang pada cabang", (on[:6] + more) if on else "belum dipasang pada cabang mana pun")]
    return panel(f"p-{ctl.id}", f"KONTROL · {ctl.id} · {kinds}", CTL_INK, f.get("title", ctl.id), rows, w, h, mid)


def kri_panel(kri, status: str, w: float, h: float, mid: float) -> tuple[str, float]:
    f = kri.fields
    direction = "lebih tinggi lebih buruk" if f.get("direction") == "higher_is_worse" else "lebih rendah lebih buruk"
    newest = sorted(enumerate(readings(kri)), key=lambda p: (p[1][0], p[0]), reverse=True)[:5]
    last = [f"{d} = {num(v)}" for _i, (d, v) in newest] or "belum ada pembacaan"
    measured = " ".join(x for x in (f.get("what_measured"), f"({f['unit']})" if f.get("unit") else "") if x)
    rows = [("Yang diukur", measured or None), ("Jenis · frekuensi · arah", f"{f.get('kri_type')} · {f.get('frequency')} · {direction}"),
            ("Ambang", limits(kri)), ("Memantau cabang", f.get("watch") or "risiko (simpul tengah)"), ("Pembacaan terbaru", last)]
    tag = f"KRI · {kri.id} · {f.get('kri_type')} · {KRI_LABEL.get(status, status)}"
    return panel(f"p-{kri.id}", tag, KRI_COLOUR.get(status, KRI_COLOUR["grey"]), f.get("title", kri.id), rows, w, h, mid)
