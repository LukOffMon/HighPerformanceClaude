# Context and Memory

Context is finite and can be summarized away mid-task. Anything that must survive — decisions, progress, gotchas — goes into files, not into your head.

## 1. During a long task

- Keep a task list (the environment's todo/task tool if present, otherwise a checklist in the handoff file). Mark items done as you go, not at the end.
- After each milestone: re-read the original goal and the acceptance criteria. Am I still solving that?
- After compaction or a long pause: re-read the handoff file, `git status`, `git log --oneline -10`, and any file before editing it.
- Commit at green checkpoints when commits are authorized; otherwise note the last green state (`git stash` / diff) in the handoff file.

## 2. Handoff file (for multi-session or post-compaction continuity)

Write to `.claude/handoff.md` (or a path the project prefers; keep it out of commits unless the user wants it):

```
# Handoff — <task> — <date>
Goal: <one sentence + acceptance criteria>
Status: <in progress | blocked | done>
Done:
- <item> (verified: <how>)
Next:
1. <concrete next step with file/function>
Decisions: <decision — reason> (one line each)
Gotchas: <env quirks, commands that work, traps found>
Open questions for user: <if any>
```

Keep it under ~60 lines. It's a cache of conclusions, not a diary.

## 3. Project memory (CLAUDE.md)

A lean `CLAUDE.md` at the repo root saves every future session from re-discovering the same facts. Propose creating or updating one when you've learned things that are expensive to rediscover. Only write it when the user agrees or the project already keeps one.

Template (aim for < 80 lines; every line should save a future search or prevent a mistake):

```
# <Project> — notes for Claude

## Commands
- Install: `pnpm i`
- Dev: `pnpm dev` (http://localhost:3000)
- Check: `pnpm typecheck && pnpm lint && pnpm test`
- Single test: `pnpm vitest run path -t "name"`

## Architecture (one line each)
- `apps/web` — Next.js App Router frontend
- `packages/db` — Drizzle schema + migrations (run `pnpm db:migrate`)

## Conventions
- Named exports; zod validation at every API boundary; money in cents.

## Gotchas
- Tests need `DATABASE_URL` pointing at the test DB (see `.env.example`).
- Don't edit `src/generated/*` — run `pnpm codegen`.
```

Don't put in it: things obvious from the code, long prose, secrets, or rules that duplicate the linter.

## 4. What deserves to be remembered

| Remember | Don't bother |
|---|---|
| Commands that actually work here (and the ones that don't) | Generic language knowledge |
| Non-obvious architecture boundaries | File-by-file summaries |
| Conventions the linter doesn't enforce | Anything stated in the README already |
| Environment quirks and their fixes | Transient debugging details |
| Decisions with their reasons | Your process narrative |
