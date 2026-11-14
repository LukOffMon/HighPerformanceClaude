# Review: Finding What Matters

Order of concern: **correctness → security → data integrity → performance at real scale → maintainability → style**. Style nits come last and only if the project has no formatter.

## 1. Procedure

1. Understand intent: PR description, linked issue, commit messages. What is this change *supposed* to do?
2. Get the shape: `git diff --stat <base>...HEAD`, then read the diff file by file, biggest-risk files first (data, auth, money, concurrency, public APIs).
3. For each changed function: read enough surrounding code to know its callers and invariants. Grep callers when signatures change.
4. Walk the checklist below.
5. Run what you can: typecheck, lint, tests for touched areas (`scripts/checks.py --run`).
6. Verify every finding before reporting it: point at the exact line and explain the concrete failure scenario. Drop findings you cannot substantiate.

## 2. Checklist

**Correctness**
- Does it do what the intent says, for all inputs — empty, null, boundary, large, unicode?
- Error paths: are failures handled, surfaced, and not swallowed?
- Concurrency: shared state, ordering, retries, double-submits, transactions.
- Contracts: changed signatures, return shapes, status codes, events — are all consumers updated?
- Tests: do they test behaviour (not implementation), cover the change, and fail without it?

**Security**
- Input validation at boundaries; injection (SQL, shell, HTML/XSS, path traversal, SSRF, template).
- AuthN on routes; AuthZ on each object (can user A read/modify user B's thing?).
- Secrets: none in code, logs, errors, client bundles.
- Unsafe deserialization, open redirects, permissive CORS, missing CSRF protection.
- New dependencies: maintained, reputable, pinned.

**Data integrity**
- Migrations reversible and safe on large tables; defaults for new non-null columns.
- Uniqueness and foreign keys enforced by the database, not just the app.
- Idempotency for webhooks/jobs/payments.

**Performance (only at realistic scale)**
- N+1 queries, missing indexes, unbounded queries/lists, work inside hot loops, large payloads, unnecessary re-renders.

**Maintainability**
- Names say what things are; functions do one thing; no dead code or commented-out blocks.
- Duplication of existing utilities; abstractions that don't pay for themselves.
- Consistency with surrounding conventions.

## 3. Severity

| Level | Meaning |
|---|---|
| **Blocker** | Wrong behaviour, data loss, security hole, broken build — must fix before merge |
| **Major** | Likely bug in realistic conditions, missing test for risky logic, contract break |
| **Minor** | Edge case unlikely in practice, maintainability issue with real cost |
| **Nit** | Style/preference — mention at most a few, or skip |

## 4. Finding format

```
[Blocker] src/api/orders.ts:88 — order total uses float math
Scenario: 3 × 19.99 → 59.970000000000006, stored and charged.
Fix: compute in integer cents (`priceCents * qty`), format at the edge.
```

Lead with the count by severity, most severe first. If nothing significant: say so plainly — don't invent findings to look thorough.

## 5. Self-review of your own diff

Before reporting your own work, review it as if someone else wrote it: re-read `git diff`, then ask "what input breaks this?" and "who else calls this?". For T2 changes, hand the diff plus acceptance criteria to the `hpc-critic` agent — fresh context isn't anchored on your reasoning.
