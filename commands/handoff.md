---
description: Save session state to a handoff file so work survives compaction or continues in a new session
argument-hint: "[path — default .claude/handoff.md]"
---
Use the `high-performance` skill and follow `references/context-and-memory.md`.

Write (or update) the handoff file at the path given here, or `.claude/handoff.md` if none: $ARGUMENTS

Include: goal and acceptance criteria, status, what's done (with how each item was verified), the concrete next steps, decisions with reasons, gotchas (working commands, env quirks), and open questions. Under ~60 lines, conclusions not narrative. Check `git status` so the file reflects reality.

If a handoff file already exists and I'm starting a session, instead read it, run `git status` and `git log --oneline -10`, and tell me in ≤6 lines where we are and what's next.
