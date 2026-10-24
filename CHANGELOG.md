# Changelog

Newest first. Releases are tags (`vX.Y.Z`) with `VERSION` in `vinyasa/__init__.py`.

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
