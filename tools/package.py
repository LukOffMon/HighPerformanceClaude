#!/usr/bin/env python3
"""Build dist/high-performance.zip for uploading the skill to claude.ai (Settings → Capabilities → Skills).

Deterministic: fixed timestamps and sorted entries, so the zip only changes when the skill changes.
  python3 tools/package.py          build
  python3 tools/package.py --check  exit 1 if dist/ is stale (used by CI)
"""
import io
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "high-performance"
OUT = ROOT / "dist" / "high-performance.zip"
SKIP = {"__pycache__", ".DS_Store"}


def build() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(SKILL.rglob("*")):
            if path.is_dir() or any(part in SKIP for part in path.parts) or path.suffix == ".pyc":
                continue
            arc = Path("high-performance") / path.relative_to(SKILL)
            info = zipfile.ZipInfo(arc.as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
            info.external_attr = (0o755 if path.suffix in (".py", ".sh") else 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, path.read_bytes())
    return buf.getvalue()


def main() -> int:
    data = build()
    if "--check" in sys.argv:
        if not OUT.exists() or OUT.read_bytes() != data:
            print("dist/high-performance.zip is stale — run: python3 tools/package.py")
            return 1
        print("dist/high-performance.zip is up to date")
        return 0
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_bytes(data)
    print(f"wrote {OUT.relative_to(ROOT)} ({len(data):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
