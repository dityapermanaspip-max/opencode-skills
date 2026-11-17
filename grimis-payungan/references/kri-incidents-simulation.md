# KRI, incidents and the Monte Carlo suggestion

## KRI
- A KRI belongs to one risk. It is ACTIVE as soon as it exists (no approval step) and ends RETIRED (history kept, no new readings).
  At most **three active KRIs per risk**.
- Status of the latest reading (latest by date, same date = the last entered): `higher_is_worse`: value >= red -> red, >= amber -> amber,
  else green. `lower_is_worse`: value <= red -> red, <= amber -> amber, else green. Without both thresholds or without a reading: grey.
  Thresholds must be ordered (higher_is_worse: amber <= red; lower_is_worse: amber >= red).
- Thresholds are set by a person: `kri threshold KRI-001 --amber 2 --red 5 --reason "..."`. The reason is mandatory and every change is
  appended to the `Riwayat ambang` table. You may suggest a number only if the user asks for one, and say it is a proposal.
- Readings: `kri read KRI-001 3 --date 2026-03-31`. A retired KRI refuses readings.

## Incidents
- `new insiden pre=PRE-001 date=2026-02-10 title="..." impact=3`: a realised event on an anchor. `impact` is the **impact level** on the matrix
  (1..max), because the simulation samples severities on the matrix's own scale. `use_in_simulation=false` leaves an incident out.
- Incoming reports (`new laporan`) are an inbox: PENDING, then APPROVED (linked to a risk) or IGNORED. Nothing is counted until a person
  creates the incident.

## Monte Carlo (`simulate EVA-... [--iterations 10000] [--percentile 75] [--seed N]`)
Compound Poisson model, checked against a reference implementation of the same functions (385 comparisons, see limits.md):
- lambda = number of incidents of the anchor in the evaluation's fiscal year that are used in simulation (the maximum-likelihood estimate
  of the yearly frequency).
- Each iteration draws N ~ Poisson(lambda) events and for each one a severity sampled with replacement from the observed impact levels; S = sum.
- Suggested cell: likelihood = the 75th percentile of the simulated yearly frequency, rounded; impact = the chosen percentile (default 75) of
  the observed severities, rounded; both clamped to the matrix. No incidents: lambda 0 and the suggestion is 1x1 (say plainly "tidak ada data").
- The result is written in the evaluation note (`Simulasi Monte Carlo`, `sim_suggestion`). It changes nothing until the user decides:
  `rate EVA-... --residual sim` (or `--inherent` / `--expected`; the user chooses which value it supports).

How to present it: say how many incidents the estimate rests on; with fewer than about five incidents call it a weak basis; show the
suggested cell, its score and zone, and the P50/P90/P95 of the yearly aggregate from the table; never present it as a forecast of money.
Use `--seed` when the user wants a reproducible number.
