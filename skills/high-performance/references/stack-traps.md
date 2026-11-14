# Stack Traps

High-frequency mistakes per ecosystem. Read only the section for the stack in front of you.

## Contents
JavaScript/TypeScript · React · Next.js · Node backends · Python · Django/FastAPI · SQL and ORMs · Go · Rust · CSS/Tailwind · Git · Docker/CI · Security everywhere

## JavaScript / TypeScript
- `array.forEach(async …)` doesn't await. Use `for…of` with `await` or `Promise.all(array.map(…))`.
- `==` coercion; `0`, `""`, `NaN` are falsy — use `??` instead of `||` for defaults when 0/"" are valid.
- `JSON.parse` of untrusted input without try/catch; dates become strings after JSON round-trip.
- Floating point: `0.1 + 0.2 !== 0.3`; money in integer cents.
- `Date` months are 0-based; `new Date("2024-01-01")` is UTC, `new Date(2024, 0, 1)` is local.
- Sorting numbers: `arr.sort()` sorts lexicographically; use `(a, b) => a - b`.
- Mutating arguments/shared objects; prefer spreads/structuredClone when the caller keeps a reference.
- ESM vs CJS mismatch (`require` in `"type": "module"` packages, `__dirname` undefined in ESM).
- TS: `as` casts and `any` hide bugs; `!` non-null assertions crash at runtime. Narrow instead.
- `process.env.X` is `string | undefined`; validate env at startup.

## React
- Missing/unstable `key` (index keys on reorderable lists) → state bleeding between items.
- `useEffect` dependency arrays: missing deps → stale closures; objects/functions as deps → infinite loops.
- Derived state stored in state → out of sync. Compute it during render instead.
- Setting state from a stale value: use the updater form `setX(x => x + 1)`.
- Effects that fetch without cleanup/abort → race conditions on fast navigation.
- Rules of hooks: no hooks inside conditions/loops.
- Huge components re-rendering everything: split, memoize only where measured.

## Next.js (App Router)
- Server vs client components: hooks, event handlers and browser APIs need `"use client"`; keep it at leaves.
- Secrets must never be read in client components; only `NEXT_PUBLIC_*` reach the browser.
- Caching defaults vary by version — check the installed major version's docs for `fetch` caching and route segment config before relying on behaviour.
- Hydration mismatches from `Date.now()`, `Math.random()`, `window` checks during render.
- `next build` catches errors `next dev` hides — always run it before saying done.

## Node backends
- Unhandled promise rejections crash or vanish; always handle errors in async route handlers.
- Missing input validation (use zod/valibot or the framework's validator) at every boundary.
- Blocking the event loop with sync IO/CPU in request paths.
- CORS `*` with credentials; trusting `X-Forwarded-For` without a proxy config.

## Python
- Mutable default arguments: `def f(x=[])` — use `None` and create inside.
- Late-binding closures in loops (`lambda: i`) — bind with a default arg.
- Bare `except:` swallows `KeyboardInterrupt`; catch specific exceptions.
- Naive datetimes; use `datetime.now(timezone.utc)`.
- `is` vs `==` for values; string/int identity is an implementation detail.
- Wrong environment: always use the project's venv / `uv run` / `poetry run`.
- Modifying a list while iterating it; dict changing size during iteration.
- Floating money — use `Decimal`.

## Django / FastAPI
- N+1 queries: `select_related` / `prefetch_related`; in SQLAlchemy `selectinload`.
- Migrations: never edit applied migrations; generate new ones; check they're reversible.
- FastAPI: sync DB calls in `async def` endpoints block the loop — use `def` or async drivers.
- Pydantic v1 vs v2 APIs differ (`.dict()` vs `.model_dump()`); check the installed version.
- Missing auth/permission checks per object (IDOR), not just per route.

## SQL and ORMs
- Missing indexes on foreign keys and filter/sort columns.
- `NULL` semantics: `x != 'a'` excludes NULLs; `COUNT(col)` skips NULLs.
- Transactions for multi-step writes; unique constraints for "only one" rules (don't rely on check-then-insert).
- Schema changes on big tables: additive first (expand → migrate → contract); avoid locking rewrites.
- `ORDER BY` required for deterministic pagination; prefer keyset over large `OFFSET`.
- Never build SQL with string concatenation from input.

## Go
- Ignoring returned `err`; shadowing `err` with `:=` in inner scopes.
- Loop variable capture in goroutines (pre-1.22 semantics) — check the `go` directive in `go.mod`.
- Nil maps panic on write; nil interface vs interface holding nil pointer.
- Goroutine leaks: always a way to stop (context cancellation, closed channel).
- Data races: run `go test -race` for concurrent code.

## Rust
- `.unwrap()` / `.expect()` in non-test paths; propagate with `?` and typed errors.
- Fighting the borrow checker with `.clone()` everywhere — restructure ownership instead.
- Blocking calls inside async runtimes; use `spawn_blocking`.
- Feature flags on crates: the API you remember may need a feature enabled in `Cargo.toml`.

## CSS / Tailwind
- Tailwind classes built dynamically (`bg-${color}-500`) get purged — use full class names or a map.
- Check the Tailwind major version: v4 configures via CSS (`@import "tailwindcss"`, `@theme`), v3 via `tailwind.config.js`.
- `100vh` on mobile includes browser chrome; use `100dvh`.
- `z-index` wars: create stacking contexts deliberately.
- Missing `min-width: 0` on flex children causes overflow with long text.

## Git
- Never `git add -A` blindly: check `git status` for secrets, build output, screenshots, `.env`.
- Don't rewrite shared history; no force push without explicit permission.
- Commit messages: imperative summary line, body explaining *why*.
- Large binary/generated files don't belong in the repo; check `.gitignore`.

## Docker / CI
- Copy lockfile and install deps before copying source (layer caching).
- `latest` tags are non-reproducible; pin versions.
- CI runs a clean checkout: anything relying on local, ignored files fails there.
- Secrets via the platform's secret store, never in the workflow file or image.

## Security everywhere (minimum bar)
- Validate input at the boundary; encode output for its context (HTML, SQL, shell, URL).
- AuthN on every non-public route; AuthZ on every object access.
- Hash passwords with bcrypt/argon2/scrypt (never plain SHA); use the framework's session/CSRF protection.
- Don't log tokens, passwords, or full PII. Return generic errors to clients, detailed ones to logs.
- Least privilege for keys and DB users; rotate anything that leaked into a commit.
