---
name: cubeee-tours
description: Author, extend, or repair Cubeee guided tours (page tours and multi-page chains/missions). Use when adding a tutorial or walkthrough for a page/module, when a tour dead-ends or highlights the wrong element, when steps ignore permissions or roles, or when the tour picker offers tours a session cannot walk.
---

# Cubeee tours (portable playbook)

Cubeee is an in-app guide that walks a user through one page (a **page tour**) or a multi-page
workflow (a **chain / mission**). This playbook covers the authoring side: designing steps, tagging
anchors, wiring permissions, verifying, and documenting. It is project-agnostic — adapt the file
names and registry calls to the codebase you are in; the concepts and rules stay the same.

## First integration in a project

1. Locate the tour types and step vocabulary (fields below). If the project has no tour runtime,
   adopt one before authoring.
2. Locate the tour registry (the array of tour definitions) and the two entry points: the page-level
   launcher (bee/help button) and the tour picker.
3. Locate the anchor mechanism (an attribute on DOM nodes, for example `data-tour="…"`).
4. Confirm the picker and the launcher only offer tours with at least one visible step for the
   signed-in session (see *Permissions*).
5. Add one file per page/module; register it in the registry. Put multi-page missions in their own
   file and import the page legs.
6. Keep the project's tour record document updated with the exact counts after each batch.

## Authoring order (hard rule)

1. **Page tour first.** Write the standalone `kind: "page"` tour: exact route, first step carries
   the "take me there" target, closing on the page's next action. Export the reusable legs.
2. **Chain after.** Build the mission from the imported page legs; add only connectors and
   permission-fallback endings.
3. **No step counting while creating** — not in copy, titles, or intermediate docs.
4. **Document exact counts after the module is done** — total per tour, noting that permission and
   page-state gating shape each session's walk.

## Permissions and strict visibility

Gate steps on **permission codes**, never on role names. A role is only a bundle of codes.

- **Personas come from the identity source.** Derive the role→permission matrix from the identity
  system (read-only queries) or the project's role documentation. Never invent a persona or a code.
- **First step is the visibility gate.** The greeting carries the page's menu/read code (or the pair
  covering every admitted persona). No visible first step means no walk.
- **Pair rule, asymmetric primary.** For a persona split, give the primary variant a `code` with **no**
  `notCode`, then the secondary variant a `code` + `notCode`. A session holding both still gets one
  walk. Never give both variants a `notCode` of the other — a session holding both would see nothing.
- **Every action step follows its button.** Use the button's own guard; add a fallback variant for the
  persona that lacks it. Keep a step neutral only when every persona admitted to the page can see the
  target.
- **Endings stay permission-symmetric.** The primary ending carries a `code`; the fallback ending
  carries `notCode`, so no persona ends on an off-page step.
- **Connector invariants.** A connector must not lead into a page whose steps all require a
  permission the persona lacks. Document implied permissions (for example, create implies read) or
  gate the connector on the read code.
- **Picker and launcher stay strict.** Offer a tour only when at least one step survives its
  `code`/`notCode` gates; show the session's visible step count; start from the first visible step.
  Page-state filters (`hideWhen`) stay live in the runtime, not in the picker.
- **New role or permission change:** re-run the persona matrix. Verify the first visible step exists
  for every persona the menu admits, the last visible step is on-page, and the chain still ends where
  the outcome is visible.

## Step vocabulary

| field | use |
|---|---|
| `path` | Pattern of the page where the step shows. Exact list route; a dynamic-segment pattern for `[id]` routes (anchor it so the list route does not match); separate routes for detail/AI pages. |
| `target` | Anchor value on the DOM node. Omit for a corner bubble. |
| `text` | Friendly, user-facing copy. One idea per step: what it is, what the button does, what happens next. For appear-after-click targets add "(Not open yet? Click … first.)" in the local language. |
| `code` | Permission the step needs; it silently drops without it. |
| `notCode` | Inverse: drops when the session **has** it (fallback wording). |
| `go` | Where "take me there" leads when off-page. Every tour's first step carries it. |
| `until` | Auto-advance once the user reaches this page (connectors, "apply → auto back"). While current it waits. |
| `hideWhen` | CSS selector; drop the step while the page matches (page-driven state). The page must tag its root. |

## Design rules

- One explanation per clickable control and per form; repeated patterns collapse into one step;
  sections bundle into the nearest step. Cap page tours (e.g. 20 rendered steps); chains are free.
- Order along the user's real path: create → configure → browse → leave. Creation forms sit above the
  list they feed; clickable things must look clickable. If the UI violates that, it is a separate UI
  change — never a tour-only workaround.
- A form's step comes right after its button. If a modal covers the next target, say "Save or Cancel
  first" in that step's text.
- Invite navigation only on a closing step or through a chain connector. A mid-tour "click this row"
  strands the tour on a page it does not cover.
- One button that alternates between two permissions (activate/deactivate render one at a time): give
  the step the common state's code and explain the inverse in the text. Split them only when both
  buttons are visible at once.
- Tab steps target the tab button, never hidden tab content.
- Never target a component that renders `null` when it is empty (mention it in a neighbouring step).
- Dynamic `[id]` routes cannot carry a static `go` to themselves: the first step's `go` points at the
  parent list and the text explains the way in.

## Chains vs page tours

- **Page tour** — `kind: "page"`, exact route, started by the page-level launcher, must stand alone on
  that page. Close on the page's next action (often the row that opens the detail).
- Context-dependent page tours (dynamic `[id]` routes, pages opened from a row) set `picker: false`:
  available from the launcher but hidden from the picker.
- **Chain** — `kind: "chain"`, assembled from shared legs. Composite chains carry **no** `route` and
  connect pages with connectors (`until`), using `go` as recovery. A mission that never leaves one
  page is a single-page chain with a `route`, so the picker and the launcher share one object.
- Detour needing a navigation item: target the navigation anchor with `until` + `go`, and gate the
  whole leg with the menu's permission so nobody sees an unreachable leg.
- Connector: on-page + `until` → waits (no Next); off-page → "take me there" via `go`. Never set `go`
  to a page where the step itself does not exist.

## Hard-won pitfalls

- Fixed modals cover the page: steps behind them still resolve, but the user cannot click. Text must
  say close/save first.
- `hideWhen` is for "this block can never render in this state", not "modal not open yet" — when the
  attribute is simply absent, the selector never matches and both steps show. Modals get bubbles.
- Anchors on `[id]` pages must be anchored patterns; otherwise the list route matches too.
- First-row anchors: tag only the first item; shared/recursive components get an optional anchor prop
  instead of a hardcoded attribute.
- Do not add an anchor inside a shared component used by an already-toured page unless the target is
  meaningful there too.
- `until` must be re-checked on every render and the overlay must repair by step identity, not index;
  otherwise walking back across a connector dead-ends.
- Navigation anchors come from the sidebar/menu helper; add the key there.
- A neutral action step is a trap for future read-only roles: gate action boxes with their act code,
  or document the persona that only reads.
- State tags are a contract: a page without state tags makes `hideWhen` silently never match, so steps
  stall on missing targets.
- Both-codes trap: two variants that each exclude the other's code leave a combined role with no walk.
  Keep the broader variant's `code` unconditional.
- Keep the project's tour record and this playbook in sync; when a rule changes, update both.

## Template (page-first, then chain)

```ts
// tours/<app>/<module>.ts — the page tour owns the legs.
import type { Tour, TourStep } from "../types";
import { APP_PERMS as P } from "./<perms-module>";

export const LIST = /^\/<app>\/<module>$/;
export const DETAIL = /^\/<app>\/<module>\/[^/]+$/;

export const LIST_INTRO: TourStep[] = [
  { path: LIST, go: "/<app>/<module>", target: "mod-header", code: P.<x>.read,
    text: "Hello! …" },
  { path: LIST, target: "mod-add", code: P.<x>.create, text: "…" },
  { path: LIST, target: "mod-form", code: P.<x>.create,
    text: "… (Not open yet? Click Add first.)" },
  { path: LIST, target: "mod-row", until: DETAIL, go: "/<app>/<module>",
    hideWhen: "[data-<app>-mod-state=\"empty\"]",
    text: "Click any row — we continue on the detail page." },
];

export const LIST_CLOSE: TourStep = {
  path: LIST, target: "mod-header", code: P.<x>.read,
  text: "Done! …",
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
import { LIST_INTRO, DETAIL_INTRO } from "./<module>";

export const MODULE_MISSION: Tour = {
  id: "<app>-<module>-mission", title: "… (mission)", desc: "…",
  kind: "chain", app: "<APP>", // composite: no route
  steps: [...LIST_INTRO, ...DETAIL_INTRO, /* connectors + symmetric fallback ending */],
};
```

## Verification checklist

- Typecheck/lint clean.
- Every `target` has a matching anchor (grep both; remember conditional expressions and prop-passed
  anchors).
- Persona pass per role pack: the first visible step exists for every persona the menu admits; no
  step points at a control that persona cannot see; the last visible step is on-page; the chain ends
  where the outcome is visible.
- Picker pass: a session only sees tours with at least one visible step, and the card's count matches
  its visible steps.
- Empty-data pass: bubbles make sense, no step pointing at nothing.
- Modal pass: each modal step appears only after the opening click; the following step tells the user
  to close/save.
- Chain pass: every connector advances on the expected navigation; Back never bounces forever.
- Counts documented in the project's tour record after the module is complete.
- Human browser test is the acceptance gate.
