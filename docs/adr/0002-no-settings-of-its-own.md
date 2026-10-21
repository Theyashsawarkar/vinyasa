# 2. vinyasa holds no settings of its own

**Status:** Accepted  
**Date:** 2026-10-21

## Context

A settings app can keep its own database of preferences and push them to tools, or read and write each tool's own setting. Its own database drifts from reality the moment anything else changes a setting: `varna apply` from a terminal, kendra's theme tile, editing a config by hand.

## Decision

Every page reads the setting from the tool that owns it each time it's shown, and writes it back there: themes, accents, fonts, gaps and per-tool picks through varna's `core` (the same code `varna` runs), the wallpaper through `current.jpg` and `wallpaper.timer`, fonts through GTK's settings as well.

## Consequences

- The command line, panels and the app always agree; there's nothing to sync.
- A page for a new area means finding that area's owner (NetworkManager, PipeWire, sway outputs...), not inventing a format.
