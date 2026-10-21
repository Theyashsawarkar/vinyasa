# Contributing to vinyasa

Thanks for helping. New pages, fixes and ideas are welcome.

## Development setup

```sh
git clone https://github.com/Theyashsawarkar/varna ~/code/varna
git clone https://github.com/Theyashsawarkar/vinyasa ~/code/vinyasa
cd ~/code/vinyasa
ruff check .
VARNA_HOME=~/code/varna python -m unittest discover -s tests -v
HOME=$(mktemp -d) VARNA_HOME=~/code/varna bin/vinyasa   # try it without touching your desktop's theme
```

`VINYASA_DEBUG=1` prints every key the window sees.

## How it fits together

- `vinyasa/app.py`: the window, sidebar, search, keys, toast and the app's own CSS.
- `vinyasa/pages.py`: one class per page (`title`, `group`, `keywords`, `build()`, `refresh()`).
- `vinyasa/widgets.py`: settings rows, theme previews, swatches.
- `vinyasa/bridge.py`: finds varna.

## Rules

- **No settings of its own**: a page reads and writes the tool that owns the
  setting (varna for themes, systemd for the wallpaper timer...).
- **Never block the window**: anything slow runs in a thread, then
  `GLib.idle_add` updates the UI.
- **Keys**: every key has a `# keybind: Vinyasa/settings | <keys> | <Verb> <object>`
  line in `app.py`, a row in `KEYS` (the `?` overlay) and in the README.
- **Test with a throwaway HOME**, never by changing your own desktop from a test.
- Every change gets a `CHANGELOG.md` entry; releases are tags with `VERSION`
  bumped; the website is generated (`python3 scripts/build-site.py`).

## Pull requests

Describe what and why, and tick the template's checklist. By contributing
you agree your work is released under the [MIT License](LICENSE).
