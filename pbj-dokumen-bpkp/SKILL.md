---
name: pbj-dokumen-bpkp
description: "Draft and track Indonesian government procurement (PBJ) documents for a BPKP work unit from a project folder, from the start: new contract (SPK or Surat Perjanjian), SPPBJ, SPMK, BA rapat, BAST, addendum, kontrak kritis (BA SCM, surat peringatan), keadaan kahar, pemutusan, sanksi daftar hitam, and a replacement contract that takes over a failed one. Keeps a progress tracker (proyek.md, readable in Obsidian) that tests the critical-contract criteria from the weekly reports, reads scanned supervisor reports, and fills the owner's own BPKP draft forms. Use when asked to create paket pengadaan or kontrak documents, to check or track a contract's progress (kontrak kritis, deviasi, SCM, pemutusan), to make a kontrak pengganti, to fill forms in a folder like 'Referensi Dokumen', or when working in a dossier folder of a PPK, pengadaan langsung, tender or rehab/renovasi project."
---

# PBJ dokumen BPKP

Opened on a project folder, this skill drafts the documents a procurement needs, in order, from the facts typed once, and
keeps a progress record that tells when a contract is in trouble. The wording is the same as HILDA's template pack
`pbj-pengadaan-langsung-2026` (32 templates, 7 packages): `assets/` is a generated copy, never edit it.

Run everything with `python "<skill-dir>/scripts/pbj.py" <command>` from the project folder (or `--folder`). On Windows
use `python -P` so the dossier folder is not put on the import path, and set `PYTHONIOENCODING=utf-8` for Indonesian text.

## Workflow

1. **Look first.** List the folder. Find `proyek.md` (the tracker). If there is none, offer `init` and confirm the facts
   below with the user; do not create it silently in someone's dossier.
2. **Read the sources.** Contract, SPMK, drafts and reports. Scanned PDFs have no text layer: `scripts/ocr_pdf.py`
   (render + Tesseract `ind`). OCR loses decimals and signs ("-18,44" became "1844"), so open the page image or a `--crop`
   and read every figure by eye before it is typed anywhere.
3. **Record facts once.** `set key=value ...` (keys are the HILDA template keys, see `references/kunci-isian.md`; typos
   and bad dates are rejected). Weekly figures from the supervisor's report: `progress add --pekan N --mulai .. --selesai
   .. --rencana .. --realisasi ..` (cumulative %). Re-adding a week replaces it.
4. **Ask `status`.** It prints deviation, pace, projection, data checks (e.g. a week that does not follow the last, an
   end date that disagrees with start + duration) and the next step. Report what it says; it states that criteria are
   MET, never that a contract IS critical or terminated: those are acts of the officials.
5. **Pick the document set.** `route` lists the packages, `route <package>` shows the steps and how far the project is.
   For a replacement contract read `references/kontrak-pengganti.md` and run `replacement`.
6. **Draft.** `need <template>` lists what is missing; ask the user for those values in one grouped question (people,
   dates, numbers, reasons), then `fill <template> --nomor "<number from the register>" --set key=value ...`. Missing
   values stay visible as `[label]` in the document. The result lands in `./dokumen/` and in the Dokumen table.
7. **The owner's own forms.** When the folder holds BPKP draft forms (e.g. `Referensi Dokumen`) and no template exists:
   `blanks <form>` and `text <form>` show what can be filled, `fillform --map map.json` fills blanks by index,
   `edit --after "Nama Paket:=> value"`, `--cell "label=>value"` and `--sub "old=>new"` do the rest. Values replace the
   blank exactly, so add a leading space when the form has none. Remove the form's sample text (blue "Contoh isi...")
   with `--sub`. Outputs never overwrite the source.
8. **Look at the result.** Convert to PDF (`soffice --headless --convert-to pdf`), rasterize a page and view it before
   saying it is done. Check names, numbers and dates against the sources.
9. **Report plainly:** files written, values still missing, and for each document whether it is an official format
   or authored from the SSUK ("perlu reviu"). Update the tracker (`doc set`, `log`).

## Commands

| Command | Use |
|---|---|
| `init`, `set`, `get` | create and edit the facts (`proyek.md` front matter) |
| `progress add / list` | weekly plan and actual; marks the weeks that meet the critical criteria |
| `status` | where the contract stands and what to do next |
| `route [package]` | the 7 packages: pengadaan_langsung, kontrak_kritis, perubahan_kontrak, keadaan_kahar, pemutusan_kontrak, sanksi_daftar_hitam, pembatalan_sppbj |
| `templates`, `need`, `fill` | the 32 templates, their missing values, the document |
| `doc list / add / set`, `log` | the document table and dated notes |
| `replacement` | indicative remainder and the route for a new contract |
| `blanks`, `text`, `fillform`, `edit` | the owner's own forms |

`scripts/selftest.py` checks the skill (derived values against the HILDA frontend, all templates filling, the tracker).
After the HILDA pack changes, run `scripts/sync_templates.py` and then `selftest.py`.

## Hard rules

- **Never invent** an amount, number, name, NIP, date or percentage. A value not in the folder or given by the user stays
  a `[label]`. Amounts in words and weekday names are computed from the typed number or date, never written by hand.
- **Document numbers** come from the owner's register (HILDA when it is the system of record); pass `--nomor`. Never
  allocate or reserve a number here.
- **HPS** comes from the owner's BoQ (Excel) and is typed as `nilai_hps`. The `replacement` remainder is a method check only.
- **Legal acts are the officials'.** The skill drafts; the Pejabat Penandatangan Kontrak declares a contract critical,
  warns, runs the SCM and terminates; the KPA decides sanctions; LKPP sets sanction details (no durations are baked).
- **Say the status of the wording.** Only the SPMK and the four sanction documents follow official formats; the other
  lifecycle documents are authored and need the owner's or legal's review. `references/status-regulasi.md` has the
  caveats (Rp400 juta ceiling vs Lampiran II, LKPP 4/2021 predating Perpres 46/2025) and is a snapshot: re-check a rule
  with the `audit-legal-crawler` skill before relying on it.
- **Personal and project data stays in the project folder.** Never copy a name, NIP, company or amount from a dossier
  into this skill, a repository or a chat summary beyond what the task needs.
- Output only into `./dokumen/` (or `--out`). Never edit or overwrite the dossier's own files. Never read or create `.env`.
- For kop, numbering shapes and who signs, follow the `tata-naskah-dinas-bpkp` skill; for Indonesian text quality
  `eyd-indonesia`. This skill does not restate them.

## References

- `references/alur-dokumen.md`: every package, step, signer and where the wording comes from (generated).
- `references/kunci-isian.md`: every key per template, with label and kind (generated, long: use `need` instead).
- `references/kontrak-pengganti.md`: the route for a new contract that takes over a failed one.
- `references/status-regulasi.md`: regulation basis, amendment check, caveats.
- `references/format-proyek.md`: the tracker layout and why it is a Markdown note and not SQLite.
