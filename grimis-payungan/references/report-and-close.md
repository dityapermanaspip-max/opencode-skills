# Report and close

## `status` (and `status --write`)
Counts for the working year: risks evaluated, within / above appetite, ACTUAL missing (only while the period is open), plans due within
14 days (PLANNED or IN_PROGRESS with a target date up to 14 days ahead, including overdue), KRI colours, incident reports waiting, the four
consistency flags (see risk-cycle.md) and anchors that have no evaluation this year. `--write` also refreshes `00-Dashboard.md`.

## `report [--year Y]`
Writes `99-Laporan/Laporan-<year>.md` and `.csv`. Sections follow the ISO 31000 cycle: 1 konteks, 2 peta risiko (count of risks per active
cell), 3 profil risiko (sorted by score; active value, cell, score, zone, appetite status, controls, plans, incidents, trend), 4 risiko di
atas appetite, 5 efektivitas kontrol (installed controls by effectiveness, plus a note on controls without evidence; the profile table and the CSV column `Kontrol tanpa bukti` show them too), 6 realisasi rencana (plans by status, total budget), 7 KRI,
8 insiden tahun ini, 9 catatan data (only for the working year). The CSV uses `;` as delimiter and a UTF-8 BOM so Excel opens it; one row
per evaluation. After running it, summarise the findings for the user (what is above appetite, what is red, what is overdue) and name the
files. The report contains only what is in the vault: say so if the data is thin.

## `report --pdf`
Also writes `99-Laporan/Laporan-<year>.html` (one self-contained file: inline CSS and SVG, no scripts, no web fonts) and prints it to
`Laporan-<year>.pdf` with headless Edge, Chrome or Chromium (found automatically; set `GRIMIS_BROWSER` to a program path to choose one).
No browser found, or the print fails: the HTML is kept and the command says so; tell the user to open it and print to PDF (A4, background
graphics on). The PDF follows ISO 31000:2018 clause 6: cover and summary, 1 scope, context and criteria (6.3), 2 risk assessment (6.4: register,
heat map, scores against appetite, one card per risk, Monte Carlo), 3 treatment (6.5), 4 monitoring and review (6.6: KRI charts, incidents),
5 recording and reporting (6.7: data notes, `check` result, drafts still waiting). Zone colours always come with the zone name.
Open it and look before telling the user it is fine: tables that break badly or text that overflows are not caught by the engine.

## Custom format on request

`report` and `report --pdf` are the default and remain the canonical output. If the user asks for a specific template
(a regulation outline, an inspectorate format), produce an **additional** note from the same vault data; do not overwrite
`Laporan-<year>.*` or reorder the engine's sections. Read `references/custom-report.md` first: it covers naming, the mapping
from the requested outline to vault notes, how to handle sections the vault cannot fill, and the jurisdiction caveat when the
template comes from another region.

## Close, in order
1. `check` and fix errors. 2. `status`: what is missing? 3. `open-period`. 4. Enter every ACTUAL (`rate EVA-... --actual LxI`); ask the
user for each value, or for the source of the year-end assessment. 5. Make sure `active_matrix` is the matrix for next year
(`matrix activate`). 6. Tell the user what the close does (risk-cycle.md) and get a clear yes. 7. `close`. 8. Read the engine's summary to
the user: evaluations closed, controls carried, plans NOT_REALISED, blank new evaluations, and the evaluations that need their controls
installed again (each with its evidence files in the new evaluation's `08-Bukti/<EVA>/<CTL>/` folder). 9. `check`, then `report --year <closed year>` if wanted (it works on the closed evaluations).
