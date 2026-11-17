# OpenCode skills (custom)

The owner's custom OpenCode skills. This working copy is the live global skills directory
(`~/.config/opencode/skills`) — the files here are the ones OpenCode actually loads, and a commit
is also a backup. Nothing to build or sync.

## Install

- Global (all repos): clone this repo into `~/.config/opencode/skills`.
- Single project: copy one skill folder into `<repo>/.opencode/skills/<id>/`.

## Skills

- `engineering-rules` — portable working rules for delivering changes with an agent: the "go code"
  gate, plan-before-code, `.env`/secrets rules, read-only identity and schema boundaries, safe
  re-runnable DDL patches, the 300-line cap with re-export barrels, language conventions, doc
  updates, and the bottom-up "sandwich" workflow. Adapt the team profile at the top.
- `cubeee-tours` — a portable playbook for authoring Cubeee guided tours: page tours first, chains
  composed from their exported legs, permission/role gating, anchors, and verification.
- `multi-app-iam-foundation` — a portable blueprint for a multi-tenant, multi-app identity platform:
  many root orgs, per-app roles/permissions, cascading grants, contexts, account-level theming, and
  one frontend hosting several backends through per-app BFF proxies.
- `long-document-loop` - deterministic slicing, context carry, per-part persistence, coverage
  verification and stitching for documents that do not fit one model call: analyzing folders of long
  PDFs/scans (with OCR fallback) and authoring long contracts, policies or reports part by part.
  Ships `scripts/slice.py` (stdlib only) as the reference slicer and manifest writer.
- `pbj-dokumen-bpkp` — Indonesian government procurement (PBJ) documents for a BPKP work unit: the
  32-template pack in lifecycle order (SPK, SPPBJ, SPMK, BA, addendum, SCM, termination, sanctions,
  replacement), a `proyek.md` tracker readable in Obsidian that tests the critical-contract criteria,
  OCR for scanned supervisor reports, and filling of the owner's own BPKP draft forms. Legal acts
  stay with the officials; the skill only drafts and computes.
- `grimis-payungan` — enterprise risk management (ISO 31000) for one organisation on an Obsidian vault of
  Markdown notes, no web app or database: context, matrix and appetite, risk and bowtie drafts a person
  accepts, the four risk values with the active-value rule, controls and plans, KRI, incidents, a Monte
  Carlo suggestion, an ISO 31000 report and the annual close. A stdlib Python engine enforces the rules;
  the agent drafts and explains. Ships two demo vaults (`examples/`). Output is Indonesian.

Stock/community skills (`docx-builder`, `frontend-design`, `mcp-builder`, `theme-factory`,
`webapp-testing`) exist in this directory on the machine but are gitignored — they are not part
of this repo.
