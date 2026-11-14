# HighPerformanceClaude — notes for Claude

This repo **is** the High-Performance Claude plugin. When this repo is attached or open, apply the skill in `skills/high-performance/SKILL.md` to all work here, and to any other code the user asks about in this session.

## Layout
- `skills/high-performance/` — the skill (SKILL.md is always loaded; `references/` load on demand; `scripts/` are stdlib-only Python)
- `agents/` — `hpc-scout`, `hpc-critic`
- `commands/` — slash commands (`/hpc:<name>` as a plugin, `/hpc-<name>` via install.sh)
- `.claude-plugin/` — plugin + marketplace manifests, icon
- `tools/` — `validate.py`, `package.py`; `dist/` — committed claude.ai zip

## Commands
- Validate everything: `python3 tools/validate.py`
- Rebuild the claude.ai zip after any change under `skills/`: `python3 tools/package.py`
- Official plugin check: `claude plugin validate .`

## Rules for editing the skill
- SKILL.md is paid for on every load: keep it ≤ ~2,500 words; push detail into `references/`.
- Every reference file must be mentioned in SKILL.md (the validator enforces it), and stay one level deep.
- Skill content is written in English (fewer tokens, better instruction following); Claude replies in the user's language.
- Description ≤ 1024 chars, no angle brackets — it is the trigger, so it lists when to use the skill.
- Bump the version in both manifests and add a CHANGELOG entry for releases.
