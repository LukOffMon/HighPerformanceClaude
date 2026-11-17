# Changelog

## [1.2.0] — 2026-11-17
### Added
- Obsidian memory: `skills/iceberg/scripts/vault.py` (init a `Claude/` workspace with profile, projects, briefs, lessons and templates; capped `context`; keyword `recall`; `save`, `lesson`, `project`). New `/hpc:obsidian` command.
- Toolbelt: `skills/iceberg/scripts/toolbelt.py` detects the stack and installed MCP servers/plugins, recommends only missing tools with install commands, and merges a safe permission allowlist/denylist into `.claude/settings.json` on request. New `/hpc:setup` command and `references/toolbelt.md`.
- `tools/token_report.py`: always-on / on-trigger / on-demand token cost, with budgets enforced by the validator.
- Eval scenarios 13–17 for Iceberg; CI smoke tests for the new scripts; installer check for the iceberg skill; CI uploads every claude.ai zip.
### Changed
- Iceberg skill rewritten: depth now matches the task (no brief for trivial work, 3-line brief for standard, full brief for deep), memory and toolbelt steps, no duplication of the high-performance skill. ~18% shorter.
- Descriptions trimmed: always-on cost down from ~810 to ~660 tokens despite two new commands.
- The validator runs `--help` on every script and resolves command references against every skill.

## [1.1.0] — 2026-11-17
### Added
- `iceberg` skill: say "Iceberg" and Claude maps the hidden part of a task (surface → waterline → depths → bedrock), rewrites the request into a ≤15-line ICEBERG BRIEF with acceptance checks and a token budget, then executes in verified slices.
- `/hpc:iceberg` command and `references/depth-probes.md` (probe checklists per task type + brief template).
- `site/iceberg.html`: animated Antarctic iceberg explainer site (source of the published page).
### Changed
- `tools/package.py` builds one claude.ai zip per skill (`dist/iceberg.zip` added); `install.sh` installs both skills.

## [1.0.0] — 2026-11-14
### Added
- `high-performance` skill: triage tiers (T0/T1/T2), orient → define → decide → build → verify → report loop, token-economy rules, failure-mode countermeasures, circuit breakers, final self-check.
- References loaded on demand: token economy, decisions, verification, debugging, vibecoding, failure modes, stack traps, review, delegation, context & memory, communication.
- Scripts: `repo_brief.py` (one-call repo orientation) and `checks.py` (detect and run the verification ladder with compact output).
- Agents: `hpc-scout` (cheap read-only reconnaissance) and `hpc-critic` (adversarial reviewer).
- Commands: brief, plan, options, ship, debug, review, vibe, handoff, memory.
- Plugin + marketplace manifests, manual installer, deterministic claude.ai zip, validator and CI.
