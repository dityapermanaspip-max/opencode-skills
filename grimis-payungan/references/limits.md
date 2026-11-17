# What this skill is not

Be honest about these when the user compares it with a full, multi-user risk-management system.

| Multi-user risk system | This skill |
|---|---|
| Many organisations in a tree, dictionaries shared by a root, per-organisation ownership of processes | One organisation per vault; `owner` on a process is plain text |
| Login, roles, permissions per organisation, an audit log in a database | No users or permissions; anyone with the folder can edit it. `LOG.md` is a plain append-only note, not tamper-proof |
| Escalation between organisations, comments, warning dismissals | Not implemented |
| Merging duplicate dictionary entries, re-keying exposures, activation cascades (inactive objective -> inactive anchor) | Not implemented; deactivate with `set` on a risk or anchor (`active=false`) |
| A public incident form and built-in AI engines behind a model gate | Claude drafts in the conversation; the user's own tool settings apply. Do not put documents into the conversation that the user's rules do not allow to be sent to an AI service |
| Concurrent editing, database integrity | One writer at a time; `check` finds broken links and rule breaks after the fact |
| Dashboards in a browser | `status`, `00-Dashboard.md`, `report` |

## What was verified
- The Monte Carlo (15 full runs with the same seeds), percentile, KRI status and default zone functions give results identical to an
  independent reference implementation of the same functions for the same inputs (385 comparisons, 2026-11-17).
- The engine self-test (`python -P scripts/selftest.py`) covers the note format, the value cycle, the rules, KRI, the simulation, drafts,
  the two-year close, a matrix change, the report and `check`.
- NOT verified against a running reference system: the active-value, trend and close logic were implemented from its documented rules and
  are covered by the self-test only. Nobody has used the skill on a real register yet.
- The demo vaults hold illustrative ratings written by the demo's author. They show how the skill works; they are not assessments.
