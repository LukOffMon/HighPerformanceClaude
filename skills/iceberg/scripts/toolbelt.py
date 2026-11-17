#!/usr/bin/env python3
"""Toolbelt check for Iceberg: what this project needs, what Claude Code already has, what to add.

  toolbelt.py [path]            report: stack, installed MCP servers/plugins, missing recommendations,
                                suggested permission allowlist (read-only, nothing written)
  toolbelt.py [path] --write    merge the suggested allow/deny rules into <path>/.claude/settings.json
                                (adds only; never removes or loosens an existing rule)

Standard library only. Output is capped and compact so it is cheap to read.
"""
import argparse
import json
import re
import sys
from pathlib import Path

# name -> (why, install command, detector keywords in deps/files; empty = always useful)
MCP = {
    "context7": ("current library docs instead of remembered APIs",
                 "claude mcp add --transport http context7 https://mcp.context7.com/mcp", []),
    "playwright": ("open, click and screenshot the app to verify UI work",
                   "claude mcp add playwright -- npx @playwright/mcp@latest",
                   ["react", "next", "vue", "svelte", "vite", "astro", "angular", "nuxt", "solid", "html"]),
    "github": ("issues, PRs and CI from inside the session",
               "claude mcp add --transport http github https://api.githubcopilot.com/mcp/", [".github"]),
    "supabase": ("schema, SQL, logs and advisors of your Supabase project",
                 "claude mcp add --transport http supabase https://mcp.supabase.com/mcp", ["supabase"]),
    "sentry": ("real production errors with stack traces",
               "claude mcp add --transport http sentry https://mcp.sentry.dev/mcp", ["sentry"]),
    "stripe": ("payments objects and docs", "claude mcp add --transport http stripe https://mcp.stripe.com", ["stripe"]),
}

SAFE_BASH = ["git status", "git diff", "git log", "git show", "ls", "pwd", "rg", "grep", "wc", "head", "tail", "which"]
DENY = ["Read(./.env)", "Read(./.env.*)", "Read(./**/*.pem)", "Read(./**/id_rsa*)",
        "Bash(rm -rf /*)", "Bash(git push --force:*)", "Bash(git push -f:*)", "Bash(git reset --hard:*)"]


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def detect(root: Path) -> dict:
    info = {"pm": None, "scripts": [], "deps": set(), "langs": [], "files": set()}
    for name in (".github", "supabase", "Cargo.toml", "go.mod", "pyproject.toml", "requirements.txt", "index.html", "Makefile"):
        if (root / name).exists():
            info["files"].add(name)
    pkg = load_json(root / "package.json")
    if pkg:
        info["langs"].append("node")
        info["deps"] |= {d.lower() for k in ("dependencies", "devDependencies") for d in (pkg.get(k) or {})}
        info["scripts"] = [s for s in (pkg.get("scripts") or {}) if s in ("dev", "build", "test", "lint", "typecheck", "check", "format", "start", "e2e")]
        for lock, pm in (("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("bun.lockb", "bun"), ("bun.lock", "bun"), ("package-lock.json", "npm")):
            if (root / lock).exists():
                info["pm"] = pm
                break
        info["pm"] = info["pm"] or "npm"
    if {"pyproject.toml", "requirements.txt"} & info["files"]:
        info["langs"].append("python")
        text = " ".join((root / f).read_text(encoding="utf-8", errors="ignore").lower() for f in ("pyproject.toml", "requirements.txt") if (root / f).exists())
        info["deps"] |= set(re.findall(r"[a-z][a-z0-9_-]+", text))
    if "Cargo.toml" in info["files"]:
        info["langs"].append("rust")
    if "go.mod" in info["files"]:
        info["langs"].append("go")
    return info


def installed(root: Path) -> tuple:
    servers, plugins = set(), set()
    home = Path.home()
    user = load_json(home / ".claude.json")
    servers |= set((user.get("mcpServers") or {}))
    servers |= set(((user.get("projects") or {}).get(str(root.resolve())) or {}).get("mcpServers") or {})
    servers |= set((load_json(root / ".mcp.json").get("mcpServers") or {}))
    for settings in (home / ".claude/settings.json", root / ".claude/settings.json", root / ".claude/settings.local.json"):
        data = load_json(settings)
        plugins |= {k for k, v in (data.get("enabledPlugins") or {}).items() if v}
    return {s.lower() for s in servers}, plugins


def suggested_rules(info: dict) -> dict:
    allow = [f"Bash({c}:*)" for c in SAFE_BASH]
    pm = info["pm"]
    if pm:
        run = {"npm": "npm run", "pnpm": "pnpm", "yarn": "yarn", "bun": "bun run"}[pm]
        allow += [f"Bash({run} {s}:*)" for s in info["scripts"] if s not in ("dev", "start")]
        allow.append(f"Bash({'npx' if pm != 'bun' else 'bunx'} tsc:*)")
    if "python" in info["langs"]:
        allow += ["Bash(python3 -m pytest:*)", "Bash(pytest:*)", "Bash(ruff check:*)"]
    if "rust" in info["langs"]:
        allow += ["Bash(cargo check:*)", "Bash(cargo test:*)", "Bash(cargo clippy:*)"]
    if "go" in info["langs"]:
        allow += ["Bash(go build:*)", "Bash(go test:*)", "Bash(go vet:*)"]
    return {"allow": allow, "deny": DENY}


def write_rules(root: Path, rules: dict) -> int:
    path = root / ".claude" / "settings.json"
    data = load_json(path) if path.exists() else {}
    if path.exists() and not data and path.read_text(encoding="utf-8").strip():
        print(f"{path} is not valid JSON; not touching it")
        return 1
    perms = data.setdefault("permissions", {})
    added = 0
    for key in ("allow", "deny"):
        current = perms.setdefault(key, [])
        for rule in rules[key]:
            if rule not in current and not (key == "allow" and rule in perms.get("deny", [])):
                current.append(rule)
                added += 1
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"{path.relative_to(root)}: {added} rules added")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--write", action="store_true", help="merge suggested permissions into .claude/settings.json")
    args = ap.parse_args()
    root = Path(args.path).resolve()
    info = detect(root)
    servers, plugins = installed(root)
    rules = suggested_rules(info)
    if args.write:
        return write_rules(root, rules)

    signals = info["deps"] | {f.lower() for f in info["files"]}
    print(f"# Toolbelt: {root.name}")
    print(f"stack: {', '.join(info['langs']) or 'unknown'}" + (f" · {info['pm']}" if info["pm"] else "")
          + (f" · scripts: {', '.join(info['scripts'])}" if info["scripts"] else ""))
    print(f"mcp installed: {', '.join(sorted(servers)) or 'none found'}")
    print(f"plugins enabled: {', '.join(sorted(plugins)) or 'none found'}")
    print("\n## Add (only what this project would use)")
    missing = 0
    for name, (why, cmd, keys) in MCP.items():
        if any(name in s for s in servers):
            continue
        if keys and not any(any(k == s or s.startswith(k) or k in s for s in signals) for k in keys):
            continue
        print(f"- {name}: {why}\n  {cmd}")
        missing += 1
    if not missing:
        print("- nothing missing for this stack")
    print("\n## Permissions (run with --write to merge into .claude/settings.json)")
    print("allow: " + ", ".join(rules["allow"]))
    print("deny:  " + ", ".join(rules["deny"]))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # reader closed early (e.g. `| head`, `grep -q`)
        sys.exit(0)
