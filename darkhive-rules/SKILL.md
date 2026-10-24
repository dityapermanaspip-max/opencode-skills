---
name: darkhive-rules
description: The owner's hard working rules for the Darkhive platform repos (AIDAA FastAPI backend on 8002, darkhive-fev2 Next.js frontend, plus GrIMIS/IAM). Use whenever working on any of these repos: the "go code" gate, plan-before-code, secrets/.env rules, IAM and sql/ read-only, the 300-line cap with a re-export barrel, English comments/Indonesian UI labels, doc updates, and the bottom-up "sandwich" workflow.
---

# Darkhive working rules

How to work with the owner across the Darkhive repos: `aidaa` (FastAPI backend), `darkhive-fev2`
(Next.js frontend), plus `grimis-bev2` / `darkhive-bev2` / `hilda-be1`. These rules win over general
habits. Per-repo detail lives in each repo's own `AGENTS.md` (frontend) and `docs/00_RULES.md` (backend).

## Collaboration gate

- **"go code" gate:** plan first, write code ONLY after the owner writes "go code". A question, a
  pasted file, or "nice"/"ok" is not "go code".
- One small task at a time. Show the plan before the code.
- Keep answers short. Never ask the owner for manual test steps — the owner tests in the browser and
  does not want token tests in chat.
- Do not commit or push until the owner approves. (The owner keeps a standing approval to update the
  status/decisions/history docs and push after a finished batch.)
- Report at the end with a concrete owner checklist (which `sql/` patch to run, backend restart,
  browser flow, IAM matrix mapping). Never claim something "works" until the owner has verified it.

## Secrets and files

- Never read or create `.env` files. Never put secrets, tokens, or `.env` contents in chat or docs.
- New settings are announced in chat and added by the owner, not by the agent.
- The agent reads files from disk itself; the owner never has to paste a file. Ask for the target file
  before replacing/editing it when names are ambiguous (e.g. `funding.py`, `masters_costing.py`,
  `library_ai.py` exist as a router, a schema, and a service — confirm which one).
- A file touched in more than one place is given as a FULL REPLACEMENT. Scattered chunks left old code
  behind before.

## Data and schema integrity

- Do not invent amounts or rates. Money comes from approved master data or a code parser, never from
  AI text.
- Do NOT modify IAM tables. Never edit `sql/` or `reference/` unless asked. Ask before creating tables.
- `sql/` is for owner-approved DDL patches only; write them safe-to-rerun (`CREATE TABLE IF NOT EXISTS`,
  `ADD COLUMN IF NOT EXISTS`, `ON CONFLICT DO NOTHING` backfills). Number them sequentially.
- `reference/` is read-only (IAM schema, GrIMIS patterns, READMEs).

## Code conventions (AIDAA backend)

- Raw SQL through `text()` only. Cast ids with `CAST(:x AS uuid)`. Table names never come from input.
- Bottom-up **"sandwich"**: schema → service → dependency → router → `main.py` →
  `python -c "import app.main; print('ok')"`. Do not start the next layer until the current one passes.
- Services do not commit; routers commit. Every write logs to `aidaa_log` (via `services/logs.py`) and
  to `iam.audit_log` via `log_audit(db, actor_id, action, target_type, target_id, metadata)`.
- `aidaa_log` tables are append-only; never update or delete log rows.
- Service signature: master-data read functions take `user_id` after `db`; write functions take
  `user_id` last.
- Static routes before `/{id}` routes in the same router.
- Reuse permission codes only (IAM cannot be seeded from app code). Public/no-auth routers mount
  WITHOUT the root-scoped dependency.

## Frontend (darkhive-fev2)

- One Next.js repo, three apps: IAM, GRiMIS, AIDAA. Never modify IAM or GRiMIS for AIDAA work (and the
  reverse).
- Run `npx tsc --noEmit` after each batch.
- Public/no-auth pages live outside the `(app)` auth group and need their own no-auth BFF forwarder;
  note them in `docs/security.md` under "Public surface".

## 300-line cap

- No source file over 300 lines. Split by domain and keep a thin re-export barrel so importers never
  change:
  - Backend schemas: `app/schemas/execution_*.py` re-exported from `app/schemas/execution.py`.
  - Frontend types: `src/types/aidaa/*.ts` re-exported from `src/types/aidaa.ts`.
  - Services/components: split sub-files and import the pieces.
- The barrel only re-exports (one `export *` / `from ... import *` per submodule); it never holds
  definitions. New batch = one new file + one re-export line; the barrel stays tiny forever.

## Language and docs

- Agent-facing docs and code comments are English. UI labels are Indonesian. Error strings English.
- After work, update the docs: backend `docs/STATUS.md` + `docs/DECISIONS.md` (append-only); frontend
  `docs/status.md` + `docs/history.md` + `docs/decisions.md`.

## PowerShell gotcha

- `Select-String` has no `-Recurse`. Use: `Get-ChildItem app -Recurse -Filter *.py | Select-String "text"`.
