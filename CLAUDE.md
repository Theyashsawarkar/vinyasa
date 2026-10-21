# vinyasa -- notes for agents

Vayu's settings app (GTK 4, Python): a page per area, driving varna (the
theme engine) and the tools that own each setting. Its own repo, pulled into
Vayu (github.com/Theyashsawarkar/vayu, whose CLAUDE.md "Plugins" rules
apply); it must work without Vayu (needs varna).

- `vinyasa/app.py` window, sidebar, search, keys, CSS; `vinyasa/pages.py`
  pages; `vinyasa/widgets.py` rows and previews; `vinyasa/bridge.py` finds varna.
- **Test with a throwaway HOME** (`HOME=$(mktemp -d) VARNA_HOME=~/personal/varna
  bin/vinyasa`) in a headless sway, never against the user's session; varna
  won't reload the desktop from a throwaway HOME.
- Keys: `# keybind: Vinyasa/settings | <keys> | <Verb> <object>` lines in app.py,
  `KEYS` (the ? overlay) and the README must agree; in Vayu run
  `~/.local/bin/keybind-search.py --check`.
- Slow work in threads, UI updates through GLib.idle_add.
- `ruff check .` and `python -m unittest discover -s tests` must pass.
- Every change: a CHANGELOG.md entry; releases are tags with `VERSION` bumped.
- The website (docs/, GitHub Pages) is generated: after changing README.md, CHANGELOG.md or docs/adr/, run `python3 scripts/build-site.py` and commit docs/ (CI checks it). A significant design decision gets a new ADR in docs/adr/ (next number; supersede, never rewrite).
