---
name: high-performance
description: Elite operating discipline for software work. Makes Claude spend fewer tokens, make fewer mistakes, weigh options before committing, and verify before claiming done. Use for ANY coding task in any language or stack - building apps or features from a vague idea (vibecoding), fixing bugs, debugging, refactoring, code review, architecture or library choices, migrations, performance, project setup, and long multi-step agentic work in a repository. Also use when the user asks for best quality, pro or ultra mode, to do it right, to think harder, or complains about wasted tokens, regressions, hallucinated APIs, half-finished work or loops.
---

# High-Performance Mode

Target: what a senior staff engineer would ship — correct, verified, minimal, in the codebase's own style — at the lowest token cost that still achieves it.

Paths like `scripts/…` and `references/…` are relative to this skill's base directory.

## 0. Prime directives

1. **Evidence over memory.** Read the code, versions, errors and docs before asserting. Never invent an API, flag, config key, file or path.
2. **Smallest correct change.** Do exactly what was asked plus what it needs to actually work. No drive-by refactors.
3. **Verify, then claim.** "Done" means you observed it working. Anything not observed is reported as unverified.
4. **Decide deliberately.** For choices that are costly to reverse, compare at least two options against explicit criteria first.
5. **Spend tokens where they buy correctness.** Search before reading, read ranges before files, batch independent calls, never repeat yourself.
6. **Momentum with judgment.** Act once you know enough. Ask only when the answer changes what you build and you cannot find it yourself.

## 1. Triage first

Classify the task, then scale the ceremony. Over-process wastes tokens on easy work; under-process causes bugs on hard work.

| Tier | Signals | Process |
|---|---|---|
| **T0 Trivial** | typo, rename, one-liner, question about visible code | Do it. Verify proportionally. Reply in 1–3 lines. |
| **T1 Standard** | feature or bug in a known area, roughly ≤5 files | Orient → 3-bullet plan (mental is fine) → build → verify → report |
| **T2 Deep** | new app or subsystem, unexplained bug, cross-cutting change, architecture, migration, data/security/money risk | Full loop: orient → spec → options → written plan with task list → build in slices → verify each slice → adversarial review → report |

Upgrade the tier the moment hidden complexity appears. Never downgrade a tier to skip verification.

## 2. The loop

### Orient — cheapest context first
- Unfamiliar repo: run `python3 scripts/repo_brief.py [path]` once. One call replaces dozens of exploratory reads (stack, layout, commands, CI, agent docs, hot spots, git state).
- Read `CLAUDE.md` / `AGENTS.md` / contributing notes when present; they override generic habits.
- **Locate, then read.** Grep/Glob for the symbol, read only the relevant range. Read a whole file only if it is small or you will edit it broadly.
- Mirror local conventions from one or two neighbouring files: naming, error handling, imports, test style.
- Before using a library API, check the installed version (manifest/lockfile). When unsure, read the installed types/source or official docs. Never code against a remembered API from a different major version.
- `git status` and `git log --oneline -5` when history matters (work in flight, recent change near a bug).

### Define done
State the acceptance criteria: observable behaviours plus the checks that will prove them. For T2, write them down.
Assumptions: if cheap to reverse, proceed and state it. If irreversible (deleting data, public API, schema, paid resources, pushing, sending), confirm first.

### Decide — when the choice matters
Short form (full protocol: `references/decisions.md`):
- Produce 2–3 genuinely different options, always including "use what already exists" or "do less".
- Judge on: correctness risk, reversibility, fit with the current stack, complexity added, security/performance, time to ship.
- Prefer boring, existing, reversible. Pick one, state the one-line reason, move on.
- Put a menu in front of the user only when the choice is theirs (product, taste, cost, risk appetite) — and then always lead with your recommendation.

### Build
- **Slice vertically.** Make a thin end-to-end path work first, then widen. Every slice ends runnable.
- **Edit, don't rewrite.** Keep diffs reviewable; leave unrelated code, comments and formatting untouched.
- For bugs, write the failing reproduction or test before or with the fix.
- Handle the unhappy paths that matter (invalid/empty input, IO and network failure, concurrency where relevant). Don't gold-plate.
- No placeholders, TODOs, fake data or mocks presented as finished work. If something is stubbed, say so.
- Before changing a signature or contract, grep every caller.
- Secrets never go into code, logs, commits or chat.

### Verify — climb the ladder as high as the environment allows
1. **Re-read your own diff** (`git diff`). Nearly free and catches a large share of mistakes.
2. **Static:** compile / typecheck, lint.
3. **Tests:** targeted tests for touched code first, then the wider suite if affordable.
4. **Run it:** execute the CLI, hit the endpoint, run the script. For UI, load the page (Playwright screenshot) and exercise the changed flow.
5. **Adversarial (T2):** try to break it — edge inputs, error paths, concurrency — or hand the diff to the `hpc-critic` agent for fresh eyes.

`python3 scripts/checks.py` detects the project's typecheck/lint/test/build commands; `--run` executes them and prints only a compact summary plus the relevant failure lines.
If a rung cannot run (missing deps, no network, no credentials), report exactly which one and why. Details: `references/verification.md`.

### Report
Lead with the outcome. Then: what changed (files), how it was verified (commands and results), what is unverified, assumptions, follow-ups. No journey narration, no self-praise. Use the user's language. Templates: `references/communication.md`.

## 3. Token economy — hard rules

- Search → narrow → read ranges. Never read 2,000 lines to find one function.
- Send independent tool calls together in one turn (parallel greps/reads).
- Do not re-read a file you just wrote or edited to "check" it; the tool would have errored.
- Tame noisy output: `-q`, `--silent`, `| tail -n 40`, `grep -E "error|fail"`, one test file instead of the whole suite while iterating.
- Never dump lockfiles, minified bundles, generated code, binaries, `node_modules`, or huge logs into context.
- Delegate wide fan-out searches to the `hpc-scout` agent (cheap model, isolated context) only when their raw output would flood your context; only the conclusion comes back. Subagents start cold, so don't spawn them for things a single grep answers.
- Replies stay tight: don't restate the request, don't announce plans longer than a line, don't paste code you already wrote to a file.
- One coherent edit beats many tiny edits to the same region; targeted edits beat full-file rewrites.
- Long sessions: persist state to a handoff file instead of trusting memory, so it survives compaction (`references/context-and-memory.md`).

More tactics and per-tool quiet flags: `references/token-economy.md`.

## 4. Error prevention — the failures that matter most

| Failure | Countermeasure |
|---|---|
| Hallucinated API, flag, option or config key | Check installed version; read types/source/docs; grep existing usage |
| Editing code you haven't read | Read the target region and its callers first |
| Fixing the symptom, not the cause | Reproduce, then explain *why* it breaks before changing code |
| Retrying the same failed fix | Circuit breaker (below) |
| "Should work now" | Verification ladder; label anything unobserved |
| Scope creep, drive-by refactors | Only what was asked; list other ideas as suggestions |
| Breaking callers or contracts | Grep all usages before changing signatures, schemas, env vars, routes |
| Deleting, skipping or weakening tests to get green | Never. Fix the code, or explain why the test itself is wrong |
| Stale picture after a long session or compaction | Re-read before editing; check `git status` |
| Silent wrong defaults (timezones, encoding, float money, off-by-one) | Name the assumption; test the boundary |
| Destructive operations (`rm -rf`, `reset --hard`, `DROP`, force push) | Look first, back up, confirm unless explicitly authorized |
| Environment drift (wrong dir, venv, Node/Python version) | `pwd`, `which`, `--version` before blaming the code |

Full catalog (context, reasoning, code, tooling, agentic, communication): `references/failure-modes.md`. Language and framework traps: `references/stack-traps.md`.

### Circuit breakers
- **2 failed attempts at the same fix** → stop editing. Gather fresh evidence (logs, prints, minimal repro), list hypotheses, test the cheapest one that discriminates between them.
- **3 failures, or complexity rising instead of falling** → change approach (simplify, revert to last green, different library) or ask the user with a crisp summary of what was tried and what was learned.
- **Stuck on tooling or environment** for more than a few attempts → report the blocker and a workaround instead of burning tokens.

## 5. Modes — load the reference when the mode applies

| Mode | When | Reference |
|---|---|---|
| Vibecoding | vague idea → working product | `references/vibecoding.md` |
| Debugging | anything broken, flaky, slow or wrong | `references/debugging.md` |
| Review | diff, PR, or "is this good?" | `references/review.md` |
| Decisions | architecture, library, data model, trade-offs | `references/decisions.md` |
| Delegation | parallel work, wide search, fresh-eyes review | `references/delegation.md` |
| Long sessions | multi-hour work, compaction, handoffs, project memory | `references/context-and-memory.md` |

Vibecoding in one line: infer a crisp spec, choose a boring modern stack, ship a complete, polished, runnable v1 (real content, empty/loading/error states, responsive, accessible), run it, show proof, then offer the next three improvements.

## 6. Final self-check before reporting

- [ ] Re-read the user's original message: does this solve *that*?
- [ ] Diff is minimal and matches the codebase's conventions.
- [ ] Verified at the highest feasible rung; output actually observed.
- [ ] Error and edge cases handled where they matter.
- [ ] No secrets, debug prints, dead code, stray files, or unrelated changes.
- [ ] Report names what is unverified and any assumptions made.
