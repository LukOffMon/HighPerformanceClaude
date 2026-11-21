"""Automatic organization: project drawers, project maps, inbox sorting, lesson de-duplication,
and token-budgeted context packs (the part that saves Claude from re-reading everything)."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from .store import Vault, now, parse_front, render_front, slug, today

PROJECT_FILES = {
    "README.md": "# {name}\n\n## Goal\nTODO: one sentence on what this project is for.\n\n## Current focus\n- \n\n## Rules\n- \n",
    "Decisions.md": "# Decisions — {name}\n\nOne line each: date · decision · why.\n",
    "Lessons.md": "# Lessons — {name}\n\nThings that would have saved time. One line each.\n",
    "Tasks.md": "# Tasks — {name}\n\n",
    "Log.md": "# Log — {name}\n\n",
}
STACK_MARKERS = {
    "package.json": "Node.js", "pnpm-lock.yaml": "pnpm", "yarn.lock": "Yarn", "bun.lockb": "Bun",
    "tsconfig.json": "TypeScript", "next.config.js": "Next.js", "next.config.mjs": "Next.js", "next.config.ts": "Next.js",
    "vite.config.ts": "Vite", "vite.config.js": "Vite", "pyproject.toml": "Python", "requirements.txt": "Python",
    "Cargo.toml": "Rust", "go.mod": "Go", "pom.xml": "Java (Maven)", "build.gradle": "Gradle", "Gemfile": "Ruby",
    "composer.json": "PHP", "Dockerfile": "Docker", "docker-compose.yml": "Docker Compose", "pubspec.yaml": "Flutter",
    ".claude-plugin": "Claude Code plugin", "CLAUDE.md": "CLAUDE.md", "supabase": "Supabase", "prisma": "Prisma",
}
ES = {"decision": "decisión", "lesson": "lección", "task": "tarea", "log": "registro", "note": "nota"}
KINDS = {"decision": "Decisions.md", "lesson": "Lessons.md", "task": "Tasks.md", "log": "Log.md"}
SKIP_SCAN = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next", "target", ".idea", ".vscode"}


def est_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def project_name(root: Path) -> str:
    try:
        url = subprocess.run(["git", "-C", str(root), "remote", "get-url", "origin"], capture_output=True, text=True, timeout=3).stdout.strip()
        if url:
            return slug(re.sub(r"\.git$", "", url.rstrip("/").split("/")[-1].split(":")[-1]))
    except (OSError, subprocess.SubprocessError):
        pass
    return slug(root.name)


def scan_project(root: Path) -> dict:
    """Cheap, read-only look at a code folder: stack, commands, layout, README gist."""
    root = root.resolve()
    info = {"name": project_name(root), "path": str(root), "stack": [], "commands": [], "layout": [], "readme": ""}
    for marker, label in STACK_MARKERS.items():
        if (root / marker).exists() and label not in info["stack"]:
            info["stack"].append(label)
    pkg = root / "package.json"
    if pkg.exists():
        try:
            scripts = json.loads(pkg.read_text(encoding="utf-8")).get("scripts", {})
            runner = "pnpm" if (root / "pnpm-lock.yaml").exists() else "yarn" if (root / "yarn.lock").exists() else "npm run"
            info["commands"] += [f"{runner} {k}  →  {v}"[:120] for k, v in list(scripts.items())[:12]]
        except ValueError:
            pass
    mk = root / "Makefile"
    if mk.exists():
        targets = re.findall(r"^([A-Za-z][\w-]*):", mk.read_text(encoding="utf-8", errors="replace"), re.M)
        info["commands"] += [f"make {t}" for t in targets[:10]]
    try:
        entries = sorted(p for p in root.iterdir() if p.name not in SKIP_SCAN and not p.name.startswith("."))
    except OSError:
        entries = []
    for p in entries[:40]:
        if p.is_dir():
            n = sum(1 for _ in p.rglob("*") if _.is_file() and not any(s in SKIP_SCAN for s in _.parts))
            info["layout"].append(f"{p.name}/  ({min(n, 9999)} files)")
        else:
            info["layout"].append(p.name)
    for name in ("README.md", "readme.md", "README"):
        r = root / name
        if r.exists():
            paras = [x.strip() for x in r.read_text(encoding="utf-8", errors="replace").split("\n\n") if x.strip() and not x.strip().startswith(("#", "!", "[!", "<", "```"))]
            info["readme"] = (paras[0] if paras else "")[:500]
            break
    return info


class Organizer:
    def __init__(self, vault: Vault, emit=lambda *a, **k: None):
        self.v = vault
        self.emit = emit

    # ---------- project drawers ----------
    def project_dir(self, name: str) -> str:
        return f"Projects/{slug(name)}"

    def ensure_project(self, name: str) -> tuple:
        d = self.project_dir(name)
        created = []
        for fname, tpl in PROJECT_FILES.items():
            rel = f"{d}/{fname}"
            if not self.v.safe(rel).exists():
                meta = {"project": slug(name), "kind": fname[:-3].lower(), "created": now()}
                self.v.write(rel, render_front(meta) + tpl.format(name=name))
                created.append(rel)
        return d, created

    def open_project(self, path: str) -> dict:
        root = Path(path).expanduser()
        if not root.is_dir():
            raise ValueError(f"not a folder: {path}")
        info = scan_project(root)
        d, created = self.ensure_project(info["name"])
        lines = [render_front({"project": info["name"], "kind": "map", "auto": "true", "updated": now()}).rstrip(),
                 f"# Map — {info['name']}", "", f"Folder: `{info['path']}`", "",
                 "Regenerated automatically each time Claude opens this project. Do not edit; write in README.md.", "",
                 "## Stack", *(f"- {s}" for s in info["stack"] or ["(not detected)"]), "",
                 "## Commands", *(f"- `{c}`" for c in info["commands"] or ["(none found)"]), "",
                 "## Layout", *(f"- {x}" for x in info["layout"])]
        if info["readme"]:
            lines += ["", "## From the README", info["readme"]]
        self.v.write(f"{d}/Map.md", "\n".join(lines) + "\n")
        readme = self.v.safe(f"{d}/README.md")
        if created and info["readme"] and "TODO: one sentence" in readme.read_text(encoding="utf-8"):
            self.v.write(f"{d}/README.md", readme.read_text(encoding="utf-8").replace("TODO: one sentence on what this project is for.", info["readme"].split("\n")[0][:300]))
        self.v.append(f"{d}/Log.md", f"- {now()} · Claude opened the project")
        self.emit("project", f"Cajón listo para {info['name']}" + (f" ({len(created)} notas nuevas)" if created else ""), mood="celebrate" if created else "work")
        return {"project": info["name"], "drawer": d, "created": created, "scan": info}

    # ---------- remembering ----------
    def remember(self, kind: str, text: str, project: str = "", title: str = "") -> str:
        kind = (kind or "note").lower()
        text = " ".join(text.split()) if kind in KINDS else text.strip()
        if not text:
            raise ValueError("empty text")
        if kind in KINDS and project:
            d, _ = self.ensure_project(project)
            rel = f"{d}/{KINDS[kind]}"
            if kind == "lesson" and self._has_line(rel, text):
                self.emit("dedupe", "Esa lección ya la sabía; no la dupliqué", mood="idle")
                return rel
            line = {"task": f"- [ ] {text}", "decision": f"- {today()} · {text}", "lesson": f"- {text}", "log": f"- {now()} · {text}"}[kind]
            out = self.v.append(rel, line)
        elif kind in KINDS:
            out = self.v.append(f"Knowledge/{KINDS[kind]}", f"- {today()} · {text}" if kind != "task" else f"- [ ] {text}")
        else:
            folder = self.project_dir(project) if project else "Inbox"
            if project:
                self.ensure_project(project)
            out = self.v.new_note(title or text.split("\n")[0][:60], text, folder, {"auto": "true", "project": slug(project)} if project else {"auto": "true"})
        self.emit("remember", f"Guardé {ES.get(kind, kind)}: {text[:70]}", mood="celebrate")
        return out

    def _has_line(self, rel: str, text: str) -> bool:
        p = self.v.safe(rel)
        if not p.exists():
            return False
        norm = lambda s: re.sub(r"\W+", " ", s.lower()).strip()
        target = norm(text)
        return any(norm(l.lstrip("-* ").split(" · ")[-1]) == target for l in p.read_text(encoding="utf-8").splitlines())

    # ---------- inbox ----------
    def organize(self) -> dict:
        """Sort Inbox notes into project drawers or Knowledge, link related notes Claude wrote, de-dupe lessons."""
        self.v.reindex()
        moved, linked, deduped = [], 0, 0
        projects = {p.name.lower(): p.name for p in (self.v.root / "Projects").iterdir() if p.is_dir()}
        for p in sorted((self.v.root / "Inbox").glob("*.md")):
            text = p.read_text(encoding="utf-8", errors="replace")
            meta, body = parse_front(text)
            target = ""
            if meta.get("project") and meta["project"].lower() in projects:
                target = f"Projects/{projects[meta['project'].lower()]}"
            else:
                low = body.lower()
                hits = [(low.count(k), v) for k, v in projects.items() if len(k) > 2 and k in low]
                if hits:
                    target = f"Projects/{max(hits)[1]}"
                elif meta.get("tags") or "#" in body or len(body) > 400:
                    target = "Knowledge"
            if target:
                moved.append(f"{p.name} → {target}")
                self.v.move(self.v.rel(p), target)
        # related links for notes Claude wrote (auto: true); never touches your hand-written notes
        notes = self.v.tree()
        titles = {n["title"]: n["path"] for n in notes if len(n["title"]) >= 5 and n["kind"] not in ("profile", "guide")}
        for n in notes:
            p = self.v.safe(n["path"])
            text = p.read_text(encoding="utf-8", errors="replace")
            meta, body = parse_front(text)
            if meta.get("auto") != "true" or meta.get("kind") == "map":
                continue
            body_wo = re.sub(r"\n## Related\n.*", "", body, flags=re.S)
            rel = sorted(t for t, path in titles.items() if path != n["path"] and re.search(rf"(?<!\[)\b{re.escape(t)}\b", body_wo, re.I))
            if rel:
                new = render_front(meta) + body_wo.rstrip() + "\n\n## Related\n" + "\n".join(f"- [[{t}]]" for t in rel[:8]) + "\n"
                if new != text:
                    self.v.write(n["path"], new)
                    linked += 1
        for lessons in self.v.root.glob("Projects/*/Lessons.md"):
            lines = lessons.read_text(encoding="utf-8").splitlines()
            seen, out = set(), []
            for l in lines:
                k = re.sub(r"\W+", " ", l.lower()).strip()
                if l.startswith("- ") and k in seen:
                    deduped += 1
                    continue
                seen.add(k)
                out.append(l)
            if len(out) != len(lines):
                self.v.write(self.v.rel(lessons), "\n".join(out) + "\n")
        self.v.reindex()
        summary = {"moved": moved, "linked": linked, "deduped": deduped}
        self.emit("organize", f"Ordené: {len(moved)} movidas, {linked} enlazadas, {deduped} duplicados fuera", mood="celebrate")
        return summary

    # ---------- context pack ----------
    def context(self, project: str = "", query: str = "", budget: int = 1500) -> dict:
        """The smallest useful memory for a task, capped at `budget` tokens, most important first."""
        self.v.reindex()
        parts, sources, used = [], [], 0

        def add(label: str, rel: str, text: str, cap: int) -> None:
            nonlocal used
            text = text.strip()
            if not text:
                return
            room = min(cap, budget - used)
            if room < 40:
                return
            if est_tokens(text) > room:
                text = text[: room * 4].rsplit("\n", 1)[0] + "\n…(truncated; read the note for more)"
            parts.append(f"## {label}  ({rel})\n{text}")
            sources.append(rel)
            used += est_tokens(text) + 8

        def body(rel: str) -> str:
            try:
                return parse_front(self.v.read(rel))[1]
            except (OSError, ValueError):
                return ""

        add("Profile", "Profile.md", body("Profile.md"), 250)
        if project:
            d = self.project_dir(project)
            add("Project brief", f"{d}/README.md", body(f"{d}/README.md"), 350)
            add("Map", f"{d}/Map.md", body(f"{d}/Map.md"), 300)
            open_tasks = "\n".join(l for l in body(f"{d}/Tasks.md").splitlines() if l.startswith("- [ ]"))
            add("Open tasks", f"{d}/Tasks.md", open_tasks, 200)
            add("Recent decisions", f"{d}/Decisions.md", "\n".join([l for l in body(f"{d}/Decisions.md").splitlines() if l.startswith("- ")][-8:]), 200)
            add("Lessons", f"{d}/Lessons.md", "\n".join([l for l in body(f"{d}/Lessons.md").splitlines() if l.startswith("- ")][-12:]), 250)
        if query:
            for hit in self.v.search(query, limit=5, project=slug(project) if project else ""):
                if hit["path"] not in sources:
                    add(f"Match: {hit['title']}", hit["path"], hit["snippet"], 120)
        self.emit("context", f"Le pasé a Claude {used} tokens de memoria en vez de releer todo", mood="work")
        return {"text": "\n\n".join(parts) or "(memory is empty so far)", "tokens": used, "budget": budget, "sources": sources}
