---
description: One-call orientation - stack, commands, layout, CI, hot spots and git state of the current repo
argument-hint: "[path]"
---
Use the `high-performance` skill. Run `python3 <skill-dir>/scripts/repo_brief.py $ARGUMENTS` (default path: the current directory), then read any agent docs it lists (CLAUDE.md, AGENTS.md).

Reply with at most 12 lines: what the project is, its stack and versions, how to run/verify it, where the main code lives, anything risky (dirty git tree, huge files, missing tests). Don't read further files unless I asked a question that needs them.
