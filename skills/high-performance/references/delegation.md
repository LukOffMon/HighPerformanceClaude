# Delegation and Parallelism

Subagents give you two things: an **isolated context** (their tool output never enters yours) and **parallelism**. They cost a cold start: they don't know what you know, so they re-derive it. Delegate when isolation or parallelism is worth that cost.

## 1. When to delegate

| Delegate | Don't delegate |
|---|---|
| Wide sweep across many files/naming conventions where you only need the conclusion | Anything one or two greps answer |
| Independent subtasks that can run in parallel (separate modules, separate research questions) | Work that needs the context you already built up |
| Fresh-eyes adversarial review of your own diff | Tightly coupled edits to the same files |
| Mechanical, fully specified bulk work (on a cheap model) | Decisions that need judgement about the user's intent |
| Reading long docs/pages to extract one answer | Tiny tasks where the brief is longer than the work |

If the environment or the user restricts spawning agents, do the work inline using the same discipline.

## 2. Model tiering

| Work | Tier |
|---|---|
| Locating code, listing usages, summarizing files, extracting facts | Cheap/fast model (`hpc-scout` uses `haiku`) |
| Mechanical edits from an exact spec (renames, barrels, boilerplate) | Cheap/fast model |
| Implementation of a designed feature | Default model |
| Architecture, root-cause analysis of hard bugs, security review, adversarial critique | Strongest model (`hpc-critic` inherits yours) |

## 3. Writing the brief (the subagent only knows what you write)

```
Goal: <one sentence — the decision or artifact you need back>
Context: <repo path, stack, relevant files/dirs, what you already know or ruled out>
Scope: <what to look at; what NOT to touch>
Constraints: <read-only? conventions to follow? time/size limits>
Deliverable: <exact format — e.g. "list of file:line + one-line explanation, max 15 items" or "unified diff summary">
Done when: <stop condition>
```

Good brief: "Find every place that reads `user.plan` or calls `getPlan()` in `apps/web/src` and `packages/billing`. Read-only. Return file:line and whether the read can see `undefined`. Max 20 items."
Bad brief: "Look into the billing stuff."

## 4. Parallel fan-out

- Split by independent axis (per package, per question, per hypothesis), send all briefs in one turn.
- One writer per file. If subagents edit, give them disjoint file sets (or separate git worktrees) and merge yourself.
- Synthesize: deduplicate, resolve contradictions by checking the cited lines yourself.

## 5. Trust, but verify

Subagent reports are claims. Before acting on a load-bearing claim, open the cited file:line. Never forward an unverified subagent conclusion to the user as fact.

## 6. Bundled agents

- **`hpc-scout`** — read-only, cheap model. Codebase reconnaissance: "where/how/what uses X". Returns compact file:line findings.
- **`hpc-critic`** — read-only, strongest model. Adversarial review of a diff or plan against acceptance criteria. Returns verified findings by severity.

If these aren't installed, use the environment's built-in explore/general agent with the same brief format.
