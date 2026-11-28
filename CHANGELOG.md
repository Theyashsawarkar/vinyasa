# Changelog

Newest first. Releases are tags (`vX.Y.Z`) with `VERSION` in `vinyasa/__init__.py`.

## Unreleased

- Website: pranali joins the family list in the footer; the site builder passes ruff.
- The website, closer to Vayu's own: the tool's screenshot blurred behind the page, a centred hero with the logo and the verse, the page you're on as the white pill, glass "On this page" and footer panels, releases as cards. No glow behind the logo, no coloured line beside the verse.
- **Spatial look**: rounder cards and controls; the selected page is brighter glass with a light rim, not a left bar; the chosen theme's name stays in the text colour (GTK drew it in its own accent); segmented buttons are pills.
- The website has Vayu's Spatial look: graphite glass, a floating navigation bar, near-white for links and the main button, and the tool's own colour only as its signature (the logo's glow, the shloka's line, the release dots). No more all-caps labels.

## v0.2.0 -- 2026-11-09

- Every corner is rounded: the website's callouts.
- A logo and a shloka at the top of the README and the website: every Vayu tool has them now.
- Vim keys, modal, the Space grammar every Vayu tool shares. Settings open
  in **normal** mode: typing changes nothing (a form opens read-only), and a
  focused number or text field only takes typing after `i` (or a click);
  `Esc` goes back. The mode shows under the app's name.
- `h` / `l` turn the focused value down / up with counts (`5l`): sliders,
  number fields, menus, switches, the Dark/Light pair and the grids of cards.
  No arrow keys needed.
- `H` / `L` previous / next page; `gg` / `G` and `Ctrl+d` / `Ctrl+u` inside
  a page too; `r` reloads every page from varna.
- `Space` is the leader (it no longer presses the focused button: `Enter`
  does), with a which-key strip after 0.3 s: `Space t` pages, `Space a a` a
  theme of your own, `Space e e` the editor, `Space d d` deletes your theme
  (asks; only `y` says yes), `Space o e` / `o f` open varna's config / your
  themes folder, `Space u f` fullscreen, `Space Space` a palette of every
  action and page.
- The setting row the keys act on is marked like the sidebar's page.
- `?` lists every key from the same table; the keys are data (`BINDS` in
  `vinyasa/app.py`) resolved by Vyom's keys module (vendored as
  `vinyasa/keys.py`), and `scripts/keybinds.py` writes the `# keybind:` lines
  (tests check them).
- Fixed: the theme editor's Delete button deleted at once, so `Enter` on it
  threw a theme away; it asks now, like `Space d d` (only `y` says yes).
  CI's "every key is in the README" check matched no lines after the
  annotations gained `:normal`, so it passed without checking.

## v0.1.1 -- 2026-10-24

- **The same glass as Vyom's panels.** The window's background is varna's
  `ui.glass` (varna 0.1.9), shared by Vyom, nāda and the notifications, so
  it looks like the rest of the desktop. It used `ui.opacity` (0.85, the
  terminal's), which made it a nearly solid slab next to them. Never under
  0.4, so the settings stay easy to read.

## v0.1.0 -- 2026-10-21

The first release: Vayu's settings app, starting with how it looks.

- **Theme**: a card per theme with a tiny desktop drawn in its colours; the
  accent colour; the dark/light twin; terminal transparency; GTK apps on or off.
- **Theme editor**: start from any theme, change its 26 colours and its
  accents with a live preview, save it as your own, delete it.
- **Fonts**, **Wallpaper** (pick one, daily wallpaper on/off, fetch today's)
  and **Windows & gaps** (gaps, border width, corner radius).
- **Tools**: give any tool its own theme or switch it off; tools whose
  config doesn't include varna are marked.
- **About**: versions, re-apply everywhere, every tool's status.
- Every change applies at once through varna, in the background, and the
  window restyles itself to match. A search box finds any setting (theme and
  tool names too); vim keys (`j`/`k`, `h`/`l`, `gg`/`G`, `/`, `?`, `q`).
