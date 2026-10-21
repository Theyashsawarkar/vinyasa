# 4. Keyboard first, with vim keys

**Status:** Accepted  
**Date:** 2026-10-21

## Context

Vayu is driven from the keyboard. A settings app usually isn't: sidebars and grids expect the mouse.

## Decision

A capture-phase key handler on the window: `j`/`k` move through pages in the sidebar and by rows in a grid of cards (else to the next control), `h`/`l` switch between sidebar and page, `gg`/`G`, `/` searches every setting including theme and tool names, `Enter`/`Space` pick a card, `?` lists the keys, `q`/`Esc` quit. Typing into a text field is never intercepted.

## Consequences

- Every key is annotated for Vayu's keybinding search and documented in the README and the `?` overlay.
- Mouse use works as in any GTK app.
