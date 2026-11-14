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

## Measuring token economy

For scenarios 2, 3 and 7, record total tokens and tool calls with and without the skill. Expected: equal or fewer tool calls, fewer large reads, and no loss in pass rate. A skill that saves tokens but lowers the pass rate is a regression.
