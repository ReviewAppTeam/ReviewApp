# AGENTS.md

Rules for AI coding agents and reviewers working in this repository. README.md has the human onboarding; this file is the binding rulebook.

## Layout

- `apps/web`: React 19 + TypeScript 6, Vite 8, TanStack Router (file routes in `src/routes`) and TanStack Query, Tailwind 4, shadcn/ui (Base UI primitives, components in `src/components/ui`), Vitest + Testing Library.
- `apps/backend`: Python 3.14, FastAPI, Pydantic v2, SQLAlchemy 2 (async, asyncpg), Alembic, Postgres 18 + pgvector. Managed with uv. `package.json` there only wraps uv commands for the root `pnpm` scripts.
- Root: pnpm 12 workspace, Node 26, ESLint 10 flat config (`eslint.config.js`), Prettier, commitlint, husky, lint-staged.

## Generated files: never edit by hand

- `apps/backend/openapi.json`: produced by `pnpm --filter @reviewapp/backend openapi`. Committed; CI fails if stale.
- `apps/web/src/api/generated/`: produced from `openapi.json` by Hey API (`pnpm --filter @reviewapp/web gen`). Not committed.
- `apps/web/src/routeTree.gen.ts`: produced by TanStack Router. Not committed.

Changing an endpoint: edit the Pydantic models and route, run `pnpm api:sync`, fix every TypeScript error it surfaces, commit `openapi.json`.

## TypeScript rules (enforced by ESLint)

- No `any`; use `unknown` and narrow.
- No type assertions (`as Foo`, `<Foo>x`). `as const` is fine. Validate with Zod instead.
- No non-null assertions (`x!`).
- Type-only imports use `import type`.
- Exhaustive `switch` over unions.
- Every external input (env, API responses, URL params, localStorage) goes through Zod. API responses are already validated by the generated SDK.
- Data fetching goes through the generated TanStack Query options (`*Options()`), not hand-written `fetch`.
- shadcn/ui: compose existing components, use semantic color tokens, `gap-*` instead of `space-*`. Add components with `pnpm dlx shadcn@latest add <name>` from `apps/web`.

## Python rules (enforced by Ruff and Pyright strict)

- Full type hints everywhere; Pyright runs in strict mode, so no `Any` leaks and no untyped dependencies without stubs.
- Request and response bodies are Pydantic models. Route handlers declare a return type so FastAPI documents the response.
- Every router has a `tags=[...]`; the operation id is `<tag>_<function_name>`, which becomes the TS function name (`health_read_health` becomes `healthReadHealth`). Keep function names unique within a tag.
- DB access is async. Never call `select` without a limit on unbounded tables; avoid N+1 (use `selectinload`/joins).
- Schema changes go through Alembic: `pnpm --filter @reviewapp/backend migration "<message>"`, then review the generated file. CI runs `alembic upgrade head` and `alembic check`.
- Settings come from `app/config.py` (`pydantic-settings`), never `os.environ` directly.

## General

- Default to no comments. Write one only when the reason is not obvious from the code.
- One responsibility per function or component; extract instead of adding "step 1/step 2" comments.
- Branches: feature branches target `dev` via PR; `dev` deploys to the dev environment, `main` to prod; `main` only receives `dev → main` PRs. Never push directly to either.
- Commits: Conventional Commits, scopes `web`, `backend`, `ci`, `docker`, `deps`, `repo`, `release` (see `commitlint.config.js`). PRs land with merge commits, so every commit reaches `main`; CI lints each commit in a PR.
- Before calling work done, run from the root: `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm format:check`.
- Never bypass hooks (`--no-verify`) and never force-push to `main`.
