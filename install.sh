#!/usr/bin/env bash
# vinyasa's installer: varna (the theme engine it drives) first, then
# vinyasa into ~/.local/share/vinyasa (its newest release), linked as
# ~/.local/bin/vinyasa, with a desktop entry. No root.
#
#   curl -fsSL https://raw.githubusercontent.com/Theyashsawarkar/vinyasa/main/install.sh | bash
set -euo pipefail
dest="${XDG_DATA_HOME:-$HOME/.local/share}/vinyasa"
bin="$HOME/.local/bin"
command -v git >/dev/null || { echo "vinyasa needs git" >&2; exit 1; }
python3 -c 'import sys, gi; gi.require_version("Gtk", "4.0"); from gi.repository import Gtk; sys.exit(sys.version_info < (3, 11))' 2>/dev/null ||
  { echo "vinyasa needs Python 3.11+ with GTK 4 (python-gobject, gtk4)" >&2; exit 1; }
command -v varna >/dev/null || curl -fsSL https://raw.githubusercontent.com/Theyashsawarkar/varna/main/install.sh | bash
if [ -d "$dest/.git" ]; then
  git -C "$dest" fetch -q --tags origin
else
  git clone -q https://github.com/Theyashsawarkar/vinyasa "$dest"
fi
latest=$(git -C "$dest" tag -l 'v*' --sort=-v:refname | head -1)
[ -n "$latest" ] && git -C "$dest" -c advice.detachedHead=false checkout -q "$latest"
mkdir -p "$bin" "${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ln -sfn "$dest/bin/vinyasa" "$bin/vinyasa"
ln -sfn "$dest/data/dev.vayu.Vinyasa.desktop" "${XDG_DATA_HOME:-$HOME/.local/share}/applications/dev.vayu.Vinyasa.desktop"
echo "vinyasa ${latest:-(main)} installed: $bin/vinyasa"
