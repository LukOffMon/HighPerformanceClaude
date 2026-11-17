---
name: iceberg
description: Iceberg mode, the definitive coding framework. Use when the user says Iceberg, modo iceberg or usa iceberg, or asks to analyze a task deeply before starting, improve their prompt, find improvement areas, set up the best tools, plugins, permissions or Obsidian memory for coding, or go all-in on quality with minimal tokens. Maps the hidden part of the request, writes a compact self-brief with checks and a token budget, then builds and verifies in slices.
---

# Iceberg Mode

The user's message is the tip. The requirements, risks and better options sit below the waterline. Map them first, then build without drifting and without giving up, at the lowest token cost that still gets it right.

Paths like `scripts/…` and `references/…` are relative to this skill's directory. If the `high-performance` skill is available, it governs execution details (verification ladder, debugging, review); do not repeat its content here.

## 0. Depth matches the task

| Task | Descent | Brief |
|---|---|---|
| Trivial (typo, one-liner, question) | none | none — just do it |
| Standard (known area, ≤5 files) | steps 1–3 in your head | 3 lines: Goal / Accept / Slices |
| Deep (new app, unknown bug, architecture, data or money risk) | full descent + memory + toolbelt | full ICEBERG BRIEF |

Upgrade the moment hidden complexity appears. Never downgrade to skip verification.

## 1. Memory first (Obsidian, if present)
For standard and deep tasks run `python3 scripts/vault.py context <project>`. It prints the user's profile, the project note and recent lessons, capped. If it exits 3 there is no vault: continue without it and mention `/hpc:obsidian` once at the end. Use `scripts/vault.py recall "<keywords>"` only when past work on the same topic is likely. Never browse the vault with file reads.

## 2. The descent
1. **Surface** — the request in one sentence; the deliverable and who uses it.
2. **Waterline** — the goal behind the goal; implicit requirements a senior would include; repo rules (CLAUDE.md, versions, permissions); ambiguities resolved from evidence or a sensible default. Ask only what changes the build: max 3 questions, each with a recommended default. Probes per task type: `references/depth-probes.md`.
3. **Depths** — irreversible or outward-facing steps (confirm them); where you are likely to be wrong; improvement areas (do those in scope, list the rest); for costly-to-reverse choices, two options against explicit criteria.
4. **Toolbelt** (deep tasks, new projects, or when asked) — run `python3 scripts/toolbelt.py`. Recommend only missing tools this task would use, with the install command, and the permission allowlist. Never install or write settings without a yes. Catalogue and rules: `references/toolbelt.md`.
5. **Bedrock** — rewrite the request as the brief the user would have written with perfect knowledge (template in `references/depth-probes.md`): ≤15 lines, observable acceptance checks, a token budget (what to read by range, which searches to batch, what to delegate, what to skip), and vertical slices.

Show the brief, then proceed. Wait only for blocking questions or irreversible steps.

## 3. The ascent
- **Gate**: build only when every acceptance check has a way to be observed.
- Slice by slice: build → run the check → read the output → keep the evidence.
- **Steel, not stubbornness**: two failures on one approach → new evidence and a new approach. Never repeat a failing action. Never call something done to escape it; report it blocked with what you tried.
- Hidden complexity → one-line brief update and re-tier, never silent drift.

## 4. Token discipline
- Search before reading, ranges before files, independent calls batched in one turn.
- Never re-read what is in context; never restate the user's message or the brief.
- Delegate wide sweeps to a cheap read-only agent; keep only conclusions.
- Think hard on decisions and risks; spend nothing narrating easy steps.
- Lead every reply with the result.

## 5. Surface the result
- **Delivered** (paths, links) · **Verified** (what you saw, how) · **Not verified** · **Below the waterline** (≤3 improvements not done, one line each).
- Memory (if a vault exists, standard and deep tasks): save the brief plus outcome with `vault.py save --title … --project …` (body on stdin), and each lesson that would have saved time with `vault.py lesson "…" --project …`. One line per lesson, no secrets, no code dumps.

Reply in the user's language.
