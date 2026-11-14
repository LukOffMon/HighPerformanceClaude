# Vibecoding: From a Vague Idea to a Product That Impresses

The user gives an intent ("make me a habit tracker", "a landing page for my bakery", "a dashboard for my CSV"). They judge the result by opening it. So the job is: infer what they really want, make decisions they'd approve of, and hand back something complete, polished and *running* — with proof.

## 1. Extract the spec (silently, in a few seconds)

Answer these from the message, the repo and common sense; ask only if a wrong guess would waste the whole build:
- **Who** uses it and **what job** does it do for them?
- **The 3 core flows** (e.g. add habit → check it off today → see streak).
- **Data**: what entities, where they persist (none / localStorage / SQLite / Postgres / existing backend)?
- **Platform**: web, mobile-web, CLI, desktop, script, bot? Existing repo stack wins.
- **Quality signal**: personal tool, demo, or production? Production raises the bar on auth, validation, tests, security.
- **Out of scope for v1** — write it down so you don't drift.

If something is genuinely ambiguous *and* matters (e.g. "should users log in?"), pick the simpler option, build it, and say how to switch.

## 2. Default stacks (when the repo doesn't decide for you)

| Project | Default | Why |
|---|---|---|
| Single interactive page / small tool / game | One `index.html` with inline CSS/JS, or Vite + vanilla TS | Zero setup, opens anywhere |
| Multi-view web app, client-only | Vite + React + TypeScript + Tailwind; state in React, persistence in localStorage | Ubiquitous, fast DX |
| Full-stack web app | Next.js (App Router) + TypeScript + Tailwind; SQLite (dev) or Postgres via Prisma/Drizzle | One deployable, server actions, huge ecosystem |
| API / backend | FastAPI (Python) or Hono/Express (TS); Postgres/SQLite | Typed, documented, simple |
| Data / CSV / analysis | Python + pandas; output charts/HTML report | Right tool |
| CLI | Python (argparse/typer) or Node (commander); single entry point | Simple distribution |
| Mobile app | Expo (React Native) + TypeScript | One codebase, runs on device quickly |
| Automation / scraping | Python + httpx/Playwright | Robust |

Pin versions that exist; check the installed/latest version rather than recalling one. Don't add a dependency for something the platform does natively.

## 3. Build order (vertical slices)

1. Skeleton that runs (hello world in the chosen stack) — verify it starts.
2. Core flow #1 end to end with real persistence.
3. Core flows #2 and #3.
4. States: empty, loading, error, success; validation messages.
5. Polish pass (§4).
6. Verify (§5), then README with run instructions.

Each step ends runnable. If time or context runs short, you still have a working product with fewer features — never a half-wired everything.

## 4. The polish bar ("looks like a real product")

**Content**: realistic, specific copy and sample data relevant to the user's domain. No lorem ipsum, no "Item 1, Item 2".
**Layout**: consistent spacing scale (4/8px), max content width (~65–75ch for text, ~1200px for apps), clear hierarchy (one primary action per view).
**Typography**: one or two families, a clear type scale, line-height ~1.5 for body, sufficient contrast.
**Color**: define tokens (CSS variables) — background, surface, text, muted, primary, danger, border; support dark mode when cheap (`prefers-color-scheme`).
**States**: hover, focus-visible, active, disabled; empty states with a call to action; skeletons or spinners for loading; friendly, actionable errors.
**Responsiveness**: works at 375px and 1440px; no horizontal scroll; tap targets ≥ 44px.
**Accessibility**: semantic HTML, labels for inputs, alt text, keyboard reachable, visible focus, `aria-live` for async messages.
**Motion**: subtle (150–250ms), respects `prefers-reduced-motion`.
**Feel**: instant feedback on every action; optimistic updates where safe; keyboard shortcuts for power flows if cheap.
**Details that impress**: favicon and page title, meaningful empty-state illustration/emoji, persistence across reload, sensible defaults, confirm before destructive actions, undo where cheap.

## 5. Verify like the user will

- Start it. Open it (Playwright screenshot desktop + mobile; see `verification.md`). Read the screenshots.
- Click through all three core flows. Reload: is data still there?
- Check the console for errors and the terminal for warnings.
- Try one bad input per form.
- `npm run build` / equivalent passes (dev mode hides errors that production build shows).

## 6. Hand-off message

```
<One line: what you built and that it runs.>
Run it: <exact commands>
What's in it: <3–6 bullets of features>
Verified: <how — build passed, flows clicked through, screenshots>
Choices I made: <stack, persistence, any assumption — and how to change it>
Next best improvements: 1. … 2. … 3. …
```

## 7. Don'ts

- Don't scaffold ten empty pages; three complete flows beat ten stubs.
- Don't add auth, payments, i18n, analytics, or microservices unless asked or clearly needed.
- Don't leave the default framework boilerplate (Vite logo, "Edit src/App.tsx").
- Don't use mock data where real persistence was implied — or label it clearly.
- Don't present "it should work" — run it.
- Don't ask five questions up front. Ask zero or one; decide the rest and report your choices.
