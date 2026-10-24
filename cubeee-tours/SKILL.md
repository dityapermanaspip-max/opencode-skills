---
name: cubeee-tours
description: Author, extend, or repair Cubeee guided tours in the darkhive frontend (IAM, GrIMIS, AIDAA). Use when asked to add a tutorial, tour, or walkthrough for a page/module, when a tour dead-ends or highlights the wrong thing, when steps ignore permissions, or when adding data-tour anchors, tour files, chains, or tour docs in darkhive-fev2.
---

# Cubeee tours

Cubeee is the in-app bee that walks a user through one page (a **page tour**) or a multi-page workflow (a **chain / mission**). The runtime already exists — this skill is the authoring side: designing steps, tagging targets, wiring permissions, verifying, and documenting.

## Where things live (`darkhive-fev2`)

- `src/lib/tours/types.ts` — `Tour`, `TourStep`; the whole step vocabulary. Read it first.
- `src/lib/tours/index.ts` — `TOURS`, `toursForApp`, `missionsForApp`, `pagesForApp`, `tourFor`. Register every new tour here (chains first, pages second).
- `src/lib/tours/<module>.ts` — one file per module (`control-catalog.ts`, `risk-dictionary.ts`, …). Mirror an existing file.
- `src/components/tour/TourOverlay.tsx` — spotlight, bubbles, Menunggu / Antar saya / Lanjut / Kembali / Selesai. Do **not** modify it for content work.
- `src/components/tour/Cubeee.tsx`, `MiniBee.tsx` — bee entry points. The header bee starts `tourFor(pathname, app)`; the picker lists missions above page tours.
- `src/stores/tour.ts` — run state.
- `docs/cubeee_grimis.md` / `docs/TUTORIAL_TODO.md` — rules of record + shipped log per app. Update with every batch.
- `app` codes: `"IAM"`, `"GRIMIS"`, `"AIDAA"`.

## Process

1. **Read the page first.** Route, permission guards, empty/error states, which controls render conditionally, where each action leads. Novel pages: map states and personas before anchors.
2. **State × persona matrix.** For every conditional block (empty list, open modal, inactive row, nothing selected) decide: step with a state tag, bubble with "klik … dulu", or no step. For every `PermissionGuard` decide `code` / `notCode`. A persona must never see a step pointing at something it cannot open, or lose the closing because of a permission it lacks.
3. **Anchor QA before using a target.** Always present in that page state? Big enough to spotlight? Under a fixed overlay? Does clicking it leave the page? Prefer the container that owns the action over a dense inner control; prefer a stable first-row anchor over repeated identical anchors.
4. **Write the tour file** (one per module). Share copy between a page tour and its chain by defining `BODY` / leg arrays and spreading them.
5. **Register** in `TOURS`, `app` set.
6. `npx tsc --noEmit`.
7. **Docs:** shipped entry in the app's Cubeee doc (module, routes, anchors, permission behaviour, chain flow) + a bullet at the top of `docs/STATUS.md` "Done recently" (owner words, what shipped, tsc, test status). Drop the module from the Next list.
8. **Report** to the owner: what can be walked, permission behaviour, and a concrete browser-test checklist. The owner tests; do not claim it works.

## Step vocabulary

| field | use |
|---|---|
| `path` | RegExp of the page the step shows on. Exact list route; `[^/]+` for `[id]` routes (anchor the regex so the list route does not match); separate routes for AI/detail pages. |
| `target` | `data-tour` value. Omit for a corner bubble. |
| `text` | Friendly Indonesian. One idea per step: what it is, what the button does, what happens next. For appear-after-click targets add "(Belum terbuka? Klik … dulu.)". |
| `code` | Permission the step needs; it silently drops without it. |
| `notCode` | Inverse: drops when the session **has** it (fallback wording). |
| `go` | Where "Antar saya" leads when off-page. Every tour's first step carries it. |
| `until` | Auto-advance once the user reaches this page (connectors, "apply → auto back"). While current it waits with "Menunggu kamu…". |
| `hideWhen` | CSS selector; drop the step while the page matches (page-driven state, e.g. `[data-matrix-empty]`). Page must tag its root. |

## Design rules

- Every clickable and every form gets one explanation; repeated patterns collapse to one step; sections bundle into the nearest step. Cap **20** steps per page tour; chains are free.
- GrIMIS tours carry **no step counting** in copy or docs; IAM does the fixed count (145/15).
- Order along the user's real path: create → configure → browse → leave. Creation forms sit above the list they feed; clickable things must look clickable. Those are owner rules — if the UI violates them, that is a separate UI change, never a tour-only workaround.
- Open a form's step right after its button. If a modal covers the next target, say "Simpan atau Batal dulu" in that step's text.
- Invite navigation only on a closing step or through a chain connector. A mid-tour "click this row" strands the tour on a page it does not cover.
- Permission-aware: `code` must match the guard around the target, not a guess. Page-level read code goes on the greeting and closing too, so an unpermitted session never sees an orphan tour.
- One button that alternates between two permissions (activate/deactivate render one at a time): give the step the common state's code and explain the inverse in the text. Split them only when both buttons are visible at once.
- Tab steps target the tab button, never hidden content.
- Never target a component that renders `null` when empty (mention it in a neighbouring step instead).
- Dynamic `[id]` routes cannot carry a static `go` to themselves: the first step's `go` points at the parent list and the text explains the way in.

## Chains vs page tours

- **Page tour** — `kind: "page"`, exact `route`, started by the header bee, must stand alone on that page. Close on the page's next action (often the row that opens the detail).
- **Chain** — `kind: "chain"`, `route` of the first page, assembled from shared legs; connects pages with connectors (`until`), uses `go` as recovery; ends where the outcome is visible.
- Detour needing a menu item: target the sidebar anchor (`nav-*`) with `until` + `go`, and gate the whole leg with the menu's permission so nobody sees an unreachable leg.
- Connector: on-page + `until` → waits (no Lanjut); off-page → "Antar saya" via `go`. Never set `go` to a page where the step itself does not exist.
- Endings must be permission-symmetric: primary ending has a `code`, plus a `notCode` fallback ending, so no persona is left with an off-page last step.

## Hard-won pitfalls

- Fixed modals cover the page: steps behind them still resolve, but the user cannot click. Text must say close/save first.
- `hideWhen` is for "this block can never render in this state", not "modal not open yet" — when the attribute simply is absent, the selector never matches and both steps show. Modals get bubbles.
- Anchors on `[id]` pages must be anchored regexes (`/^\/…\/[^/]+$/`); otherwise the list route matches too.
- First-row anchors: map with an index, tag only `i === 0`; recursive components get an optional `tourId` prop instead of a hardcoded attribute.
- Do not add `data-tour` inside a shared component used by an already-toured page unless the target is meaningful there too.
- `until` is re-checked on every render and the overlay repairs by step identity, not index — good for auto-advance, but the copy must say the navigation happens automatically.
- Sidebar anchors come from the `tourId()` helper in `Sidebar.tsx`; add a key there.
- Keep the app doc (owner's record) and this skill (agent playbook) in sync; when a rule changes, update both.

## Template

```ts
import type { Tour, TourStep } from "./types";
import { PERMS } from "@/lib/api/grimis"; // IAM/AIDAA: that app's perms module

const LIST = /^\/dashboard\/app\/module$/;
const DETAIL = /^\/dashboard\/app\/module\/[^/]+$/;

const LIST_BODY: TourStep[] = [
  { path: LIST, go: "/dashboard/app/module", target: "mod-header", code: PERMS.x.read,
    text: "Halo! 🐝 …" },
  { path: LIST, target: "mod-add", code: PERMS.x.create, text: "…" },
  { path: LIST, target: "mod-form", code: PERMS.x.create,
    text: "… (Belum terbuka? Klik + Tambah … dulu.)" },
];

const LIST_ROW_CLOSING: TourStep = {
  path: LIST, target: "mod-row", code: PERMS.x.read,
  text: "Klik satu baris … Selesai! 🐝",
};

const TO_DETAIL: TourStep = {
  path: LIST, target: "mod-row", until: DETAIL, go: "/dashboard/app/module", code: PERMS.x.read,
  text: "Klik baris mana pun — kita lanjut di detail.",
};

const DETAIL_BODY: TourStep[] = [
  { path: DETAIL, go: "/dashboard/app/module", target: "mod-detail-header", code: PERMS.x.read,
    text: "…" },
];

export const MODULE_TOUR: Tour = {
  id: "module", title: "Modul (misi)", desc: "…",
  kind: "chain", route: LIST, app: "GRIMIS",
  steps: [...LIST_BODY, TO_DETAIL, ...DETAIL_BODY],
};

export const MODULE_PAGE_TOUR: Tour = {
  id: "module-page", title: "Modul", desc: "…",
  kind: "page", route: LIST, app: "GRIMIS",
  steps: [...LIST_BODY, LIST_ROW_CLOSING],
};
```

## Verification checklist

- `npx tsc --noEmit` clean.
- Every `target` used in a tour file has a matching `data-tour` (grep both; remember conditional expressions and prop-passed anchors).
- Persona pass (lowest permissions): no unreachable step, no orphan closing.
- Empty-data pass: bubbles make sense, no step pointing at nothing.
- Modal pass: each modal step appears only after the opening click; the step after it tells the user to close/save.
- Chain pass: every connector advances on the expected navigation; Kembali never bounces forever; the last step lands on a page the user actually reaches.
- Owner browser test is the acceptance gate.
