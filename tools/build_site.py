#!/usr/bin/env python3
"""Wrap site/iceberg.html (artifact source, no document skeleton) into docs/index.html for GitHub Pages.

  python3 tools/build_site.py          build
  python3 tools/build_site.py --check  exit 1 if docs/index.html is stale
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "site" / "iceberg.html", ROOT / "docs" / "index.html"
HEAD = (
    '<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    "<style>html,body{margin:0}:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}</style>\n"
)


def build() -> str:
    src = SRC.read_text(encoding="utf-8")
    style_at = src.index("<style>")
    head_part, rest = src[:style_at], src[style_at:]
    style_end = rest.index("</style>") + len("</style>")
    return HEAD + head_part + rest[:style_end] + "\n</head>\n<body>\n" + rest[style_end:].lstrip() + "</body>\n</html>\n"


def main() -> int:
    html = build()
    if "--check" in sys.argv:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != html:
            print("docs/index.html is stale — run: python3 tools/build_site.py")
            return 1
        return 0
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    (OUT.parent / ".nojekyll").touch()
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
