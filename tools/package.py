#!/usr/bin/env python3
"""Build dist/<skill>.zip for every skill under skills/, for uploading to claude.ai (Settings → Capabilities → Skills).

Deterministic: fixed timestamps and sorted entries, so the zip only changes when the skill changes.
  python3 tools/package.py          build
  python3 tools/package.py --check  exit 1 if dist/ is stale (used by CI)
"""
import io
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = sorted(p for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").exists())
SKIP = {"__pycache__", ".DS_Store"}


def build(skill: Path) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(skill.rglob("*")):
            if path.is_dir() or any(part in SKIP for part in path.parts) or path.suffix == ".pyc":
                continue
            arc = Path(skill.name) / path.relative_to(skill)
            info = zipfile.ZipInfo(arc.as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
            info.external_attr = (0o755 if path.suffix in (".py", ".sh") else 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, path.read_bytes())
    return buf.getvalue()


def main() -> int:
    stale = 0
    for skill in SKILLS:
        data, out = build(skill), ROOT / "dist" / f"{skill.name}.zip"
        rel = out.relative_to(ROOT)
        if "--check" in sys.argv:
            if not out.exists() or out.read_bytes() != data:
                print(f"{rel} is stale — run: python3 tools/package.py")
                stale = 1
            continue
        out.parent.mkdir(exist_ok=True)
        out.write_bytes(data)
        print(f"wrote {rel} ({len(data):,} bytes)")
    if "--check" in sys.argv and not stale:
        print("dist/ is up to date")
    return stale


if __name__ == "__main__":
    sys.exit(main())
