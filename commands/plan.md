---
description: Plan a change before writing code - triage, acceptance criteria, options, slices, verification
argument-hint: "<what to build or change>"
---
Use the `high-performance` skill. Task: $ARGUMENTS

Do not edit files yet. Produce:
1. **Tier** (T0/T1/T2) and why, in one line.
2. **Orientation** — only what you needed to read (cite `path:line`). Use `scripts/repo_brief.py` if the repo is new to you.
3. **Acceptance criteria** — observable behaviours, each with the check that will prove it.
4. **Options** — if any non-obvious choice exists, 2–3 options scored per `references/decisions.md`, with a recommendation. Skip if there is a clear default.
5. **Plan** — vertical slices, each ending runnable, with files to touch.
6. **Risks & assumptions** — irreversible steps flagged.
7. **Questions** — only those that change what gets built (max 3, each with a recommended default).

Keep it under ~40 lines. Then wait for my go-ahead.
