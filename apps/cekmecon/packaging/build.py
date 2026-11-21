#!/usr/bin/env python3
"""Build the downloadable Çekmecón program for the current OS (run on each OS, e.g. in CI).

  Windows -> out/Cekmecon-Setup-Windows.exe   (installer: Start Menu + Desktop, no admin)
  macOS   -> out/Cekmecon-macOS.dmg           (drag Çekmecón.app to Applications)
  Linux   -> out/Cekmecon-Linux-x86_64.tar.gz (binary + install-linux.sh)

Needs: pip install pyinstaller  (Windows also needs Inno Setup 6: choco install innosetup)
"""
import os
import platform
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
APP = HERE.parent
UI = APP / "cekmecon" / "ui"
OUT, WORK = HERE / "out", HERE / "build"
SEP = ";" if os.name == "nt" else ":"
sys.path.insert(0, str(APP))
from cekmecon import __version__  # noqa: E402


def pyinstaller(name: str, windowed: bool, onefile: bool = True, icon: str = "") -> None:
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--name", name,
           "--paths", str(APP), "--distpath", str(WORK / "dist"), "--workpath", str(WORK / "tmp"), "--specpath", str(WORK),
           "--add-data", f"{UI}{SEP}cekmecon/ui", "--add-data", f"{APP / 'cekmecon' / 'skill'}{SEP}cekmecon/skill",
           "--onefile" if onefile else "--onedir", "--windowed" if windowed else "--console"]
    if icon:
        cmd += ["--icon", icon]
    if sys.platform == "darwin":
        cmd += ["--osx-bundle-identifier", "io.github.lukoffmon.cekmecon"]
    subprocess.run(cmd + [str(HERE / "entry.py")], check=True)


def windows() -> Path:
    pyinstaller("Cekmecon", windowed=True, icon=str(UI / "icon.ico"))
    pyinstaller("cekmecon-cli", windowed=False, icon=str(UI / "icon.ico"))
    iscc = shutil.which("iscc") or r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    subprocess.run([iscc, f"/DAppVersion={__version__}", f"/DSrcDir={WORK / 'dist'}", f"/DIconFile={UI / 'icon.ico'}",
                    f"/O{OUT}", "/FCekmecon-Setup-Windows", str(HERE / "cekmecon.iss")], check=True)
    return OUT / "Cekmecon-Setup-Windows.exe"


def macos() -> Path:
    icns = WORK / "AppIcon.icns"
    iconset = WORK / "AppIcon.iconset"
    iconset.mkdir(parents=True, exist_ok=True)
    for s in (16, 32, 128, 256, 512):
        subprocess.run(["sips", "-z", str(s), str(s), str(UI / "icon.png"), "--out", str(iconset / f"icon_{s}x{s}.png")], check=True, capture_output=True)
    subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(icns)], check=True)
    pyinstaller("Cekmecon", windowed=True, onefile=False, icon=str(icns))
    app = WORK / "dist" / "Cekmecon.app"
    plist = app / "Contents" / "Info.plist"
    import plistlib
    info = plistlib.loads(plist.read_bytes())
    info.update(CFBundleDisplayName="Çekmecón", CFBundleName="Çekmecón", CFBundleShortVersionString=__version__)
    plist.write_bytes(plistlib.dumps(info))
    subprocess.run(["codesign", "--force", "--deep", "--sign", "-", str(app)], check=True)  # ad-hoc re-sign after the plist edit
    stage = WORK / "dmg"
    shutil.rmtree(stage, ignore_errors=True)
    stage.mkdir()
    shutil.copytree(app, stage / "Çekmecón.app", symlinks=True)
    os.symlink("/Applications", stage / "Applications")
    dmg = OUT / "Cekmecon-macOS.dmg"
    subprocess.run(["hdiutil", "create", "-volname", "Çekmecón", "-srcfolder", str(stage), "-ov", "-format", "UDZO", str(dmg)], check=True)
    return dmg


def linux() -> Path:
    pyinstaller("cekmecon", windowed=False, icon="")
    tgz = OUT / f"Cekmecon-Linux-{platform.machine()}.tar.gz"
    with tarfile.open(tgz, "w:gz") as t:
        for src, arc, mode in ((WORK / "dist" / "cekmecon", "cekmecon/cekmecon", 0o755), (UI / "icon.png", "cekmecon/icon.png", 0o644),
                               (HERE / "install-linux.sh", "cekmecon/install-linux.sh", 0o755)):
            info = t.gettarinfo(str(src), arc)
            info.mode = mode
            with open(src, "rb") as f:
                t.addfile(info, f)
    return tgz


def main() -> int:
    OUT.mkdir(exist_ok=True)
    WORK.mkdir(exist_ok=True)
    out = windows() if sys.platform == "win32" else macos() if sys.platform == "darwin" else linux()
    print(f"built {out} ({out.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
