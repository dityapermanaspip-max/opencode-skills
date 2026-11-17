# Bowtie renderer (SVG + Markdown)

The renderer only **draws** data that is already in the vault. It does not create risk events, causes, impacts, controls,
KRI or scores. Branches come from the `## Penyebab` and `## Dampak` sections of a risk note and must have been accepted through
`draft new --kind bowtie` -> `draft accept` (see `drafting-rules.md`). Controls on a bowtie are **picked by a person** with
`bowtie attach`, as in the web app.

## Commands

```
bowtie show RSK-050                                   # branch keys, picks so far, controls that may be picked
bowtie attach RSK-050 CTL-005 [CTL-001 ...] --branch c1 [--branch c4.0 ...]
bowtie detach RSK-050 [CTL-005] --branch c1           # no control id: every control on that branch
bowtie render RSK-009 [RSK-010 ...] [--out FOLDER]
bowtie render --above-appetite [--out FOLDER]
```

- `--branch` is a branch key from `bowtie show` (`c1` = second cause, `c4.0` = first child of the fifth cause, `i0` = first
  impact) or the branch text (exact, else one unique part of it). Ambiguous or unknown: the command refuses and lists the keys.
- `attach` accepts only a control that is **installed on an evaluation of this risk in the working year** (`control add`,
  or a DONE plan). Anything else is refused with the controls that are installed. Do not pick for the user: show the options
  and let them choose. Preventive, detective and corrective controls may sit on any branch; the type is shown, not enforced.
- The pick is stored in the risk note, section `## Kontrol bowtie` (table `Cabang | Kontrol`), by branch **text**, so it
  survives re-ordering. `check` warns when a branch was renamed/deleted or the control left the evaluation (a WARN, not an ERROR).
- Without `--out`, render writes to `99-Laporan/Bowtie/`. `--above-appetite` selects every risk above the appetite of the
  working year, using the same profile as `status`/`report`; never build that list by hand.
- A risk with no `Penyebab` **and** no `Dampak` section is refused.
- `attach`/`detach` write the risk note and the ledger (`LOG.md`); `render` only writes files under the output folder.

## Output

For each risk the renderer writes:

- `RSK-nnn.svg`: a standalone SVG (no external fonts or libraries). Causes on the left, the risk in the centre, impacts on
  the right, both sides centred on the risk. Each side is a tree: a sub-cause sits one column further left and is joined to
  its parent, a sub-impact one column further right; first-level branches join the risk. The centre carries the active
  value, score, zone and appetite from the engine, so the diagram matches `status` and `report`.
- Chips on the diagram: a round **filled** badge is a KRI (colour = engine status), a **boxed** chip with a dot is a control
  (dot = effectiveness on the evaluation; the weakest one when the control sits on several evaluations of the risk). Controls
  installed on the evaluation but not picked for a branch are listed in a strip under the diagram, so they stay clickable.
- **Click-to-open detail panels** for every KRI and control: title, type, effectiveness per evaluation, source plan, notes,
  the branches it is picked for (control); measured quantity, unit, type, direction, thresholds, watched branch, newest
  readings (KRI). They are plain SVG + CSS `:target` (no script), so they work when the `.svg` is opened in a browser or an
  Obsidian "open in default app". An SVG **embedded in a note is drawn as an image and stays static**; do not promise popups
  inside Obsidian. The Markdown note carries the same details as tables for that reason. Hovering a chip shows a short tooltip.
- `RSK-nnn.md`: the tree as Markdown (KRI and controls marked on each branch), the SVG link, a `Kontrol terpasang` table
  (including picks that no longer fit), a KRI table with thresholds and the newest reading, and the source note path.

## KRI overlay

Active KRIs linked to the risk (`risk: [[RSK-nnn]]`, status `ACTIVE`) are placed from their `watch` field:

- `watch: RISIKO` (or empty) -> centre node.
- Otherwise the renderer matches `watch` against each cause/impact text and category, including children, using the same
  normalisation as draft deduplication (`gv_draft.norm`). It marks every matching branch. When nothing matches, the KRI
  is shown on the centre node and listed in the Markdown table; tell the user that the watch text did not match a branch
  and ask them to fix `watch` with `set KRI-nnn watch=...`.
- The badge colour follows the engine's KRI status (`current_status`): hijau, kuning, merah, abu-abu when a threshold or
  reading is missing. The renderer never decides the colour and never sets a threshold.

## Rules

1. Never edit the SVG/Markdown by hand to add a cause, an impact, a control or a score: change the risk note, the evaluation
   or the pick (`bowtie attach`) and render again.
2. A retired KRI is not drawn.
3. A risk with only one side filled is drawn, with "Belum ada cabang pada catatan risiko." on the empty side.
4. Say what is not verified: the popups were checked by opening the SVG at each panel's `#p-ID` target in a browser, which is
   what a click does; the layout is tuned for branch texts of up to about 31 characters per line and very long texts wrap.

## Code map

`gv_bowtie.py` (render, Markdown, which controls/KRI go where) · `gv_bowtie_svg.py` (tree layout and drawing) ·
`gv_bowtie_pop.py` (colours, text helpers, the panels) · `gv_bowtie_data.py` (branch keys, attach/detach/show, `check` findings).
