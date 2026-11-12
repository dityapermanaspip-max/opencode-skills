# Regulation basis and status (snapshot 2026-11-12)

Verified on peraturan.bpk.go.id through the `audit-legal-crawler` skill. A snapshot, not a promise: run that skill's
status check before relying on a rule for a real decision, and say so in the answer.

## Rules the templates rest on

| Rule | Where | What it gives |
|---|---|---|
| Perpres 16/2018 as amended by Perpres 12/2021 and Perpres 46/2025 | Pasal 38 | Pengadaan Langsung for construction up to Rp400 juta (barang/jasa lainnya up to Rp200 juta); above Rp50 juta through SPSE transactional; Penunjukan Langsung criteria, among them continuing the work after a contract is terminated (ayat (5)) |
| | Pasal 54, 56 | addendum, value increase at most 10% (emergency exception with PA approval); giving the provider extra time is done by addendum |
| | Pasal 57, 58 | handover (BAST), administrative check by PjPHP/PPHP, PPK to PA/KPA |
| | Pasal 78 | administrative sanctions; ayat (4b) delegates the details to a Peraturan Kepala Lembaga; ayat (5) deleted |
| | Pasal 79 | late fine 1 per mil (1/1000) of the contract value excluding PPN |
| Peraturan LKPP 12/2021, Lampiran II (construction) | 5.2 | Penunjukan Langsung; after termination, to the reserve winner (5.2.2 a.2) |
| | 7.3 | pre-signing meeting (minutes mandatory), SPPBJ cancellation, sign within 14 working days |
| | 7.4 to 7.11 | handover of site, SPMK within 14 working days, pre-implementation meeting, joint inspection, SCM, changes |
| | 7.16, 7.17 | force majeure: notice within 14 calendar days, temporary or permanent stop |
| | 7.18 to 7.21 | termination, what is left on site, extra time (up to 50 calendar days, then a second chance or termination), penalty |
| | 8.1 to 8.4 | PHO, FHO, maintenance period (at least 6 months permanent, 3 months semi-permanent), handover to PA/KPA |
| Peraturan LKPP 4/2021, Bagian VIII | formats a to d | official formats of the sanction proposal, notification, Keputusan and Keputusan on audit findings |
| SSUK of the LKPP contract models | kontrak kritis, pemutusan | period I late by more than 10%, period II more than 5% (or less than 5% but past the fiscal year) is critical; SCM I to III with SP I to III; unilateral termination after SP III; at least 3 warnings and 14 calendar days notice |

## Amendment check

Peraturan LKPP 12/2021 was amended only by Peraturan LKPP 4/2024 (design-build annexes). LKPP 5/2024 is an
unrelated staffing rule. No later LKPP rule found supersedes LKPP 12/2021 or LKPP 4/2021 (Perka 3, 4 and 5 of 2025,
Perlem 1/2025, SE 3 and 4 of 2025 and Perpres 108/2025 were checked: unrelated).

## Caveats to repeat to the user

- The Rp400 juta ceiling (Perpres 46/2025) is higher than the "SPK up to Rp200 juta" in Lampiran II of LKPP 12/2021.
  The owner accepted the SPK form at the higher ceiling. Who runs a Penunjukan Langsung (Pejabat Pengadaan or Pokja
  Pemilihan) is also tied to value thresholds in LKPP 12/2021; recheck them against Perpres 46/2025.
- LKPP 4/2021 (sanctions) predates Perpres 46/2025 Pasal 78. Sanction durations and levels are left to LKPP's
  Peraturan Kepala Lembaga: the documents carry a typed field, never a baked duration. Court-driven formats (penundaan,
  perubahan, pembatalan) are not templated.
- Only the SPMK and the four sanction documents follow official formats. Every other lifecycle document is authored
  from the SSUK and the regulation text and needs the owner's or legal's review.
- A contract is "declared critical", warned, terminated and blacklisted by the officials named in the SSUK (the
  Pejabat Penandatangan Kontrak, the KPA, LKPP). This skill drafts and computes; it never declares.
