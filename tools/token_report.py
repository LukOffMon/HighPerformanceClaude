#!/usr/bin/env python3
"""Estimate what the plugin costs in context, so it stays cheap.

  always-on : skill, agent and command descriptions (paid in every session)
  on trigger: each SKILL.md body (paid when the skill loads)
  on demand : each reference file (paid only when read)

Tokens are estimated as chars / 4 (close enough to budget with). Standard library only.
  python3 tools/token_report.py           report
  python3 tools/token_report.py --check   exit 1 if a budget is exceeded
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUDGET = {"always_on": 800, "skill": 3200, "reference": 2500}


def tok(text: str) -> int:
    return round(len(text) / 4)


def desc(path: Path) -> str:
    m = re.search(r"^description: (.*)$", path.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else ""


def report() -> list:
    over = []
    files = sorted(ROOT.glob("skills/*/SKILL.md")) + sorted(ROOT.glob("agents/*.md")) + sorted(ROOT.glob("commands/*.md"))
    always = sum(tok(desc(f)) for f in files)
    print(f"always-on   ~{always:5} tokens  ({len(files)} descriptions; budget {BUDGET['always_on']})")
    if always > BUDGET["always_on"]:
        over.append(f"always-on descriptions ~{always} tokens > {BUDGET['always_on']}")
    for skill in sorted(ROOT.glob("skills/*/SKILL.md")):
        body = tok(skill.read_text(encoding="utf-8"))
        print(f"on trigger  ~{body:5} tokens  {skill.relative_to(ROOT)}")
        if body > BUDGET["skill"]:
            over.append(f"{skill.relative_to(ROOT)} ~{body} tokens > {BUDGET['skill']}")
        for ref in sorted((skill.parent / "references").glob("*.md")):
            n = tok(ref.read_text(encoding="utf-8"))
            if n > BUDGET["reference"]:
                over.append(f"{ref.relative_to(ROOT)} ~{n} tokens > {BUDGET['reference']}")
        refs = sum(tok(r.read_text(encoding="utf-8")) for r in (skill.parent / "references").glob("*.md"))
        print(f"on demand   ~{refs:5} tokens  {skill.parent.name}/references (read one at a time)")
    return over


def main() -> int:
    over = report()
    for o in over:
        print(f"OVER BUDGET: {o}")
    return 1 if over and "--check" in sys.argv else 0


if __name__ == "__main__":
    sys.exit(main())
