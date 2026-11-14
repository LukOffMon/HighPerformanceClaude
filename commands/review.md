---
description: Review the current diff (or a branch/PR/path) for real defects - correctness, security, data integrity - with verified findings only
argument-hint: "[base branch, PR, or path — default: uncommitted changes + branch vs default]"
---
Use the `high-performance` skill and follow `references/review.md`. Target: $ARGUMENTS
(If no target was given: the uncommitted changes plus this branch's commits vs the default branch.)

- Understand the intent first (commit messages, PR text, my request).
- Read the diff riskiest-files-first; read callers for changed contracts.
- Run what's cheap: `scripts/checks.py --run --keep-going`.
- If the `hpc-critic` agent is available and the change is non-trivial, have it review independently, then merge and verify both sets of findings yourself.
- Report only findings you can point to (`path:line`) with a concrete failure scenario and a fix, ranked Blocker → Major → Minor. If it's clean, say so.

Don't modify files unless I ask you to apply the fixes.
