# OpenCode skills (custom)

The owner's custom OpenCode skills. This working copy is the live global skills directory
(`~/.config/opencode/skills`) — the files here are the ones OpenCode actually loads, and a commit
is also a backup. Nothing to build or sync.

## Install

- Global (all repos): clone this repo into `~/.config/opencode/skills`.
- Single project: copy one skill folder into `<repo>/.opencode/skills/<id>/`.

## Skills

- `darkhive-rules` — hard working rules for the Darkhive repos (AIDAA FastAPI backend,
  darkhive-fev2 frontend, GrIMIS/IAM): the "go code" gate, plan-before-code, `.env`/secrets rules,
  IAM and `sql/` read-only, the 300-line cap with re-export barrels, English comments / Indonesian
  UI labels, and the doc-update rule.
- `cubeee-tours` — authoring Cubeee guided tours in darkhive-fev2: designing steps, tagging
  data-tour anchors, wiring permissions, chains, and tour docs.

Stock/community skills (`docx-builder`, `frontend-design`, `mcp-builder`, `theme-factory`,
`webapp-testing`) exist in this directory on the machine but are gitignored — they are not part
of this repo.
