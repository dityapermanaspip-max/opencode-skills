# Vault model

A vault is a normal Obsidian folder. One note = one object; the file name is the id (`RSK-001.md`). Links in frontmatter are
written `"[[ID]]"` so Obsidian shows them as links. The engine reads and writes a small YAML subset (`key: value`, quoted
strings, `true/false`, numbers, lists such as `["[[IND-001]]", "[[IND-002]]"]` or block lists). Unknown fields (for example
Obsidian `tags`) are kept as they are. Nested YAML maps are not supported and are reported by `check`.

Root file `GRIMIS.md` holds the settings: `org`, `fiscal_year` (the working year), `period_open` (the close period of that
year is open: ACTUAL may be entered and `close` may run) and `active_matrix` (the matrix new evaluations and next year use).
`LOG.md` is append-only (every change), `00-Dashboard.md` and `99-Laporan/` are generated.

## Folders

```
00-Konteks/Indikator/
00-Konteks/Mandat/
00-Konteks/Proses/
00-Konteks/Sasaran/
01-Matriks/
02-Kamus/Kontrol/
02-Kamus/Risiko/
03-Register/
04-Evaluasi/
05-Rencana/
06-KRI/
07-Insiden/
07-Insiden/Laporan/
_Draft/
99-Laporan/
```

## Note kinds and fields

`*` = required. Kinds: `enum:` lists the allowed values, `cell` is `LxI` such as `3x4`, `link:X` points to a note of kind X, `links:X` to several.

### mandat (`MND-nnn`, folder `00-Konteks/Mandat`)

The organisation's authority (law, regulation, strategic plan).

| Field | Kind | Default |
|---|---|---|
| title* | str |  |
| source | str |  |

### sasaran (`SAS-nnn`, folder `00-Konteks/Sasaran`)

A strategic objective that follows a mandate.

| Field | Kind | Default |
|---|---|---|
| title* | str |  |
| mandate* | link:mandat |  |

### indikator (`IND-nnn`, folder `00-Konteks/Indikator`)

A performance indicator of an objective.

| Field | Kind | Default |
|---|---|---|
| title* | str |  |
| objective* | link:sasaran |  |
| unit | str |  |
| target | str |  |

### proses (`PRS-nnn`, folder `00-Konteks/Proses`)

A business process. `indicators` is the indicator-to-process mapping: a risk can only be anchored on an indicator the process serves.

| Field | Kind | Default |
|---|---|---|
| title* | str |  |
| owner | str |  |
| indicators | links:indikator |  |

### matriks (`MTX-nnn`, folder `01-Matriks`)

A risk matrix. Tables in the body hold labels, impact criteria, appetite per year and zone overrides.

| Field | Kind | Default |
|---|---|---|
| title* | str |  |
| max_likelihood* | int |  |
| max_impact* | int |  |

### risiko (`RSK-nnn`, folder `02-Kamus/Risiko`)

Risk dictionary entry: ONE event. Body sections `Penyebab` and `Dampak` (bullet trees), `Saran ditolak`.

| Field | Kind | Default |
|---|---|---|
| title* | str |  |
| description | str |  |
| active | bool | True |

### kontrol (`CTL-nnn`, folder `02-Kamus/Kontrol`)

Control dictionary entry. `code` is the optional business code that a plan's `new_control_code` refers to.

| Field | Kind | Default |
|---|---|---|
| title* | str |  |
| control_type* | enum:preventif|detektif|korektif |  |
| code | str |  |

### pasang (`PRE-nnn`, folder `03-Register`)

The anchor: a risk event on a process through an indicator. Unique per risk, process, indicator.

| Field | Kind | Default |
|---|---|---|
| risk* | link:risiko |  |
| process* | link:proses |  |
| indicator* | link:indikator |  |
| active | bool | True |

### evaluasi (`EVA-nnn`, folder `04-Evaluasi`)

One evaluation per anchor per year. Id is `EVA-<year>-<PRE number>`. Four values plus computed fields. Body: `Kontrol yang ada` table, `Simulasi Monte Carlo`.

| Field | Kind | Default |
|---|---|---|
| pre* | link:pasang |  |
| fiscal_year* | int |  |
| matrix* | link:matriks |  |
| inherent | cell |  |
| residual | cell |  |
| expected | cell |  |
| actual | cell |  |
| active_type | enum:INHERENT|RESIDUAL|EXPECTED |  |
| active_cell | cell |  |
| trend | enum:IMPROVING|WORSENING|STABLE |  |
| closed | date |  |
| sim_suggestion | cell |  |
| sim_date | date |  |

### rencana (`PLN-nnn`, folder `05-Rencana`)

A mitigation plan of an evaluation. Statuses move only through `plan start` / `plan done` and the close.

| Field | Kind | Default |
|---|---|---|
| evaluation* | link:evaluasi |  |
| action* | str |  |
| pic* | str |  |
| target_date* | date |  |
| budget | float | 0 |
| status | enum:PLANNED|IN_PROGRESS|DONE|NOT_REALISED | PLANNED |
| new_control_code | str |  |
| new_control_title | str |  |
| new_control_type | enum:preventif|detektif|korektif |  |
| evidence | str |  |
| notes | str |  |

### kri (`KRI-nnn`, folder `06-KRI`)

A key risk indicator of a risk. Body: `Pembacaan` (readings), `Riwayat ambang` (every threshold change with its reason).

| Field | Kind | Default |
|---|---|---|
| risk* | link:risiko |  |
| title* | str |  |
| what_measured | str |  |
| unit | str |  |
| kri_type* | enum:LEADING|LAGGING |  |
| direction* | enum:higher_is_worse|lower_is_worse |  |
| frequency* | enum:daily|weekly|monthly |  |
| watch | str |  |
| amber | float |  |
| red | float |  |
| status | enum:ACTIVE|RETIRED | ACTIVE |

### insiden (`INS-nnn`, folder `07-Insiden`)

A realised incident on an anchor. `impact` is the impact LEVEL on the matrix (1..max), the severity the simulation samples.

| Field | Kind | Default |
|---|---|---|
| pre* | link:pasang |  |
| date* | date |  |
| title* | str |  |
| impact* | int |  |
| use_in_simulation | bool | True |
| report | link:laporan |  |

### laporan (`LAP-nnn`, folder `07-Insiden/Laporan`)

An incoming incident report (a public inbox): PENDING, APPROVED (linked to a risk) or IGNORED.

| Field | Kind | Default |
|---|---|---|
| title* | str |  |
| reporter | str |  |
| date* | date |  |
| status | enum:PENDING|APPROVED|IGNORED | PENDING |
| risk | link:risiko |  |

### draft (`DRF-nnn`, folder `_Draft`)

An AI draft: a JSON list of items waiting for a person. Body `Hasil` table tracks each item.

| Field | Kind | Default |
|---|---|---|
| kind* | enum:konteks|risiko|bowtie|kri |  |
| target | str |  |
| status | enum:DRAFT|ACCEPTED|PARTIAL|REJECTED | DRAFT |

## Body sections

- Table sections (`## Name` followed by a Markdown table): `Kontrol yang ada` (Kontrol, Efektivitas, Sumber rencana, Catatan), `Pembacaan` (Tanggal, Nilai),
  `Riwayat ambang`, `Hasil` (draft items), matrix tables `Label kemungkinan`, `Label dampak`, `Kriteria dampak`, `Appetite` (Tahun, Batas skor), `Zona sel`.
- Bullet-tree sections (`Penyebab`, `Dampak`, `Saran ditolak`): `- text [Category]`, two spaces per level; a child is a cause of its parent.
  Cause categories: Kebijakan, Kelalaian Manusia, Bencana, Fraud, Stakeholders. Impact categories: Finansial, Reputasi, Hukum, Gangguan Layanan.
- Control effectiveness is a convention here (EFFECTIVE, PARTIAL, INEFFECTIVE).

## Ids

Prefix + three digits, next free number (`RSK-001`). Evaluations are `EVA-<year>-<number of the anchor>` so the year and anchor are readable. Ids are never reused or renamed; rename a risk by editing its `title`.
