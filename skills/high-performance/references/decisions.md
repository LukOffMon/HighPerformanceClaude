# Decisions: Weighing Options Like a Staff Engineer

Use this whenever a choice is not obvious and not cheap to undo: architecture, data model, library or framework, API shape, state management, storage, deployment, auth, migration path, build-vs-buy.

## 1. Classify the door

| Door | Examples | Treatment |
|---|---|---|
| **Two-way** (cheap to reverse) | internal helper structure, naming, a UI layout, a dev-only tool | Decide fast with sensible defaults. State it in one line. |
| **One-way** (expensive to reverse) | DB schema and data migrations, public API/URL contracts, auth model, framework choice, payment flows, file formats others will read, deleting anything | Run the full protocol below. Confirm with the user when it's their call. |

Most decisions are two-way. Treating them as one-way wastes time; treating one-way doors as two-way causes the worst bugs.

## 2. Protocol (one-way doors and non-obvious two-way ones)

1. **Frame**: one sentence — what are we deciding, and what constraint makes it hard?
2. **Constraints that are facts**: existing stack and versions, hosting, team skills implied by the codebase, performance/scale numbers, budget, deadlines, compliance. Look them up; don't assume.
3. **Options (2–4, genuinely different)**. Always include:
   - **A. Use what exists** (an existing dependency, pattern, or service already in the repo).
   - **B. The boring standard** (the most widely used solution in this ecosystem).
   - **C. The minimal option** (do less; defer; solve 80% with 20%).
   - Optionally **D.** the ambitious option, if it's credible.
4. **Criteria, weighted for this situation** (pick 4–6):
   - Correctness / risk of subtle bugs
   - Reversibility / lock-in
   - Fit with current stack and conventions
   - Complexity added (new deps, new concepts, ops burden)
   - Security and privacy
   - Performance at the *actual* expected scale
   - Time to ship / effort
   - Maintainability by whoever comes next
5. **Score** quickly (1–5), noting the decisive factor. Precision is fake; the point is to surface trade-offs.
6. **Pre-mortem the winner**: "It's six months later and this choice failed. Why?" If a plausible answer is severe, mitigate or pick another option.
7. **Decide and record**: one-line rationale in the reply; for one-way doors, a short ADR (below) in the repo if the project keeps docs.

## 3. Compact matrix template

```
Decision: <what>            Door: one-way | two-way
Option            Risk  Revers.  Fit  Complexity  Effort   Notes
A use existing     4      5       5      5          5      limited for X
B standard lib     4      3       4      3          3      best docs
C minimal          3      5       5      5          5      revisit at 10k users
Pick: A — <decisive reason>. Revisit if <trigger>.
```

(5 = best for every column.)

## 4. Strong defaults (deviate only with a reason)

- Existing dependency or pattern in the repo > standard library > well-known library > new niche library > hand-rolled.
- Boring, mature technology over new and exciting. Every new dependency is a liability (security, upgrades, bundle size).
- Postgres/SQLite over exotic stores until proven otherwise. SQLite is fine for single-node apps and prototypes.
- Server-rendered or simple SPA over micro-frontends; monolith over microservices for small teams.
- Plain functions and data over class hierarchies and DI frameworks, unless the codebase already uses them.
- Explicit over clever; duplication is cheaper than the wrong abstraction (wait for the third occurrence before abstracting).
- Money as integer minor units or decimal types, never floats. Times stored in UTC, rendered in the user's zone.
- Idempotent operations for anything retried (webhooks, jobs, payments).
- Feature flags or additive migrations for risky changes; expand → migrate → contract for schema changes.

## 5. When the choice belongs to the user

Product scope, visual taste, cost, vendor accounts, data retention, legal/compliance stance, risk appetite. Ask once, compactly:

```
Need one decision: <what>.
1. <Option A> — <trade-off>. (Recommended: <why>)
2. <Option B> — <trade-off>.
I'll proceed with 1 unless you prefer otherwise.
```

If the work can continue on a reasonable default while you wait, continue — but never on an irreversible step.

## 6. ADR-lite (for one-way doors)

```
# ADR-NNN: <title>
Date: YYYY-MM-DD   Status: accepted
Context: <2–4 lines: problem and constraints>
Decision: <1–2 lines>
Alternatives: <A — why not>, <B — why not>
Consequences: <what gets easier, what gets harder, revisit trigger>
```

## 7. Traps

- Choosing by familiarity from training data instead of what the repo already uses.
- Optimizing for scale the product will never see.
- "Let's also migrate X while we're here" — separate decisions, separate changes.
- Presenting the user with a menu and no recommendation.
- Analysis paralysis on two-way doors. If options are close, pick the more reversible one and go.
