#!/usr/bin/env python3
"""Wrap the artifact-style sources in site/ (no document skeleton) into GitHub Pages files under docs/.

  site/iceberg.html   -> docs/index.html
  site/cekmecon.html  -> docs/cekmecon/index.html

Sources may inline other repo files with  /*@include relative/path*/  (resolved relative to site/).

  python3 tools/build_site.py                       build
  python3 tools/build_site.py --check               exit 1 if any docs/ page is stale
  python3 tools/build_site.py --artifact NAME OUT   write site/NAME.html with includes resolved (for publishing as an Artifact)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE, DOCS = ROOT / "site", ROOT / "docs"
PAGES = {"iceberg": DOCS / "index.html", "cekmecon": DOCS / "cekmecon" / "index.html"}
HEAD = (
    '<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    "<style>html,body{margin:0}:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}</style>\n"
)
EXTRA_HEAD = {"cekmecon": "<style>[hidden]{display:none!important}img{max-width:100%}</style>\n"}


def resolve(src: str) -> str:
    return re.sub(r"/\*@include ([\w./-]+)\*/", lambda m: (SITE / m.group(1)).resolve().read_text(encoding="utf-8"), src)


def build(name: str) -> str:
    src = resolve((SITE / f"{name}.html").read_text(encoding="utf-8"))
    style_at = src.index("<style>")
    head_part, rest = src[:style_at], src[style_at:]
    style_end = rest.index("</style>") + len("</style>")
    return HEAD + EXTRA_HEAD.get(name, "") + head_part + rest[:style_end] + "\n</head>\n<body>\n" + rest[style_end:].lstrip() + "</body>\n</html>\n"


def main() -> int:
    if "--artifact" in sys.argv:
        i = sys.argv.index("--artifact")
        name, out = sys.argv[i + 1], Path(sys.argv[i + 2])
        out.write_text(resolve((SITE / f"{name}.html").read_text(encoding="utf-8")), encoding="utf-8")
        print(f"wrote {out}")
        return 0
    stale = 0
    for name, out in PAGES.items():
        html = build(name)
        if "--check" in sys.argv:
            if not out.exists() or out.read_text(encoding="utf-8") != html:
                print(f"{out.relative_to(ROOT)} is stale — run: python3 tools/build_site.py")
                stale = 1
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        print(f"wrote {out.relative_to(ROOT)}")
    if "--check" not in sys.argv:
        (DOCS / ".nojekyll").touch()
    return stale


if __name__ == "__main__":
    sys.exit(main())
