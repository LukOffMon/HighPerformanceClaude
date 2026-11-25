"""`cekmecon update`: bring this install up to the latest GitHub Release, the same version the web app runs.

  installed program (Windows) -> download Cekmecon-Setup-Windows.exe and run it silently (it closes the app first)
  installed program (macOS)   -> download Cekmecon-macOS.dmg and open it (drag GeekMcON to Applications)
  installed program (Linux)   -> download Cekmecon-Linux-x86_64.tar.gz and run its install-linux.sh
  pip / install.sh install    -> pip install --upgrade from the GitHub source
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

from . import APP_NAME, __version__

REPO = "LukOffMon/HighPerformanceClaude"
API_LATEST = f"https://api.github.com/repos/{REPO}/releases/latest"
SOURCE = f"https://github.com/{REPO}/archive/refs/heads/main.zip#subdirectory=apps/cekmecon"
ASSET = {"win32": "Cekmecon-Setup-Windows.exe", "darwin": "Cekmecon-macOS.dmg"}.get(sys.platform, "Cekmecon-Linux-x86_64.tar.gz")


def parse(v: str) -> tuple:
    try:
        return tuple(int(x) for x in v.strip().lstrip("v").split(".")[:3])
    except ValueError:
        return ()


def latest() -> tuple[str, dict]:
    """(version, {asset name: download url}) of the latest release."""
    req = urllib.request.Request(API_LATEST, headers={"User-Agent": "cekmecon-updater", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    tag = str(data.get("tag_name", ""))
    return tag.rsplit("v", 1)[-1], {a["name"]: a["browser_download_url"] for a in data.get("assets", [])}


def download(url: str, name: str) -> Path:
    dst = Path(tempfile.mkdtemp(prefix="cekmecon-update-")) / name
    print(f"-> Downloading {name}...")
    req = urllib.request.Request(url, headers={"User-Agent": "cekmecon-updater"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dst, "wb") as f:
        while chunk := r.read(1 << 16):
            f.write(chunk)
    return dst


def run(check_only: bool = False, force: bool = False) -> int:
    frozen = getattr(sys, "frozen", False)
    try:
        version, assets = latest()
    except OSError as e:
        print(f"Could not reach GitHub ({e}). Check your internet connection and try again.")
        return 1
    print(f"{APP_NAME}: installed {__version__}, latest {version or '?'}")
    if not force and parse(version) and parse(version) <= parse(__version__):
        print("✓ Already up to date.")
        return 0
    if check_only:
        print("An update is available: run  cekmecon update")
        return 0

    if not frozen:  # pip / install.sh install: upgrade from source, keep the same shortcuts and MCP command
        res = subprocess.run([sys.executable, "-m", "pip", "install", "--user", "--upgrade", "--quiet", SOURCE])
        if res.returncode != 0:
            return res.returncode
        print("✓ Updated. Close and reopen GeekMcON to use the new version.")
        return 0

    url = assets.get(ASSET)
    if not url:
        print(f"The latest release has no {ASSET} yet. Download it later from https://github.com/{REPO}/releases")
        return 1
    file = download(url, ASSET)
    if sys.platform == "win32":
        # Detached so this console program (cekmecon-cli.exe) can exit and let the installer replace it.
        flags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        subprocess.Popen([str(file), "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CLOSEAPPLICATIONS"],
                         creationflags=flags, close_fds=True)
        print("✓ Installer started: it closes GeekMcON, updates it and opens it again.")
        return 0
    if sys.platform == "darwin":
        subprocess.run(["open", str(file)])
        print("✓ Opened the disk image: drag GeekMcON to Applications and choose Replace.")
        return 0
    with tarfile.open(file) as t:
        t.extractall(file.parent, filter="data") if hasattr(tarfile, "data_filter") else t.extractall(file.parent)
    script = next(file.parent.rglob("install-linux.sh"), None)
    if not script:
        print("install-linux.sh not found in the download.")
        return 1
    os.chmod(script, 0o755)
    return subprocess.run(["bash", str(script)], cwd=script.parent).returncode
