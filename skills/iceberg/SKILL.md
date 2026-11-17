---
name: iceberg
description: Iceberg mode - a pre-flight framework that turns any request into an impeccable plan before acting. Use when the user says Iceberg, iceberg mode, modo iceberg, usa iceberg, or starts or ends a message with the word Iceberg. Also use when the user asks Claude to analyze the task deeply before starting, find what they did not say, improve or rewrite their own prompt, find areas of improvement, build the best possible framework first, work with full awareness, or not stop until it is done right. Reads the visible request (the tip), surfaces the hidden requirements, risks and improvement areas beneath it, rewrites the prompt into a compact self-brief with a token budget, then executes with the high-performance discipline and verifies before claiming done.
---

# Iceberg Mode

The user's message is the tip. Most of the task sits below the waterline: unstated requirements, constraints, risks and better options. Iceberg mode maps the whole mass **before** building, then executes without drifting and without giving up — at the lowest token cost that still gets it right.

If the `high-performance` skill is available, it governs execution (triage, verification ladder, token economy). Iceberg adds the descent and the self-brief on top.

## The descent (do it before touching anything)

Depth scales with the task. A typo gets one line of thought; a new app gets the full dive. Never skip the brief; shrink it.

### 1. Surface — what was literally asked
Restate the request in one sentence, in your own words. Name the deliverable (code, file, answer, page, link) and the audience.

### 2. Waterline — what was meant
- **Goal behind the goal**: why does the user want this? What does success look like to them?
- **Implicit requirements**: things any competent person would include without being told (responsive layout, error states, tests, docs, links that actually work).
- **Constraints**: repo rules (CLAUDE.md, AGENTS.md), stack and versions, budgets, deadlines, permissions.
- **Ambiguities**: list them; resolve each from the code, the context or a sensible default. Ask only when the answer changes what you build and you cannot find it — max 3 questions, each with a recommended default.

Use `references/depth-probes.md` for the probe checklist matching the task type.

### 3. Depths — what could sink it
- **Risks**: irreversible actions, data loss, security, cost, things that touch other people.
- **Failure modes**: where you are likely to be wrong (remembered APIs, unverified assumptions, half-finished slices, scope creep).
- **Improvement areas**: what in the request, the code or the approach could be better. Offer them; apply only those inside scope.
- **Options**: if a choice is costly to reverse, compare at least two against explicit criteria and pick one.

### 4. Bedrock — rewrite the prompt for yourself
Compress everything above into an **Iceberg Brief**: the prompt the user would have written with perfect knowledge. Format in `references/depth-probes.md` (section Brief). Rules:
- At most ~15 lines. Concrete, testable, no filler.
- Acceptance criteria are observable checks, not adjectives.
- A **token budget**: which files to read (ranges, not whole files), which searches to batch, what to delegate, what to skip.
- A **slice plan**: vertical slices, each ending runnable and verified.

Show the brief to the user in a compact block, then proceed. Do not wait for approval unless an open question or an irreversible step needs it.

## The ascent (execute)

1. **Gate**: start building only when every acceptance criterion has a way to be checked. If one cannot be checked, fix the brief first.
2. Build slice by slice. After each slice: run the check, read the output, record evidence.
3. **Steel, not stubbornness**: on failure, diagnose the root cause before retrying. Two failed attempts on the same approach → step back, re-read the brief, change approach. Never repeat the same failing action. Never declare done to escape a hard problem; report it as blocked with what you tried.
4. Keep the brief alive: if hidden complexity appears, update the brief (one line) and re-tier — do not silently drift.

## Token economy (always on)
- Search before reading; read ranges before files; batch independent calls in one turn.
- Never re-read what is already in context; never restate the user's message back at length.
- Delegate broad sweeps to a cheap read-only agent when one exists; keep only conclusions.
- Spend thinking on decisions and risks, not on narrating easy steps.
- Output: lead with the result. No preamble, no recap of what the user already knows.

## Surfacing — the final report
Short, evidence-first:
- **Delivered**: what exists now, with paths or links.
- **Verified**: what you observed working, and how.
- **Not verified / assumptions**: stated plainly.
- **Below the waterline**: up to 3 improvement areas you found but did not do, each one line.

## Self-check before finishing
- Did I answer the goal behind the goal, not only the literal words?
- Is every acceptance criterion backed by evidence I saw this session?
- Did I waste tokens (whole-file reads, repeated searches, long narration)? Trim next turn.
- Did I respect the user's language? Reply in the language the user writes in.
