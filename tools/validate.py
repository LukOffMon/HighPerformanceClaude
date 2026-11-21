#!/usr/bin/env python3
"""Validate the plugin: skill frontmatter, size budgets, links, manifests, agents, commands, scripts, dist zip.

Run: python3 tools/validate.py   (exit 0 = all good). Standard library only.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors: list = []
warnings: list = []


def err(msg: str) -> None:
    errors.append(msg)


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        err(f"{path.relative_to(ROOT)}: missing YAML frontmatter")
        return {}
    data = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            key, _, value = line.partition(":")
            data[key.strip()] = value.strip().strip('"')
    return data


def check_skill(skill_dir: Path) -> None:
    md = skill_dir / "SKILL.md"
    rel = md.relative_to(ROOT)
    if not md.exists():
        err(f"{skill_dir.relative_to(ROOT)}: no SKILL.md")
        return
    fm = frontmatter(md)
    name, desc = fm.get("name", ""), fm.get("description", "")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or len(name) > 64:
        err(f"{rel}: invalid name {name!r} (lowercase letters, digits, hyphens; ≤64 chars)")
    if name != skill_dir.name:
        err(f"{rel}: name {name!r} must match directory {skill_dir.name!r}")
    if not desc:
        err(f"{rel}: empty description")
    if len(desc) > 1024:
        err(f"{rel}: description is {len(desc)} chars (max 1024)")
    if "<" in desc or ">" in desc:
        err(f"{rel}: description must not contain angle brackets")
    body_lines = md.read_text(encoding="utf-8").count("\n")
    if body_lines > 500:
        err(f"{rel}: {body_lines} lines (keep SKILL.md ≤ 500; move detail to references/)")
    words = len(md.read_text(encoding="utf-8").split())
    if words > 3500:
        warnings.append(f"{rel}: {words} words — heavy for an always-loaded skill")

    # every referenced file exists; every reference file is referenced
    text = md.read_text(encoding="utf-8")
    for ref in set(re.findall(r"`((?:references|scripts)/[\w./-]+)`", text)):
        target = ref.split()[0]
        if not (skill_dir / target).exists():
            err(f"{rel}: references missing file {target}")
    for ref_file in sorted((skill_dir / "references").glob("*.md")):
        if f"references/{ref_file.name}" not in text:
            err(f"{rel}: references/{ref_file.name} is never mentioned, so Claude will never load it")
        lines = ref_file.read_text(encoding="utf-8").count("\n")
        if lines > 120 and "## Contents" not in ref_file.read_text(encoding="utf-8"):
            warnings.append(f"{ref_file.relative_to(ROOT)}: {lines} lines without a Contents section")
    for ref_file in sorted((skill_dir / "references").glob("*.md")):
        for ref in re.findall(r"`((?:references|scripts)/[\w.-]+\.\w+)", ref_file.read_text(encoding="utf-8")):
            if not (skill_dir / ref).exists():
                err(f"{ref_file.relative_to(ROOT)}: mentions missing {ref}")
    for script in sorted((skill_dir / "scripts").glob("*.py")):
        try:
            compile(script.read_text(encoding="utf-8"), str(script), "exec")
        except SyntaxError as exc:
            err(f"{script.relative_to(ROOT)}: does not compile: {exc}")
    for path in sorted((skill_dir / "scripts").glob("*.py")):
        if path.exists():
            res = subprocess.run([sys.executable, str(path), "--help"], capture_output=True, text=True)
            if res.returncode != 0:
                err(f"{path.relative_to(ROOT)} --help failed: {res.stderr[-300:]}")


def check_manifests() -> None:
    try:
        plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
        market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    except (OSError, ValueError) as exc:
        err(f"manifest unreadable: {exc}")
        return
    for key in ("name", "version", "description"):
        if not plugin.get(key):
            err(f"plugin.json: missing {key}")
    entries = [p for p in market.get("plugins", []) if p.get("name") == plugin.get("name")]
    if not entries:
        err("marketplace.json: no entry for the plugin name in plugin.json")
    else:
        if entries[0].get("version") != plugin.get("version"):
            err("marketplace.json and plugin.json versions differ")
    if market.get("metadata", {}).get("version") not in (None, plugin.get("version")):
        err("marketplace.json metadata.version differs from plugin.json version")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8") if (ROOT / "CHANGELOG.md").exists() else ""
    if f"[{plugin.get('version')}]" not in changelog:
        warnings.append(f"CHANGELOG.md has no entry for {plugin.get('version')}")


def check_agents_and_commands() -> None:
    for agent in sorted((ROOT / "agents").glob("*.md")):
        fm = frontmatter(agent)
        if fm.get("name") != agent.stem:
            err(f"{agent.relative_to(ROOT)}: name must equal file name ({agent.stem})")
        if not fm.get("description"):
            err(f"{agent.relative_to(ROOT)}: missing description")
    for cmd in sorted((ROOT / "commands").glob("*.md")):
        fm = frontmatter(cmd)
        if not fm.get("description"):
            err(f"{cmd.relative_to(ROOT)}: missing description")
        text = cmd.read_text(encoding="utf-8")
        if "${ARGUMENTS" in text:
            err(f"{cmd.relative_to(ROOT)}: shell-style ${{ARGUMENTS…}} is not expanded; use $ARGUMENTS")
        for ref in re.findall(r"`(references/[\w.-]+\.md)`", text):
            if not any((d / ref).exists() for d in (ROOT / "skills").iterdir()):
                err(f"{cmd.relative_to(ROOT)}: mentions missing {ref}")


def check_dist() -> None:
    for tool in ("package.py", "build_site.py", "token_report.py"):
        res = subprocess.run([sys.executable, str(ROOT / "tools" / tool), "--check"], capture_output=True, text=True)
        if res.returncode != 0:
            err(res.stdout.strip() or res.stderr.strip())


def check_cekmecon() -> None:
    app = ROOT / "apps" / "cekmecon"
    if not app.exists():
        return
    skill, copy = ROOT / "skills/cekmecon/SKILL.md", app / "cekmecon/skill/SKILL.md"
    if not copy.exists() or skill.read_bytes() != copy.read_bytes():
        err("apps/cekmecon/cekmecon/skill/SKILL.md must be an exact copy of skills/cekmecon/SKILL.md")
    for py in sorted(app.rglob("*.py")):
        try:
            compile(py.read_text(encoding="utf-8"), str(py), "exec")
        except SyntaxError as exc:
            err(f"{py.relative_to(ROOT)}: does not compile: {exc}")
    for name in ("index.html", "app.js", "style.css", "mascot.js", "logo.svg", "icon.ico", "icon.png"):
        if not (app / "cekmecon/ui" / name).exists():
            err(f"apps/cekmecon/cekmecon/ui/{name} is missing")


def main() -> int:
    for skill_dir in sorted((ROOT / "skills").iterdir()):
        if skill_dir.is_dir():
            check_skill(skill_dir)
    check_manifests()
    check_agents_and_commands()
    check_dist()
    check_cekmecon()
    for w in warnings:
        print(f"warn  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"\n{'OK' if not errors else 'FAILED'}: {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
