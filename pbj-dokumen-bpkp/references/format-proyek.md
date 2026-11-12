# proyek.md: the project tracker

One Markdown note per contract, kept in the project folder, openable in Obsidian. `scripts/pbj.py` reads and
writes it; a person may also edit it by hand.

## Layout

```
---
tipe: "proyek-pbj"
nama_paket: "..."            <- front matter: flat keys, JSON-quoted values
nomor_spk: "..."                same key vocabulary as the HILDA templates
tanggal_mulai: "2026-08-04"     dates are yyyy-mm-dd, numbers are plain or Indonesian-formatted
nilai_kontrak: "7726944800"
metode: "Tender"             <- optional meta keys: metode, status_kontrak
---
# <title>

## Progres fisik     weekly cumulative plan and actual (%); deviation and the critical test are recomputed
## Dokumen           one row per document: template, name, number, date, status, file link [[...]]
## Catatan           dated log lines
## <anything else>   sections you add by hand are kept untouched
```

Front matter values are quoted strings (`key: "value"`), which Obsidian shows as properties. An unquoted value is
read as plain text. Keys must come from `references/kunci-isian.md` (`pbj.py set` rejects typos and checks dates
and numbers). Document status: `draf`, `ditandatangani`, `dikirim`, `selesai`, `batal`.

## What is typed and what is computed

Typed (from the supervisor's reports and the contract): `rencana` and `realisasi` per week, every key. Computed on
every run: deviation, period (I up to 70% planned, II above), the critical test, elapsed and remaining days, pace,
projection, and the data checks. A figure that follows from the last progress row (rencana, realisasi, deviasi,
batas kritis) pre-fills the SCM and sanction documents; a value you type always wins.
A deviation can differ by 0.01 from the printed report because the report rounds unrounded figures.

## Decision: a Markdown note (Obsidian), not SQLite

- The owner already works in Obsidian and wants to read and correct the record without a tool. A typo in a plan
  figure is a one-line fix in a note; in SQLite it needs a client or a command.
- The data are small and flat: about 40 keys, a table of weekly rows, a document list. One project is one note;
  nothing here needs joins or transactions.
- Claude works on "the folder it is opened in". A text file sits in that folder next to the dossier, is diff-able,
  survives being copied or zipped, and needs no runtime.
- Computed values are never stored as truth (they are recomputed), so hand edits cannot leave them stale.
- SQLite would win for reporting across many contracts (a "which contracts are critical" board), concurrent writers,
  or more than about fifty projects. The upgrade is mechanical because the keys are flat and the tables are plain:
  import every `proyek.md` into one SQLite file. Until then Obsidian Dataview can already query the front matter of
  all notes in a vault.

## Relation to HILDA

`proyek.md` is a working record, not the register. Document numbers come from the owner's register (HILDA numbers a
document itself when it is the system of record); pass them with `--nomor` and never invent or reserve one here. The
keys are the same as HILDA's package "Isian Bersama", so the same facts can be typed into a HILDA package.
