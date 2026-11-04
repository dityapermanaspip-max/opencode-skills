---
name: long-document-loop
description: Analyze folders of long PDFs, scans or text and author long documents (contracts, policies, reports) that do not fit one model call. Use when a document exceeds a single context window, when a task spans many files, when extraction needs OCR, when output must keep page/clause coverage without duplicates, or when a long generation must be resumable. Covers deterministic slicing, context carry, per-part persistence, coverage verification, and final stitching.
---

# Long document loop

One pattern for two jobs:

- **Read**: a folder of long documents to inventory, extract, slice, analyze, and aggregate.
- **Write**: a long deliverable (contract, policy, report, template) generated part by part from a source or an outline.

Both are the same contract. Only the prompts and the final merge differ.

If the source fits one call, **do not use this skill**. Estimate first: ~1 token per 4 characters; if
source + instructions + output fit comfortably in the model's context, single-shot is better.

## The contract

1. **Inventory first.** List every input with size, pages, hash, and type. Deduplicate by hash. Decide
   which files need OCR (no text layer / low characters per page) and say so before processing.
2. **Slice deterministically.** Boundaries come from the document structure, never from the model.
   Same input must produce byte-identical parts on every run.
3. **One part per call.** Every call gets: part `i/N`, the part text only, the carried state, and the
   output schema. No call ever sees another part's raw text.
4. **Carry state, not raw output.** Pass a compact running summary, the list of accepted items
   (`known`), a do-not-repeat list, and counters (numbering, totals). Raw previous output is a last
   resort and must be summarized first.
5. **Persist each part before the next.** One file per part plus a manifest. A crash or a closed tab
   must lose at most the part in flight, never the finished ones.
6. **Verify coverage, then stitch.** Every page, line, clause, or source range must be accounted for
   exactly once. Stitch last, in one small pass that sees only summaries and identifiers.

## Slicing rules

Priority order for boundaries:

1. Explicit page markers (`===== HALAMAN n =====`, form feeds, PDF page boundaries).
2. Semantic structure: chapters/`BAB`, articles/`Pasal`, sections, numbered headings, `ARTICLE`.
3. Paragraph/line boundaries, never mid-sentence.

Default caps (tune to the backend; leave 20–30% headroom under its hard cap):

| Limit | Default | Why |
|---|---|---|
| pages per part | 8 | OCR pages and table pages are heavy |
| non-blank lines | 300 | dense financial/legal text hits this before pages |
| characters | 28,000 | stays under 30k/60k request caps |

Rules that prevent most failures:

- Cut at the last complete page or clause **before** the cap; do not split a table, a signature block,
  or a clause list across parts unless you also carry its header into the next part.
- Keep each part self-contained: repeat the document title, parties, and defined terms that the part
  uses.
- If a single indivisible unit (one giant table, one page of 40k chars) exceeds the cap, downscale:
  extract that unit alone, or split by rows/columns with an explicit header repeat.
- Record every part's range (`from`–`to` page, line count, char count) in the manifest.

## Manifest and resume

Write a manifest next to the parts. It is the source of truth, not the chat history.

```json
{
  "source": "scan/contract-2026.pdf",
  "sha256": "…",
  "pages": 212,
  "parts": [
    {"id": 1, "from": 1, "to": 8, "lines": 244, "chars": 21110, "status": "done", "output": "parts/001.json"},
    {"id": 2, "from": 9, "to": 16, "lines": 300, "chars": 27980, "status": "pending", "output": null}
  ]
}
```

- `status`: `pending` → `running` → `done` | `failed` | `skipped`.
- On resume, skip `done`; retry `failed` only after reading its error. Never silently retry a part that
  may already have been committed to a database or file — make the write idempotent (upsert by part id
  or hash) or check before writing.
- Delete a part's output **and** reset its status together; a half-deleted pair causes duplicate rows.

## Read workflow (folder analysis)

1. Inventory: `find`, `pdfinfo`, or PyMuPDF; record pages, text-layer ratio, hash.
2. Extract: text layer first; OCR only pages whose extracted text is below a threshold (for example
   fewer than 40 characters). Prefix every page with its number so citations survive slicing.
3. Reduce if many files: per-document notes first (one part at a time), then a cross-document synthesis
   that reads only the notes. Never concatenate a folder into one prompt.
4. Every claim keeps a citation: `file`, `page`, and the part it came from.
5. Parallelism: independent documents may run 2–3 at a time; ordered parts of one document must stay
   sequential when later parts depend on carried state.

OCR recipes (pick what is installed):

```bash
pdftotext -layout input.pdf -            # text layer, fast
pdftoppm -r 300 -png input.pdf page      # pages for OCR
tesseract page-001.png - -l ind+eng      # per-page OCR
```

```python
import pymupdf  # pages with little text -> render + OCR
doc = pymupdf.open(path)
for i, page in enumerate(doc):
    text = page.get_text("text")
    if len(text.strip()) < 40:
        pix = page.get_pixmap(dpi=300)
        # pytesseract.image_to_string(Image.open(io.BytesIO(pix.tobytes("png"))))
```

Warn per page when OCR fails or reads nothing. A silent empty page is a data-loss bug.

## Write workflow (long contract, policy, report)

1. Extract the skeleton first: headings, clause numbers, defined terms, parties, annexes.
2. Use the skeleton as the slice map. One part = one chapter/clause group/schedule, not a character
   count.
3. Carry per part: defined-terms glossary, party names, numbering state, cross-references already
   emitted, and a `do_not_repeat` list.
4. Ask for structured output (JSON or Markdown with explicit heading levels). Ask for **only this
   part**, never "continue until done".
5. Persist each part as its own file or DB row with a stable id; assemble last.
6. Final pass sees the assembled outline plus short summaries, never the full text: fix numbering,
   resolve cross-references, check that every clause in the skeleton exists, and check defined terms
   are used before they are defined.

Numbering is state, not model judgement:

```json
{"chapter": 3, "article": 14, "paragraph": 2, "annex": "B"}
```

Give the model the current counters and require it to return the updated counters with the part.

Cross-part hazards and the fix:

| Hazard | Fix |
|---|---|
| numbering restarts or skips | carry counters, renumber in the final pass |
| a table spans two parts | repeat header rows, merge at stitch time |
| defined term used before definition | carry glossary; move definition in final pass |
| duplicated clauses | maintain `known` clause ids and reject repeats |
| cross-reference points to a missing clause | final pass validates every reference |

## Prompt template (per part)

```text
You are processing part {i} of {n} of "{title}".
Scope: pages {from}-{to} (or clause {first}-{last}). Only use this part.
Carried state:
  known: {known_list}
  numbering: {counters}
  glossary: {terms}
  do_not_repeat: {items}
Task: {extract | draft | review}
Return ONLY this JSON: {schema}
If something is missing or unreadable, put it in "warnings"; do not invent it.
```

Cap output tokens per part. If a part's result is empty, stop and inspect the slice before continuing;
an empty result multiplied by N is a wasted run.

## Verification checklist

Run these before declaring success:

- **Coverage**: part ranges cover the source with no gaps or overlaps; sum of pages/lines equals the
  total (minus explicitly skipped ranges, each with a reason).
- **Uniqueness**: no duplicated clause ids, record ids, or findings across parts.
- **Citations**: every cited page exists and is inside that part's range.
- **Numbering**: continuous, no restart, every reference resolves.
- **Determinism**: re-running the slicer produces identical hashes.
- **Failures**: every `failed`/`warned` part is reported, not hidden.
- **Assembly**: the stitched output opens cleanly (docx/pdf) and has the expected headings/annexes.

## Budgets and failure handling

- Cost ≈ parts × (input + output tokens). Show the user the part count and the expected wall time
  before starting a large run.
- Above ~10 parts or ~10 minutes, run it as a background job with progress, not one HTTP request.
- Retry a part at most twice, with the error appended and the slice unchanged. If it still fails, mark
  `failed`, keep going, and report the gap at the end.
- Stop conditions: auth/permission errors, missing input, slice with zero content, three consecutive
  failures — stop and ask instead of burning the run.

## Anti-patterns

- Chunking by raw characters and cutting mid-clause or mid-table.
- Asking the model to decide slice boundaries, or to "continue from where you left off".
- Feeding every previous part's raw text back in (context blow-up, drift, repetition).
- One final prompt that concatenates all parts.
- Re-running the whole loop after one failed part.
- Hiding skipped pages, OCR warnings, or dropped clauses.
- Parallelizing ordered parts that depend on carried numbering or state.
- Declaring done without the coverage check.

## Minimal slicer

`scripts/slice.py` (stdlib only) splits a text file on page markers when present, otherwise on lines,
and writes `parts/` plus `manifest.json`. Use it as the reference implementation, or port the same rules
into the project's language.
