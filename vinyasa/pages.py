"""The settings pages. Each has a title, an icon, search keywords, a widget
and refresh(); changes go through varna (app.core) and apply right away."""
import glob
import os
import shutil
import subprocess

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, GdkPixbuf, GLib, Gtk, Pango  # noqa: E402

from .widgets import Preview, from_rgba, page_header, row, section, swatch_button, to_rgba  # noqa: E402

ACCENTS = ["mauve", "pink", "red", "maroon", "peach", "yellow", "green", "teal", "sky", "sapphire", "blue", "lavender"]


class Page:
    title = icon = ""
    keywords = ""
    group = ""

    def __init__(self, app):
        self.app = app
        self.core = app.core
        self.body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.body.add_css_class("page")
        self.widget = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, child=self.body)
        self.build()

    def build(self):
        pass

    def refresh(self):
        pass

    def search_text(self):
        """What the sidebar search matches: the title, the keywords, and whatever the page lists."""
        return f"{self.title} {self.keywords}"

    def add(self, w):
        self.body.append(w)
        return w


# ===================================================================== theme
class ThemePage(Page):
    title, icon, group = "Theme", "◐", "Appearance"
    keywords = "theme colours colors palette accent dark light mode transparency opacity gtk apps"

    def build(self):
        self.add(page_header("Theme", "The whole desktop follows it: bar, windows, tmux, terminal, editor, panels, "
                                      "notifications. A tool can pick its own under Tools."))
        self.flow = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.SINGLE, max_children_per_line=8, min_children_per_line=1,
                                column_spacing=12, row_spacing=12, homogeneous=True, activate_on_single_click=True,
                                halign=Gtk.Align.START)
        self.flow.add_css_class("themes")
        self.flow.connect("child-activated", self.on_theme)
        self.add(self.flow)
        self.add(section("Accent"))
        self.accents = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, max_children_per_line=13, column_spacing=4)
        default = Gtk.Button(label="theme's own")
        default.add_css_class("pill")
        default.connect("clicked", lambda _b: self.set_accent(None))
        self.accent_default = default
        box = Gtk.Box(spacing=8)
        box.append(self.accents)
        box.append(default)
        self.add(row("Accent colour", "The active workspace, the focused window, tmux's session and window, selections.", box))
        self.add(section("More"))
        modes = Gtk.Box(spacing=0)
        modes.add_css_class("segmented")
        self.dark = Gtk.ToggleButton(label="Dark")
        self.light = Gtk.ToggleButton(label="Light", group=self.dark)
        for b, m in ((self.dark, "dark"), (self.light, "light")):
            b.connect("toggled", lambda btn, m=m: btn.get_active() and not self.app.busy_refresh and self.set_mode(m))
            modes.append(b)
        self.mode_row = self.add(row("Mode", "Themes with a light twin switch to it (Catppuccin Mocha ⇄ Latte, Rosé Pine ⇄ Dawn).", modes))
        self.opacity = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.4, 1.0, 0.01)
        self.opacity.set_size_request(220, -1)
        self.opacity.set_draw_value(True)
        self.opacity.set_digits(2)
        self.opacity.connect("value-changed", self.on_opacity)
        self._opacity_timer = None
        self.add(row("Terminal transparency", "How much of the blurred desktop shows through kitty.", self.opacity))
        self.gtk = Gtk.Switch()
        self.gtk.connect("notify::active", self.on_gtk)
        self.add(row("Theme GTK apps too", "Writes the theme into GTK 3/4 apps' colours (file managers, settings dialogs...). "
                                           "The dark/light signal is always sent.", self.gtk))

    def refresh(self):
        conf = self.app.conf()
        while (c := self.flow.get_first_child()):
            self.flow.remove(c)
        self.cards = {}
        for tid, t in self.core.themes():
            if isinstance(t, Exception):
                continue
            ctx, _ = self.core.resolve({"theme": tid})
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, width_request=190)
            card.add_css_class("theme-card")
            card.append(Preview(ctx))
            name = Gtk.Label(label=t["meta"]["name"], xalign=0, ellipsize=Pango.EllipsizeMode.END, max_width_chars=18)
            name.add_css_class("card-title")
            sub = Gtk.Label(label=t["meta"].get("description", t["meta"]["variant"]) + ("  · yours" if t["user"] else ""),
                            xalign=0, ellipsize=Pango.EllipsizeMode.END, max_width_chars=24)
            sub.add_css_class("card-sub")
            card.append(name)
            card.append(sub)
            child = Gtk.FlowBoxChild(child=card)
            child.tid = tid
            self.flow.append(child)
            self.cards[tid] = child
            if tid == conf["theme"]:
                self.flow.select_child(child)
        ctx, t = self.core.resolve(conf)
        while (c := self.accents.get_first_child()):
            self.accents.remove(c)
        for key in ACCENTS:
            b = swatch_button(ctx[key], key)
            b.selected = ctx["accent"] == ctx[key] and bool(conf.get("accent"))
            b.connect("clicked", lambda _b, k=key: self.set_accent(k))
            self.accents.append(b)
        self.accent_default.set_sensitive(bool(conf.get("accent")))
        self.app.busy_refresh = True
        variant = t["meta"]["variant"]
        (self.dark if variant == "dark" else self.light).set_active(True)
        self.dark.set_sensitive(bool(self.core.twin(t, "dark")))
        self.light.set_sensitive(bool(self.core.twin(t, "light")))
        self.opacity.set_value(float(ctx["opacity"]))
        self.gtk.set_active(bool(conf.get("gtk")))
        self.app.busy_refresh = False

    def search_text(self):
        names = " ".join(f"{tid} {t['meta']['name']}" for tid, t in self.core.themes() if not isinstance(t, Exception))
        return f"{self.title} {self.keywords} {names}"

    def on_theme(self, _flow, child):
        conf = self.app.conf()
        if child.tid == conf["theme"]:
            return
        conf["theme"] = child.tid
        conf.pop("accent", None)
        self.core.save_config(conf)
        name = self.core.load_theme(child.tid)["meta"]["name"]
        self.app.apply(None, f"{name} applied")

    def set_accent(self, key):
        self.core.set_value("accent", key or "default")
        self.app.apply(None, f"accent: {key}" if key else "the theme's own accent")

    def set_mode(self, mode):
        try:
            tid = self.core.set_mode(mode)
        except self.core.VarnaError as e:
            self.app.toast(str(e), "err")
            return
        self.app.apply(None, f"{self.core.load_theme(tid)['meta']['name']} applied")

    def on_opacity(self, scale):
        if self.app.busy_refresh:
            return
        if self._opacity_timer:
            GLib.source_remove(self._opacity_timer)

        def commit():
            self._opacity_timer = None
            self.core.set_value("ui.opacity", f"{scale.get_value():.2f}")
            self.app.apply({"kitty", "apps"}, f"transparency {scale.get_value():.2f}", refresh=False)
            return False
        self._opacity_timer = GLib.timeout_add(450, commit)

    def on_gtk(self, sw, _p):
        if self.app.busy_refresh:
            return
        self.core.set_value("gtk", "on" if sw.get_active() else "off")
        self.app.apply({"gtk", "apps"}, "GTK apps follow the theme" if sw.get_active() else "GTK apps keep their own theme")


# ===================================================================== editor
class EditorPage(Page):
    title, icon, group = "Theme editor", "✎", "Appearance"
    keywords = "theme editor custom own make create colour palette new save"

    def build(self):
        self.add(page_header("Theme editor", "Make a theme of your own: start from any theme, change its colours, "
                                             "save it under a name. Saved themes live in ~/.config/varna/themes."))
        top = Gtk.Box(spacing=8)
        self.pick = Gtk.DropDown.new_from_strings([])
        self.pick.connect("notify::selected", lambda *_: not self.app.busy_refresh and self.load_selected())
        self.name = Gtk.Entry(placeholder_text="Name for your theme", hexpand=True)
        self.variant = Gtk.DropDown.new_from_strings(["dark", "light"])
        save_new = Gtk.Button(label="Save as new")
        save_new.add_css_class("suggested")
        save_new.connect("clicked", lambda _b: self.save(new=True))
        self.save_btn = Gtk.Button(label="Save")
        self.save_btn.connect("clicked", lambda _b: self.save(new=False))
        self.del_btn = Gtk.Button(label="Delete")
        self.del_btn.add_css_class("destructive")
        self.del_btn.connect("clicked", lambda _b: self.delete())
        for w in (Gtk.Label(label="Start from"), self.pick, self.name, self.variant, save_new, self.save_btn, self.del_btn):
            top.append(w)
        self.add(top)
        body = Gtk.Box(spacing=18)
        grid = Gtk.Grid(column_spacing=10, row_spacing=6)
        self.buttons = {}
        for i, key in enumerate(self.core.PALETTE_KEYS):
            lbl = Gtk.Label(label=key, xalign=0)
            lbl.add_css_class("setting-subtitle")
            btn = Gtk.ColorDialogButton(dialog=Gtk.ColorDialog(with_alpha=False))
            btn.connect("notify::rgba", lambda *_: self.update_preview())
            self.buttons[key] = btn
            grid.attach(lbl, (i % 3) * 2, i // 3, 1, 1)
            grid.attach(btn, (i % 3) * 2 + 1, i // 3, 1, 1)
        body.append(grid)
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.preview = Preview({}, 300, 180)
        right.append(self.preview)
        self.roles = {}
        for role, text in (("accent", "Accent"), ("accent2", "Second accent (borders)"), ("border", "Focused window border")):
            dd = Gtk.DropDown.new_from_strings(self.core.PALETTE_KEYS)
            dd.connect("notify::selected", lambda *_: self.update_preview())
            self.roles[role] = dd
            right.append(row(text, None, dd))
        body.append(right)
        self.add(body)

    def refresh(self):
        self.app.busy_refresh = True
        self.ids = [tid for tid, t in self.core.themes() if not isinstance(t, Exception)]
        names = [self.core.load_theme(t)["meta"]["name"] + ("  (yours)" if self.core.load_theme(t)["user"] else "") for t in self.ids]
        self.pick.set_model(Gtk.StringList.new(names))
        cur = self.app.conf()["theme"]
        self.pick.set_selected(self.ids.index(cur) if cur in self.ids else 0)
        self.app.busy_refresh = False
        self.load_selected()

    def load_selected(self):
        tid = self.ids[self.pick.get_selected()]
        t = self.core.load_theme(tid)
        self.source = t
        self.app.busy_refresh = True
        for key, btn in self.buttons.items():
            btn.set_rgba(to_rgba(t["palette"][key]))
        roles = dict(self.core.ROLE_DEFAULTS, **(t.get("roles") or {}))
        self.role_options = {}
        for role, dd in self.roles.items():
            v, seen = roles[role], set()
            while v in roles and v not in seen and v not in self.core.PALETTE_KEYS:   # border -> accent -> mauve
                seen.add(v)
                v = roles[v]
            opts = list(self.core.PALETTE_KEYS)
            if self.core.is_hex(v):   # a colour of its own, not a palette name
                opts.append(v)
            self.role_options[role] = opts
            dd.set_model(Gtk.StringList.new([o if not self.core.is_hex(o) else f"custom {o}" for o in opts]))
            dd.set_selected(opts.index(v) if v in opts else 0)
        self.variant.set_selected(0 if t["meta"]["variant"] == "dark" else 1)
        self.name.set_text(t["meta"]["name"] if t["user"] else "")
        self.save_btn.set_sensitive(t["user"])
        self.del_btn.set_sensitive(t["user"])
        self.app.busy_refresh = False
        self.update_preview()

    def edited(self):
        pal = {k: from_rgba(b.get_rgba()) for k, b in self.buttons.items()}
        roles = dict(self.source.get("roles") or {})
        for role, dd in self.roles.items():
            roles[role] = self.role_options[role][dd.get_selected()]
        return pal, roles

    def update_preview(self):
        if self.app.busy_refresh or not hasattr(self, "source"):
            return
        pal, roles = self.edited()
        c = dict(pal)
        for role in ("accent", "accent2", "border"):
            c[role] = roles[role] if self.core.is_hex(roles[role]) else pal[roles[role]]
        self.preview.set_colors(c)

    def save(self, new):
        pal, roles = self.edited()
        name = self.name.get_text().strip() or (self.source["meta"]["name"] + " (mine)")
        meta = {"name": name, "variant": ["dark", "light"][self.variant.get_selected()]}
        theme = {"meta": meta, "palette": pal, "roles": roles}
        for k in ("ui", "tools"):
            if self.source.get(k):
                theme[k] = self.source[k]
        try:
            tid = self.core.slug(name) if new else self.source["id"]
            if new and tid in self.core.theme_paths() and not self.core.theme_paths()[tid].startswith(self.core.USER_THEMES):
                tid += "-custom"
            self.core.write_theme(tid, theme)
        except self.core.VarnaError as e:
            self.app.toast(str(e), "err")
            return
        conf = self.app.conf()
        in_use = conf["theme"] == tid or tid in [p if isinstance(p, str) else (p or {}).get("theme") for p in conf["tools"].values()]
        self.app.refresh_all()
        self.pick.set_selected(self.ids.index(tid))
        if in_use:
            self.app.apply(None, f"saved and applied {name}")
        else:
            self.app.toast(f"saved {name}: pick it under Theme to use it")

    def delete(self):
        tid = self.source["id"]
        if self.app.conf()["theme"] == tid:
            self.app.toast("that's the desktop's theme: pick another under Theme first", "err")
            return
        try:
            self.core.delete_theme(tid)
        except self.core.VarnaError as e:
            self.app.toast(str(e), "err")
            return
        self.app.refresh_all()
        self.app.toast(f"deleted {self.source['meta']['name']}")


# ===================================================================== fonts
class FontsPage(Page):
    title, icon, group = "Fonts", "A", "Appearance"
    keywords = "fonts font typeface size monospace terminal interface"

    def build(self):
        self.add(page_header("Fonts", "The interface font (GTK apps) and the monospace font (the terminal)."))
        self.ui_font = Gtk.FontDialogButton(dialog=Gtk.FontDialog(), level=Gtk.FontLevel.FAMILY)
        self.mono_font = Gtk.FontDialogButton(dialog=Gtk.FontDialog(), level=Gtk.FontLevel.FAMILY)
        self.size = Gtk.SpinButton.new_with_range(7, 24, 1)
        self.mono_size = Gtk.SpinButton.new_with_range(7, 28, 1)
        self.add(row("Interface font", "GTK apps and dialogs.", self.ui_font))
        self.add(row("Interface size", None, self.size))
        self.add(row("Monospace font", "kitty and other terminals.", self.mono_font))
        self.add(row("Monospace size", None, self.mono_size))
        for w, sig in ((self.ui_font, "notify::font-desc"), (self.mono_font, "notify::font-desc"),
                       (self.size, "value-changed"), (self.mono_size, "value-changed")):
            w.connect(sig, lambda *_: self.changed())
        self._timer = None

    def refresh(self):
        ctx, _ = self.core.resolve(self.app.conf())
        self.app.busy_refresh = True
        self.ui_font.set_font_desc(Pango.FontDescription.from_string(ctx["font"]))
        self.mono_font.set_font_desc(Pango.FontDescription.from_string(ctx["mono"]))
        self.size.set_value(int(ctx["size"]))
        self.mono_size.set_value(int(ctx["mono_size"]))
        self.app.busy_refresh = False

    def changed(self):
        if self.app.busy_refresh:
            return
        if self._timer:
            GLib.source_remove(self._timer)
        self._timer = GLib.timeout_add(500, self.commit)

    def commit(self):
        self._timer = None
        fam = (self.ui_font.get_font_desc().get_family() or "Inter")
        mono = (self.mono_font.get_font_desc().get_family() or "monospace")
        for k, v in (("ui.font", fam), ("ui.mono", mono), ("ui.size", str(int(self.size.get_value()))),
                     ("ui.mono_size", str(int(self.mono_size.get_value())))):
            self.core.set_value(k, v)
        if shutil.which("gsettings"):
            subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "font-name", f"{fam} {int(self.size.get_value())}"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "monospace-font-name",
                            f"{mono} {int(self.mono_size.get_value())}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.app.apply({"kitty", "apps"}, f"fonts: {fam}, {mono}", refresh=False)
        return False


# ===================================================================== wallpaper
WALL_DIR = os.path.expanduser("~/Pictures/Wallpapers")


def wallpapers():
    """Every image under ~/Pictures/Wallpapers except current.jpg, newest first."""
    files = []
    for ext in ("jpg", "jpeg", "png", "webp"):
        files += glob.glob(os.path.join(WALL_DIR, "**", f"*.{ext}"), recursive=True)
    files = [f for f in files if os.path.basename(f) != "current.jpg"]
    return sorted(set(files), key=os.path.getmtime, reverse=True)


class WallpaperPage(Page):
    title, icon, group = "Wallpaper", "▣", "Appearance"
    keywords = "wallpaper background image picture daily bing"

    def build(self):
        self.add(page_header("Wallpaper", f"Pick one from {WALL_DIR.replace(os.path.expanduser('~'), '~')}, or get a new one every day."))
        self.daily = Gtk.Switch()
        self.daily.connect("notify::active", self.on_daily)
        fetch = Gtk.Button(label="Get today's now")
        fetch.connect("clicked", self.on_fetch)
        self.add(row("A new wallpaper every day", "Bing's picture of the day (wallpaper.timer).", self.daily))
        self.add(row("Today's wallpaper", None, fetch))
        self.flow = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.SINGLE, max_children_per_line=8, min_children_per_line=1,
                                column_spacing=10, row_spacing=10, homogeneous=True, activate_on_single_click=True,
                                halign=Gtk.Align.START)
        self.flow.connect("child-activated", self.on_pick)
        self.add(self.flow)
        self.loaded = False

    def refresh(self):
        r = subprocess.run(["systemctl", "--user", "is-enabled", "wallpaper.timer"], capture_output=True, text=True)
        self.app.busy_refresh = True
        self.daily.set_active(r.stdout.strip() == "enabled")
        self.app.busy_refresh = False
        if not self.loaded:
            self.loaded = True
            self.load_thumbs()

    def load_thumbs(self):
        files = wallpapers()[:60]
        for f in files:
            pic = Gtk.Picture(content_fit=Gtk.ContentFit.COVER, can_shrink=True)
            pic.set_size_request(200, 112)
            pic.add_css_class("thumb")
            child = Gtk.FlowBoxChild(child=pic)
            child.path = f
            child.set_tooltip_text(os.path.basename(f))
            self.flow.append(child)
        import threading

        def work():
            for child in list(self._children()):
                try:
                    pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(child.path, 400, 225, True)
                except GLib.Error:
                    continue
                GLib.idle_add(lambda c=child, p=pb: c.get_child().set_paintable(Gdk.Texture.new_for_pixbuf(p)) and False)
        threading.Thread(target=work, daemon=True).start()

    def _children(self):
        c = self.flow.get_first_child()
        while c:
            yield c
            c = c.get_next_sibling()

    def on_pick(self, _flow, child):
        cur = os.path.join(WALL_DIR, "current.jpg")
        try:
            shutil.copy2(child.path, cur + ".tmp")
            os.replace(cur + ".tmp", cur)
        except OSError as e:
            self.app.toast(f"couldn't set it: {e}", "err")
            return
        subprocess.run(["swaymsg", f"output * bg '{cur}' fill"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.app.toast(f"wallpaper: {os.path.basename(child.path)}")

    def on_daily(self, sw, _p):
        if self.app.busy_refresh:
            return
        verb = "enable" if sw.get_active() else "disable"
        subprocess.run(["systemctl", "--user", verb, "--now", "wallpaper.timer"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.app.toast("a new wallpaper every day" if sw.get_active() else "the wallpaper stays as it is")

    def on_fetch(self, _b):
        script = os.path.expanduser("~/.local/bin/fetch_wallpaper.sh")
        if not os.access(script, os.X_OK):
            self.app.toast("no fetch_wallpaper.sh here", "err")
            return
        subprocess.Popen([script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        self.app.toast("fetching today's wallpaper…")


# ===================================================================== windows
class WindowsPage(Page):
    title, icon, group = "Windows & gaps", "⊞", "Appearance"
    keywords = "windows gaps border width corner radius rounding sway"

    def build(self):
        self.add(page_header("Windows & gaps", "Space around windows, their borders and rounded corners (sway)."))
        self.gaps = Gtk.SpinButton.new_with_range(0, 48, 1)
        self.border = Gtk.SpinButton.new_with_range(0, 12, 1)
        self.radius = Gtk.SpinButton.new_with_range(0, 32, 1)
        self.add(row("Gaps", "Pixels between windows and around the screen edge.", self.gaps))
        self.add(row("Border width", "The focused window's border takes the theme's border colour.", self.border))
        self.add(row("Corner radius", "Rounded corners (SwayFX).", self.radius))
        for w in (self.gaps, self.border, self.radius):
            w.connect("value-changed", lambda *_: self.changed())
        self._timer = None

    def refresh(self):
        ctx, _ = self.core.resolve(self.app.conf(), "sway")
        self.app.busy_refresh = True
        self.gaps.set_value(int(ctx["gaps"]))
        self.border.set_value(int(ctx["border_width"]))
        self.radius.set_value(int(ctx["radius"]))
        self.app.busy_refresh = False

    def changed(self):
        if self.app.busy_refresh:
            return
        if self._timer:
            GLib.source_remove(self._timer)
        self._timer = GLib.timeout_add(400, self.commit)

    def commit(self):
        self._timer = None
        for k, w in (("ui.gaps", self.gaps), ("ui.border_width", self.border), ("ui.radius", self.radius)):
            self.core.set_value(k, str(int(w.get_value())))
        self.app.apply({"sway", "apps"}, "windows updated", refresh=False)
        return False


# ===================================================================== tools
OWN_TOOLS = [("vesha", "vesha (Claude Code accounts)"), ("nada", "nāda (music player)"), ("kosha", "kosha (packages)"),
             ("vinyasa", "Settings (this app)")]


class ToolsPage(Page):
    title, icon, group = "Tools", "⊡", "Tools"
    keywords = "tools per-tool theme override follow desktop kitty tmux nvim neovim waybar sway vyom mako"

    def build(self):
        self.add(page_header("Tools", "Every tool follows the desktop's theme unless you pick one for it here. "
                                      "Switch a tool off to keep varna away from it."))
        self.list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.add(self.list)

    def refresh(self):
        while (c := self.list.get_first_child()):
            self.list.remove(c)
        conf = self.app.conf()
        self.ids = [tid for tid, t in self.core.themes() if not isinstance(t, Exception)]
        names = ["Follow the desktop"] + [self.core.load_theme(t)["meta"]["name"] for t in self.ids]
        tools = [(n, s["label"]) for n, s in self.core.TOOLS.items() if n != "apps"] + OWN_TOOLS
        self.app.busy_refresh = True
        for name, label in tools:
            dd = Gtk.DropDown.new_from_strings(names)
            pick = conf["tools"].get(name)
            pick = pick if isinstance(pick, str) else (pick or {}).get("theme")
            dd.set_selected(self.ids.index(pick) + 1 if pick in self.ids else 0)
            dd.connect("notify::selected", lambda d, _p, n=name: self.on_pick(n, d))
            box = Gtk.Box(spacing=10)
            if name in self.core.TOOLS:
                hook = self.core.hook_ok(name)
                if hook is False:
                    warn = Gtk.Label(label="not included")
                    warn.add_css_class("warn")
                    warn.set_tooltip_text("Add to " + self.core.HOOKS[name][0] + ":  " + self.core.HOOKS[name][2])
                    box.append(warn)
                sw = Gtk.Switch(active=self.core.tool_enabled(conf, name), tooltip_text="Theme this tool")
                sw.connect("notify::active", lambda s, _p, n=name: self.on_switch(n, s))
                box.append(dd)
                box.append(sw)
            else:
                box.append(dd)
            self.list.append(row(label, None, box))
        self.app.busy_refresh = False

    def search_text(self):
        return f"{self.title} {self.keywords} " + " ".join(f"{n} {s['label']}" for n, s in self.core.TOOLS.items()) + \
            " " + " ".join(f"{n} {label}" for n, label in OWN_TOOLS)

    def on_pick(self, name, dd):
        if self.app.busy_refresh:
            return
        i = dd.get_selected()
        self.core.set_tool(name, "follow" if i == 0 else self.ids[i - 1])
        only = {name} if name in self.core.TOOLS else {"apps"}
        self.app.apply(only, f"{name}: " + ("follows the desktop" if i == 0 else self.ids[i - 1]), refresh=name == "vinyasa")

    def on_switch(self, name, sw):
        if self.app.busy_refresh:
            return
        conf = self.app.conf()
        dis = set(conf.get("disabled", []))
        if name == "gtk":
            conf["gtk"] = sw.get_active()
        elif sw.get_active():
            dis.discard(name)
        else:
            dis.add(name)
        conf["disabled"] = sorted(dis)
        self.core.save_config(conf)
        self.app.apply({name}, f"{name}: " + ("themed" if sw.get_active() else "left alone"), refresh=False)


# ===================================================================== about
class AboutPage(Page):
    title, icon, group = "About", "ⓘ", "System"
    keywords = "about version doctor check reapply varna"

    def build(self):
        from . import VERSION
        self.add(page_header("About", f"vinyasa {VERSION} · Vayu's settings, on top of varna, its theme engine."))
        again = Gtk.Button(label="Re-apply the theme to every tool")
        again.connect("clicked", lambda _b: self.app.apply(None, "re-applied"))
        folder = Gtk.Button(label="Open your themes folder")
        folder.connect("clicked", lambda _b: self.open_folder())
        self.add(row("Apply", "Writes every tool's colours again and reloads what's running.", again))
        self.add(row("Your themes", "~/.config/varna/themes", folder))
        self.add(section("Every tool"))
        self.status = Gtk.Label(xalign=0, wrap=True, selectable=True)
        self.status.add_css_class("mono")
        self.add(self.status)

    def refresh(self):
        conf = self.app.conf()
        lines = []
        for name, spec in self.core.TOOLS.items():
            on = self.core.tool_enabled(conf, name)
            hook = self.core.hook_ok(name)
            state = "off" if not on else "✓" if hook in (True, None) and os.path.exists(self.core.out_path(name)) else \
                "✗ not included" if hook is False else "not written yet"
            lines.append(f"{state:<16} {spec['label']}")
        self.status.set_text("\n".join(lines))

    def open_folder(self):
        os.makedirs(self.core.USER_THEMES, exist_ok=True)
        subprocess.Popen(["xdg-open", self.core.USER_THEMES], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


PAGES = [ThemePage, EditorPage, FontsPage, WallpaperPage, WindowsPage, ToolsPage, AboutPage]
