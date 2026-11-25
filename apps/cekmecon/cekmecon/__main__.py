"""GeekMcON command line.

  cekmecon                      open the app (starts it if needed)
  cekmecon --no-window          run in the background (the MCP bridge does this when needed)
  cekmecon --vault PATH         use PATH as the vault from now on (an existing Obsidian vault works)
  cekmecon connect              register GeekMcON with Claude Code (user scope) and install its skill
  cekmecon disconnect           remove it from Claude Code and forget the saved token
  cekmecon status               is the app running, which vault, which clients are allowed
  cekmecon update [--check]     update to the latest release (the same version as the web app)
  cekmecon mcp                  the MCP stdio server Claude Code launches (you never run this by hand)
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from . import APP_NAME, DEFAULT_PORT, __version__, paths

SKILL_SRC = Path(__file__).with_name("skill") / "SKILL.md"


NO_WINDOW = {"creationflags": 0x08000000} if sys.platform == "win32" else {}  # CREATE_NO_WINDOW


def claude_cli() -> str:
    exe = shutil.which("claude") or shutil.which("claude.cmd") or shutil.which("claude.exe")
    return exe or ""


def connect(quiet: bool = False) -> int:
    cmd = paths.self_command("mcp")
    exe = claude_cli()
    if exe:
        subprocess.run([exe, "mcp", "remove", "--scope", "user", "cekmecon"], capture_output=True, **NO_WINDOW)
        res = subprocess.run([exe, "mcp", "add", "--scope", "user", "cekmecon", "--", *cmd], capture_output=True, text=True, **NO_WINDOW)
        if res.returncode != 0:
            print(res.stderr or res.stdout)
            return 1
        print("✓ Registered the MCP server “cekmecon” in Claude Code (all your projects).")
        cfg = paths.config()
        cfg["connected"] = " ".join(cmd)
        paths.save_config(cfg)
    else:
        print("Claude Code CLI not found on PATH. Add this to ~/.claude.json under \"mcpServers\" (or run the command later):")
        print('  "cekmecon": {"command": %r, "args": %r}' % (cmd[0], cmd[1:]))
        print(f"  claude mcp add --scope user cekmecon -- {' '.join(cmd)}")
    dst = Path.home() / ".claude" / "skills" / "cekmecon" / "SKILL.md"
    if SKILL_SRC.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SKILL_SRC, dst)
        print(f"✓ Installed the skill at {dst}")
    print("\nNext: open GeekMcON, then start Claude Code in any project. The first time, Claude asks to use the")
    print("cekmecon tools and the GeekMcON window asks you to Allow — choose “Always” and it is automatic from then on.")
    return 0


def disconnect() -> int:
    exe = claude_cli()
    if exe:
        subprocess.run([exe, "mcp", "remove", "--scope", "user", "cekmecon"], capture_output=True)
    shutil.rmtree(Path.home() / ".claude" / "skills" / "cekmecon", ignore_errors=True)
    try:
        (paths.state_dir() / "token.json").unlink()
    except OSError:
        pass
    print("✓ Disconnected from Claude Code (your notes are untouched).")
    return 0


def status() -> int:
    from .server import already_running
    port = already_running()
    print(f"{APP_NAME} {__version__}")
    print(f"  app:     {'running on http://127.0.0.1:%d/' % port if port else 'not running'}")
    print(f"  vault:   {paths.vault_dir()}")
    clients = paths.read_json(paths.state_dir() / "clients.json", [])
    print(f"  allowed: {len(clients)} client(s)" + "".join(f"\n    - {c.get('name')} ({c.get('host')}) since {c.get('created')}" for c in clients))
    print(f"  claude:  {'token saved' if (paths.state_dir() / 'token.json').exists() else 'not paired yet'}")
    return 0


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")  # never crash on a console that cannot print ✓ or Ç
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(prog="cekmecon", description=f"{APP_NAME}: Claude's local memory drawer.")
    ap.add_argument("command", nargs="?", default="open", choices=["open", "mcp", "connect", "disconnect", "status", "update"])
    ap.add_argument("--check", action="store_true", help="update: only say whether a newer version exists")
    ap.add_argument("--force", action="store_true", help="update: reinstall even if already up to date")
    ap.add_argument("--no-window", action="store_true", help="run without opening the window")
    ap.add_argument("--vault", default="", help="vault folder to use from now on")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--version", action="version", version=__version__)
    a = ap.parse_args(argv)
    if a.vault:
        cfg = paths.config()
        cfg["vault"] = str(Path(a.vault).expanduser().resolve())
        paths.save_config(cfg)
    if a.command == "mcp":
        from .mcp import main as mcp_main
        mcp_main()
        return 0
    if a.command == "connect":
        return connect()
    if a.command == "disconnect":
        return disconnect()
    if a.command == "status":
        return status()
    if a.command == "update":
        from .update import run
        return run(check_only=a.check, force=a.force)
    from .server import serve
    serve(a.port, window=not a.no_window)
    return 0


if __name__ == "__main__":
    sys.exit(main())
