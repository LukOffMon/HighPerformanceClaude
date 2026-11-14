#!/usr/bin/env python3
"""checks.py — detect and run a project's verification ladder with compact output.

Ladder order: typecheck → lint → test → build. Commands come from the project
itself (Makefile, justfile, package.json scripts, tool configs) before falling
back to ecosystem defaults.

Default: list the detected commands (runs nothing).
  --run              execute them; print one line per check + relevant failure lines
  --only test,lint   restrict categories
  --cwd DIR          project directory (default: current directory)
  --timeout SEC      per-check timeout (default 600)
  --tail N           failure lines to show per check (default 40)
  --keep-going       don't stop at the first failing check

Exit code: 0 all passed (or list mode), 1 a check failed, 2 nothing detected.
Standard library only.
"""
from __future__ import annotations

import argparse
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True  # keep the skill directory clean
sys.path.insert(0, str(Path(__file__).resolve().parent))
import hpc_detect as d  # noqa: E402

SIGNAL = re.compile(
    r"(error|fail|failed|failure|exception|traceback|assert|panic|fatal|cannot|undefined|"
    r"not found|expected|✗|✕|×|FAIL|ERR!|E\s{2,}|^\s*>\s)", re.I)
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
MISSING_TOOL = re.compile(r"(No module named [\w.']+|command not found|is not recognized as an internal|"
                          r"could not determine executable to run|ENOENT.*spawn)", re.I)
NOISE = re.compile(r"^\s*(at .+node_modules|\s*$|npm (notice|warn)|warning: .*deprecated)", re.I)


def summarize_failure(output: str, tail: int) -> list[str]:
    lines = [ANSI.sub("", ln).rstrip() for ln in output.splitlines()]
    lines = [ln for ln in lines if not NOISE.match(ln)]
    signal_idx = [i for i, ln in enumerate(lines) if SIGNAL.search(ln)]
    keep: set[int] = set()
    for i in signal_idx[: tail // 2]:
        keep.update(range(max(0, i - 1), min(len(lines), i + 3)))
    keep.update(range(max(0, len(lines) - tail // 2), len(lines)))
    picked = [lines[i] for i in sorted(keep)][-tail:]
    return [ln[:300] for ln in picked]


def first_binary(cmd: str) -> str:
    try:
        parts = shlex.split(cmd)
    except ValueError:
        return cmd.split()[0]
    return parts[0] if parts else ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--cwd", default=".")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--tail", type=int, default=40)
    ap.add_argument("--keep-going", action="store_true")
    args = ap.parse_args()

    root = Path(args.cwd).resolve()
    checks = d.detect_checks(root)
    if args.only:
        wanted = {c.strip() for c in args.only.split(",") if c.strip()}
        checks = [c for c in checks if c[0] in wanted]
    if not checks:
        print(f"No verification commands detected in {root}. "
              "Check CLAUDE.md, CI workflows (.github/workflows) or the README.")
        return 2

    if not args.run:
        print(f"Verification ladder for {root}:")
        for cat, cmd, src in checks:
            print(f"  {cat:<9} {cmd}   [{src}]")
        print("Run with --run (optionally --only test) to execute.")
        return 0

    env = dict(os.environ, CI="1", FORCE_COLOR="0", NO_COLOR="1", PYTHONUNBUFFERED="1")
    failed = 0
    results: list[str] = []
    for cat, cmd, src in checks:
        binary = first_binary(cmd)
        if binary and not binary.startswith(("./", "vendor/", "bin/")) and shutil.which(binary) is None:
            results.append(f"SKIP {cat:<9} {cmd}  — `{binary}` not installed")
            continue
        start = time.time()
        try:
            proc = subprocess.run(cmd, cwd=str(root), shell=True, capture_output=True, text=True,
                                  timeout=args.timeout, env=env, stdin=subprocess.DEVNULL)
            code, output = proc.returncode, (proc.stdout or "") + "\n" + (proc.stderr or "")
        except subprocess.TimeoutExpired as exc:
            code = 124
            output = ((exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes)
                      else (exc.stdout or "")) + f"\nTIMEOUT after {args.timeout}s"
        took = time.time() - start
        output = ANSI.sub("", output)
        missing = MISSING_TOOL.search(output) if code != 0 else None
        if missing and (code == 127 or len(output.strip().splitlines()) <= 5):
            results.append(f"SKIP {cat:<9} {cmd}  — tool missing: {missing.group(0)[:80]}")
            continue
        if code == 0:
            results.append(f"PASS {cat:<9} {cmd}  ({took:.1f}s)")
            print(results[-1], flush=True)
            continue
        failed += 1
        results.append(f"FAIL {cat:<9} {cmd}  (exit {code}, {took:.1f}s)")
        print(results[-1], flush=True)
        for line in summarize_failure(output, args.tail):
            print(f"  | {line}")
        if not args.keep_going:
            remaining = checks[checks.index((cat, cmd, src)) + 1:]
            if remaining:
                print("  (stopped; remaining: " + ", ".join(c[0] for c in remaining) + " — use --keep-going)")
            break

    skipped = [r for r in results if r.startswith("SKIP")]
    for r in skipped:
        print(r)
    passed = sum(r.startswith("PASS") for r in results)
    print(f"\nSummary: {passed} passed, {failed} failed, {len(skipped)} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
