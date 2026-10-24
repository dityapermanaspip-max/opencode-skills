---
name: iam-foundation
description: Foundation architecture of the Darkhive IAM platform and how every app rides on it — multi-instance (many root orgs), multi-app (applications, roles, permissions per app), multi-user grants with ancestor/descendant cascading, the context switcher, the account-level theme picker, and one Next.js FE hosting four FastAPI BEs through per-app BFF proxies. Use when laying platform foundations (darkhive-bev2, a new BE, darkhive-fev2), wiring a new app or BE into the platform, working with orgs/grants/permission cascades or contexts, or touching the theme system.
---

# IAM foundation (multi-instance, multi-app, multi-user)

IAM (`darkhive-bev2`, port 8000, prefix `/api/v1/iam`) is the identity backbone. It is the only app
with a login. GrIMIS (8001), AIDAA (8002), HILDA (8004) have no login: they decode the same JWT,
check `iam.revoked_tokens`, and read permissions from `iam.role_permissions`. When laying the
foundation for anything in this platform, this file is the map; the detailed docs live in each repo
(`darkhive-bev2/docs/01_OVERVIEW.md`, `darkhive-fev2/docs/architecture.md`).

## Multi-instance = many root orgs

- One IAM database serves many tenants. `root_org_id` is a self FK on `iam.organizations` and there
  are MANY roots. Each root org (+ its subtree of `organizations.parent_id` children) is one
  instance: its own app activations, roles, users, data.
- `OrgOption`/`:root_org_id` selects the instance almost everywhere; apps anchor data with `org_id`.

## Multi-apps

- Applications are registry rows in `iam.applications` (uppercase codes: `IAM`, `GRIMIS`, `AIDAA`,
  `HILDA`).
- An app is enabled per root org via `organization_applications`; **sub-orgs inherit** (cascade #1).
  `iam.v_active_organization_applications` is the active view a permission check uses — a
  permission only passes when the grant's app is active on the target org's root.
- Permission codes are dotted per app: `iam.user.read`, `grimis.matrix.read`, `audit.plan.read`.
  Stored in `iam.permissions` per application; FK permission → app.
- On the FE, `src/lib/appRegistry.ts` maps menu entries → permission codes, so one nav registry
  covers all four apps.

## Multi-user and the cascading grants

- A grant is `iam.user_organization_roles (user_id, org_id, app_id, role_id)`; roles are per
  application; `iam.role_permissions` (not the legacy `permission_flags`) holds the codes.
- Grant scope — cascade #2:
  - `org_id NULL` = **global grant**: counts for every org.
  - A grant on an ancestor org counts for every org **below it**: the permission SQL walks **up**
    from the target org to its ancestors (`_PERMISSION_SQL`, shared by `require_permission` and
    `check_org_permission`).
  - `get_user_accessible_org_ids(db, user_id, code)` returns `None` (global) or the granted orgs
    **plus their descendants** — the org-filter every org-scoped list query builds on (e.g. AIDAA
    `u.org_id = ANY(...)`).
- Granter discipline: `can_grant` refuses to grant a permission the granator does not hold, and a
  user may never change their own access. Superadmin is data, not a username: role code SUPERADMIN +
  wildcard `*` permission exists in `iam.role_permissions`.
- permission-consuming SQL only ever checks the codes — never assume an org's app activation implies
  another org's.

## Context = one login, many positions

- JWT claims: `user_id`, `jti`, `tv` (must equal `users.token_version`), `exp`. One signing config
  for all four BEs.
- The active position is a **context**: `UserContext` = `org_id/root_org_id × app_id × role_id`
  plus the flattened `permissions[]` of that grant. The user picks it at `/select-context`; the FE
  keeps `contexts` + active context in `sessionStorage` (`darkhive_session`), never the token.
- `can()` and `PermissionGuard` read the active context to hide UI. Display-only — the BE
  re-checks every permission; never treat FE hiding as security.
- Token hygiene: logout inserts `jti` into `iam.revoked_tokens` (checked on every authed request);
  password change/reset bumps `token_version`, killing older sessions instantly. Login has a rate
  limit (5 failures / 15 min → 429), constant-time password check, and one generic error message.

## Built-in theme picker

- `ThemeMode` presets live in `darkhive-fev2/src/lib/theme.ts` (`dark`, `warm-light`, `steampunk`,
  `windows-xp`, `windows-xp-classic`, `custom`); the palettes are `[data-theme]` blocks in
  `src/app/globals.css` using `--c-*` tokens (use tokens, never raw palette colours).
- Theme is a **per-account preference** stored in IAM (`preferences` — BE
  `app/api/v1/iam/preferences.py` has an `_MODES` allowlist), so it cascades across all apps and
  routes once picked at `/dashboard/theme`.
- Adding a palette needs exactly three touch-points: one preset entry in `theme.ts`, one
  `[data-theme]` block in `globals.css`, one `_MODES` entry in the BE allowlist.

## One FE, many BEs

- One Next.js repo (`darkhive-fev2`) is the shell for all four apps; one login, one context
  switcher, one nav registry — but separate apps in UI and BE. Ports: IAM 8000, GRIMIS 8001,
  AIDAA 8002, HILDA 8004; archivist OCR sidecar 8003 (called by BEs only). Local runner
  `git_part_2\dev.ps1` starts 8000/8001/8002 + FE 3000.
- The browser never calls a BE directly. Each app has its own BFF proxy: `/api/iam/[...path]`,
  `/api/grimis/[...path]`, `/api/aidaa/[...path]`, `/api/hilda/[...path]` →
  `/api/v1/<app>/...`. The proxy reads the `dh_token` httpOnly cookie and forwards it as
  `Authorization: Bearer <token>`; token never touches browser JS; `cache: "no-store"`.
- Proxies are intentionally not identical: IAM returns 404 for `auth/login|logout` (those go to
  `/api/auth/*`), GRIMIS allows one public call and forwards client IP for rate limiting, HILDA is
  binary-safe (bytes in/out, preserves Content-Type/Disposition), AIDAA is no-auth-exposed except
  forwarders you add. Auth (login/logout/reset) is centralized under `/api/auth/*`.
- Unauthenticated pages live outside the `(app)` group under `src/proxy.ts`'s public allowlist and
  need their own no-auth BFF forwarder (see AIDAA `/q/[token]` + `/api/aidaa-public/[...path]`).
- Data ownership: ONE PostgreSQL database, schema per owner (`iam`, `grimis_*`, `aidaa_*`,
  `hilda_*`). **No FK leaves its schema** except `org_id`/`user_id` into `iam` — this is the
  platform's data-coupling rule, not an IAM rule.

## Onboarding a new app (foundation recipe)

1. Register the app in `iam.applications` (uppercase code), activate it on the root org.
2. Add its dotted permission codes to `iam.permissions` (FK → app), build roles over them, grant
   users — decide global vs org-scoped per the cascade rules above.
3. Create the FastAPI BE on its own port with prefix `/api/v1/<app>`; decode the shared JWT, check
   `iam.revoked_tokens`, read permissions from `iam.role_permissions`; own schema (`<app>_core`,
   `<app>_log`, ...); writes go to your own audit log + `iam.audit_log` via `log_audit`.
4. Add the BFF proxy `/api/<app>/[...path]`, the `src/lib/api/<app>/` clients, types
   (`types/<app>.ts`), and appRegistry entries. IAM pages under `dashboard/admin/*`, app pages under
   `dashboard/<app>/*`.
5. Never re-seed or alter `iam.*` from an app — IAM is owned only by `darkhive-bev2` (and
   `schemasql/` + `seed_iam.py` are read-only for everyone else).
