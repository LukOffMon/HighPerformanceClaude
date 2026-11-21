#!/usr/bin/env bash
# Toilet Bamboo Paper Çekmecón — macOS / Linux installer (no sudo).
#   curl -fsSL https://raw.githubusercontent.com/LukOffMon/HighPerformanceClaude/main/apps/cekmecon/install.sh | bash
# Installs into its own virtualenv, adds `cekmecon` to ~/.local/bin, an app launcher, connects Claude Code and opens it.
#   install.sh --uninstall   remove the app (your notes in ~/Cekmecon are kept)
set -euo pipefail
SRC="https://github.com/LukOffMon/HighPerformanceClaude/archive/refs/heads/main.zip#subdirectory=apps/cekmecon"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)"
[[ -f "$HERE/pyproject.toml" ]] && SRC="$HERE"
APPDIR="${XDG_DATA_HOME:-$HOME/.local/share}/cekmecon"
VENV="$APPDIR/venv"
BIN="$HOME/.local/bin"

if [[ "${1:-}" == "--uninstall" ]]; then
  "$BIN/cekmecon" disconnect 2>/dev/null || true
  rm -rf "$APPDIR" "$BIN/cekmecon" "$HOME/.local/share/applications/cekmecon.desktop" "$HOME/Applications/Çekmecón.app"
  echo "✓ Çekmecón removed. Your notes are still in ~/Cekmecon."
  exit 0
fi

PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'; then PY="$c"; break; fi
done
if [[ -z "$PY" ]]; then
  echo "Python 3.9+ is required."
  [[ "$(uname)" == "Darwin" ]] && echo "  Install it with: xcode-select --install   (or brew install python)" || echo "  Install it with your package manager, e.g. sudo apt install python3 python3-venv"
  exit 1
fi

echo "→ Installing Çekmecón"
mkdir -p "$APPDIR" "$BIN"
if "$PY" -m venv "$VENV" >/dev/null 2>&1; then
  "$VENV/bin/python" -m pip install --quiet --upgrade pip >/dev/null 2>&1 || true
  "$VENV/bin/python" -m pip install --quiet --upgrade "$SRC"
  RUN="$VENV/bin/python"
else
  echo "  (python venv unavailable; installing with pip --user)"
  "$PY" -m pip install --user --quiet --upgrade "$SRC" || "$PY" -m pip install --user --quiet --upgrade --break-system-packages "$SRC"
  RUN="$(command -v "$PY")"
fi
printf '#!/bin/sh\nexec "%s" -m cekmecon "$@"\n' "$RUN" > "$BIN/cekmecon"
chmod +x "$BIN/cekmecon"
ICON="$("$RUN" -c 'import cekmecon, os; print(os.path.join(os.path.dirname(cekmecon.__file__), "ui", "icon.png"))')"

if [[ "$(uname)" == "Darwin" ]]; then
  APP="$HOME/Applications/Çekmecón.app"
  mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
  printf '#!/bin/sh\nexec "%s" -m cekmecon\n' "$RUN" > "$APP/Contents/MacOS/cekmecon"
  chmod +x "$APP/Contents/MacOS/cekmecon"
  sips -s format icns "$ICON" --out "$APP/Contents/Resources/AppIcon.icns" >/dev/null 2>&1 || true
  cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleName</key><string>Çekmecón</string><key>CFBundleIdentifier</key><string>io.github.lukoffmon.cekmecon</string>
<key>CFBundleExecutable</key><string>cekmecon</string><key>CFBundleIconFile</key><string>AppIcon</string>
<key>CFBundlePackageType</key><string>APPL</string><key>LSUIElement</key><false/>
</dict></plist>
PLIST
  echo "→ App added to ~/Applications (Launchpad / Spotlight: Çekmecón)"
else
  mkdir -p "$HOME/.local/share/applications"
  cat > "$HOME/.local/share/applications/cekmecon.desktop" <<DESK
[Desktop Entry]
Type=Application
Name=Çekmecón
GenericName=Claude memory drawer
Comment=Toilet Bamboo Paper Çekmecón — Claude's memory drawer
Exec=$BIN/cekmecon
Icon=$ICON
Categories=Office;Development;
Terminal=false
DESK
  echo "→ Launcher added to your applications menu"
fi

"$BIN/cekmecon" connect || true
( "$BIN/cekmecon" >/dev/null 2>&1 & )
case ":$PATH:" in *":$BIN:"*) ;; *) echo "  Note: add $BIN to your PATH to use the cekmecon command.";; esac
echo "✓ Done. Çekmecón is open. Start Claude Code in any project; the first time, click “Permitir siempre”."
