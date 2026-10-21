# 3. Plain GTK 4, styled by the theme, not libadwaita

**Status:** Accepted  
**Date:** 2026-10-21

## Context

A settings window needs real controls: colour and font pickers, sliders, image thumbnails, live previews. A terminal UI can't show them; a web view is heavy. GTK 4 is already on the system (nāda uses it). libadwaita would bring GNOME's look and its own colour handling.

## Decision

Plain GTK 4 through PyGObject. The app's CSS is generated from the theme varna resolves for it (its own pick under Tools, or the desktop's), and reloaded after every change, so the window always looks like the desktop it configures.

## Consequences

- Picking a theme recolours the settings window along with everything else.
- vinyasa draws its own pieces libadwaita would give (rows, toasts, a segmented control).
