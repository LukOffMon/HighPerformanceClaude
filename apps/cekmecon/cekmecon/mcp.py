"""MCP bridge (stdio, JSON-RPC 2.0, one message per line) between Claude and the running Çekmecón app.

First use: asks the app for access; you click Allow in the window (Always / Just this session).
With "Always" the token is kept in ~/.cekmecon/token.json and every later session connects silently.
If the app is closed, the bridge starts it.
"""
from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import time
import urllib.error
import urllib.request

from . import __version__, paths

PROTOCOLS = ("2025-06-18", "2025-03-26", "2024-11-05")
TOKEN_FILE = "token.json"

TOOLS = [
    {"name": "cekmecon_open_project",
     "description": "Call once at the start of work in a project. Creates or refreshes the project's drawer (brief, auto map of stack/commands/layout, decisions, lessons, tasks, log) and returns a token-budgeted memory pack, so you do not need to re-read the codebase or old chats.",
     "inputSchema": {"type": "object", "properties": {"path": {"type": "string", "description": "Project folder; defaults to the current working directory"},
                                                       "query": {"type": "string", "description": "Keywords of the current task, to include matching past notes"},
                                                       "budget": {"type": "integer", "description": "Max tokens of memory to return (default 1500)"}}}},
    {"name": "cekmecon_context",
     "description": "Get the smallest useful memory for a task (profile, project brief, map, open tasks, recent decisions, lessons, matching notes), capped at a token budget.",
     "inputSchema": {"type": "object", "properties": {"project": {"type": "string"}, "query": {"type": "string"}, "budget": {"type": "integer"}}}},
    {"name": "cekmecon_search",
     "description": "Ranked full-text search across all notes. Returns titles, paths and short snippets; read only the notes you need.",
     "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "project": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["query"]}},
    {"name": "cekmecon_read",
     "description": "Read one note by vault path or title, optionally a line range.",
     "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}, "title": {"type": "string"}, "start": {"type": "integer"}, "end": {"type": "integer"}}}},
    {"name": "cekmecon_remember",
     "description": "Save memory in the right drawer automatically. kind=decision (what and why), lesson (would have saved time), task (open item), log (what was done), note (anything longer; give a title). One line for decision/lesson/task/log. Never store secrets.",
     "inputSchema": {"type": "object", "properties": {"kind": {"type": "string", "enum": ["decision", "lesson", "task", "log", "note"]},
                                                       "text": {"type": "string"}, "project": {"type": "string"}, "title": {"type": "string"}}, "required": ["kind", "text"]}},
    {"name": "cekmecon_write_note",
     "description": "Create or replace a Markdown note at a vault path (e.g. Projects/my-app/Architecture.md). Prefer cekmecon_remember for short items.",
     "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
    {"name": "cekmecon_organize",
     "description": "Tidy the vault: sort Inbox notes into project drawers or Knowledge, link related notes you wrote, remove duplicate lessons.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "cekmecon_status",
     "description": "Check the connection and see vault stats and the list of projects.",
     "inputSchema": {"type": "object", "properties": {}}},
]
ACTION = {"cekmecon_open_project": "open_project", "cekmecon_context": "context", "cekmecon_search": "search", "cekmecon_read": "read",
          "cekmecon_remember": "remember", "cekmecon_write_note": "write", "cekmecon_organize": "organize", "cekmecon_status": "status"}


class NotReady(Exception):
    pass


def http(method: str, port: int, path: str, data=None, token: str = "", timeout: float = 30):
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", method=method,
                                 data=json.dumps(data or {}).encode() if method == "POST" else None,
                                 headers={"Content-Type": "application/json", **({"X-Cekmecon-Token": token} if token else {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except ValueError:
            return e.code, {"error": str(e)}


def find_port(start_if_closed: bool = True) -> int:
    for attempt in range(2):
        port = paths.read_json(paths.running_file(), {}).get("port")
        if port:
            try:
                code, body = http("GET", int(port), "/api/ping", timeout=1.5)
                if code == 200 and body.get("app") == "cekmecon":
                    return int(port)
            except OSError:
                pass
        if attempt == 0 and start_if_closed and not os.environ.get("CEKMECON_NO_AUTOSTART"):
            flags = {"creationflags": 0x00000008 | 0x00000200} if sys.platform == "win32" else {"start_new_session": True}
            pkg_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            env = {**os.environ, "PYTHONPATH": pkg_parent + os.pathsep + os.environ.get("PYTHONPATH", "")}
            subprocess.Popen(paths.self_command("--no-window", console=False), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             stdin=subprocess.DEVNULL, env=env, **flags)
            for _ in range(30):
                time.sleep(0.3)
                if paths.read_json(paths.running_file(), {}).get("port"):
                    break
    raise NotReady("Çekmecón is not running on this computer. Open it (Start menu / Applications: “Çekmecón”, or run `cekmecon`) and try again.")


def load_token() -> str:
    return paths.read_json(paths.state_dir() / TOKEN_FILE, {}).get("token", "")


def pair(port: int, wait: float) -> str:
    code, body = http("POST", port, "/api/pair", {"client": "Claude Code", "cwd": os.getcwd(), "host": platform.node()})
    if code != 200:
        raise NotReady(body.get("error", "pairing failed"))
    rid, deadline = body["request_id"], time.time() + wait
    while time.time() < deadline:
        time.sleep(1)
        _, st = http("GET", port, f"/api/pair/{rid}")
        if st.get("status") == "approved" and st.get("token"):
            if st.get("always"):
                paths.write_json(paths.state_dir() / TOKEN_FILE, {"token": st["token"], "saved": time.strftime("%Y-%m-%d %H:%M")})
            return st["token"]
        if st.get("status") in ("denied", "expired", "unknown"):
            raise NotReady(f"Access was {st.get('status')} in the Çekmecón window. Continue without memory, or ask the user to allow it.")
    raise NotReady("Waiting for the user to click Allow in the Çekmecón window. Tell the user, then call the tool again.")


class Bridge:
    def __init__(self):
        self.token = load_token()

    def call(self, action: str, args: dict) -> dict:
        port = find_port()
        if action == "open_project" and not args.get("path"):
            args["path"] = os.getcwd()
        for _ in range(2):
            if not self.token:
                self.token = pair(port, float(os.environ.get("CEKMECON_PAIR_WAIT", "75")))
            code, body = http("POST", port, f"/api/claude/{action}", args, self.token, timeout=60)
            if code == 401:
                self.token = ""
                try:
                    (paths.state_dir() / TOKEN_FILE).unlink()
                except OSError:
                    pass
                continue
            if code != 200:
                raise ValueError(body.get("error", f"HTTP {code}"))
            return body
        raise NotReady("Could not authenticate with Çekmecón.")


def fmt(action: str, res: dict) -> str:
    if action in ("context",):
        return f"{res['text']}\n\n(memory: ~{res['tokens']}/{res['budget']} tokens from {len(res['sources'])} notes)"
    if action == "open_project":
        c = res["context"]
        new = f"Created {len(res['created'])} notes. " if res["created"] else ""
        return f"Project drawer: {res['drawer']} ({res['project']}). {new}Use project=\"{res['project']}\" in other cekmecon tools.\n\n{c['text']}\n\n(memory: ~{c['tokens']}/{c['budget']} tokens)"
    if action == "search":
        rs = res["results"]
        return "\n".join(f"- {r['title']} — {r['path']}\n  {r['snippet']}" for r in rs) or "No matches."
    if action == "read":
        return f"# {res['path']}\n{res['text']}"
    if action in ("remember", "write"):
        return f"Saved to {res['path']}"
    if action == "organize":
        return f"Moved {len(res['moved'])}: {', '.join(res['moved']) or '-'}; linked {res['linked']}; removed {res['deduped']} duplicate lessons."
    return json.dumps(res, ensure_ascii=False, indent=1)


def main() -> None:
    # JSON-RPC over stdio must be UTF-8 with bare \n, also on Windows consoles (cp1252, \r\n)
    for stream, kw in ((sys.stdin, {"encoding": "utf-8"}), (sys.stdout, {"encoding": "utf-8", "newline": "\n"})):
        try:
            stream.reconfigure(**kw)
        except (AttributeError, ValueError):
            pass
    bridge = Bridge()
    out = sys.stdout

    def send(msg):
        try:
            out.write(json.dumps(msg, ensure_ascii=False) + "\n")
            out.flush()
        except (BrokenPipeError, OSError):  # the client went away: exit quietly
            try:
                sys.stdout = open(os.devnull, "w")
            except OSError:
                pass
            raise SystemExit(0)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            send({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}})
            continue
        mid, method, params = msg.get("id"), msg.get("method", ""), msg.get("params") or {}
        if mid is None:  # notification (initialized, cancelled…)
            continue
        if method == "initialize":
            want = params.get("protocolVersion")
            send({"jsonrpc": "2.0", "id": mid, "result": {
                "protocolVersion": want if want in PROTOCOLS else PROTOCOLS[0],
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "cekmecon", "version": __version__},
                "instructions": "Çekmecón is the user's local memory drawer. At the start of work in a project call cekmecon_open_project once and use its memory pack instead of re-reading; save decisions, lessons and tasks with cekmecon_remember as you go."}})
        elif method == "ping":
            send({"jsonrpc": "2.0", "id": mid, "result": {}})
        elif method == "tools/list":
            send({"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}})
        elif method == "tools/call":
            name, args = params.get("name", ""), dict(params.get("arguments") or {})
            if name not in ACTION:
                send({"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": f"unknown tool {name}"}})
                continue
            try:
                text, err = fmt(ACTION[name], bridge.call(ACTION[name], args)), False
            except NotReady as exc:
                text, err = str(exc), True
            except (ValueError, OSError) as exc:
                text, err = f"Çekmecón error: {exc}", True
            send({"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": text}], "isError": err}})
        else:
            send({"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {method}"}})
