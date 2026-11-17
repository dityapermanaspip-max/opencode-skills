# Custom report formats (on request)

The engine's `report` stays the default. It writes the canonical `99-Laporan/Laporan-<year>.md` and `.csv`, and with `--pdf` the
`.html` and `.pdf`, following ISO 31000 clause 6.7. Do not change those files or the engine's section order to satisfy a
requested template.

A custom report is an **additional** document for a specific recipient or regulation (for example a Perwali/Perda reporting
outline, an inspectorate format, or a bank/insurer template). Build it from the vault as free text when the user asks for a
named format.

## Rules

1. Ask for the outline, or read it from the regulation the user points at. If the user only says "follow Perwali", extract the
   outline from the document and repeat it back before writing anything.
2. Leave the default files untouched. Name the custom note `99-Laporan/Laporan-<year>-<slug>.md`, where `<slug>` is a short
   Latin slug of the format (e.g. `perwali-kendari`). If the user wants a PDF, render it from a separate HTML with the same
   base name; never overwrite `Laporan-<year>.html` or `.pdf`.
3. The vault is the only source of facts. Read values with `show`, `list`, `status` and the default report. Never invent
   scores, dates, amounts, owners or prose. Ratings stored in the vault are still proposals, so carry the same caveat into
   the custom report.
4. Map the requested outline to what exists. Usual mappings:
   - "Penetapan konteks/tujuan" -> mandates, objectives, indicators, processes, matrix, appetite.
   - "Hasil identifikasi risiko" -> risk events, PRE anchors, process and indicator.
   - "Hasil analisis risiko" -> active cell, score, zone, appetite status, heat map.
   - "Pengendalian sudah ada / masih dibutuhkan" -> installed controls with effectiveness, plans and their status.
   - "Rencana Tindak Pengendalian (RTP)" -> plans (`PLN-nnn`): action, PIC, target date, budget, status.
   - "Pemantauan" -> KRI and incidents; both are allowed to be empty.
5. Templates often ask for sections the vault does not hold (e.g. "kondisi lingkungan pengendalian saat ini", "rancangan
   informasi dan komunikasi", the gap between planned and realised quarterly activities). Write a short honest line such as
   "Belum tersedia di vault" and list the input needed from the user. Do not fill such a section with plausible prose.
6. Add a short provenance note at the top or bottom: which format was requested, that it was assembled from vault notes,
   that the default ISO 31000 report remains the canonical output, and which ratings still need owner confirmation.
7. Run `check` before generating. The custom note is free text, so the engine does not validate it; read it once against
   `status` and the default report for consistency.
8. Summarise in Indonesian: name both the default and the custom file, and say which sections could not be filled.

## Jurisdiction

A regulation may belong to a different region than the organisation in the vault. Treat it as a format and method reference
and say so in the provenance note; do not present it as the binding legal basis for the organisation. Ask the user whether
to substitute the local regulation.
