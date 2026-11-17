---
description: Connect Iceberg to your Obsidian vault - create the Claude/ memory workspace and fill your profile
argument-hint: "[vault path]"
---
Use the `iceberg` skill. Set up Obsidian memory:

1. Run `python3 <iceberg-skill-dir>/scripts/vault.py init` (add `--vault "$ARGUMENTS"` if I gave a path). If it exits 3, ask me for my vault path in one line, then retry with `--vault`.
2. Read `Claude/Profile.md` in the vault. For the TODO lines you cannot fill from this repo or this conversation, ask me at most 4 short questions in one message, each with a suggested answer.
3. Write my answers into `Claude/Profile.md` (keep it under 40 lines, no secrets). If we are inside a project, create its note with `vault.py project <name>` from what you can see (stack, run/test/build commands).
4. Reply in ≤6 lines: vault path, files created, how Iceberg will use them.
