"""Local app server: the Çekmecón window (HTML UI), its API, a live activity stream for the
assistant, and the Claude bridge protected by one-time pairing.

Security model (localhost app):
  * binds 127.0.0.1 only and rejects any Host header that is not 127.0.0.1/localhost:<port> (DNS rebinding)
  * UI calls need a per-process UI key embedded in the served page (other websites cannot read it)
  * Claude calls need a client token, issued only after you click Allow in the window;
    "Always" stores a hash of it in ~/.cekmecon/clients.json, "Just this session" keeps it in memory
"""
from __future__ import annotations

import collections
import hashlib
import json
import os
import queue
import secrets
import shutil
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import APP_NAME, DEFAULT_PORT, __version__, paths
from .organizer import Organizer
from .store import Vault

UI_DIR = Path(__file__).with_name("ui")
MIME = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
        ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon", ".json": "application/json"}


def h(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class App:
    def __init__(self, vault: Vault, port: int):
        self.vault, self.port = vault, port
        self.ui_key = secrets.token_urlsafe(24)
        self.instance = secrets.token_hex(8)
        self.events = collections.deque(maxlen=300)
        self.listeners: list = []
        self.lock = threading.Lock()
        self.pending: dict = {}          # request_id -> {client, cwd, host, created, status, token}
        self.session_tokens: set = set()  # hashes valid until the app quits
        self.clients_path = paths.state_dir() / "clients.json"
        self.org = Organizer(vault, self.emit)
        self.last_ui_seen = 0.0

    # ---------- activity ----------
    def emit(self, kind: str, text: str, mood: str = "idle", **extra) -> None:
        ev = {"id": secrets.token_hex(4), "t": time.time(), "kind": kind, "text": text, "mood": mood, **extra}
        with self.lock:
            self.events.append(ev)
            for q in list(self.listeners):
                q.put(ev)

    # ---------- clients ----------
    def clients(self) -> list:
        return paths.read_json(self.clients_path, [])

    def check_token(self, token: str) -> dict | None:
        if not token:
            return None
        th = h(token)
        if th in self.session_tokens:
            return {"name": "Claude (this session)"}
        clients = self.clients()
        for c in clients:
            if secrets.compare_digest(c.get("hash", ""), th):
                c["last_seen"] = time.strftime("%Y-%m-%d %H:%M")
                paths.write_json(self.clients_path, clients)
                return c
        return None

    def request_pair(self, client: str, cwd: str, host: str) -> str:
        with self.lock:
            live = [r for r in self.pending.values() if r["status"] == "pending"]
            if len(live) >= 5:
                raise ValueError("too many pending requests; answer them in the window first")
            rid = secrets.token_hex(6)
            self.pending[rid] = {"id": rid, "client": client[:60], "cwd": cwd[:300], "host": host[:80], "created": time.time(), "status": "pending"}
        self.emit("pair", f"{client[:40]} pide permiso para abrir tu cajón", mood="alert", request=self.pending[rid])
        if time.time() - self.last_ui_seen > 20:
            open_window(self.port)
        return rid

    def answer_pair(self, rid: str, allow: bool, always: bool) -> dict:
        with self.lock:
            r = self.pending.get(rid)
            if not r or r["status"] != "pending":
                raise ValueError("no such pending request")
            if not allow:
                r["status"] = "denied"
            else:
                token = secrets.token_urlsafe(32)
                r.update(status="approved", token=token, always=always)
                if always:
                    clients = self.clients()
                    clients.append({"id": rid, "name": r["client"], "cwd": r["cwd"], "host": r["host"], "hash": h(token),
                                    "created": time.strftime("%Y-%m-%d %H:%M"), "last_seen": ""})
                    paths.write_json(self.clients_path, clients)
                else:
                    self.session_tokens.add(h(token))
        self.emit("pair", f"{'Permitido' if allow else 'Rechazado'}: {r['client']}" + (" (siempre)" if allow and always else ""),
                  mood="celebrate" if allow else "idle")
        return {"status": r["status"]}

    def poll_pair(self, rid: str) -> dict:
        with self.lock:
            r = self.pending.get(rid)
            if not r:
                return {"status": "unknown"}
            out = {"status": r["status"]}
            if r["status"] == "approved" and r.get("token"):
                out["token"] = r.pop("token")  # handed over exactly once
                out["always"] = r.get("always", False)
            if r["status"] == "pending" and time.time() - r["created"] > 600:
                r["status"] = "expired"
                out["status"] = "expired"
            return out

    def revoke(self, cid: str) -> None:
        paths.write_json(self.clients_path, [c for c in self.clients() if c.get("id") != cid])
        self.emit("pair", "Conexión revocada", mood="idle")

    # ---------- Claude actions ----------
    def claude(self, action: str, a: dict, who: str) -> dict:
        v, org = self.vault, self.org
        label = who or "Claude"
        if action == "status":
            self.emit("claude", f"{label} se conectó", mood="wave")
            return {"app": APP_NAME, "version": __version__, **v.stats()}
        if action == "open_project":
            self.emit("claude", f"{label} está abriendo {Path(a.get('path', '')).name}", mood="work")
            res = org.open_project(a.get("path", ""))
            res["context"] = org.context(res["project"], a.get("query", ""), int(a.get("budget") or 1500))
            return res
        if action == "context":
            return org.context(a.get("project", ""), a.get("query", ""), int(a.get("budget") or 1500))
        if action == "search":
            self.emit("claude", f"{label} buscó “{a.get('query', '')[:40]}”", mood="think")
            return {"results": v.search(a.get("query", ""), int(a.get("limit") or 8), a.get("project", ""))}
        if action == "read":
            path = a.get("path") or v.resolve_title(a.get("title", ""))
            self.emit("claude", f"{label} está leyendo {path}", mood="read")
            return {"path": path, "text": v.read(path, int(a.get("start") or 0), int(a.get("end") or 0))}
        if action == "remember":
            return {"path": org.remember(a.get("kind", "note"), a.get("text", ""), a.get("project", ""), a.get("title", ""))}
        if action == "write":
            path = v.write(a.get("path", ""), a.get("content", ""))
            self.emit("claude", f"{label} escribió {path}", mood="write")
            return {"path": path}
        if action == "organize":
            self.emit("claude", f"{label} está ordenando los cajones", mood="work")
            return org.organize()
        if action == "tree":
            pr = a.get("project", "")
            return {"notes": [{"path": n["path"], "title": n["title"]} for n in v.tree() if not pr or n["project"] == pr][:300]}
        raise ValueError(f"unknown action {action}")


def find_app_browser() -> list:
    cands = []
    if sys.platform == "win32":
        for env in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            base = os.environ.get(env)
            if base:
                cands += [Path(base) / "Microsoft/Edge/Application/msedge.exe", Path(base) / "Google/Chrome/Application/chrome.exe"]
    elif sys.platform == "darwin":
        cands += [Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
                  Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
                  Path("/Applications/Brave Browser.app/Contents/MacOS/Brave Browser")]
    else:
        cands += [Path(p) for p in map(shutil.which, ("google-chrome", "chromium", "chromium-browser", "microsoft-edge", "brave-browser")) if p]
    return [str(c) for c in cands if c.exists()]


def open_window(port: int) -> None:
    """Open the app in its own chromeless window when a Chromium browser exists, else in the default browser."""
    if os.environ.get("CEKMECON_NO_WINDOW"):
        return
    url = f"http://127.0.0.1:{port}/"
    for exe in find_app_browser():
        try:
            subprocess.Popen([exe, f"--app={url}", "--window-size=1320,860", f"--user-data-dir={paths.state_dir() / 'window'}"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        except OSError:
            continue
    webbrowser.open(url)


def make_handler(app: App):
    allowed_hosts = {f"127.0.0.1:{app.port}", f"localhost:{app.port}"}

    class H(BaseHTTPRequestHandler):
        server_version = "Cekmecon/" + __version__

        def log_message(self, *a):  # quiet
            pass

        def send(self, code: int, body, ctype="application/json"):
            data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            self.wfile.write(data)

        def body(self) -> dict:
            n = int(self.headers.get("Content-Length") or 0)
            if n > 5_000_000:
                raise ValueError("body too large")
            return json.loads(self.rfile.read(n) or b"{}") if n else {}

        def guard(self) -> bool:
            if self.headers.get("Host") not in allowed_hosts:
                self.send(403, {"error": "bad host"})
                return False
            origin = self.headers.get("Origin")
            if origin and origin.replace("http://", "", 1) not in allowed_hosts:
                self.send(403, {"error": "cross-origin requests are not allowed"})  # other websites can't drive the app
                return False
            if self.command in ("POST", "PUT") and "application/json" not in (self.headers.get("Content-Type") or ""):
                self.send(415, {"error": "send application/json"})
                return False
            return True

        def ui_ok(self, q: dict) -> bool:
            key = self.headers.get("X-Cekmecon-UI") or (q.get("k") or [""])[0]
            if not secrets.compare_digest(key, app.ui_key):
                self.send(401, {"error": "ui key required"})
                return False
            app.last_ui_seen = time.time()
            return True

        def static(self, name: str):
            p = (UI_DIR / name).resolve()
            if UI_DIR.resolve() not in p.parents or not p.is_file():
                return self.send(404, {"error": "not found"})
            data = p.read_bytes()
            if name == "index.html":
                data = data.replace(b"__UI_KEY__", app.ui_key.encode()).replace(b"__VERSION__", __version__.encode())
            self.send(200, data, MIME.get(p.suffix, "application/octet-stream"))

        def do_GET(self):
            if not self.guard():
                return
            u = urllib.parse.urlparse(self.path)
            q = urllib.parse.parse_qs(u.query)
            try:
                if u.path in ("/", "/index.html"):
                    return self.static("index.html")
                if u.path.startswith("/ui/"):
                    return self.static(u.path[4:])
                if u.path == "/api/ping":
                    return self.send(200, {"ok": True, "app": "cekmecon", "instance": app.instance, "version": __version__})
                if u.path.startswith("/api/pair/"):
                    return self.send(200, app.poll_pair(u.path.rsplit("/", 1)[-1]))
                if not self.ui_ok(q):
                    return
                if u.path == "/api/state":
                    app.vault.reindex()
                    pend = [{k: r[k] for k in ("id", "client", "cwd", "host")} for r in app.pending.values() if r["status"] == "pending"]
                    clients = [{k: c.get(k, "") for k in ("id", "name", "cwd", "host", "created", "last_seen")} for c in app.clients()]
                    return self.send(200, {"tree": app.vault.tree(), "folders": app.vault.folders(), "stats": app.vault.stats(),
                                           "pending": pend, "clients": clients, "events": list(app.events)[-40:], "version": __version__})
                if u.path == "/api/note":
                    rel = q.get("path", [""])[0]
                    return self.send(200, {"path": rel, "text": app.vault.read(rel), "backlinks": app.vault.backlinks(rel)})
                if u.path == "/api/resolve":
                    return self.send(200, {"path": app.vault.resolve_title(q.get("title", [""])[0])})
                if u.path == "/api/search":
                    return self.send(200, {"results": app.vault.search(q.get("q", [""])[0], 30)})
                if u.path == "/api/graph":
                    return self.send(200, app.vault.graph())
                if u.path == "/api/events":
                    return self.stream()
                return self.send(404, {"error": "not found"})
            except (ValueError, OSError) as exc:
                return self.send(400, {"error": str(exc)})

        def stream(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            qq: queue.Queue = queue.Queue()
            with app.lock:
                app.listeners.append(qq)
            try:
                while True:
                    try:
                        ev = qq.get(timeout=15)
                        self.wfile.write(f"data: {json.dumps(ev, ensure_ascii=False)}\n\n".encode())
                    except queue.Empty:
                        self.wfile.write(b": keepalive\n\n")
                    app.last_ui_seen = time.time()
                    self.wfile.flush()
            except (OSError, ValueError):
                pass
            finally:
                with app.lock:
                    if qq in app.listeners:
                        app.listeners.remove(qq)

        def do_PUT(self):
            self.do_POST()

        def do_POST(self):
            if not self.guard():
                return
            u = urllib.parse.urlparse(self.path)
            q = urllib.parse.parse_qs(u.query)
            try:
                a = self.body()
                if u.path == "/api/pair":
                    return self.send(200, {"request_id": app.request_pair(str(a.get("client") or "Claude"), str(a.get("cwd") or ""), str(a.get("host") or ""))})
                if u.path.startswith("/api/claude/"):
                    tok = self.headers.get("X-Cekmecon-Token", "")
                    who = app.check_token(tok)
                    if not who:
                        return self.send(401, {"error": "not paired", "pair": "/api/pair"})
                    return self.send(200, app.claude(u.path.rsplit("/", 1)[-1], a, who.get("name", "Claude")))
                if not self.ui_ok(q):
                    return
                if u.path == "/api/note":
                    path = app.vault.write(a["path"], a["content"])
                    app.emit("save", f"Guardado {path}", mood="write")
                    return self.send(200, {"path": path})
                if u.path == "/api/note/new":
                    path = app.vault.new_note(a.get("title") or "Untitled", a.get("body", ""), a.get("folder") or "Inbox")
                    app.emit("save", f"Nota nueva {path}", mood="celebrate")
                    return self.send(200, {"path": path})
                if u.path == "/api/note/move":
                    return self.send(200, {"path": app.vault.move(a["path"], a["folder"])})
                if u.path == "/api/note/archive":
                    path = app.vault.archive(a["path"])
                    app.emit("save", f"Archivada {Path(path).name}", mood="idle")
                    return self.send(200, {"path": path})
                if u.path == "/api/organize":
                    return self.send(200, app.org.organize())
                if u.path == "/api/project/open":
                    return self.send(200, app.org.open_project(a["path"]))
                if u.path.startswith("/api/pair/") and u.path.endswith("/answer"):
                    rid = u.path.split("/")[3]
                    return self.send(200, app.answer_pair(rid, bool(a.get("allow")), bool(a.get("always"))))
                if u.path == "/api/clients/revoke":
                    app.revoke(a["id"])
                    return self.send(200, {"ok": True})
                return self.send(404, {"error": "not found"})
            except KeyError as exc:
                return self.send(400, {"error": f"missing field {exc}"})
            except (ValueError, OSError) as exc:
                return self.send(400, {"error": str(exc)})

    return H


def already_running() -> int:
    info = paths.read_json(paths.running_file(), {})
    port = info.get("port")
    if not port:
        return 0
    try:
        with urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/api/ping"), timeout=1.5) as r:
            if json.loads(r.read()).get("app") == "cekmecon":
                return int(port)
    except (OSError, ValueError):
        pass
    return 0


def serve(port: int = DEFAULT_PORT, window: bool = True, vault_root: str = "") -> None:
    running = already_running()
    if running:
        print(f"Çekmecón is already running on http://127.0.0.1:{running}/")
        if window:
            open_window(running)
        return
    vault = Vault(Path(vault_root).expanduser() if vault_root else None)
    httpd = None
    for p in [port] + list(range(port + 1, port + 20)):
        try:
            app = App(vault, p)
            httpd = ThreadingHTTPServer(("127.0.0.1", p), make_handler(app))
            break
        except OSError:
            continue
    if httpd is None:
        raise SystemExit("no free port near %d" % port)
    httpd.daemon_threads = True
    paths.write_json(paths.running_file(), {"port": app.port, "pid": os.getpid(), "instance": app.instance, "vault": str(vault.root)})
    app.emit("hello", "¡Hola! Cuido la memoria de Claude. Esperando trabajo…", mood="wave")
    print(f"{APP_NAME} {__version__} — http://127.0.0.1:{app.port}/  (vault: {vault.root})")
    if window:
        threading.Timer(0.4, open_window, args=(app.port,)).start()

    def watch():  # notice edits made in Obsidian/VS Code
        while True:
            time.sleep(4)
            try:
                if vault.reindex():
                    app.emit("index", "Vi cambios hechos fuera (Obsidian/VS Code) y reindexé", mood="idle")
            except Exception:  # never let the watcher die
                pass

    threading.Thread(target=watch, daemon=True).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            if paths.read_json(paths.running_file(), {}).get("instance") == app.instance:
                paths.running_file().unlink()
        except OSError:
            pass
