"""Where Çekmecón keeps things.

  ~/.cekmecon/            app state (config, approved clients, index, running-app record)
  ~/Cekmecon/             the vault: plain Markdown you own (override with CEKMECON_VAULT or config)
"""
from __future__ import annotations

import json
import os
from pathlib import Path


def state_dir() -> Path:
    d = Path(os.environ.get("CEKMECON_HOME") or (Path.home() / ".cekmecon"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def config() -> dict:
    return read_json(state_dir() / "config.json", {})


def save_config(cfg: dict) -> None:
    write_json(state_dir() / "config.json", cfg)


def vault_dir() -> Path:
    v = os.environ.get("CEKMECON_VAULT") or config().get("vault") or str(Path.home() / "Cekmecon")
    p = Path(v).expanduser()
    p.mkdir(parents=True, exist_ok=True)
    return p


def running_file() -> Path:
    """Written by the app while it runs: {port, pid, instance}. The MCP bridge finds the app through it."""
    return state_dir() / "running.json"


def self_command(*args: str, console: bool = True) -> list:
    """How to run Çekmecón itself: the installed program (frozen build) or `python -m cekmecon`.

    On Windows the download ships two programs: Cekmecon.exe (window, no console) and cekmecon-cli.exe
    (console, used for the MCP stdio bridge and `connect`)."""
    import sys
    if getattr(sys, "frozen", False):
        exe = Path(sys.executable)
        if sys.platform == "win32":
            cli, gui = exe.with_name("cekmecon-cli.exe"), exe.with_name("Cekmecon.exe")
            exe = cli if console and cli.exists() else gui if gui.exists() else exe
        return [str(exe), *args]
    return [sys.executable, "-m", "cekmecon", *args]
