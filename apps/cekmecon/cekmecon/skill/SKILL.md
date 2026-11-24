---
name: cekmecon
description: Toilet Bamboo Paper GeekMcON, the user's local memory app. Use when cekmecon tools are available, or the user mentions GeekMcON (formerly Çekmecón), Cekmecon, Toilet Bamboo Paper, their memory drawer, or wants Claude to remember, recall or organize project knowledge across sessions without re-reading context.
---

# GeekMcON — the memory drawer

GeekMcON is a desktop app on the user's computer. It keeps Markdown notes (Obsidian-compatible) under one drawer per project and serves them to you through the `cekmecon` MCP server. Use it so you never re-read what is already known.

## Where it works
- Only when this session runs on the user's own computer (local Claude Code, or a session attached to their machine). A cloud container cannot reach it: do not try, do not mention it unless asked.
- If the `cekmecon_*` tools are missing on a local session and the user wants memory, tell them once: install with the one-liner from the site, then run `cekmecon connect`.

## Permission (ask once, then automatic)
- The first `cekmecon_*` call makes Claude Code ask the user to allow the tool, and the GeekMcON window asks them to Allow the connection. Say in one line what you are about to do and that they will see both prompts; recommend "don't ask again" and "Always".
- After that, never ask again: use the tools directly. If a call says it is waiting for approval, tell the user to click Allow in the GeekMcON window and retry once. If access was denied, continue without memory and do not ask again in this session.

## Workflow
1. **Start of work in a project**: call `cekmecon_open_project` once (path = project root, query = task keywords). It auto-creates or refreshes the drawer (brief, auto map, decisions, lessons, tasks, log) and returns a capped memory pack. Treat that pack as already read.
2. **Before exploring**: `cekmecon_search` for past work on the topic; `cekmecon_read` only the notes you need, by line range when long.
3. **As you go** (`cekmecon_remember`, one line each, with `project`):
   - `decision` — a choice and why; `lesson` — something that would have saved time; `task` — an open item; `log` — what was done at the end of a slice.
   - Longer material (architecture, runbooks): `kind=note` with a title, or `cekmecon_write_note` under `Projects/<project>/`.
4. **End of a task**: log the outcome; save the lessons; call `cekmecon_organize` if you created several notes.

## Rules
- Never store secrets, tokens, personal data or code dumps. Summaries and pointers (`file:line`) only.
- Do not rewrite the user's hand-written notes; append, or write new notes. `Map.md` is regenerated automatically.
- Keep memory packs small: default budget 1500 tokens; raise it only for a deep task.
- If the high-performance or iceberg skills are active, GeekMcON replaces the Obsidian vault step: use `cekmecon_open_project` instead of `vault.py context` when the tools are available.
