---
description: Build it end to end in high-performance mode - orient, decide, build in slices, verify on the ladder, report with evidence
argument-hint: "<feature, fix or change>"
---
Use the `high-performance` skill and run its full loop for: $ARGUMENTS

- Triage the tier first and scale the process to it.
- Orient cheaply (`scripts/repo_brief.py` if the repo is new), define acceptance criteria, decide deliberately on any one-way door.
- Build in vertical slices; each slice must end runnable. Keep a task list for T2.
- Verify on the ladder as high as the environment allows (`scripts/checks.py --run`, then run the real thing). For T2, have `hpc-critic` review the diff if available.
- Respect the circuit breakers. Never weaken tests to get green.
- Report with the skill's template: outcome, changes, evidence, unverified items, decisions, next steps.

Don't commit or push unless I asked for it.
