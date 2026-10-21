"""Small building blocks: a settings row, a page header, theme previews."""
import math

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gtk  # noqa: E402


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def to_rgba(h):
    c = Gdk.RGBA()
    c.parse(h if h.startswith("#") else "#" + h)
    return c


def from_rgba(c):
    return "#" + "".join(f"{round(v * 255):02x}" for v in (c.red, c.green, c.blue))


def page_header(title, subtitle):
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    t = Gtk.Label(label=title, xalign=0)
    t.add_css_class("page-title")
    s = Gtk.Label(label=subtitle, xalign=0, wrap=True)
    s.add_css_class("page-subtitle")
    box.append(t)
    box.append(s)
    return box


def section(title):
    lbl = Gtk.Label(label=title, xalign=0)
    lbl.add_css_class("section")
    return lbl


def row(title, subtitle=None, widget=None):
    """A settings row: title and explanation on the left, the control on the right."""
    box = Gtk.Box(spacing=14)
    box.add_css_class("setting")
    text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1, hexpand=True, valign=Gtk.Align.CENTER)
    t = Gtk.Label(label=title, xalign=0)
    t.add_css_class("setting-title")
    text.append(t)
    if subtitle:
        s = Gtk.Label(label=subtitle, xalign=0, wrap=True)
        s.add_css_class("setting-subtitle")
        text.append(s)
    box.append(text)
    if widget is not None:
        widget.set_valign(Gtk.Align.CENTER)
        box.append(widget)
    return box


def rounded(cr, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    cr.close_path()


def draw_desktop(cr, w, h, c):
    """A tiny desktop in a theme's colours: bar, active workspace, a focused
    window with a tmux bar, and a second window. c = {name: '#rrggbb'}."""
    import cairo
    g = cairo.LinearGradient(0, 0, w, h)
    g.add_color_stop_rgb(0, *rgb(c["surface0"]))
    g.add_color_stop_rgb(0.6, *rgb(c["crust"]))
    g.add_color_stop_rgb(1, *rgb(c["mantle"]))
    rounded(cr, 0, 0, w, h, 10)
    cr.set_source(g)
    cr.fill()
    pad = max(4, w * 0.04)
    bar_h = max(6, h * 0.12)
    # bar: workspace capsule with the accent, a clock capsule
    cr.set_source_rgb(*rgb(c["base"]))
    rounded(cr, pad, pad, w * 0.34, bar_h, bar_h / 2)
    cr.fill()
    cr.set_source_rgb(*rgb(c["accent"]))
    rounded(cr, pad + 2, pad + 2, bar_h - 4 + w * 0.04, bar_h - 4, (bar_h - 4) / 2)
    cr.fill()
    cr.set_source_rgb(*rgb(c["base"]))
    rounded(cr, w * 0.42, pad, w * 0.18, bar_h, bar_h / 2)
    cr.fill()
    # windows
    top = pad * 2 + bar_h
    wh = h - top - pad
    ww = (w - pad * 3) * 0.6
    for x, width, focus in ((pad, ww, True), (pad * 2 + ww, w - pad * 3 - ww, False)):
        cr.set_source_rgb(*rgb(c["base"]))
        rounded(cr, x, top, width, wh, 6)
        cr.fill_preserve()
        cr.set_source_rgb(*rgb(c["border"] if focus else c["surface1"]))
        cr.set_line_width(1.6 if focus else 1)
        cr.stroke()
    # text lines in the focused window
    lh = max(2, wh * 0.06)
    for i, key in enumerate(("accent", "text", "green", "subtext0")):
        cr.set_source_rgb(*rgb(c[key]))
        rounded(cr, pad + 6, top + 6 + i * lh * 1.9, ww * (0.7 - i * 0.12), lh, lh / 2)
        cr.fill()
    # tmux bar: session (accent), window (accent), idle window
    ty = top + wh - lh * 2.6
    for i, key in enumerate(("accent", "accent", "surface1")):
        cr.set_source_rgb(*rgb(c[key]))
        rounded(cr, pad + 6 + i * ww * 0.2, ty, ww * 0.17, lh * 1.6, lh * 0.8)
        cr.fill()
    # palette dots in the second window
    keys = ("red", "peach", "yellow", "green", "blue", "mauve")
    x2 = pad * 2 + ww
    dot = min((w - pad * 3 - ww - 12) / len(keys), wh * 0.16)
    for i, key in enumerate(keys):
        cr.set_source_rgb(*rgb(c[key]))
        cr.arc(x2 + 6 + dot / 2 + i * dot, top + 6 + dot / 2, dot * 0.38, 0, 2 * math.pi)
        cr.fill()


class Preview(Gtk.DrawingArea):
    """A desktop preview that redraws when its colours change."""

    def __init__(self, colors, width=168, height=96):
        super().__init__(content_width=width, content_height=height)
        self.colors = colors
        self.set_draw_func(lambda _a, cr, w, h: draw_desktop(cr, w, h, self.colors))

    def set_colors(self, colors):
        self.colors = colors
        self.queue_draw()


def swatch_button(color, tooltip, size=26):
    """A round colour button."""
    b = Gtk.Button(tooltip_text=tooltip)
    b.add_css_class("swatch")
    area = Gtk.DrawingArea(content_width=size, content_height=size)

    def draw(_a, cr, w, h):
        cr.set_source_rgb(*rgb(b.color))
        cr.arc(w / 2, h / 2, min(w, h) / 2 - 1, 0, 2 * math.pi)
        cr.fill()
        if b.selected:
            cr.set_source_rgb(1, 1, 1)
            cr.set_line_width(2)
            cr.arc(w / 2, h / 2, min(w, h) / 2 - 3, 0, 2 * math.pi)
            cr.stroke()
    b.color, b.selected = color, False
    area.set_draw_func(draw)
    b.set_child(area)
    b.area = area
    return b
