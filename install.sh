#!/usr/bin/env bash
# High-Performance Claude — manual installer (alternative to `/plugin install`).
#
#   ./install.sh                      install for your user (~/.claude)
#   ./install.sh --project <dir>      install into one project (<dir>/.claude)
#   ./install.sh --uninstall [...]    remove what this script installed
#
# Remote one-liner (clones the repo to a temp dir first):
#   curl -fsSL https://raw.githubusercontent.com/LukOffMon/HighPerformanceClaude/main/install.sh | bash
set -euo pipefail

REPO_URL="${HPC_REPO:-https://github.com/LukOffMon/HighPerformanceClaude.git}"
REF="${HPC_REF:-main}"
TARGET="${HOME}/.claude"
MODE="install"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) TARGET="$(cd "${2:?--project needs a directory}" && pwd)/.claude"; shift 2 ;;
    --uninstall) MODE="uninstall"; shift ;;
    -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

SRC="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)"
if [[ ! -f "${SRC}/skills/high-performance/SKILL.md" ]]; then
  TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
  echo "→ fetching ${REPO_URL} (${REF})"
  git clone -q --depth 1 --branch "$REF" "$REPO_URL" "$TMP/hpc"
  SRC="$TMP/hpc"
fi

SKILL_DST="${TARGET}/skills/high-performance"
if [[ "$MODE" == "uninstall" ]]; then
  rm -rf "$SKILL_DST" "${TARGET}/skills/iceberg"
  rm -f "${TARGET}"/agents/hpc-scout.md "${TARGET}"/agents/hpc-critic.md
  for f in "${SRC}"/commands/*.md; do rm -f "${TARGET}/commands/hpc-$(basename "$f")"; done
  echo "✓ removed High-Performance Claude from ${TARGET}"
  exit 0
fi

mkdir -p "${TARGET}/skills" "${TARGET}/agents" "${TARGET}/commands"
rm -rf "$SKILL_DST"
cp -R "${SRC}/skills/high-performance" "$SKILL_DST"
rm -rf "${TARGET}/skills/iceberg"
cp -R "${SRC}/skills/iceberg" "${TARGET}/skills/iceberg"
find "$SKILL_DST" -name '__pycache__' -type d -prune -exec rm -rf {} +
cp "${SRC}"/agents/hpc-*.md "${TARGET}/agents/"
for f in "${SRC}"/commands/*.md; do cp "$f" "${TARGET}/commands/hpc-$(basename "$f")"; done

echo "✓ installed into ${TARGET}"
echo "  skill:    skills/high-performance (loads automatically on coding tasks, or /high-performance)"
echo "  skill:    skills/iceberg (say \"Iceberg\" to dive below the surface of a task)"
echo "  agents:   hpc-scout, hpc-critic"
echo "  commands: $(for f in "${SRC}"/commands/*.md; do printf '/hpc-%s ' "$(basename "$f" .md)"; done)"
echo "  Restart Claude Code (or start a new session) to pick it up."
