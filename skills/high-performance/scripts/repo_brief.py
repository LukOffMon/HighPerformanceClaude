#!/usr/bin/env python3
"""repo_brief.py — one-call orientation for an unfamiliar repository.

Prints a compact brief (≈40–90 lines): stack, layout, commands, agent docs, CI,
entry points, large files to avoid reading whole, and git state. Replaces dozens
of exploratory tool calls. Read-only; standard library only.

Usage: python3 repo_brief.py [path] [--depth 2] [--max-dirs 25]
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.dont_write_bytecode = True  # keep the skill directory clean
sys.path.insert(0, str(Path(__file__).resolve().parent))
import hpc_detect as d  # noqa: E402

AGENT_DOCS = [
    "CLAUDE.md", ".claude/CLAUDE.md", "AGENTS.md", "GEMINI.md", ".cursorrules", ".cursor/rules",
    ".github/copilot-instructions.md", "CONTRIBUTING.md", "docs/CONTRIBUTING.md", ".windsurfrules",
]

MANIFESTS = [
    "package.json", "pnpm-workspace.yaml", "turbo.json", "nx.json", "lerna.json", "deno.json",
    "pyproject.toml", "requirements.txt", "setup.py", "Pipfile", "manage.py", "go.mod", "Cargo.toml",
    "Gemfile", "composer.json", "pom.xml", "build.gradle", "build.gradle.kts", "Package.swift",
    "pubspec.yaml", "mix.exs", "Makefile", "justfile", "Dockerfile", "docker-compose.yml",
    "compose.yaml", "vercel.json", "netlify.toml", "fly.toml", "wrangler.toml", "app.json",
    "default.project.json", "aftman.toml", "rokit.toml", "wally.toml",
]

ENTRY_CANDIDATES = [
    "src/main.ts", "src/main.tsx", "src/index.ts", "src/index.tsx", "src/main.js", "src/index.js",
    "src/App.tsx", "src/App.jsx", "app/page.tsx", "app/layout.tsx", "src/app/page.tsx",
    "src/app/layout.tsx", "pages/index.tsx", "pages/_app.tsx", "index.html", "server.ts",
    "server.js", "index.js", "main.py", "app.py", "manage.py", "app/main.py", "src/main.py",
    "main.go", "src/main.rs", "src/lib.rs", "lib/main.dart", "Program.cs", "bin/rails",
]

LARGE_BYTES = 150_000


def human(n: int) -> str:
    for unit in ("B", "KB", "MB"):
        if n < 1024:
            return f"{n:.0f}{unit}"
        n /= 1024  # type: ignore[assignment]
    return f"{n:.1f}GB"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--depth", type=int, default=2, help="directory depth for the layout section")
    ap.add_argument("--max-dirs", type=int, default=25)
    args = ap.parse_args()

    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    files = d.list_files(root)
    out: list[str] = [f"# Repo brief: {root.name}  ({root})"]

    # ---- languages
    lang_files: Counter = Counter()
    lang_lines: Counter = Counter()
    large: list[tuple[int, str]] = []
    counted = 0
    for rel in files:
        ext = rel.suffix.lower()
        full = root / rel
        try:
            size = full.stat().st_size
        except OSError:
            continue
        if ext in d.BINARY_EXT:
            continue
        lang = d.LANG_BY_EXT.get(ext)
        name = rel.name.lower()
        if size > LARGE_BYTES:
            large.append((size, str(rel)))
        if lang:
            lang_files[lang] += 1
            if counted < 20000 and size <= 1_000_000 and not any(h in name for h in d.GENERATED_HINTS):
                try:
                    with open(full, "rb") as fh:
                        lang_lines[lang] += sum(1 for _ in fh)
                    counted += 1
                except OSError:
                    pass
    out.append(f"Files: {len(files)}" + (" (git-tracked + untracked, ignores applied)" if d.is_git_repo(root) else ""))
    if lang_files:
        top = ", ".join(f"{lang} {lang_files[lang]}f/{lang_lines[lang]:,}L"
                        for lang, _ in lang_lines.most_common(8) or lang_files.most_common(8))
        out.append(f"Languages: {top}")

    # ---- stack
    stack: list[str] = []
    pkg = d.load_json(root / "package.json")
    if pkg:
        pm = d.js_package_manager(root)
        stack.append(f"JS package manager: {pm}")
        js = d.js_stack(pkg)
        if js:
            stack.append("JS stack: " + ", ".join(js))
        ws = pkg.get("workspaces")
        if ws or (root / "pnpm-workspace.yaml").exists():
            stack.append(f"Monorepo workspaces: {ws if ws else 'pnpm-workspace.yaml'}")
        engines = pkg.get("engines")
        if isinstance(engines, dict) and engines:
            stack.append("Engines: " + ", ".join(f"{k} {v}" for k, v in engines.items()))
    py_text = d.py_config_text(root)
    if py_text:
        py = d.py_stack(py_text)
        runner = d.py_runner(root).strip() or "python (no uv/poetry lock detected)"
        stack.append(f"Python runner: {runner}" + (f"; libs: {', '.join(py)}" if py else ""))
    for f, label in (("go.mod", "Go module"), ("Cargo.toml", "Rust crate"), ("Gemfile", "Ruby/Bundler"),
                     ("composer.json", "PHP/Composer"), ("pubspec.yaml", "Dart/Flutter"),
                     ("default.project.json", "Roblox (Rojo)")):
        if (root / f).exists():
            stack.append(label)
    for vf in (".nvmrc", ".node-version", ".python-version", ".tool-versions", "rust-toolchain.toml"):
        text = d.read_text(root / vf)
        if text:
            stack.append(f"{vf}: {text.strip().splitlines()[0][:60]}")
    if stack:
        out.append("\n## Stack")
        out.extend(f"- {s}" for s in stack)

    # ---- manifests & agent docs
    present = [m for m in MANIFESTS if (root / m).exists()]
    if present:
        out.append("\n## Manifests / config")
        out.append("- " + ", ".join(present))
    docs = [p for p in AGENT_DOCS if (root / p).exists()]
    nested_claude = sorted(str(r) for r in files if r.name in ("CLAUDE.md", "AGENTS.md") and len(r.parts) > 1
                           and str(r) not in docs)[:8]
    out.append("\n## Agent / contributor docs (read these first)")
    out.append("- " + (", ".join(docs + nested_claude) if docs or nested_claude else "none found"))
    envs = [str(r) for r in files if r.name.startswith(".env") and r.name != ".env"][:5]
    if envs:
        out.append(f"- Env templates: {', '.join(envs)}")

    # ---- commands
    out.append("\n## Commands")
    if pkg and isinstance(pkg.get("scripts"), dict) and pkg["scripts"]:
        scripts = pkg["scripts"]
        shown = list(scripts.items())[:18]
        for k, v in shown:
            out.append(f"- {d.js_run(d.js_package_manager(root), k)}  →  {str(v)[:90]}")
        if len(scripts) > len(shown):
            out.append(f"- … {len(scripts) - len(shown)} more scripts in package.json")
    targets = d.make_targets(root)
    if targets:
        out.append("- make: " + ", ".join(targets[:20]))
    recipes = d.just_recipes(root)
    if recipes:
        out.append("- just: " + ", ".join(recipes[:20]))
    checks = d.detect_checks(root)
    if checks:
        out.append("- Verification ladder (scripts/checks.py --run):")
        out.extend(f"    {cat:<9} {cmd}   [{src}]" for cat, cmd, src in checks)
    elif not (pkg or targets or recipes):
        out.append("- none detected")

    # ---- CI
    ci = sorted(str(r) for r in files if str(r).startswith(".github/workflows/"))
    ci += [c for c in (".gitlab-ci.yml", ".circleci/config.yml", "azure-pipelines.yml", "bitbucket-pipelines.yml")
           if (root / c).exists()]
    if ci:
        out.append("\n## CI (shows what must pass)")
        out.append("- " + ", ".join(ci[:10]))

    # ---- layout
    out.append(f"\n## Layout (depth {args.depth}, file counts)")
    tree: Counter = Counter()
    for rel in files:
        parts = rel.parts[:-1]
        for depth in range(1, min(len(parts), args.depth) + 1):
            tree["/".join(parts[:depth])] += 1
    top_files = sorted(str(r) for r in files if len(r.parts) == 1)
    children = defaultdict(list)
    for path, count in tree.items():
        parent = path.rsplit("/", 1)[0] if "/" in path else ""
        children[parent].append((path, count))
    shown_dirs = 0

    def walk(parent: str, indent: int) -> None:
        nonlocal shown_dirs
        for path, count in sorted(children.get(parent, []), key=lambda x: (-x[1], x[0])):
            if shown_dirs >= args.max_dirs:
                return
            out.append(f"{'  ' * indent}- {path.rsplit('/', 1)[-1]}/  ({count})")
            shown_dirs += 1
            walk(path, indent + 1)

    walk("", 0)
    if top_files:
        out.append("- root files: " + ", ".join(top_files[:25]) + (" …" if len(top_files) > 25 else ""))

    # ---- entry points
    entries = [e for e in ENTRY_CANDIDATES if (root / e).exists()]
    entries += sorted(str(r) for r in files if len(r.parts) == 3 and r.parts[0] == "cmd" and r.name == "main.go")[:5]
    if entries:
        out.append("\n## Likely entry points")
        out.append("- " + ", ".join(entries[:12]))

    # ---- tests
    test_files = [r for r in files if any(t in r.name.lower() for t in ("test_", "_test.", ".test.", ".spec."))
                  or (len(r.parts) > 1 and r.parts[0] in ("tests", "test", "__tests__", "spec", "e2e"))]
    out.append(f"\n## Tests: {len(test_files)} files" + (f" (e.g. {test_files[0]})" if test_files else " — none found"))

    # ---- large files
    if large:
        large.sort(reverse=True)
        out.append("\n## Large text files (grep, don't read whole)")
        out.extend(f"- {p}  {human(s)}" for s, p in large[:8])

    # ---- git
    if d.is_git_repo(root):
        branch = (d.run(["git", "branch", "--show-current"], root) or "").strip() or "(detached)"
        status = (d.run(["git", "status", "--porcelain"], root) or "").splitlines()
        log = (d.run(["git", "log", "--oneline", "-5"], root) or "").strip().splitlines()
        out.append("\n## Git")
        out.append(f"- branch: {branch}; uncommitted changes: {len(status)}")
        if status:
            out.extend(f"    {s}" for s in status[:8])
            if len(status) > 8:
                out.append(f"    … {len(status) - 8} more")
        if log:
            out.append("- recent: " + " | ".join(line[:70] for line in log))

    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
