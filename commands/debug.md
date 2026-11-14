---
description: Scientific debugging - reproduce, localize, hypothesize, probe, explain the root cause, fix, guard with a test
argument-hint: "<symptom, error message or failing command>"
---
Use the `high-performance` skill and follow `references/debugging.md`. Symptom: $ARGUMENTS

1. Capture the exact symptom and reproduce it with the smallest command or test.
2. Localize along the data path; read only the code on that path.
3. Write a hypothesis table (2–4 candidates) and run the most discriminating probe first.
4. Explain the root cause in one or two sentences **before** changing code.
5. Fix minimally at the root, turn the repro into a regression test, remove probes.
6. Apply the circuit breaker: after two failed fixes stop editing and gather new evidence.

Report: cause, fix (`path:line`), proof, and other places with the same pattern.
