---
name: multi-app-iam-foundation
description: Foundation architecture for a multi-tenant, multi-application identity platform: many root organizations, per-application roles and permissions, cascading organization grants, user contexts, account-level theming, and one frontend hosting several backends through per-app BFF proxies. Use when laying a platform foundation, onboarding a new application or backend, or working with organizations, grants, permission cascades, contexts, themes, or BFF wiring.
---

# Multi-app IAM foundation

A portable blueprint for an identity service shared by many applications. The identity service is
the only place with a login; every other app decodes the same JWT and reads permissions from the
identity tables. Example table names are illustrative — map them to your schema.

## Multi-tenancy: many root organizations

- One identity database serves many tenants. `root_org_id` is a self-FK on the organization table and
  there are MANY roots. Each root plus its `parent_id` subtree is one instance: its own app
  activations, roles, users, and data.
- Selection by `root_org_id` happens almost everywhere; apps anchor their data with `org_id`.

## Multi-application

- Applications are registry rows (`applications`, uppercase code).
- An app is enabled per root organization (`organization_applications`); sub-orgs inherit. An
  "active applications" view is what permission checks read — a permission passes only when the
  grant's app is active on the target org's root.
- Permission codes are dotted per application (`<app>.<domain>.<action>`), stored in `permissions`
  per app; grants live in `role_permissions`.
- The frontend keeps one navigation registry mapping menu entries → permission codes, so one shell
  covers every app.

## Multi-user and cascading grants

- A grant is `(user_id, org_id, app_id, role_id)`; roles are per application; `role_permissions`
  holds the codes (avoid legacy permission-flag columns).
- Grant scope:
  - `org_id NULL` = **global grant**: counts for every org.
  - A grant on an ancestor org counts for every org **below it**: the permission SQL walks **up** from
    the target org to its ancestors.
  - An "accessible org ids" helper returns `None` (global) or the granted orgs **plus their
    descendants** — the org filter every org-scoped list query builds on.
- Granter discipline: you cannot grant a permission you do not hold, and nobody may change their own
  access. Superadmin is data, not a username: role code + wildcard `*` permission.
- Consumer SQL checks codes only; never infer one org's app activation from another's.

## Context: one login, many positions

- JWT claims: `user_id`, `jti`, `tv` (must equal the user's token version), `exp`; one signing config
  for all backends.
- A context is `(org/root × app × role)` plus the flattened `permissions[]` of that grant. The user
  picks it at a context switcher; the frontend keeps contexts + the active context in session
  storage, never the token.
- `can()` and permission guards read the active context to hide UI. Display-only — the backend
  re-checks every permission; never treat frontend hiding as security.
- Token hygiene: logout inserts `jti` into a revocation table (checked on every authed request);
  password change/reset bumps the token version, killing older sessions; login has a rate limit, a
  constant-time password check, and one generic error message.

## Account-level theming

- Theme presets (for example dark, light, custom) are CSS `[data-theme]` blocks using `--c-*` design
  tokens; use tokens, never raw palette colours.
- The theme is a **per-account preference** stored in the identity service, so it follows the user
  across all apps and routes once picked.
- Adding a palette needs exactly three touch-points: one preset entry, one `[data-theme]` block, one
  backend allowlist entry.

## One frontend, many backends

- One frontend shell hosts all apps: one login, one context switcher, one navigation registry — but
  separate apps in UI and backend.
- The browser never calls a backend directly. Each app has a BFF proxy
  (`/api/<app>/[...path]` → `/api/v1/<app>/...`) that reads the httpOnly auth cookie and forwards it
  as `Authorization: Bearer <token>`; the token never touches browser JS; `cache: "no-store"`.
- Proxies are intentionally not identical: binary-safe apps preserve bytes and content headers;
  public forwarders allow anonymous calls; some forward the client IP for rate limiting; auth
  (login/logout/reset) is centralized.
- Unauthenticated pages live outside the authenticated group and need their own no-auth BFF
  forwarder; record them in the security doc.
- Data ownership: ONE database, one schema per owner. **No FK leaves its schema** except
  `org_id`/`user_id` into identity — this is the platform's data-coupling rule.

## Operating rules

- **No wildcard for app admins.** Wildcard superadmin is reserved and is data, not a username. App
  roles are explicit bundles; an "admin" role does not automatically get every action.
- **Codes are final per application.** Prefer reusing an existing code; adding one is an owner-approved
  identity change, never seeded from app code.
- **Menus mirror backend gates.** Master/config menus sit behind the `.create` code, pages behind
  their read code, action groups behind their act code. A menu entry and its tour/step gates use the
  same code.
- **User pickers stay behind the app backend.** A candidate endpoint reads identity grants inside the
  caller's org scope; the browser never queries the identity service directly.
- **App settings own app data only.** Preferences, templates, letterheads, delegations — never users,
  organizations, roles, or grants.
- **Public surface:** a no-auth router mounts without the root-scoped dependency and gets its own BFF
  forwarder; record it in the security doc.
- **Role/permission audit before shipping.** Derive the matrix from the live identity data or the app's
  role doc. For each role, check: a visible first tour step, no step pointing at a hidden control, no
  connector into an unreadable page, and no combined role that matches neither side of a
  `code`/`notCode` pair.
- **Registered but unused codes are a product gap.** Do not fake UI or tour steps for them.

## Onboarding a new app (foundation recipe)

1. Register the app in `applications` (uppercase code), activate it on the root org.
2. Add its dotted permission codes (FK → app), build roles over them, grant users — decide global vs
   org-scoped per the cascade rules.
3. Create the backend on its own port with prefix `/api/v1/<app>`; decode the shared JWT, check
   revocations, read permissions from `role_permissions`; own its schema (`<app>_core`, `<app>_log`,
   …); writes go to its own audit log + the identity audit log.
4. Add the BFF proxy, the API clients, types (`types/<app>.ts`), and navigation entries. Identity
   pages and app pages live under their own route groups.
5. Never re-seed or alter identity tables from an app — the identity service owns them.
