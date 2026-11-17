# Matrix and appetite

## The matrix
A matrix has `max_likelihood` x `max_impact` levels (2 to 10 each, usually 5x5). A cell is written `LxI` (3x4 = likelihood 3, impact 4).
The score of a cell is likelihood x impact unless the matrix overrides it in its `Zona sel` table. `matrix show MTX-001` prints the
grid of scores and the zones in use.

Default zones, by the cell's share of the maximum score:

| Share of maximum score | Zone |
|---|---|
| up to 16% | LOW |
| up to 36% | MODERATE_LOW |
| up to 56% | MODERATE |
| up to 76% | HIGH |
| above 76% | EXTREME |

For 5x5 (max 25): LOW 1-4, MODERATE_LOW 5-9, MODERATE 10-14, HIGH 15-19, EXTREME 20-25. To change a cell's zone or score, add a row to the
`Zona sel` table of the matrix note (`Kemungkinan | Dampak | Skor | Zona`); the engine uses it everywhere.

## Labels and criteria
The matrix note has tables `Label kemungkinan`, `Label dampak` (level, label) and `Kriteria dampak` (category, level, description). Fill them WITH
the user: they define what "impact 4" means for money, reputation, law and service. Do not make them up; offer a first draft from the
organisation's own risk policy if the user has one, and mark it as a proposal.

## Appetite
The appetite is a **threshold score per matrix per fiscal year**: `appetite MTX-001 2026 9`. A risk whose active score is at or below
the threshold is DI_BAWAH_APPETITE (within appetite); above it is DI_ATAS_APPETITE. No threshold for the year = BELUM_ADA_APPETITE; no
active value yet = BELUM_DIEVALUASI. The threshold must be between 1 and the maximum score. It is a decision of the organisation's
leadership: ask for it, do not pick it. If the user wants options, show what each candidate means ("batas 9 = semua risiko MODERATE_LOW
ke bawah di dalam appetite").

## Changing the matrix
Only through the close: `matrix activate MTX-002` before `close`; next year's evaluations start empty on the new matrix (see risk-cycle.md).
Evaluations already created keep their matrix. Trend is only compared inside one matrix.
