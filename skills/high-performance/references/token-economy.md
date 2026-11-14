# Token Economy

Tokens are attention. Every irrelevant line in context dilutes the relevant ones and makes mistakes more likely, so saving tokens and making fewer errors are the same goal.

## Contents
1. Budget mindset
2. Reading strategy
3. Command output discipline (per ecosystem)
4. Search patterns
5. Editing economy
6. Response economy
7. Subagents and isolation
8. Anti-patterns

## 1. Budget mindset

Before each tool call ask: *what is the cheapest action that reduces my uncertainty the most?*

| Need | Cheapest sufficient action |
|---|---|
| Does X exist? Where? | `Grep` with `files_with_matches` / `rg -l` |
| How is X used? | `Grep` with `-n` and a few lines of context |
| What's in this module? | Read the first ~60 lines (imports, exports), or grep `^(export|def|class|func|fn) ` |
| What's the project like? | `scripts/repo_brief.py` once |
| Did it work? | Exit code + last ~30 lines of output |
| What changed? | `git diff --stat`, then `git diff -- <file>` |

## 2. Reading strategy

- Grep first, then Read with `offset`/`limit` around the hits.
- Whole-file reads only when the file is small (< ~300 lines) or you will edit it broadly.
- Large or generated files (lockfiles, `*.min.js`, snapshots, migrations dumps, `dist/`, vendored code): never read whole. Grep inside them if you must.
- JSON/YAML: query with `jq` / `yq` / a Python one-liner instead of reading. Example: `jq '.scripts' package.json`, `jq '.dependencies | keys' package.json`.
- Logs: `tail -n 100`, `grep -n -E "ERROR|Exception|Traceback" log | tail -20`.
- Types are a compressed spec: for an unknown library, read its `.d.ts` / stub / signature, not its implementation.
- Read a file once per task phase. Re-read only if it may have changed (after a tool, a formatter, another agent, or compaction).

## 3. Command output discipline

Use quiet flags while iterating; run verbose only on the one failing case.

| Ecosystem | Quiet iteration | Single failing target |
|---|---|---|
| pytest | `pytest -q -x --tb=short` | `pytest path/test_x.py::test_name -q --tb=long` |
| Jest | `npx jest --silent` | `npx jest path -t "name"` |
| Vitest | `npx vitest run --reporter=dot` | `npx vitest run path -t "name"` |
| Go | `go test ./... 2>&1 \| tail -40` | `go test ./pkg/x -run TestName -v` |
| Rust | `cargo test -q` / `cargo check -q` | `cargo test name -- --nocapture` |
| TypeScript | `npx tsc --noEmit --pretty false \| head -40` | n/a |
| ESLint | `npx eslint . --quiet` (errors only) | `npx eslint path` |
| Ruff | `ruff check . --output-format concise` | `ruff check path` |
| npm/pnpm | `npm run build --silent 2>&1 \| tail -40` | — |
| pip | `pip install -q ...` | — |
| git | `git log --oneline -10`, `git diff --stat` | `git show <sha> -- path` |
| docker | `docker build -q .`, `docker logs --tail 50 c` | — |

General filters: `2>&1 | tail -n 40`, `| grep -E -i "error|fail|warn" | head -30`, `| head -c 4000`.

`scripts/checks.py --run` applies this automatically: it prints one line per check and only the relevant tail of failures.

## 4. Search patterns

- Definition: `rg -n "^(export )?(async )?(function|const|class|def|func|fn|type|interface) Name\b"`
- All callers before changing a signature: `rg -n "\bName\(" --type-add 'src:*.{ts,tsx,js,py,go,rs}' -t src`
- Config key usage: `rg -n "API_URL|apiUrl" -g '!**/node_modules/**'`
- Route/endpoint: `rg -n "['\"]/api/users"`
- Restrict scope: `-g 'src/**'`, `-t py`, `--max-count 3` per file.
- Prefer `files_with_matches` first when the hit count may be large; then narrow.

## 5. Editing economy

- One Edit per coherent change; avoid five micro-edits to adjacent lines.
- Unique, minimal `old_string` anchors (a few distinctive lines), not half the file.
- Full rewrites only for new files or files you are restructuring end to end.
- Mechanical mass changes (rename across 40 files): use a scripted replace (`sed`, `ruff --fix`, `eslint --fix`, codemod) and then review `git diff --stat` plus a sample, instead of 40 hand edits.
- Don't Read after Edit/Write to confirm; trust the tool result.

## 6. Response economy

| Situation | Length |
|---|---|
| T0 done | 1–3 lines |
| T1 done | Outcome line + 3–6 bullets |
| T2 done | Outcome + short sections (changed / verified / risks / next) |
| Question answered | Answer first, then only the reasoning needed to trust it |

Cut: restating the request, "Great question", "I will now…", summaries of code that is already in files, repeated caveats, long lists of things you didn't do unless they matter.

## 7. Subagents and isolation

A subagent's tool output stays out of your context; only its report returns. That's a win when:
- the search is wide (many files, many patterns) and you only need the conclusion;
- work is independent and parallelizable;
- you want a fresh-eyes review that isn't anchored on your own reasoning.

It's a loss when one grep would do, or when the task needs the context you already have (the subagent re-derives it at cost). Write self-contained briefs: `references/delegation.md`.

## 8. Anti-patterns (each one burns tokens *and* raises error rates)

- Reading every file in a directory "to understand the project".
- Running the full test suite after each one-line change.
- `cat`-ing a 5,000-line log.
- Re-explaining the plan every turn.
- Pasting the full final file into chat after writing it.
- Asking the user something you could answer with one grep.
- Trial-and-error edits without new evidence between attempts.
