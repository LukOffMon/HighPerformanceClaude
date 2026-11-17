# Toolbelt — capabilities that make Claude better at building

Run `scripts/toolbelt.py [path]` first: it detects the stack and what is already installed, and prints only what is missing. Recommend from this list only what the task at hand would use. Every MCP server adds tool definitions to the context, so more is not better. Never install anything without the user's go-ahead. Names and commands change: if one fails, check `/plugin` or `claude mcp --help` instead of guessing.

## MCP servers (by need)
| Need | Server | Install |
|---|---|---|
| Library docs for the installed version, not memory | context7 | `claude mcp add --transport http context7 https://mcp.context7.com/mcp` |
| See the UI: navigate, click, screenshot, console errors | playwright | `claude mcp add playwright -- npx @playwright/mcp@latest` |
| Issues, PRs, CI logs | github | `claude mcp add --transport http github https://api.githubcopilot.com/mcp/` |
| Database schema, SQL, logs, advisors | supabase | `claude mcp add --transport http supabase https://mcp.supabase.com/mcp` |
| Production errors with stack traces | sentry | `claude mcp add --transport http sentry https://mcp.sentry.dev/mcp` |
| Payments | stripe | `claude mcp add --transport http stripe https://mcp.stripe.com` |

Use `--scope project` to share a server with the team through `.mcp.json`; the default scope is the current user only.

## Plugins and skills worth checking
In Claude Code run `/plugin` and browse the marketplaces you have. Look for, and prefer official ones:
- **Frontend / design** skills for distinctive, responsive UI (vibecoding).
- **Code review** and **security review** commands for a second pass before shipping.
- **Commit / PR** helpers when the user ships often.
- Stack-specific skills (Supabase, Stripe, Next.js, React Native) only for the stack in use.
This plugin already covers: planning, options, debugging, review, vibecoding, handoff, project memory, Obsidian memory and token economy. Do not add a second plugin that does the same job; two overlapping skills cost tokens and give conflicting instructions.

## Permissions (fewer prompts, same safety)
`scripts/toolbelt.py --write` merges into `.claude/settings.json`:
- **allow**: read-only git and search commands, plus the project's own build, lint, test and typecheck scripts.
- **deny**: reading `.env*`, keys and certificates; force-push; `git reset --hard`; `rm -rf /`.
It only adds rules, never removes or loosens one. Dev servers stay on prompt because they do not exit. Show the user the rules and get a yes before writing.

## Vibecoding kit (idea → working product)
1. playwright (see what you built) + context7 (correct APIs) are the two that pay off most.
2. A hosting connector or CLI the user already uses (Netlify, Vercel, Cloudflare) for a real URL.
3. The project's own test runner allowed in permissions so each slice is verified without prompts.
4. Obsidian memory (`scripts/vault.py`) so preferences and lessons carry over between sessions.
