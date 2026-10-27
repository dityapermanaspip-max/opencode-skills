---
name: cubeee-tours
description: Author, extend, or repair Cubeee guided tours in the darkhive frontend (IAM, GRiMIS, HILDA, AIDAA). Use when asked to add a tutorial, tour, or walkthrough for a page/module in any app, when a tour dead-ends or highlights the wrong thing, when steps ignore permissions or roles, when the Mode Tutorial picker shows tours a session cannot walk, or when adding data-tour anchors, tour files, chains, or tour docs.
---

# Cubeee tours (global playbook)

Cubeee is the in-app bee that walks a user through one page (a **page tour**) or a multi-page
workflow (a **chain / mission**). The runtime already exists — this skill is the authoring side:
designing steps, tagging targets, wiring permissions, verifying, and documenting. It is app-agnostic;
the same playbook covers IAM, GRiMIS, HILDA, AIDAA, and any future darkhive app.

## Reference implementation: HILDA (the smooth pattern)

HILDA is the model to copy:

- **Page tour first, chain after.** Every page has a standalone `kind: "page"` tour whose walkable legs
  are exported (`LIST_INTRO`, `DETAIL_INTRO`, `INBOX_OPEN/ROW/CLOSE`, `ARCHIVE_OPEN/GUIDE/ROW`). The
  mission file (`tours/hilda/siklus.ts`) imports those legs wholesale — no duplicated copy, so the
  mission and its page-tour twin can never drift.
- **Own folder + barrel.** `src/lib/tours/hilda/<module>.ts` plus a re-export `hilda/index.ts`;
  the root barrel imports it once. New apps should follow this shape.
- **Uniform state tags.** `data-<app>-<page>-state = loading | error | empty | ready`, plus
  `-status` / `-<flag>` tags where an action depends on record state. `hideWhen` depends on these.
- **Permissions from the perms module only.** `HILDA_PERMS` (`lib/api/hilda/perms.ts`), never literals.
- **First step is the visibility gate.** The greeting carries the page's menu/read code, so a session
  without the page gets zero visible steps and the overlay stops instead of pointing at nothing.
- **Documented persona coverage.** `docs/tours/hilda.md` records each tour's step count, anchors,
  permission behaviour, and a per-role coverage matrix that is re-run after every batch.

## Where things live (`darkhive-fev2`)

- `src/lib/tours/types.ts` — `Tour`, `TourStep`; the whole step vocabulary. Read it first.
- `src/lib/tours/index.ts` — `TOURS`, `toursForApp`, `missionsForApp`, `pagesForApp`, `tourFor`, and the
  permission-aware helpers (`tourHasVisibleStep`, `visibleStepCount`, `firstVisibleStep`, `stepVisible`).
  Register every new tour here. The header bee and the Mode Tutorial picker only offer tours that have
  at least one step visible for the session; keep that behaviour.
- `src/lib/tours/<module>.ts` (IAM, GRiMIS today) or `src/lib/tours/<app>/<module>.ts` + barrel
  (HILDA, the target shape) — one file per page/module; missions live in their own file and import legs.
- `src/components/tour/TourOverlay.tsx` — spotlight, bubbles, Menunggu / Antar saya / Lanjut / Kembali /
  Selesai, and the live `code` / `notCode` / `hideWhen` filtering. Do **not** modify it for content work.
- `src/components/tour/Cubeee.tsx`, `MiniBee.tsx` — bee entry points. The header bee starts
  `tourFor(pathname, appCode, can)`; the picker lists missions above page tours.
- `src/stores/tour.ts` — run state (`done`, `start`, `next`, `stop`).
- `src/lib/api/<app>/perms.ts` — the only source of permission codes in tour files.
- `src/lib/appRegistry.ts` — app codes and menu gates. Today: `IAM`, `GRIMIS`, `AIDAA`, `HILDA`.
- `docs/tours/README.md` + `docs/tours/<app>.md` — owner-facing records. Failed approaches go in the
  README "Do not attempt" table.

## Authoring order (hard rule)

1. **Page tour first.** Write the page file and its standalone `kind: "page"` tour (exact `route`,
   first step carries `go`, closing on the page's next action). Export the reusable legs.
2. **Chain after.** Build the mission in its own file, importing the page legs and adding only the
   connectors (`until` / `go`) and the permission-fallback endings.
3. **No step counting while creating.** Do not put counts in copy, titles, or intermediate docs.
4. **Document exact counts after the module is done** — in the app tour doc: total per tour, and a note
   that permission filtering shapes each session's walk.

## Roles, permissions, and strict visibility

Gate steps on **permission codes**, never on role names. A role is only a bundle of codes.

- **Personas come from IAM.** Derive the role→permission matrix from the IAM database (read-only) or,
  when the app documents it, from the app's role doc (HILDA: `hilda-be1/docs/user-role.md`). IAM's
  exact `iam.*` table names live in `darkhive-bev2/schemasql`; queries must be read-only.
- **First step = menu/read gate.** The greeting and closing carry the page-level code (or the pair
  covering every admitted persona). No visible first step means no walk.
- **Pair rule, asymmetric primary.** For a persona split use `code` on the primary variant with **no**
  `notCode`, then the secondary variant with `code` + `notCode`. Correct scope pair:
  `code: read_own` / `code: read_all, notCode: read_own` — a session holding both still gets one walk.
  Never give both variants a `notCode` of the other: a session holding both would see nothing.
- **Every act step follows its button.** Use the button's own code; add a `notCode` fallback for the
  persona that lacks it. Keep steps neutral only when every persona admitted to the page can see the
  target.
- **Endings stay permission-symmetric.** Primary ending has a `code`; the fallback ending carries
  `notCode`, so no persona ends on an off-page step.
- **Connector invariants.** A connector must not lead into a page whose steps all need a permission the
  persona lacks. If the chain distinguishes actor/reader with `create` vs `read`, state the invariant in
  the role doc (today: `archive.create` implies `archive.read`) or gate the connector on the read code.
- **New role or permission change:** re-run the persona matrix for every affected tour; verify the first
  visible step exists for each persona admitted by the menu, the last visible step is on-page, and the
  chain still ends where the outcome is visible.

## Process

1. **Read the page first.** Route, permission guards, empty/error states, which controls render
   conditionally, where each action leads. Novel pages: map states and personas before anchors.
2. **State × persona matrix.** For every conditional block (empty list, open modal, inactive row,
   nothing selected) decide: step with a state tag, bubble with "klik … dulu", or no step. For every
   `PermissionGuard` decide `code` / `notCode` using the rules above.
3. **Anchor QA before using a target.** Always present in that page state? Big enough to spotlight?
   Under a fixed overlay? Does clicking it leave the page? Prefer the container that owns the action
   over a dense inner control; prefer a stable first-row anchor over repeated identical anchors.
4. **Write the page file + tour**, exporting its legs. Mirror an existing app file.
5. **Write the mission file** importing those legs (page-first, then chain).
6. **Register** in `TOURS` with the right `app` code (missions block first, pages second).
7. `npx tsc --noEmit`.
8. **Docs:** add the tour inventory row (id, kind, start, route, exact step count), the anchors added,
   the permission behaviour, and the persona coverage matrix to `docs/tours/<app>.md`; add a dated
   bullet to `docs/history.md`; update `docs/status.md` if the current state changes. Record failed
   approaches in `docs/tours/README.md`.
9. **Report** to the owner: what can be walked, which roles see which parts, and a concrete
   browser-test checklist. The owner tests; do not claim it works.

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

- Every clickable and every form gets one explanation; repeated patterns collapse to one step;
  sections bundle into the nearest step. Cap **20** steps per page tour; chains are free.
- Order along the user's real path: create → configure → browse → leave. Creation forms sit above the
  list they feed; clickable things must look clickable. Those are owner rules — if the UI violates
  them, that is a separate UI change, never a tour-only workaround.
- Open a form's step right after its button. If a modal covers the next target, say "Simpan atau Batal
  dulu" in that step's text.
- Invite navigation only on a closing step or through a chain connector. A mid-tour "click this row"
  strands the tour on a page it does not cover. If the final page-tour step navigates, give it `until`
  so the tour ends on arrival.
- One button that alternates between two permissions (activate/deactivate render one at a time): give
  the step the common state's code and explain the inverse in the text. Split them only when both
  buttons are visible at once.
- Tab steps target the tab button, never hidden content.
- Never target a component that renders `null` when empty (mention it in a neighbouring step instead).
- Dynamic `[id]` routes cannot carry a static `go` to themselves: the first step's `go` points at the
  parent list and the text explains the way in.

## Chains vs page tours

- **Page tour** — `kind: "page"`, exact `route`, started by the header bee, must stand alone on that
  page. Close on the page's next action (often the row that opens the detail).
- Context-dependent page tours (dynamic `[id]` routes, comment pages opened from a row) set
  `picker: false`: they stay on the header bee but are hidden from the Mode Tutorial list.
- **Chain** — `kind: "chain"`, assembled from shared legs; composite chains carry **no** `route` and
  connect pages with connectors (`until`), using `go` as recovery. A mission that never leaves one page
  is a single-page chain with `route`, so the picker and the header bee share one object.
- Detour needing a menu item: target the sidebar anchor (`nav-*`) with `until` + `go`, and gate the
  whole leg with the menu's permission so nobody sees an unreachable leg.
- Connector: on-page + `until` → waits (no Lanjut); off-page → "Antar saya" via `go`. Never set `go` to
  a page where the step itself does not exist. The picker and bee skip a tour with zero visible steps.

## Hard-won pitfalls

- Fixed modals cover the page: steps behind them still resolve, but the user cannot click. Text must
  say close/save first.
- `hideWhen` is for "this block can never render in this state", not "modal not open yet" — when the
  attribute simply is absent, the selector never matches and both steps show. Modals get bubbles.
- Anchors on `[id]` pages must be anchored regexes (`/^\/…\/[^/]+$/`); otherwise the list route
  matches too.
- First-row anchors: map with an index, tag only `i === 0`; recursive components get an optional
  `tourId` prop instead of a hardcoded attribute.
- Do not add `data-tour` inside a shared component used by an already-toured page unless the target is
  meaningful there too.
- `until` is re-checked on every render and the overlay repairs by step identity, not index — good for
  auto-advance, but the copy must say the navigation happens automatically.
- Sidebar anchors come from the `tourId()` helper in `Sidebar.tsx`; add a key there.
- A neutral act-step is a trap for future read-only roles: gate action boxes with their act code, or
  document the persona that only reads.
- State tags are a contract: a page without `<app>-<page>-state` tags makes `hideWhen` silently never
  match, so steps stall on missing targets.
- Both-codes trap: two variants that each exclude the other's code leave a combined role with no walk.
  Keep the broader variant's `code` unconditional.
- Keep the app doc (owner's record) and this skill (agent playbook) in sync; when a rule changes,
  update both.

## Template (page-first, then chain)

```ts
// tours/<app>/<module>.ts — the page tour owns the legs.
import type { Tour, TourStep } from "../types";
import { APP_PERMS as P } from "@/lib/api/<app>";

export const LIST = /^\/dashboard\/<app>\/<module>$/;
export const DETAIL = /^\/dashboard\/<app>\/<module>\/[^/]+$/;

export const LIST_INTRO: TourStep[] = [
  { path: LIST, go: "/dashboard/<app>/<module>", target: "mod-header", code: P.<x>.read,
    text: "Halo! 🐝 …" },
  { path: LIST, target: "mod-add", code: P.<x>.create, text: "…" },
  { path: LIST, target: "mod-form", code: P.<x>.create,
    text: "… (Belum terbuka? Klik + Tambah … dulu.)" },
  { path: LIST, target: "mod-row", until: DETAIL, go: "/dashboard/<app>/<module>",
    hideWhen: '[data-<app>-mod-state="empty"]',
    text: "Klik baris mana pun — kita lanjut di detail." },
];

export const LIST_CLOSE: TourStep = {
  path: LIST, target: "mod-header", code: P.<x>.read,
  text: "Selesai! 🎉 … 🐝",
};

export const MODULE_PAGE_TOUR: Tour = {
  id: "<app>-<module>", title: "…", desc: "…",
  kind: "page", route: LIST, app: "<APP>",
  steps: [...LIST_INTRO, LIST_CLOSE],
};
```

```ts
// tours/<app>/<mission>.ts — the chain imports the page legs, never re-copies them.
import type { Tour } from "../types";
import { LIST_INTRO, DETAIL_INTRO, ... } from "./<module>";

export const MODULE_MISSION: Tour = {
  id: "<app>-<module>-mission", title: "… (misi)", desc: "…",
  kind: "chain", app: "<APP>", // composite: no route
  steps: [...LIST_INTRO, ...DETAIL_INTRO, /* connectors + symmetric fallback ending */],
};
```

## Verification checklist

- `npx tsc --noEmit` clean.
- Every `target` used in a tour file has a matching `data-tour` (grep both; remember conditional
  expressions and prop-passed anchors).
- Persona pass per role pack: the first visible step exists for every persona the menu admits; no step
  points at a control that persona cannot see; the last visible step is on-page; the chain ends where
  the outcome is visible.
- Picker pass: a session only sees tours with at least one visible step, and the card's count matches
  its visible steps.
- Empty-data pass: bubbles make sense, no step pointing at nothing.
- Modal pass: each modal step appears only after the opening click; the step after it tells the user to
  close/save.
- Chain pass: every connector advances on the expected navigation; Kembali never bounces forever.
- Counts documented in `docs/tours/<app>.md` after the module is complete.
- Owner browser test is the acceptance gate.
