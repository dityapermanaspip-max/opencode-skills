---
name: grimis-payungan
description: "Run enterprise risk management (ISO 31000) from an Obsidian vault of Markdown notes, with no web app or database: context (mandate, objectives, indicators, processes), risk matrix and appetite, risk identification and bowtie drafts, evaluation with the four risk values (inherent, residual, expected, actual), controls and mitigation plans, KRI, incident register, Monte Carlo suggestion, the default ISO 31000 report, ad-hoc report formats on request, and the annual close. Use when the user mentions a risk register, register risiko, bowtie, KRI, risk appetite, matriks risiko, tutup buku risiko, or asks to build, rate, review, report or close a risk register for an organisation, in Indonesian public-sector or corporate settings. Output to the user is Indonesian."
---

# grimis-payungan: risk management in an Obsidian vault

This skill runs the enterprise risk cycle of ONE organisation on a folder of Markdown notes (governance, risk and incident
management): **Claude drafts and explains, a Python engine enforces the rules, a person decides.**
Everything the user reads is Indonesian. This file and the references are English.

Run the engine with `python -P "<skill-dir>/scripts/grimis.py" --vault <vault-folder> <command>`
(set `GRIMIS_VAULT` once instead of `--vault`; on Windows also `PYTHONIOENCODING=utf-8`). Python 3.11+, standard library only.
`python -P ... selftest.py` runs the engine's self-test.
Works the same in Claude Code and OpenCode. Use `python3` where `python` is not Python 3.11+. Where `-P` is unknown (Python older than 3.11),
upgrade Python rather than dropping it: the flag keeps a stray `random.py` or `json.py` in the working folder from shadowing the standard library.
Two finished vaults to learn from are in `examples/` (`demo-diskompen` from a performance report, `demo-vault` over three years).

## Hard rules (never bend these)

1. **Never invent a score, level, threshold, amount or date.** Ratings come from the user, from the matrix, or from a
   computed value. The Monte Carlo cell is a suggestion until the user says "pakai" and you run `rate ... sim`.
2. **AI output is a draft.** Anything you propose goes through `draft new` and lands in the register only with `draft accept`
   after the user chose the items. Do not write proposed risks, causes, impacts or KRIs straight into notes.
3. **The engine decides, you report.** The active value, trend, KRI colour, appetite status, close and its refusals come from
   the engine. Never compute or "correct" them by hand, and never edit `active_type`, `active_cell`, `trend`, `closed` in a note.
4. **Use the CLI for anything with a rule** (`new`, `set`, `rate`, `control`, `plan`, `kri`, `simulate`, `draft`, `bowtie attach|detach`,
   `open-period`, `close`). Free text (descriptions, bowtie bullets, comments in the body) may be edited directly in the note.
5. **Run `check` after any direct edit of a note** and before a report or the close. Fix every ERROR; explain every WARN.
6. **A refusal is information.** When the engine refuses (a missing ACTUAL, a fourth KRI, a closed year), tell the user what and
   why in plain Indonesian. Do not look for a way around it.
7. **Say what you did not verify.** This is a simulation: one user, no permissions, no approval flow. Do not claim it equals
   a full multi-user risk-management system, and do not present drafts or suggested cells as findings.
8. **Existing controls are evidence-based.** A control counts as existing only when a person has put at least one evidence file
   (SOP, app screenshot, photo, CCTV still) in `08-Bukti/<EVA>/<CTL>/`. Never create, copy, rename or invent evidence to satisfy
   the engine, and never decide something is a control from its title alone: ask for the file, name the folder, wait.
   `evidence sort` moves files dropped in the wrong folder. See `references/risk-cycle.md`.

## Workflow

Work in this order; a step may be skipped only if its notes already exist (`status` and `list <jenis>` show what exists).

1. **Find or make the vault.** A vault is a folder with `GRIMIS.md`. None yet: ask for the organisation name and the working
   year, then `init <folder> --org "<nama>" --year <tahun>`. Open it in Obsidian if the user wants to browse.
2. **Matrix first.** `new matriks title=... max_likelihood=5 max_impact=5`, `matrix activate MTX-001`, then
   `appetite MTX-001 <tahun> <batas skor>`. Ask the user for the appetite; offer the score bands in
   `references/matrix-and-appetite.md` as options, not as the answer. Fill the labels and impact criteria with the user.
3. **Context.** Mandate -> objective -> indicator -> process (`new mandat|sasaran|indikator|proses`). A process lists the
   indicators it serves in `indicators=IND-001,IND-002`. From a document (PDF, regulation, strategic plan) draft the whole tree
   with `draft new konteks`; read `references/drafting-rules.md` first. PDFs without a text layer need OCR (use whatever OCR the
   environment offers; read figures by eye).
4. **Identify risks.** Per process, draft risk events (`draft new risiko --target PRS-001`). Before drafting read the dictionary
   (`list risiko`) and set `match` when the same event already exists. After acceptance each risk is attached to a
   process and indicator as an anchor (`PRE-nnn`). Then bowtie per risk (`draft new bowtie --target RSK-001`); after acceptance,
   draw it with `bowtie render RSK-001` (SVG + Markdown). Controls on a bowtie are picked by the user, from the controls
   installed on the risk's evaluation: `bowtie show RSK-001` lists the branches and the options, `bowtie attach` records the
   user's choice (never choose for them). See `references/bowtie-render.md`.
5. **Evaluate.** `new evaluasi pre=PRE-001` (year and matrix default to the working year and the active matrix), then
   `rate EVA-... --inherent 4x4`, install controls (`control add`, refused until the person has put evidence files in
   `08-Bukti/<EVA>/<CTL>/`; `evidence show` lists the gaps), rate `--residual`, plan treatments (`new rencana ...`),
   rate `--expected`. Read `references/risk-cycle.md`: which value is active follows the controls and the plans, and ACTUAL is
   only input for the close. Classify every SOP by its start date: already in force before this year -> existing control
   (`CTL` + `control add`); newly designed or established this year -> `PLN` + `plan done`. Keep the two apart; see
   `references/risk-cycle.md`. Offer `simulate` once the risk has incidents.
6. **Monitor.** KRI drafts (`draft new kri`), thresholds set by a person (`kri threshold ... --reason`), readings (`kri read`),
   incidents (`new insiden`), public incident reports (`new laporan`; approve or ignore with `set LAP-001 status=...`). Start a
   plan with `plan start`, finish it with `plan done` (this creates the control and installs it). KRI positions on a bowtie are
   drawn by `bowtie render` from the KRI `watch` field; `watch=RISIKO` lands on the centre node.
7. **Look and report.** `status` (counts, appetite, KRI colours, consistency checks), `status --write` (dashboard note),
   `report [--year] [--pdf]` (Markdown + CSV under `99-Laporan/`; `--pdf` adds a formatted ISO 31000:2018 report as HTML and PDF, printed by
   Edge or Chrome, and still leaves the HTML when no browser is found). Summarise for the user; point to the files.
   This report is the default and stays canonical. When the user asks for another template (a Perwali/Perda outline, an
   inspectorate format), also produce a separate custom note from vault data without touching the default files; read
   `references/custom-report.md` first. Bowtie diagrams live separately under `99-Laporan/Bowtie/`.
8. **Close the year.** `open-period`, every `rate ... --actual`, then `close`. Read `references/report-and-close.md` first and
   tell the user what the close will do before running it. Report existing controls and plan-born controls separately: only
   controls from a DONE plan are carried; existing controls must be installed again by hand and the engine lists them.

## Commands at a glance

| Need | Command |
|---|---|
| Create / inspect | `init`, `new <jenis> k=v ...`, `show ID`, `list <jenis>`, `set ID k=v ...` |
| Values | `rate EVA [--inherent LxI] [--residual ..] [--expected ..] [--actual ..]` (a cell is written `3x4`; `sim` uses the saved suggestion; `-` clears) |
| Controls and plans | `control add\|remove EVA CTL [--status EFFECTIVE\|PARTIAL\|INEFFECTIVE]` (add needs evidence files, see below), `plan start\|done PLN [--evidence ..]` |
| Evidence | `evidence show [EVA]` (controls without evidence, folder to use), `evidence sort [--dry-run]` (move files dropped in the wrong folder to `08-Bukti/<EVA>/<CTL>/`) |
| KRI | `kri read KRI VALUE [--date]`, `kri threshold KRI --amber A --red R --reason ".."`, `kri retire KRI` |
| Simulation | `simulate EVA [--iterations N] [--percentile P] [--seed S]` |
| Matrix | `matrix show\|activate MTX`, `appetite MTX YEAR SCORE` |
| Drafts | `draft new --kind konteks\|risiko\|bowtie\|kri [--target ID] --file items.json`, `draft show\|accept\|reject DRF [--items 1,3]` |
| Views | `status [--write]`, `check`, `report [--year] [--pdf]` |
| Bowtie | `bowtie render RSK-001 [RSK-002 ...] [--above-appetite] [--out FOLDER]` (SVG + Markdown, KRI via `watch`, clickable KRI/control panels in the SVG), `bowtie show RSK-001`, `bowtie attach\|detach RSK-001 CTL-001 --branch c1` |
| Custom format | (no CLI) `references/custom-report.md`: an extra note from vault data when a specific template is requested |
| Year | `open-period`, `close [--year]` |

Jenis: `mandat sasaran indikator proses matriks risiko kontrol pasang evaluasi rencana kri insiden laporan`. Field names per
jenis are in `references/vault-model.md`. IDs equal file names (`RSK-001`, evaluation `EVA-2026-001`).

## Talking to the user

- Indonesian, plain words, ISO 31000 terms where they exist (konteks, identifikasi, analisis, evaluasi, perlakuan, pemantauan).
- When a step needs a decision (the appetite, which drafted items to keep, whether to apply the simulated cell, closing the year),
  put the options and your recommendation in one short message and wait.
- After each command batch report only what changed and what the engine said about it, including WARN lines. Quote a refusal
  as it was given.
- Keep the user's documents private: do not paste document text into notes beyond what the field needs.

## References (load when the step needs them)

- `references/vault-model.md`: folders, note kinds, fields, id rules, section formats.
- `references/risk-cycle.md`: the four values, active value, controls, plans, SOP lama versus rencana, trend, the close.
- `references/drafting-rules.md`: the rules for drafting risks, bowtie, KRI, context and incident matching, and the JSON shape of each draft.
- `references/matrix-and-appetite.md`: score, zones, appetite and how to set them with the user.
- `references/kri-incidents-simulation.md`: KRI status, incidents, how to read and present the Monte Carlo.
- `references/report-and-close.md`: report sections, CSV columns, close steps and their order.
- `references/custom-report.md`: how to build an extra report in a requested template while keeping the default report canonical.
- `references/bowtie-render.md`: SVG + Markdown rendering of accepted bowties, the KRI overlay, picking controls for branches, and the click-to-open panels.
- `references/limits.md`: what this skill does not do compared with a multi-user risk-management system.

`examples/demo-vault/` is a complete fictional vault ("Instansi Demo", two fiscal years) to open in Obsidian or to copy from.
