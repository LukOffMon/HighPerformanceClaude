# Failure-Mode Catalog

Each entry: the failure, how it shows up, and the countermeasure. Scan the section that matches what you're doing.

## Contents
A. Context failures · B. Reasoning failures · C. Code failures · D. Tooling and environment · E. Agentic and long-horizon · F. Communication

## A. Context failures

| # | Failure | Tell | Countermeasure |
|---|---|---|---|
| A1 | Editing unread code | Edit anchors fail; style mismatch | Read the region and its callers before editing |
| A2 | Stale mental model | Edits reference code that changed | Re-read after formatters, other agents, compaction, or a long gap |
| A3 | Wrong file / duplicate module | Change has no effect | Confirm which file actually runs (imports, build output, path aliases) |
| A4 | Ignoring project rules | Violates CLAUDE.md / lint / conventions | Read agent docs and one neighbouring file first |
| A5 | Over-reading | Context fills with irrelevant code; later mistakes | Grep → ranges; `repo_brief.py`; subagent for wide sweeps |
| A6 | Missing the existing solution | New util duplicates an existing one | Grep for the concept (not just the name) before writing helpers |

## B. Reasoning failures

| # | Failure | Tell | Countermeasure |
|---|---|---|---|
| B1 | Hallucinated API | "is not a function", unknown option | Check installed version; read types/source; grep usage |
| B2 | Version confusion | Using v4 API in a v5 project | Read the manifest + lockfile version before coding |
| B3 | Symptom fixing | Bug returns elsewhere | Explain the cause in writing before fixing |
| B4 | Anchoring on first hypothesis | Repeated fixes on the same theory | Hypothesis table; test the most *discriminating* probe |
| B5 | Overgeneralizing from one case | Fix works for the example, breaks others | Test a second, different case |
| B6 | Solving a different problem | Polished answer to the wrong question | Re-read the user's message before reporting |
| B7 | Premature abstraction | Framework for one use case | Concrete first; abstract on the third occurrence |
| B8 | Unstated assumption | Surprise for the user later | Name assumptions in the report |

## C. Code failures

| # | Failure | Tell | Countermeasure |
|---|---|---|---|
| C1 | Broken callers | Typecheck errors elsewhere; runtime errors in other routes | Grep all usages before changing signatures/contracts |
| C2 | Unhandled unhappy path | Crash on empty/null/network error | Handle the failure modes that are realistic for this code |
| C3 | Swallowed errors | Silent failure | Never `catch {}` / bare `except: pass`; log or rethrow with context |
| C4 | Floating money, naive dates | Rounding or timezone bugs | Integer cents/decimal; UTC storage; explicit zones |
| C5 | Injection | SQL/shell/HTML built from strings | Parameterized queries, arg arrays, escaping by default |
| C6 | Secrets in code | Keys in diff | Env vars + `.env.example`; check `git diff` |
| C7 | Race conditions | Intermittent failures, double writes | Transactions, unique constraints, idempotency keys, await everything |
| C8 | Unbounded work | Slow with real data | Pagination, limits, indexes, batching; avoid N+1 |
| C9 | Leftover debug code | `console.log`, `print`, commented code in diff | Re-read the diff |
| C10 | Placeholder shipped as real | TODO, mock data, `pass` | Finish it, or label it clearly in the report |
| C11 | Inconsistent style | Different naming/formatting from neighbours | Mirror existing conventions; run formatter |
| C12 | Weakened tests | Deleted/skipped assertions | Forbidden; fix the code or justify the test change explicitly |

## D. Tooling and environment

| # | Failure | Tell | Countermeasure |
|---|---|---|---|
| D1 | Wrong working directory | "file not found", wrong package | `pwd`; use absolute paths |
| D2 | Wrong interpreter/runtime | Module not found despite install | `which python`/`node -v`; use the project's venv/version manager |
| D3 | Wrong package manager | Lockfile churn, duplicate lockfiles | Use the one the lockfile implies |
| D4 | Cached artifacts | Change doesn't show | Clear the relevant cache (`.next`, `dist`, `__pycache__`, browser) |
| D5 | Interactive commands hang | Tool call never returns | Non-interactive flags (`-y`, `--yes`, `CI=1`), no `-i` |
| D6 | Long-running server blocks | Session stalls | Run in background, poll readiness, kill afterwards |
| D7 | Network-restricted sandbox | Install/fetch fails | Detect early, report the blocker, use what's available |
| D8 | Destructive command | Lost work | Inspect target first; prefer reversible variants (`git stash`, move to trash); confirm |

## E. Agentic and long-horizon

| # | Failure | Tell | Countermeasure |
|---|---|---|---|
| E1 | Retry loop | Same edit/command repeated | Circuit breaker: new evidence or new approach |
| E2 | Drift from goal | Working on side quests | Keep a task list; re-read goal at each milestone |
| E3 | Losing state across compaction | Re-doing work; contradictions | Handoff file with done/next/decisions (`context-and-memory.md`) |
| E4 | Partial completion reported as done | User finds missing pieces | Checklist against acceptance criteria before reporting |
| E5 | Over-delegation | Subagents re-deriving context, conflicting edits | Delegate only isolated, well-briefed work; one writer per file |
| E6 | Trusting subagent output blindly | Wrong conclusions propagated | Spot-check claims (file:line) before acting |
| E7 | Committing/pushing without being asked | Unwanted remote changes | Commit/push only on request or standing instruction |

## F. Communication

| # | Failure | Tell | Countermeasure |
|---|---|---|---|
| F1 | Overclaiming | "Should work", "fully tested" without evidence | State exactly what was verified |
| F2 | Burying the lede | Outcome at the bottom | Outcome first |
| F3 | Wall of text | User skims and misses risk | Short sections; risks called out explicitly |
| F4 | Menu without recommendation | User has to do your job | Always recommend |
| F5 | Asking what you could look up | Avoidable round trip | Grep/read first, ask only for true decisions |
| F6 | Wrong language | Replying in English to a Spanish speaker | Mirror the user's language (code and identifiers stay as the codebase uses) |
