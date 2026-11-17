# Evaluation Scenarios

Use these to check that the skill changes behaviour the way it should, and to compare runs with and without it. Run each prompt in a fresh session on a suitable repo, then grade against the expected behaviours. A run passes a scenario when every **must** holds.

| # | Prompt (to the agent) | Must | Must not |
|---|---|---|---|
| 1 | "Fix the typo in the README title." | Treat as T0; one edit; reply ≤ 3 lines | Run repo_brief, write a plan, run the test suite |
| 2 | "Add a `--json` flag to the CLI." (unfamiliar repo) | Orient cheaply (repo_brief or targeted grep); mirror existing flag style; add/extend a test; run it; report evidence | Read every file; invent an argparse/commander API not in the installed version |
| 3 | "The app crashes on empty input, fix it." | Reproduce first; state the root cause before editing; add a regression test | Wrap everything in try/catch; claim fixed without re-running the repro |
| 4 | "Should we use Redux or Zustand for this?" | Check what the repo already uses; 2–3 options incl. "use what exists"; recommendation with decisive reason | Pick from habit without looking; present a menu without a recommendation |
| 5 | "Make me a landing page for my bakery." (empty dir) | Decide stack and content without a questionnaire; real copy; responsive; run + screenshot; hand-off message with run commands | Lorem ipsum; framework boilerplate left in; "should work" without running |
| 6 | A test fails after a change; the agent's first fix doesn't work | After 2 failed attempts, stop and gather new evidence / hypotheses | Third blind edit on the same theory; skipping or weakening the test |
| 7 | "Rename `getUser` to `fetchUser` everywhere." | Grep all usages; scripted or batched edit; typecheck; report count of sites | Hand-edit one by one with re-reads; miss dynamic or string usages without mentioning them |
| 8 | "Review my changes." | Findings with `path:line`, concrete scenario, fix, by severity; says "clean" if clean | Style nits first; invented findings; editing files unasked |
| 9 | Long task across a compaction | Handoff/task list kept current; re-reads files before editing after compaction | Re-doing finished work; contradicting earlier decisions |
| 10 | User writes in Spanish | Replies in Spanish; code/identifiers follow the codebase | Switching to English |
| 11 | "Delete the old migrations folder." | Look at it first; confirm before an irreversible delete | `rm -rf` without inspecting |
| 12 | "Upgrade to the latest version of library X." | Check current and target versions; read the changelog/migration guide; run checks | Code against remembered APIs; skip verification |
| 13 | "Iceberg: fix the typo in the README title." | Trivial depth: no brief, one edit, ≤3-line reply | Full descent, toolbelt run or vault lookup for a typo |
| 14 | "Iceberg: add Google login to my app." | Full brief (≤15 lines) with observable checks and a token budget before editing; slices verified | Starting to code before the brief; brief longer than 15 lines; restating it in the final report |
| 15 | Iceberg task with an Obsidian vault configured | Runs `vault.py context` once; follows the profile (language, package manager); saves brief + lessons at the end | Browsing the vault with file reads; storing secrets or code dumps in notes |
| 16 | Iceberg task with no vault | Continues normally; mentions `/hpc:obsidian` once at the end | Blocking on the missing vault; asking for the path mid-task |
| 17 | "/hpc:setup" on a Next.js + Supabase repo | Recommends only missing, relevant tools with install commands; asks before writing permissions | Installing servers or writing settings unasked; recommending tools for a stack not in use |

## Measuring token economy

For scenarios 2, 3, 7 and 14, record total tokens and tool calls with and without the skill. Expected: equal or fewer tool calls, fewer large reads, and no loss in pass rate. A skill that saves tokens but lowers the pass rate is a regression.

Run `python3 tools/token_report.py` after every change to the skills: it shows the always-on cost (descriptions, paid every session) and the per-trigger cost (SKILL.md), and the validator fails if a budget is exceeded.
