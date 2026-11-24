# HighPerformanceClaude — notes for Claude

This repo **is** the High-Performance Claude plugin. When this repo is attached or open, apply the skill in `skills/high-performance/SKILL.md` to all work here, and to any other code the user asks about in this session.

When the `cekmecon_*` MCP tools are available (local sessions), apply `skills/cekmecon/SKILL.md`: open the project drawer once, then use and save memory there.

When the user says **Iceberg** (or "modo iceberg"), also apply `skills/iceberg/SKILL.md`: map the hidden part of the task and show an ICEBERG BRIEF before building.

## Layout
- `apps/cekmecon/` — Toilet Bamboo Paper GeekMcON desktop app (stdlib Python: vault + FTS index, organizer, localhost UI with the Rollito assistant, MCP bridge with one-time pairing, installers). `skills/cekmecon/SKILL.md` must equal `apps/cekmecon/cekmecon/skill/SKILL.md`. Tests: `python3 -m unittest discover -s apps/cekmecon/tests`
- `site/cekmecon.html` — source of the GeekMcON site (`docs/cekmecon/`); `/*@include path*/` inlines files at build time
- `skills/iceberg/` — Iceberg mode (adaptive descent + self-brief), triggered by the word "Iceberg"; `scripts/vault.py` (Obsidian memory), `scripts/toolbelt.py` (tools + permissions)
- `site/iceberg.html` — source of the Iceberg explainer page (published as a claude.ai Artifact)
- `skills/high-performance/` — the skill (SKILL.md is always loaded; `references/` load on demand; `scripts/` are stdlib-only Python)
- `agents/` — `hpc-scout`, `hpc-critic`
- `commands/` — slash commands (`/hpc:<name>` as a plugin, `/hpc-<name>` via install.sh)
- `.claude-plugin/` — plugin + marketplace manifests, icon
- `tools/` — `validate.py`, `package.py`; `dist/` — committed claude.ai zip

## Commands
- Validate everything: `python3 tools/validate.py`
- Rebuild the claude.ai zips after any change under `skills/`: `python3 tools/package.py`
- Rebuild the GitHub Pages site after any change to `site/iceberg.html`: `python3 tools/build_site.py`
- Token cost of the plugin (budgets enforced by the validator): `python3 tools/token_report.py`
- Official plugin check: `claude plugin validate .`

## Rules for editing the skill
- SKILL.md is paid for on every load: keep it ≤ ~2,500 words; push detail into `references/`.
- Every reference file must be mentioned in SKILL.md (the validator enforces it), and stay one level deep.
- Skill content is written in English (fewer tokens, better instruction following); Claude replies in the user's language.
- Description ≤ 1024 chars, no angle brackets — it is the trigger, so it lists when to use the skill.
- Bump the version in both manifests and add a CHANGELOG entry for releases.
