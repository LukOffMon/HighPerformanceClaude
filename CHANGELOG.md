# Changelog

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
