"""Stylesheet of the HTML/PDF report: A4, print first, no external fonts or files."""

CSS = """
@page { size: A4; margin: 18mm 15mm 20mm 15mm;
        @bottom-left { content: var(--foot); font: 7.5pt 'Segoe UI', Arial, sans-serif; color: #6b6a65; }
        @bottom-right { content: 'Halaman ' counter(page) ' dari ' counter(pages); font: 7.5pt 'Segoe UI', Arial, sans-serif; color: #6b6a65; } }
:root { --ink: #0b0b0b; --ink2: #52514e; --muted: #6b6a65; --line: #d9d8d3; --soft: #f3f2ef; --series: #2a78d6; --crit: #d03b3b; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font: 9.2pt/1.45 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; color: var(--ink); margin: 0; }
h1 { font-size: 21pt; line-height: 1.15; margin: 0 0 4px; letter-spacing: -.2px; }
h2 { font-size: 13.5pt; margin: 22px 0 6px; padding-bottom: 4px; border-bottom: 1.5px solid var(--ink); break-after: avoid; }
h3 { font-size: 10.5pt; margin: 14px 0 4px; break-after: avoid; }
h4 { font-size: 9.2pt; margin: 8px 0 2px; color: var(--ink2); break-after: avoid; }
p { margin: 4px 0 6px; } small { color: var(--muted); } code { font: 8.4pt Consolas, monospace; background: var(--soft); padding: 0 3px; border-radius: 3px; }
.cover { padding: 18px 0 14px; border-bottom: 3px solid var(--ink); margin-bottom: 14px; }
.kicker { font-size: 8.5pt; letter-spacing: 1.2px; text-transform: uppercase; color: var(--ink2); margin-bottom: 8px; }
.meta { display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px 14px; margin-top: 12px; font-size: 8.5pt; }
.meta b { display: block; font-size: 7.5pt; letter-spacing: .6px; text-transform: uppercase; color: var(--muted); font-weight: 600; }
.note { border-left: 3px solid var(--ink2); background: var(--soft); padding: 6px 10px; margin: 8px 0; font-size: 8.6pt; }
.tiles { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin: 8px 0 10px; }
.tile { border: 1px solid var(--line); border-radius: 6px; padding: 7px 9px; break-inside: avoid; }
.tile .v { font-size: 19pt; font-weight: 600; line-height: 1.1; } .tile .l { font-size: 7.8pt; color: var(--ink2); }
table { border-collapse: collapse; width: 100%; margin: 6px 0 10px; font-size: 8.3pt; }
thead { display: table-header-group; } tr { break-inside: avoid; }
th { background: var(--soft); text-align: left; font-weight: 600; padding: 4px 6px; border-bottom: 1.2px solid var(--ink2); vertical-align: bottom; }
td { padding: 4px 6px; border-bottom: 0.6px solid var(--line); vertical-align: top; }
td.r, th.r { text-align: right; font-variant-numeric: tabular-nums; } td.c, th.c { text-align: center; }
.chip { display: inline-block; padding: 0 6px; border-radius: 9px; font-size: 7.6pt; font-weight: 600; white-space: nowrap; line-height: 1.5; }
.cols { display: grid; grid-template-columns: 1fr 1fr; gap: 0 18px; }
.heat { width: auto; margin: 6px 0; } .heat th { background: none; border: 0; text-align: center; font-size: 7.6pt; padding: 2px 4px; }
.heat th small { display: block; font-weight: 400; } .heat td { width: 68px; height: 44px; text-align: center; vertical-align: middle; border: 2px solid #fff; padding: 0; position: relative; }
.heat .sc { position: absolute; left: 4px; top: 2px; font-size: 7pt; opacity: .85; } .heat .n { font-size: 15pt; }
.legend { display: flex; flex-wrap: wrap; gap: 4px 14px; font-size: 8pt; margin: 4px 0 8px; } .legend i { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 4px; vertical-align: -1px; }
.card { border: 1px solid var(--line); border-radius: 6px; padding: 8px 11px; margin: 8px 0; break-inside: avoid; }
.card .head { display: flex; gap: 8px; align-items: baseline; justify-content: space-between; } .card .t { font-weight: 600; font-size: 9.6pt; }
.card .sub { color: var(--ink2); font-size: 8.2pt; margin: 1px 0 4px; } .card ul { margin: 2px 0 4px 16px; padding: 0; } .card li { margin: 0; }
.vals { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin: 5px 0; } .vals div { background: var(--soft); border-radius: 4px; padding: 3px 7px; font-size: 8.2pt; }
.vals b { display: block; font-size: 7.4pt; color: var(--muted); text-transform: uppercase; letter-spacing: .5px; font-weight: 600; }
.vals .on { outline: 1.5px solid var(--ink); background: #fff; }
.chart { margin: 6px 0 10px; break-inside: avoid; } .chart svg { width: 100%; height: auto; display: block; }
.chart text { font-family: 'Segoe UI', Arial, sans-serif; fill: #0b0b0b; } .chart .mut { fill: #52514e; }
pre { font: 8pt/1.4 Consolas, monospace; background: var(--soft); padding: 7px 10px; border-radius: 4px; white-space: pre-wrap; }
.pb { break-before: page; } .keep { break-inside: avoid; } .lead { break-after: avoid; } .nw { white-space: nowrap; }
"""
