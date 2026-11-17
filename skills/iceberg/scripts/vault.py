#!/usr/bin/env python3
"""Obsidian bridge for Iceberg: recall past briefs and lessons, save new ones. Standard library only.

Vault lookup order: --vault PATH, $OBSIDIAN_VAULT, then Obsidian's own vault list
(obsidian.json; the open vault first, else the most recently used).

  vault.py init                           create the Claude/ workspace in the vault (idempotent)
  vault.py where                          print the vault path (exit 3 if none)
  vault.py context [project]              Profile + project note + recent lessons, capped (start of a task)
  vault.py recall "auth login google"     top matching notes, a few matching lines each
  vault.py save --title "Google login" --project my-app --tags auth,nextjs < brief.md
  vault.py lesson "pnpm, not npm, in my-app" --project my-app
  vault.py project my-app < notes.md      create or append to Claude/Projects/my-app.md
  vault.py list                           list the vaults Obsidian knows about

Everything lives under <vault>/Claude/ (override with --root). Existing notes are never overwritten;
the only file outside that folder that is ever written is .obsidian/templates.json, and only if absent.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

NO_VAULT = 3
SKIP_DIRS = {".obsidian", ".trash", ".git", "node_modules"}


def config_paths() -> list:
    home = Path.home()
    paths = [
        home / "Library/Application Support/obsidian/obsidian.json",
        home / ".config/obsidian/obsidian.json",
        home / ".var/app/md.obsidian.Obsidian/config/obsidian/obsidian.json",
        home / "snap/obsidian/current/.config/obsidian/obsidian.json",
    ]
    if os.environ.get("APPDATA"):
        paths.insert(0, Path(os.environ["APPDATA"]) / "obsidian/obsidian.json")
    return paths


def known_vaults() -> list:
    """[(path, is_open, last_ts)] from Obsidian's config, existing folders only."""
    found = []
    for cfg in config_paths():
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for v in (data.get("vaults") or {}).values():
            p = Path(v.get("path", ""))
            if p.is_dir():
                found.append((p, bool(v.get("open")), int(v.get("ts") or 0)))
    return sorted(found, key=lambda x: (x[1], x[2]), reverse=True)


def find_vault(explicit: str = "") -> Path:
    for cand in (explicit, os.environ.get("OBSIDIAN_VAULT", "")):
        if cand:
            p = Path(cand).expanduser()
            if p.is_dir():
                return p
            sys.exit(f"vault not found: {p}")
    vaults = known_vaults()
    if not vaults:
        print("no Obsidian vault found: set OBSIDIAN_VAULT=/path/to/vault or pass --vault", file=sys.stderr)
        sys.exit(NO_VAULT)
    return vaults[0][0]


def notes(vault: Path):
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if name.endswith(".md"):
                yield Path(root) / name


def recall(vault: Path, query: str, limit: int, lines: int) -> int:
    terms = [t for t in re.findall(r"\w+", query.lower()) if len(t) > 2]
    if not terms:
        print("recall needs at least one word longer than 2 letters")
        return 2
    scored = []
    for path in notes(vault):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        low = text.lower()
        hits = {t: low.count(t) for t in terms}
        matched = sum(1 for c in hits.values() if c)
        if not matched:
            continue
        title_bonus = sum(3 for t in terms if t in path.stem.lower())
        iceberg_bonus = 2 if "type: iceberg" in low or "type: claude" in low else 0
        score = matched * 10 + min(sum(hits.values()), 20) + title_bonus + iceberg_bonus
        scored.append((score, path, text))
    if not scored:
        print(f"no notes match: {' '.join(terms)}")
        return 0
    scored.sort(key=lambda x: x[0], reverse=True)
    for score, path, text in scored[:limit]:
        print(f"## {path.relative_to(vault)}  (score {score})")
        shown = 0
        for line in text.splitlines():
            s = line.strip()
            if s and not s.startswith("---") and any(t in s.lower() for t in terms):
                print(f"  {s[:160]}")
                shown += 1
                if shown >= lines:
                    break
    if len(scored) > limit:
        print(f"... {len(scored) - limit} more notes match (raise --limit to see them)")
    return 0


def slug(title: str) -> str:
    clean = re.sub(r'[\\/:*?"<>|#^\[\]]+', " ", title).strip()
    return re.sub(r"\s+", " ", clean)[:80] or "note"


PROFILE = """---
type: claude-profile
---
# Profile

Claude reads this file at the start of every Iceberg task. Keep it under 40 lines: every line costs tokens on every task.

## Me
- Language: TODO (e.g. Spanish; code and identifiers in English)
- Role / level: TODO
- Main stack: TODO (e.g. Next.js 15, TypeScript, Supabase, Tailwind)
- Package manager / runtime: TODO

## How I like to work
- Answers: short, result first, no recap
- Ask me only when the answer changes what gets built
- Always: TODO (e.g. tests for bug fixes, mobile-first UI)
- Never: TODO (e.g. new dependencies without asking)

## Accounts and places (no secrets here)
- Repos: TODO
- Deploy targets: TODO
"""

README = """---
type: claude-readme
---
# Claude workspace

This folder is Claude's long-term memory for the Iceberg plugin. It is plain Markdown: read it, edit it, delete what is wrong.

| Note | What Claude does with it |
|---|---|
| [[Profile]] | Reads it first on every Iceberg task, so you never repeat your preferences |
| `Projects/` | One note per project: stack, commands, decisions, gotchas. Read only for the project at hand |
| `Briefs/` | Each ICEBERG BRIEF and its outcome, saved at the end of real tasks |
| [[Lessons]] | One line per mistake worth not repeating. Searched, never read whole |
| `Templates/` | Templates for your own notes (Obsidian core plugin Templates) |

## Why it saves tokens
- Claude never browses the vault. It runs `vault.py context` (capped) and `vault.py recall` (top matches, 3 lines each).
- Short, atomic notes with frontmatter are cheap to search and cheap to load.
- Lessons stop Claude from paying twice for the same mistake.

## Rules of thumb
- Keep [[Profile]] under 40 lines and project notes under 60.
- One idea per line in [[Lessons]].
- Never store secrets, tokens or passwords here.
"""

LESSONS = """---
type: claude-lessons
---
# Lessons

One line each, newest last: `YYYY-MM-DD · project · lesson`.

"""

TEMPLATES = {
    "Brief.md": "---\ntype: iceberg\ndate: {{date}}\nproject: \ntags: [iceberg]\n---\n# {{title}}\n\n```\nICEBERG BRIEF\nGoal:\nDeliver:\nAccept:  1)\nHidden:\nRisks:\nOptions:\nBudget:\nSlices:  1)\nOpen:    none\n```\n\n## Outcome\n- Delivered:\n- Verified:\n- Not verified:\n- Below the waterline:\n",
    "Project.md": "---\ntype: claude-project\nproject: {{title}}\n---\n# {{title}}\n\n## Stack\n- \n\n## Commands\n- run:\n- test:\n- build:\n\n## Decisions\n- {{date}} · \n\n## Gotchas\n- \n",
    "Lesson.md": "{{date}} · project · lesson\n",
}


def write_new(path: Path, text: str, made: list) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        made.append(path)


def init(vault: Path, root: str) -> int:
    base, made = vault / root, []
    for sub in ("Projects", "Briefs", "Templates"):
        (base / sub).mkdir(parents=True, exist_ok=True)
    write_new(base / "README.md", README, made)
    write_new(base / "Profile.md", PROFILE, made)
    write_new(base / "Lessons.md", LESSONS, made)
    write_new(base / "Briefs" / "Index.md", "# Briefs\n\nNewest last.\n\n", made)
    for name, text in TEMPLATES.items():
        write_new(base / "Templates" / name, text, made)
    tpl_cfg = vault / ".obsidian" / "templates.json"
    if (vault / ".obsidian").is_dir():
        write_new(tpl_cfg, json.dumps({"folder": f"{root}/Templates"}, indent=2) + "\n", made)
    for p in made:
        print(f"created {p.relative_to(vault)}")
    todo = (base / "Profile.md").read_text(encoding="utf-8").count("TODO")
    print(f"workspace ready at {base.relative_to(vault)}/ ({len(made)} new files)")
    if todo:
        print(f"next: fill the {todo} TODO lines in {root}/Profile.md")
    return 0


def capped(path: Path, max_lines: int) -> str:
    """Note body without frontmatter, placeholders, empty bullets, guidance or headings left empty."""
    raw = path.read_text(encoding="utf-8").splitlines()
    if raw and raw[0] == "---" and "---" in raw[1:]:
        raw = raw[raw.index("---", 1) + 1:]
    kept = [l for l in raw if l.strip() and "TODO" not in l and l.strip() not in ("-", "- run:", "- test:", "- build:")
            and not re.fullmatch(r"- \d{4}-\d{2}-\d{2} · ", l) and not l.startswith(("Claude reads this", "One line each"))]
    lines = [l for i, l in enumerate(kept)
             if not (l.startswith("#") and (i + 1 == len(kept) or kept[i + 1].startswith("#")))]
    out = lines[:max_lines]
    if len(lines) > max_lines:
        out.append(f"... ({len(lines) - max_lines} more lines in {path.name})")
    return "\n".join(out)


def context(vault: Path, root: str, project: str, lessons: int) -> int:
    base = vault / root
    if not base.is_dir():
        print(f"no {root}/ workspace yet: run vault.py init")
        return NO_VAULT
    profile = base / "Profile.md"
    if profile.exists():
        print(capped(profile, 40))
    if project:
        note = base / "Projects" / f"{slug(project)}.md"
        print(f"\n# Project: {project}")
        print(capped(note, 60) if note.exists() else "(no project note yet)")
    lfile = base / "Lessons.md"
    if lfile.exists():
        rows = [l for l in lfile.read_text(encoding="utf-8").splitlines() if re.match(r"\d{4}-\d{2}-\d{2} ·", l)]
        if project:
            rows = [r for r in rows if f"· {project} ·" in r or "· all ·" in r] or rows
        if rows:
            print("\n# Lessons")
            print("\n".join(rows[-lessons:]))
    return 0


def save(vault: Path, root: str, title: str, project: str, tags: str, body: str) -> int:
    if not body.strip():
        print("save: empty note body on stdin")
        return 2
    target_dir = vault / root / "Briefs"
    target_dir.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    base = f"{today} {slug(title)}"
    path = target_dir / f"{base}.md"
    n = 2
    while path.exists():
        path = target_dir / f"{base} ({n}).md"
        n += 1
    tag_list = [t.strip().lstrip("#") for t in tags.split(",") if t.strip()]
    front = ["---", "type: iceberg", f"date: {today}"]
    if project:
        front.append(f"project: {project}")
    front.append("tags: [" + ", ".join(["iceberg"] + [t for t in tag_list if t != "iceberg"]) + "]")
    front.append("---")
    path.write_text("\n".join(front) + f"\n\n# {title}\n\n" + body.strip() + "\n", encoding="utf-8")
    index = target_dir / "Index.md"
    if not index.exists():
        index.write_text("# Briefs\n\nNewest last.\n\n", encoding="utf-8")
    with index.open("a", encoding="utf-8") as fh:
        fh.write(f"- [[{path.stem}]]" + (f" · {project}" if project else "") + "\n")
    print(f"saved {path.relative_to(vault)}")
    return 0


def lesson(vault: Path, root: str, text: str, project: str) -> int:
    text = " ".join(text.split())
    if not text:
        print("lesson: empty text")
        return 2
    path = vault / root / "Lessons.md"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(LESSONS, encoding="utf-8")
    existing = path.read_text(encoding="utf-8")
    if text.lower() in existing.lower():
        print("lesson already recorded")
        return 0
    line = f"{dt.date.today().isoformat()} · {project or 'all'} · {text[:200]}"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(f"added to {path.relative_to(vault)}")
    return 0


def project_note(vault: Path, root: str, name: str, body: str) -> int:
    path = vault / root / "Projects" / f"{slug(name)}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = body.strip()
    if not path.exists():
        tpl = TEMPLATES["Project.md"].replace("{{title}}", name).replace("{{date}}", dt.date.today().isoformat())
        path.write_text(tpl + ("\n" + body + "\n" if body else ""), encoding="utf-8")
        print(f"created {path.relative_to(vault)}")
    elif body:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(f"\n## {dt.date.today().isoformat()}\n{body}\n")
        print(f"appended to {path.relative_to(vault)}")
    else:
        print(f"exists {path.relative_to(vault)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", default="", help="vault folder (default: $OBSIDIAN_VAULT or Obsidian's own list)")
    ap.add_argument("--root", default="Claude", help="Claude's folder inside the vault (default: Claude)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    sub.add_parser("where")
    sub.add_parser("list")
    c = sub.add_parser("context")
    c.add_argument("project", nargs="?", default="")
    c.add_argument("--lessons", type=int, default=8)
    le = sub.add_parser("lesson")
    le.add_argument("text")
    le.add_argument("--project", default="")
    pr = sub.add_parser("project")
    pr.add_argument("name")
    r = sub.add_parser("recall")
    r.add_argument("query")
    r.add_argument("--limit", type=int, default=5)
    r.add_argument("--lines", type=int, default=3)
    s = sub.add_parser("save")
    s.add_argument("--title", required=True)
    s.add_argument("--project", default="")
    s.add_argument("--tags", default="")
    args = ap.parse_args()

    if args.cmd == "list":
        vaults = known_vaults()
        for p, is_open, _ in vaults:
            print(f"{'*' if is_open else ' '} {p}")
        return 0 if vaults else NO_VAULT
    vault = find_vault(args.vault)
    if args.cmd == "where":
        print(vault)
        return 0
    if args.cmd == "init":
        return init(vault, args.root)
    if args.cmd == "context":
        return context(vault, args.root, args.project, args.lessons)
    if args.cmd == "recall":
        return recall(vault, args.query, args.limit, args.lines)
    if args.cmd == "lesson":
        return lesson(vault, args.root, args.text, args.project)
    stdin = "" if sys.stdin.isatty() else sys.stdin.read()
    if args.cmd == "project":
        return project_note(vault, args.root, args.name, stdin)
    return save(vault, args.root, args.title, args.project, args.tags, stdin)


if __name__ == "__main__":
    sys.exit(main())
