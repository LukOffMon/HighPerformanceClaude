---
description: Weigh 2-4 options for a technical decision with a scored matrix, pre-mortem and a clear recommendation
argument-hint: "<the decision, e.g. 'state management for the editor'>"
---
Use the `high-performance` skill and follow `references/decisions.md`. Decision: $ARGUMENTS

1. Frame it in one sentence and classify the door (one-way / two-way).
2. Gather the constraints that are facts from the repo (stack, versions, existing deps, scale) — cite them.
3. Give 2–4 genuinely different options, including "use what exists" and "do less".
4. Score them in the compact matrix (5 = best) on criteria weighted for this situation.
5. Pre-mortem the leading option.
6. Recommend one, with the decisive reason and the trigger that would make you revisit it.

If it's a two-way door with an obvious default, say so in three lines and stop.
