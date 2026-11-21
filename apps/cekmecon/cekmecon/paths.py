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
