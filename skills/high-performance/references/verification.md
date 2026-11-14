# Verification

"It compiles" is not "it works". "Tests pass" is not "the feature works" if no test covers the feature. Claim only what you observed.

## 1. The ladder

| Rung | What | Cost | Catches |
|---|---|---|---|
| 1 | Re-read `git diff` | ~free | typos, leftover debug code, wrong file, missed spot, unrelated changes |
| 2 | Compile / typecheck | low | wrong signatures, imports, null-safety, typos in names |
| 3 | Lint | low | unused vars, hooks rules, suspicious patterns |
| 4 | Targeted tests | low–med | logic errors in touched code |
| 5 | Full suite | med–high | regressions elsewhere |
| 6 | Run the real thing | med | wiring, config, env, integration, UX |
| 7 | Adversarial pass | med | edge cases, error paths, security |

T0: rungs 1 + whichever of 2–4 is instant. T1: 1–4 plus 6 when behaviour is user-visible. T2: everything feasible.

## 2. Detecting the project's commands

`python3 scripts/checks.py` (list) / `python3 scripts/checks.py --run` (execute, compact output) / `--only test` / `--cwd sub/package`.
Fallback order when detecting by hand: `CLAUDE.md` → `package.json` scripts / `Makefile` / `justfile` / `pyproject.toml` → CI workflow files (`.github/workflows/*.yml` show exactly what CI runs) → ecosystem defaults.

## 3. Ecosystem defaults

| Stack | Typecheck/compile | Lint | Test | Run |
|---|---|---|---|---|
| TS/JS | `npx tsc --noEmit` | `npx eslint .` / `npx biome check .` | `npx vitest run` / `npx jest` | `npm run dev` / `node file.js` |
| Python | `mypy .` / `pyright` | `ruff check .` | `pytest -q` | `python -m pkg` / `uvicorn app:app` |
| Go | `go build ./...` + `go vet ./...` | `golangci-lint run` | `go test ./...` | `go run ./cmd/x` |
| Rust | `cargo check` | `cargo clippy` | `cargo test` | `cargo run` |
| Java/Kotlin | `./gradlew compileJava` / `mvn -q compile` | — | `./gradlew test` / `mvn -q test` | — |
| Ruby | — | `rubocop` | `bundle exec rspec` / `rails test` | `rails s` |
| PHP | `phpstan` | `phpcs` | `vendor/bin/phpunit` / `pest` | `php artisan serve` |
| .NET | `dotnet build` | — | `dotnet test` | `dotnet run` |
| Swift | `swift build` | `swiftlint` | `swift test` | — |

Use the project's package manager (lockfile tells you: `pnpm-lock.yaml`, `yarn.lock`, `bun.lock(b)`, `package-lock.json`, `uv.lock`, `poetry.lock`).

## 4. Running the real thing

**CLI / script**: run with a realistic input and with a bad input. Check exit code and output.

**HTTP API**: start the server in the background, wait for readiness, then:
```bash
curl -sS -i -X POST localhost:3000/api/items -H 'content-type: application/json' -d '{"name":"x"}' | head -20
curl -sS -i localhost:3000/api/items/does-not-exist | head -5   # unhappy path
```
Stop the server afterwards.

**Web UI**: start the dev server, then screenshot and exercise the flow with Playwright:
```js
// node verify.mjs  (Playwright is often preinstalled; otherwise use the project's)
import { chromium } from 'playwright';
const b = await chromium.launch(); const p = await b.newPage();
const errors = []; p.on('pageerror', e => errors.push(e.message));
p.on('console', m => m.type() === 'error' && errors.push(m.text()));
await p.goto('http://localhost:5173', { waitUntil: 'networkidle' });
await p.screenshot({ path: 'shot-desktop.png', fullPage: true });
await p.setViewportSize({ width: 390, height: 844 });
await p.screenshot({ path: 'shot-mobile.png', fullPage: true });
// exercise the changed flow, e.g.: await p.getByRole('button', { name: 'Add' }).click();
console.log(errors.length ? 'ERRORS:\n' + errors.join('\n') : 'no console errors');
await b.close();
```
Look at the screenshots (read the image) — layout bugs don't show up in exit codes. Keep screenshot files out of commits.

**Database / migration**: run on a scratch DB or a transaction; check up *and* down; verify row counts or a sample query.

**Background jobs / webhooks**: trigger once, then trigger the same event twice (idempotency).

## 5. Adversarial checklist (T2)

- Empty, null/undefined, zero, negative, huge, unicode/emoji, whitespace-only inputs.
- Boundaries: first/last item, page size ±1, exact limit, leap day, DST change, end of month.
- Failure: network down, timeout, 4xx/5xx from dependency, disk full, permission denied.
- Concurrency: double-submit, two tabs, retries, race between read and write.
- Security: unauthenticated access, other user's ID in the URL (IDOR), injection in every input that reaches SQL/shell/HTML, secrets in logs or responses.
- State: refresh mid-flow, back button, stale cache, first run with empty DB.

Or dispatch `hpc-critic` with the diff and the acceptance criteria.

## 6. Reporting evidence

Be specific and honest:
- ✅ "`pytest -q` → 48 passed. Ran `curl` against `/api/items`: 201 created, 404 for unknown id."
- ✅ "Typecheck and lint pass. **Not verified in a browser** — no display server here; the UI change is unobserved."
- ❌ "Everything should work now."
- ❌ "Tests pass" (when there are no tests touching the change).

## 7. Never

- Never delete, skip, `xfail`, loosen assertions, or update snapshots blindly just to go green. If the test is wrong, say why and fix it deliberately.
- Never claim a check passed that you didn't run.
- Never leave background servers, temp files, or screenshots behind without saying so.
