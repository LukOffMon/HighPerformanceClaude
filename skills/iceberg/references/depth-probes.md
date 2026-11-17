# Depth probes

Pick the block that matches the task; skip probes that obviously do not apply. Each probe is a question to answer from evidence, not to ask the user.

## Any task
- Who consumes the result, and where (terminal, browser, phone, CI, another agent)?
- What does "done" look like to them — a link, a merged diff, a passing test, a decision?
- What rules does the repo impose (CLAUDE.md, AGENTS.md, CONTRIBUTING, lint, CI)?
- What is irreversible or outward-facing (push, deploy, delete, publish, send)? Confirm those.
- What will the user ask next? Prepare for it only if it is cheap.

## Build a feature / app / page
- Empty, loading, error and overflow states? Mobile width? Keyboard and screen reader?
- Dark mode, reduced motion, slow network?
- Data: where does it live, what survives a reload, what is shared between users?
- How will it be run and seen (dev server, preview, published link)?

## Fix a bug
- Can I reproduce it? What is the smallest failing input?
- Is the reported symptom the cause, or downstream of it?
- What else calls the code I will change? What test locks the fix?

## Refactor / migrate
- What behaviour must stay identical? How do I prove it (tests, snapshots, diff of outputs)?
- Which version am I moving to, and what breaks between versions (read the changelog)?
- Can it land in reversible steps?

## Decide / research
- Which criteria matter to this user (cost, speed, lock-in, team skill)? Weight them.
- What evidence would change the answer? Look for it before recommending.

## Write / explain
- Audience level and language? Desired length? Where will it be pasted?

## Prompt rewrite (improve the user's own request)
Turn vague words into checks:
- "fast" → "first render under 1 s on mid-range phone"
- "nice design" → "responsive at 360 px, consistent spacing scale, both themes"
- "secure" → "no secrets in client code, inputs validated, auth on every endpoint"
- "works" → "command X exits 0 and output shows Y"

## Brief
```
ICEBERG BRIEF
Goal:      <the goal behind the request, one line>
Deliver:   <artifacts + where they will live>
Accept:    1) <observable check>  2) <check>  3) <check>
Hidden:    <implicit requirements found below the waterline>
Risks:     <irreversible / risky steps and how they are guarded>
Options:   <choice made + why, or "clear default">
Budget:    read <files/ranges>; batch <searches>; delegate <sweep>; skip <noise>
Slices:    1) <runnable slice>  2) <slice>  3) <slice>
Open:      <questions that block, each with default> | none
```
