---
description: Create or tighten a lean CLAUDE.md for this project so future sessions start fast and make fewer mistakes
---
Use the `high-performance` skill and follow the project-memory section of `references/context-and-memory.md`.

1. Run `scripts/repo_brief.py` and read the existing CLAUDE.md/AGENTS.md if any.
2. Verify the commands actually work (or mark them unverified) before writing them down.
3. Draft a CLAUDE.md under ~80 lines: commands, one-line architecture map, conventions the linter doesn't enforce, gotchas. Every line must save a future search or prevent a mistake. No secrets, no prose, nothing obvious from the code.
4. If a CLAUDE.md exists, propose a tightened version as a diff rather than rewriting blindly.

Show me the result and write it to the file once it's settled; don't commit unless I ask.
