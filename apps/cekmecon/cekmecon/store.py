"""The vault: Markdown files on disk plus a SQLite full-text index (FTS5, BM25 ranking).

Files are the source of truth; the index is a cache rebuilt from mtimes, so editing notes in
Obsidian, VS Code or the Çekmecón window is always safe.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import re
import sqlite3
import threading
from pathlib import Path

from . import paths

FOLDERS = ("Inbox", "Projects", "Knowledge", "Archive")
SKIP_DIRS = {".obsidian", ".trash", ".git", "node_modules", ".cekmecon"}
WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
TAG = re.compile(r"(?<![\w/#])#([A-Za-z][\w/-]{1,40})")
FRONT = re.compile(r"^---\n(.*?)\n---\n?", re.S)

PROFILE_TEMPLATE = """---
kind: profile
---
# Profile

What Claude should always know about you. Keep it short; no secrets.

- Languages I reply in: TODO
- Main stack: TODO
- How I like answers: result first, short, with evidence
- Never do without asking: deploy, push to main, delete data, spend money
"""

WELCOME = """---
kind: guide
tags: [cekmecon]
---
# Welcome to Çekmecón

This drawer is your memory and Claude's. Everything is plain Markdown, so it also opens in Obsidian.

- **Inbox/**: quick notes. Press *Organize* (or let Claude) and they move to the right drawer.
- **Projects/<name>/**: one drawer per project, created the first time Claude works in it:
  `README.md` (brief), `Map.md` (auto: stack, commands, layout), `Decisions.md`, `Lessons.md`, `Tasks.md`, `Log.md`.
- **Knowledge/**: things that are true across projects.
- **Archive/**: nothing is ever deleted, only archived.

Link notes with [[Note title]] and tag with #tags. Ctrl+K searches everything.
"""


def now() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M")


def today() -> str:
    return dt.date.today().isoformat()


def slug(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text, flags=re.U).strip()
    s = re.sub(r"\s+", " ", s)
    return s[:80] or "Untitled"


def parse_front(text: str) -> tuple:
    """(meta dict, body). Tiny YAML subset: key: value and key: [a, b]."""
    m = FRONT.match(text)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" not in line or line.startswith((" ", "-")):
            continue
        k, _, v = line.partition(":")
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            meta[k.strip()] = [x.strip().strip("\"'") for x in v[1:-1].split(",") if x.strip()]
        else:
            meta[k.strip()] = v.strip("\"'")
    return meta, text[m.end():]


def render_front(meta: dict) -> str:
    if not meta:
        return ""
    lines = []
    for k, v in meta.items():
        lines.append(f"{k}: [{', '.join(v)}]" if isinstance(v, list) else f"{k}: {v}")
    return "---\n" + "\n".join(lines) + "\n---\n"


def title_of(path: Path, meta: dict, body: str) -> str:
    if meta.get("title"):
        return str(meta["title"])
    m = re.search(r"^# (.+)$", body, re.M)
    return m.group(1).strip() if m else path.stem


class Vault:
    def __init__(self, root: Path | None = None, index_path: Path | None = None):
        self.root = (root or paths.vault_dir()).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha1(str(self.root).encode()).hexdigest()[:10]
        self.index_path = index_path or (paths.state_dir() / f"index-{key}.sqlite")
        self.lock = threading.RLock()
        self.db = sqlite3.connect(str(self.index_path), check_same_thread=False)
        self.fts = self._init_db()
        self.ensure_layout()
        self.reindex()

    # ---------- setup ----------
    def _init_db(self) -> bool:
        c = self.db
        c.execute("create table if not exists notes(path text primary key, title text, mtime real, tags text, project text, kind text, size int)")
        c.execute("create table if not exists links(src text, dst text)")
        c.execute("create index if not exists links_dst on links(dst)")
        try:
            c.execute("create virtual table if not exists fts using fts5(path unindexed, title, body, tags, tokenize='unicode61 remove_diacritics 2')")
            ok = True
        except sqlite3.OperationalError:  # SQLite built without FTS5: fall back to LIKE search
            c.execute("create table if not exists fts(path text, title text, body text, tags text)")
            ok = False
        c.commit()
        return ok

    def ensure_layout(self) -> None:
        for f in FOLDERS:
            (self.root / f).mkdir(exist_ok=True)
        if not (self.root / "Profile.md").exists():
            (self.root / "Profile.md").write_text(PROFILE_TEMPLATE, encoding="utf-8")
        if not (self.root / "Welcome.md").exists():
            (self.root / "Welcome.md").write_text(WELCOME, encoding="utf-8")

    # ---------- paths ----------
    def safe(self, rel: str) -> Path:
        rel = (rel or "").replace("\\", "/").lstrip("/")
        p = (self.root / rel).resolve()
        if p != self.root and self.root not in p.parents:
            raise ValueError("path escapes the vault")
        if any(part in SKIP_DIRS for part in p.relative_to(self.root).parts):
            raise ValueError("path is in a protected folder")
        return p

    def rel(self, p: Path) -> str:
        return p.resolve().relative_to(self.root).as_posix()

    def files(self):
        for p in self.root.rglob("*.md"):
            if not any(part in SKIP_DIRS for part in p.relative_to(self.root).parts):
                yield p

    # ---------- index ----------
    def reindex(self) -> int:
        """Incremental: re-reads only files whose mtime changed. Returns the number re-indexed."""
        with self.lock:
            known = {r[0]: r[1] for r in self.db.execute("select path, mtime from notes")}
            seen, changed = set(), 0
            for p in self.files():
                r = self.rel(p)
                seen.add(r)
                m = p.stat().st_mtime
                if known.get(r) != m:
                    self._index_file(p, r, m)
                    changed += 1
            for gone in set(known) - seen:
                self._drop(gone)
                changed += 1
            self.db.commit()
            return changed

    def _drop(self, r: str) -> None:
        self.db.execute("delete from notes where path=?", (r,))
        self.db.execute("delete from fts where path=?", (r,))
        self.db.execute("delete from links where src=?", (r,))

    def _index_file(self, p: Path, r: str, mtime: float) -> None:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return
        meta, body = parse_front(text)
        tags = set(meta.get("tags") or []) if isinstance(meta.get("tags"), list) else set(filter(None, [meta.get("tags")]))
        tags |= set(TAG.findall(body))
        title = title_of(p, meta, body)
        project = meta.get("project") or (p.relative_to(self.root).parts[1] if r.startswith("Projects/") and len(p.relative_to(self.root).parts) > 2 else "")
        self._drop(r)
        self.db.execute("insert into notes values(?,?,?,?,?,?,?)", (r, title, mtime, " ".join(sorted(tags)), project, meta.get("kind", ""), len(text)))
        self.db.execute("insert into fts(path, title, body, tags) values(?,?,?,?)", (r, title, body, " ".join(sorted(tags))))
        for dst in set(WIKILINK.findall(body)):
            self.db.execute("insert into links values(?,?)", (r, dst.strip()))

    def touch_index(self, p: Path) -> None:
        with self.lock:
            self._index_file(p, self.rel(p), p.stat().st_mtime)
            self.db.commit()

    # ---------- reading ----------
    def tree(self) -> list:
        with self.lock:
            rows = self.db.execute("select path, title, mtime, tags, project, kind, size from notes order by path").fetchall()
        return [dict(zip(("path", "title", "mtime", "tags", "project", "kind", "size"), r)) for r in rows]

    def folders(self) -> list:
        out = []
        for p in sorted(self.root.rglob("*")):
            if p.is_dir() and not any(part in SKIP_DIRS or part.startswith(".") for part in p.relative_to(self.root).parts):
                out.append(self.rel(p))
        return out

    def read(self, rel: str, start: int = 0, end: int = 0) -> str:
        text = self.safe(rel).read_text(encoding="utf-8", errors="replace")
        if start or end:
            lines = text.splitlines()
            text = "\n".join(lines[max(start - 1, 0): end or None])
        return text

    def resolve_title(self, title: str) -> str:
        with self.lock:
            row = self.db.execute("select path from notes where lower(title)=lower(?) or lower(path) like lower(?) limit 1",
                                  (title, f"%/{title}.md")).fetchone()
        return row[0] if row else ""

    def backlinks(self, rel: str) -> list:
        with self.lock:
            row = self.db.execute("select title from notes where path=?", (rel,)).fetchone()
            if not row:
                return []
            names = {row[0].lower(), Path(rel).stem.lower()}
            out = [s for s, d in self.db.execute("select src, dst from links") if d.lower() in names and s != rel]
        return sorted(set(out))

    def graph(self) -> dict:
        with self.lock:
            notes = self.db.execute("select path, title, project, kind, mtime, size, tags from notes").fetchall()
            links = self.db.execute("select src, dst from links").fetchall()
        by_name = {}
        for p, t, *_ in notes:
            by_name[t.lower()] = p
            by_name[Path(p).stem.lower()] = p
        edges = [(s, by_name[d.lower()]) for s, d in links if d.lower() in by_name and by_name[d.lower()] != s]
        nodes = [{"id": p, "title": t, "project": pr, "kind": k, "folder": p.split("/")[0] if "/" in p else "",
                  "mtime": round(m or 0), "size": sz or 0, "tags": tg or ""} for p, t, pr, k, m, sz, tg in notes]
        return {"nodes": nodes, "edges": [{"source": s, "target": t} for s, t in sorted(set(edges))]}

    def search(self, q: str, limit: int = 10, project: str = "") -> list:
        q = (q or "").strip()
        if not q:
            return []
        with self.lock:
            if self.fts:
                terms = [t for t in re.findall(r"[\w-]+", q, re.U) if len(t) > 1]
                if not terms:
                    return []
                match = " OR ".join(f'"{t}"*' for t in terms)
                sql = ("select f.path, f.title, snippet(fts, 2, '«', '»', ' … ', 14), bm25(fts, 0, 8.0, 1.0, 4.0) as rank, n.project "
                       "from fts f join notes n on n.path=f.path where fts match ? ")
                args = [match]
                if project:
                    sql += "and (n.project=? or n.path not like 'Projects/%') "
                    args.append(project)
                sql += "order by rank limit ?"
                args.append(limit)
                try:
                    rows = self.db.execute(sql, args).fetchall()
                except sqlite3.OperationalError:
                    rows = []
            else:
                like = f"%{q}%"
                rows = [(p, t, (b or "")[:160], 0, "") for p, t, b in self.db.execute(
                    "select path, title, body from fts where body like ? or title like ? limit ?", (like, like, limit))]
        return [{"path": r[0], "title": r[1], "snippet": " ".join((r[2] or "").split()), "project": r[4]} for r in rows]

    def stats(self) -> dict:
        with self.lock:
            n, size = self.db.execute("select count(*), coalesce(sum(size),0) from notes").fetchone()
            links = self.db.execute("select count(*) from links").fetchone()[0]
            projects = [r[0] for r in self.db.execute("select distinct project from notes where project!='' order by project")]
        return {"notes": n, "bytes": size, "links": links, "projects": projects, "fts": self.fts, "vault": str(self.root)}

    # ---------- writing ----------
    def write(self, rel: str, content: str) -> str:
        p = self.safe(rel)
        if p.suffix != ".md":
            raise ValueError("only .md notes can be written")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        self.touch_index(p)
        return self.rel(p)

    def append(self, rel: str, text: str, header: str = "") -> str:
        p = self.safe(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        existing = p.read_text(encoding="utf-8") if p.exists() else (header or f"# {p.stem}\n")
        if not existing.endswith("\n"):
            existing += "\n"
        p.write_text(existing + text.rstrip() + "\n", encoding="utf-8")
        self.touch_index(p)
        return self.rel(p)

    def new_note(self, title: str, body: str = "", folder: str = "Inbox", meta: dict | None = None) -> str:
        base = self.safe(folder) / f"{slug(title)}.md"
        p, i = base, 2
        while p.exists():
            p = base.with_name(f"{base.stem} {i}.md")
            i += 1
        meta = dict(meta or {})
        meta.setdefault("created", now())
        content = render_front(meta) + f"# {title}\n\n{body.strip()}\n"
        return self.write(self.rel(p), content)

    def daily(self, day: str = "") -> str:
        """Today's note (Inbox/Diario/YYYY-MM-DD.md), created on first use. Returns its path."""
        day = day or today()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
            raise ValueError("day must be YYYY-MM-DD")
        rel = f"Inbox/Diario/{day}.md"
        if not self.safe(rel).exists():
            self.write(rel, render_front({"kind": "daily", "created": now()}) + f"# {day}\n\n## Notas\n\n- \n\n## Tareas\n\n- [ ] \n")
        return rel

    def move(self, rel: str, dest_folder: str) -> str:
        src = self.safe(rel)
        dst_dir = self.safe(dest_folder)
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst, i = dst_dir / src.name, 2
        while dst.exists() and dst != src:
            dst = dst_dir / f"{src.stem} {i}{src.suffix}"
            i += 1
        src.rename(dst)
        with self.lock:
            self._drop(rel)
            self.db.commit()
        self.touch_index(dst)
        return self.rel(dst)

    def archive(self, rel: str) -> str:
        return self.move(rel, "Archive")
