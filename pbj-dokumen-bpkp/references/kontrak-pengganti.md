# A new contract to cover an unfinished or failed one

Use when a contract is terminated (or about to be) and the remaining work must go to someone else. Start with
`pbj.py replacement` for the indicative figures, then follow this route. The legal acts belong to the officials
(PPK, Pokja Pemilihan or Pejabat Pengadaan, KPA); this skill drafts the paper.

## 1. Close the old contract first

`route pemutusan_kontrak`: three warning letters (or the SCM chain and SP I to III), notice of termination (at least
14 calendar days), joint inspection of the accepted work (`ba_pemeriksaan_bersama`), the termination letter,
guarantee cash-in (`pencairan_jaminan`, with the remaining advance if one was paid), then the proposal for the
blacklist (`route sanksi_daftar_hitam`, in parallel). The new contract needs the joint inspection: it fixes what
work is already accepted and therefore what is left.

## 2. Pick the method

- Penunjukan Langsung to continue the work after termination: Perpres 16/2018 Pasal 38 ayat (5) as amended, LKPP
  12/2021 Lampiran II angka 5.2.2 a.2. Offer the work to the reserve winner (pemenang cadangan) first: invitation to
  clarification and negotiation, clarification and negotiation of technical and price, determination and
  announcement. No reserve winner, or none willing: another provider through the full Penunjukan Langsung stages
  (prequalification, explanation, offer, evaluation, negotiation, determination) or a Tender.
- Pengadaan Langsung only if the remaining work is within Rp400 juta (`route pengadaan_langsung`). Above it, it is
  not an option: `replacement` prints the indicative remainder (contract value x (100 - actual %)) only to decide
  this. It is not the HPS.
- The HPS of the new work is built from the unfinished volumes of the owner's BoQ (Excel) and typed as `nilai_hps`.
  Never derive it from a percentage.

## 3. Documents, in order

| Step | Document | Source |
|---|---|---|
| Request to the selection official | `permintaan_pl` (Permintaan Penunjukan Langsung Lanjutan) | pack |
| Need and scope | `nota_dinas`, `kak` (volumes left, as-built condition) | pack |
| Review of the preparation | `ba_reviu` | pack |
| Selection (undangan, negotiation, BA, determination) | SPSE, run by the Pokja or Pejabat Pengadaan | not authored here |
| Review of the selection result | BA Reviu Hasil Pemilihan Penyedia | the owner's draft form in the dossier (`blanks`, `fillform`) |
| Appointment | SPPBJ; a tender-type SPPBJ also asks for the Jaminan Pelaksanaan and signing within 14 working days | the owner's draft SPPBJ (the pack's `sppbj` is the Pengadaan Langsung wording) |
| Pre-signing meeting (mandatory) | `ba_rapat_ttd` | pack (manual minutes) |
| Contract | SPK (`spk`) within the Pengadaan Langsung ceiling; otherwise a Surat Perjanjian | the owner's draft Rancangan Kontrak (LKPP model with SSUK and SSKK); blanks to settle: advance, payment stages, penalty 1/1000, construction life, failure of building |
| Guarantee | Jaminan Pelaksanaan (and later Pemeliharaan) | issued by the provider's bank or insurer, not authored |
| Start | `spmk`, `ba_lokasi`, `ba_rapat_pelaksanaan`, `ba_pemeriksaan_bersama` | pack |
| Execution and reports | quality plan (RMPK), S-curve, daily, weekly and monthly reports, monthly meeting minutes | the owner's draft forms; weekly figures feed `progress add` |
| Completion | `ba_pemeriksaan_pekerjaan`, `bast_pertama`, `ba_pjphp`, `bast_pa`, then `bast_akhir` and `pengembalian_jaminan` | pack |

When the new contract fails too, the same packages apply again (`route kontrak_kritis` and on).

## 4. Time and money

- Check the fiscal year before setting dates. Work that runs past it needs funding from the next year's DIPA, and
  the addendum or contract has to say so (SSUK 32.3: time given, penalty, guarantee extension, next-year funding).
- The SPPBJ is cancelled, without compensation, if the provider fails or the budget is insufficient (LKPP 12/2021
  7.3.1); `route pembatalan_sppbj` then moves to the next-ranked provider.
- Keep the old and the new contract apart in the record: one `proyek.md` per contract, the new note's `catatan`
  pointing to the old one.
