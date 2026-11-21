#!/usr/bin/env bash
# Install the downloaded Çekmecón for your user: ~/.local/bin/cekmecon + an applications-menu entry. No sudo.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DEST="${XDG_DATA_HOME:-$HOME/.local/share}/cekmecon"
mkdir -p "$DEST" "$HOME/.local/bin" "$HOME/.local/share/applications"
install -m 755 "$HERE/cekmecon" "$DEST/cekmecon"
install -m 644 "$HERE/icon.png" "$DEST/icon.png"
ln -sf "$DEST/cekmecon" "$HOME/.local/bin/cekmecon"
cat > "$HOME/.local/share/applications/cekmecon.desktop" <<DESK
[Desktop Entry]
Type=Application
Name=Çekmecón
Comment=Toilet Bamboo Paper Çekmecón — Claude's memory drawer
Exec=$DEST/cekmecon
Icon=$DEST/icon.png
Categories=Office;Development;
Terminal=false
DESK
echo "✓ Installed. Open “Çekmecón” from your applications menu (or run: cekmecon)."
( "$DEST/cekmecon" >/dev/null 2>&1 & )
