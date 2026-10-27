---
name: engineering-rules
description: Hard working rules for delivering changes with an AI coding agent in a multi-repo product: the explicit "go code" gate, plan-before-code, secrets/.env rules, read-only identity and schema boundaries, safe re-runnable DDL patches, the 300-line cap with re-export barrels, language conventions, documentation updates, and the bottom-up "sandwich" workflow. Use when starting or reviewing implementation work, when a task spans schema/backend/frontend, or when deciding what may be edited, migrated, or committed.
---

# Engineering rules (portable)

How to work with the owner/maintainer across a multi-repo product. These rules win over general
habits. Adapt the placeholders to your project; keep the gates and the workflow.

## Team profile (adapt these)

- Repos: a backend service, a frontend shell, an identity service, and one or more app services.
- UI language: Indonesian (this team) — change it to your product's user-facing language.
- Agent-facing docs and code comments: English.
- Line cap: 300 per source file, enforced with re-export barrels.

## Collaboration gate

- **"go code" gate:** plan first; write code ONLY after the owner writes "go code". A question, a
  pasted file, or "nice"/"ok" is not "go code".
- One small task at a time. Show the plan before the code.
- Keep answers short. The owner tests in the browser; do not hand over a list of manual test commands.
- Do not commit or push until the owner approves. Doc updates and a batch push happen only after that
  approval.
- Report with a concrete owner checklist (which DDL patch to run, service restart, browser flow,
  role/permission matrix). Never claim something "works" until the owner has verified it.

## Evidence and status labels

- Keep three states distinct: **written** (code/typecheck passes), **exercised locally** (dry-run or
  rollback test, local database patched), **owner-verified** (browser/acceptance). Never collapse them
  into "done".
- A patch applied locally is not live. Record environment parity explicitly (local / staging /
  production) and keep a pending list per environment until each one runs it.
- Migrations are numbered by **run order**, not feature batch. A later patch can supersede an earlier
  backfill; record "never rerun patch X after Y" where it matters. Run through the project's runner
  with a dry-run first; print only host/database, never credentials.
- Mass renames: dump the distinct values before and after; the dump is the proof the rename did not
  truncate or widen the set.
- Remove guessed abstractions (permission/action matrices, role tables) that no code enforces; a stale
  matrix is worse than none.
- Temporary tracking files (batch TODOs) are deleted after the browser pass. Their decisions belong in
  the decisions doc; their current state belongs in the status doc.
- Reuse registered permission codes before adding one. A new code is an owner-approved identity change,
  never something an app seeds itself.

## Secrets and files

- Never read or create `.env` files. Never put secrets, tokens, or `.env` contents in chat or docs.
- New settings are announced in chat and added by the owner, not by the agent.
- Read files from disk; ask for the target file when names are ambiguous (a router, schema, and
  service can share a name).
- A file touched in more than one place is given as a FULL REPLACEMENT; scattered chunks left old
  code behind.

## Data and schema integrity

- Never invent amounts, scores, or rates. They come from approved master data or a code parser,
  never from AI text.
- Treat the identity tables as read-only unless the owner explicitly asks.
- DDL lives in owner-approved, sequentially numbered patches; write them safe to rerun
  (`CREATE TABLE IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`, `ON CONFLICT DO NOTHING` backfills).
- Reference/snapshot folders are read-only.

## Backend code conventions

- Raw SQL through parameter binding only (`text()` in SQLAlchemy); cast ids explicitly
  (`CAST(:x AS uuid)`); never interpolate table names from input.
- Bottom-up **"sandwich"**: schema → service → dependency → router → app entrypoint → import check.
  Do not start the next layer until the current one passes.
- Services do not commit; routers commit. Every write goes to the app's audit log and, when the
  platform has one, the identity audit log through the shared audit helper.
- Audit/log tables are append-only; never update or delete log rows.
- Service signature: master-data read functions take the actor id after the db session; write
  functions take it last.
- Static routes before `/{id}` routes in the same router.
- Reuse registered permission codes only; do not seed identity data from app code. Public/no-auth
  routers mount WITHOUT the root-scoped dependency.

## Frontend conventions

- One frontend can host several apps; never cross-edit another app's code for a different app's
  task.
- Run the project's typecheck after each batch.
- Public/no-auth pages live outside the authenticated group and need their own no-auth BFF
  forwarder; record them in the security doc under a "public surface" section.

## 300-line cap

- No source file over 300 lines. Split by domain and keep a thin re-export barrel so importers never
  change:
  - backend schemas: re-export submodules from one facade;
  - frontend types: re-export a folder from one facade;
  - services/components: split sub-files and import the pieces.
- The barrel only re-exports (one `export *` / `from ... import *` per submodule); it never holds
  definitions. New batch = one new file + one re-export line; the barrel stays tiny forever.

## Language and docs

- Agent-facing docs and code comments are English. UI labels follow the product language (this team:
  Indonesian). Error strings are English unless the product dictates otherwise.
- Keep the three docs separate: **status** = current verified/pending state, **history** = dated work
  log, **decisions** = append-only rationale for hard-to-reverse choices.
- After work, update the status doc, append to the decisions doc, and add a dated history entry.
  Keep docs current as part of the batch.

## Shell note

- On Windows/PowerShell, `Select-String` has no `-Recurse`. Use:
  `Get-ChildItem <dir> -Recurse -Filter <pattern> | Select-String "<text>"`.
