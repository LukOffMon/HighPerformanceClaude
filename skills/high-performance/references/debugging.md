# Debugging: The Scientific Method, Applied Cheaply

Guessing is the most expensive debugging strategy: each guess costs an edit, a run and context, and wrong guesses leave residue. Spend tokens on evidence instead.

## 1. The loop

1. **Capture the symptom exactly.** Full error message, stack trace top frames, inputs, environment, expected vs actual. Quote it; don't paraphrase.
2. **Reproduce.** Smallest command or test that shows the bug. No repro → no fix (see §5 for when repro is hard).
3. **Localize.** Where does correct become incorrect? Follow the data from input to wrong output. Read the code on that path — not the whole module.
4. **Hypothesize.** List 2–4 candidate causes, ranked by likelihood × cheapness to test.
5. **Test the most discriminating hypothesis.** One probe that splits the candidates: a print/log, a debugger breakpoint, a REPL call, an assertion, a `git bisect` step.
6. **Explain the cause** in one or two sentences *before* fixing. If you can't explain it, you haven't found it.
7. **Fix at the root**, minimally.
8. **Guard**: turn the repro into a regression test.
9. **Clean up**: remove probes and debug prints; check `git diff`.

## 2. Hypothesis table (write it when the bug resists a first look)

```
Symptom: <exact>
#  Hypothesis                         Evidence for / against          Probe                 Result
1  stale cache returns old value      only after edit, fine on reload  log cache hit/miss    hit → confirmed
2  race between save and refetch      intermittent                     add await, re-run     —
```

## 3. Localization techniques (cheapest first)

- **Read the stack trace bottom-up to the first frame in project code.** That frame is usually where to look.
- **Search for the error string** in the repo and in the dependency (`rg -n "exact message" node_modules/lib` / site-packages).
- **Binary search the data path**: log the value at the midpoint between input and output; recurse into the wrong half.
- **`git bisect`** when it used to work: `git bisect start; git bisect bad; git bisect good <sha>; git bisect run <test-cmd>`.
- **Diff against working**: same code, different env? Compare versions (`npm ls pkg`, `pip show pkg`), env vars, config, data.
- **Minimize the input**: delete half the input/config/code until the bug disappears; the last deletion is the culprit.
- **Rubber duck in writing**: state each step the code takes and what you expect at that step; the false statement is the bug.

## 4. Root-cause classes (check these first — they explain most bugs)

| Class | Typical tell |
|---|---|
| Wrong assumption about data shape | `undefined`/`None`/`KeyError`; works for some records only |
| Async/ordering | intermittent; fixed by adding a delay; missing `await` |
| Stale state / cache | fixed by refresh/restart; wrong value after mutation |
| Off-by-one / boundary | first or last item wrong; pagination dupes or gaps |
| Environment/config | works locally, fails in CI/prod; missing env var; different version |
| Version mismatch | API exists in docs but "is not a function"; type errors after install |
| Encoding / locale / timezone | wrong characters; dates off by hours; sorting differs |
| Mutation of shared object | change in one place shows up in another |
| Swallowed error | silent failure; `catch {}` / bare `except:` |
| Wrong instance/import | edited file isn't the one that runs; duplicate module; build output stale |
| Caching layers | browser cache, CDN, build cache, `__pycache__`, `.next`, Docker layer |

## 5. Hard cases

- **Intermittent / flaky**: run it N times (`for i in $(seq 20); do cmd || break; done`), log with timestamps and IDs, suspect shared state, ordering, time, randomness, network. Fix the race, don't add a sleep.
- **Only in prod/CI**: diff environments explicitly (versions, env vars, data volume, OS, timezone, permissions). Reproduce with the CI image or the same versions.
- **Performance**: measure before changing. Profile (`py-spy`, `cProfile`, Chrome performance panel, `--cpu-prof`, `EXPLAIN ANALYZE`). Fix the top hotspot, re-measure, stop when the goal is met. Common culprits: N+1 queries, missing index, re-rendering, sync IO in hot loops, unbounded growth.
- **Heisenbug that vanishes under logging**: timing-dependent; use non-blocking logging or post-mortem state capture.
- **Can't reproduce at all**: add targeted logging/telemetry at the suspected boundary, ship that safely, and say so — don't ship a speculative fix as a "fix".

## 6. Circuit breaker (from SKILL.md, applied here)

After two failed fixes, stop editing code. Re-read the original error, revisit the hypothesis table, gather one new piece of evidence. After three, change strategy (simplify, revert to last known good, isolate in a fresh minimal project) or report to the user: symptom, what was tried, what was ruled out, best current hypothesis, proposed next probe.

## 7. Report template

```
Cause: <one or two sentences explaining WHY it broke>
Fix: <what changed, file:line>
Proof: <repro now passes; regression test added: path::name; suite result>
Also checked: <related places with the same pattern>
```
