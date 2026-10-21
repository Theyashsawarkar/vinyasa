# Security policy

## Supported versions

Only the latest release of vinyasa gets fixes.

## Reporting a vulnerability

Please **don't open a public issue**. Report it privately through
[GitHub's security advisories](https://github.com/Theyashsawarkar/vinyasa/security/advisories/new),
with what an attacker could do and how to reproduce it. You'll get a reply
within a week.

## What vinyasa does

vinyasa runs as your user. It changes settings through varna (files under
`~/.config/varna` and `~/.local/state/varna`), copies the wallpaper you pick
to `~/Pictures/Wallpapers/current.jpg`, enables or disables your
`wallpaper.timer`, and sets GTK's font settings. It makes no network
requests itself ("Get today's now" runs your `fetch_wallpaper.sh`).
