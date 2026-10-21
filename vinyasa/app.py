"""vinyasa: the window. A sidebar of pages with a search box, the pages in a
stack, a toast for what just happened. Restyles itself from the theme.

Keys (also `?` in the app):
  j k        next / previous page (in the sidebar), next / previous control (in a page)
  h l        sidebar / page          gg G   first / last page
  /          search every setting    Enter  open the page / change the setting
  ?          all keys                q Esc  quit
"""
import os
import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, GLib, Gtk  # noqa: E402

from . import VERSION, bridge  # noqa: E402
from .pages import PAGES  # noqa: E402

# keybind: Vinyasa/settings | j / k | Move to the next / previous page or control
# keybind: Vinyasa/settings | h / l | Go to the sidebar / the page
# keybind: Vinyasa/settings | gg / G | Jump to the first / last page
# keybind: Vinyasa/settings | / | Search every setting
# keybind: Vinyasa/settings | Enter | Open the page, or change the setting
# keybind: Vinyasa/settings | ? | Show all keys
# keybind: Vinyasa/settings | q / Esc | Quit settings

DEBUG = bool(os.environ.get("VINYASA_DEBUG"))
KEYS = [("j  k", "next / previous page (sidebar) or control (page)"), ("h  l", "sidebar / page"),
        ("gg  G", "first / last page"), ("/", "search every setting"), ("Enter  Space", "open the page / change the setting"),
        ("Tab", "the next control"), ("?", "this help"), ("q  Esc", "quit")]

CSS = """
window.vinyasa { background-color: alpha(@base, @@OPACITY@@); color: @text; }
.sidebar { background-color: alpha(@mantle, 0.6); border-right: 1px solid alpha(@surface1, 0.6); }
.sidebar list { background: transparent; }
.sidebar row { border-radius: 10px; margin: 1px 8px; padding: 6px 10px; color: @subtext0; }
.sidebar row:selected { background-color: alpha(@accent, 0.16); color: @text; box-shadow: inset 3px 0 0 @accent; }
.sidebar row.group { margin-top: 12px; padding: 2px 10px; }
.group-label { font-family: monospace; font-size: 10px; letter-spacing: 2px; color: @overlay0; font-weight: 700; }
.icon { min-width: 22px; min-height: 22px; border-radius: 7px; background-color: @accent; color: @crust; font-weight: 800; font-size: 11px; }
.brand { padding: 16px 16px 6px; }
.brand-name { font-weight: 800; font-size: 16px; }
.brand-sub { color: @overlay1; font-size: 11px; }
searchentry { margin: 6px 12px 8px; border-radius: 10px; background-color: alpha(@surface0, 0.8); }
.page { padding: 26px 32px 40px; }
.page-title { font-size: 26px; font-weight: 800; letter-spacing: -0.5px; }
.page-subtitle { color: @overlay1; margin-bottom: 12px; }
.section { margin-top: 14px; font-family: monospace; font-size: 11px; letter-spacing: 2px; color: @overlay0; font-weight: 700; }
.setting { background-color: alpha(@mantle, 0.65); border-radius: 12px; padding: 12px 16px; }
.setting-title { font-weight: 600; }
.setting-subtitle { color: @overlay1; font-size: 12px; }
.theme-card { background-color: alpha(@mantle, 0.7); border-radius: 14px; padding: 10px; border: 2px solid transparent; }
flowboxchild { border-radius: 16px; padding: 0; }
flowboxchild:selected .theme-card { border-color: @accent; }
flowboxchild:focus .theme-card, flowboxchild:focus-visible .theme-card { border-color: alpha(@accent, 0.55); background-color: alpha(@accent, 0.08); }
flowboxchild:focus .thumb { outline: 2px solid alpha(@accent, 0.55); }
row:focus { outline: none; }
.card-title { font-weight: 700; }
.card-sub { color: @overlay1; font-size: 11px; }
.thumb { border-radius: 10px; }
flowboxchild:selected .thumb { outline: 2px solid @accent; }
button.swatch { padding: 2px; border-radius: 999px; background: none; box-shadow: none; }
button.swatch:hover { background-color: alpha(@text, 0.08); }
button.pill { border-radius: 999px; }
button.suggested { background-color: @accent; color: @crust; font-weight: 700; }
button.destructive { color: @red; }
.segmented button { border-radius: 0; }
.segmented button:first-child { border-radius: 9px 0 0 9px; }
.segmented button:last-child { border-radius: 0 9px 9px 0; }
.segmented button:checked { background-color: @accent; color: @crust; }
switch:checked { background-color: @accent; }
scale highlight { background-color: @accent; }
.warn { color: @yellow; font-size: 12px; }
.mono { font-family: monospace; color: @subtext0; }
.toast { background-color: alpha(@crust, 0.92); color: @text; border: 1px solid alpha(@accent, 0.6); border-radius: 999px;
         padding: 8px 18px; margin-bottom: 18px; font-weight: 600; }
.toast.err { border-color: @red; }
.help { background-color: alpha(@crust, 0.95); border-radius: 18px; padding: 22px 26px; border: 1px solid alpha(@accent, 0.4); }
.help-key { font-family: monospace; color: @accent; font-weight: 700; }
"""


class Window(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Settings", default_width=1180, default_height=760)
        self.add_css_class("vinyasa")
        self.app = app
        self.core = app.core
        self.busy_refresh = False
        self.pending_g = False
        self.pages = [P(self) for P in PAGES]

        root = Gtk.Box()
        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, width_request=250)
        side.add_css_class("sidebar")
        brand = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        brand.add_css_class("brand")
        n = Gtk.Label(label="Settings", xalign=0)
        n.add_css_class("brand-name")
        s = Gtk.Label(label=f"vinyasa {VERSION}", xalign=0)
        s.add_css_class("brand-sub")
        brand.append(n)
        brand.append(s)
        side.append(brand)
        self.search = Gtk.SearchEntry(placeholder_text="Search settings  ( / )")
        self.search.connect("search-changed", lambda _e: self.on_search())
        self.search.connect("activate", lambda _e: self.open_first_match())
        self.search.connect("stop-search", lambda _e: (self.search.set_text(""), self.listbox.grab_focus()))
        side.append(self.search)
        self.listbox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE, vexpand=True)
        self.listbox.set_filter_func(self.filter_row)
        self.listbox.connect("row-selected", self.on_row)
        group = None
        self.rows = []
        for page in self.pages:
            if page.group != group:
                group = page.group
                gr = Gtk.ListBoxRow(selectable=False, activatable=False)
                gr.add_css_class("group")
                lbl = Gtk.Label(label=group.upper(), xalign=0)
                lbl.add_css_class("group-label")
                gr.set_child(lbl)
                gr.group = group
                gr.page = None
                self.listbox.append(gr)
            r = Gtk.ListBoxRow()
            box = Gtk.Box(spacing=10)
            ic = Gtk.Label(label=page.icon)
            ic.add_css_class("icon")
            box.append(ic)
            box.append(Gtk.Label(label=page.title, xalign=0))
            r.set_child(box)
            r.page = page
            r.group = page.group
            self.listbox.append(r)
            self.rows.append(r)
        side.append(Gtk.ScrolledWindow(child=self.listbox, vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER))
        self.nothing = Gtk.Label(label="No setting matches", visible=False, margin_bottom=16)
        self.nothing.add_css_class("setting-subtitle")
        side.append(self.nothing)
        root.append(side)

        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE, hexpand=True, vexpand=True)
        for page in self.pages:
            self.stack.add_named(page.widget, page.title)
        overlay = Gtk.Overlay(child=self.stack, hexpand=True)
        self.toast_label = Gtk.Label()
        self.toast_label.add_css_class("toast")
        self.revealer = Gtk.Revealer(child=self.toast_label, transition_type=Gtk.RevealerTransitionType.SLIDE_UP,
                                     halign=Gtk.Align.CENTER, valign=Gtk.Align.END)
        overlay.add_overlay(self.revealer)
        self.help = self.build_help()
        overlay.add_overlay(self.help)
        root.append(overlay)
        self.set_child(root)

        keys = Gtk.EventControllerKey(propagation_phase=Gtk.PropagationPhase.CAPTURE)
        keys.connect("key-pressed", self.on_key)
        self.add_controller(keys)
        self._toast_timer = None
        self.restyle()
        self.listbox.select_row(self.rows[0])
        self.listbox.grab_focus()

    # ------------------------------------------------------------ data
    def conf(self):
        return self.core.load_config()

    def refresh_all(self):
        for p in self.pages:
            try:
                p.refresh()
            except Exception as e:   # a page that can't read something shouldn't take the app down
                self.toast(f"{p.title}: {e}", "err")

    def apply(self, only, message, refresh=True):
        """Applies in the background (reloading tools takes a moment), then
        restyles this window and says what happened."""
        self.toast(message + " …")

        def work():
            try:
                results = self.core.apply(None, only=only)
                err = None
            except self.core.VarnaError as e:
                results, err = [], str(e)

            def done():
                if err:
                    self.toast(err, "err")
                    return False
                failed = [r for r in results if r[1] == "failed"]
                ok = sum(1 for r in results if r[1] == "ok")
                self.restyle()
                if refresh:
                    self.refresh_all()
                if failed:
                    self.toast(f"{message} · {failed[0][0]}: {failed[0][2]}", "err")
                else:
                    self.toast(f"{message} · {ok} tool{'s' if ok != 1 else ''} updated")
                return False
            GLib.idle_add(done)
        threading.Thread(target=work, daemon=True).start()

    # ------------------------------------------------------------ look
    def restyle(self):
        """This window in the theme (its own pick under Tools, if any)."""
        try:
            ctx, _ = self.core.resolve(self.conf(), "vinyasa")
        except self.core.VarnaError as e:
            self.toast(str(e), "err")
            return
        defs = "\n".join(f"@define-color {k} {v};" for k, v in ctx.items() if isinstance(v, str) and v.startswith("#"))
        css = defs + CSS.replace("@@OPACITY@@", f"{max(0.75, float(ctx['opacity'])):.2f}")
        if getattr(self.app, "provider", None) is None:
            self.app.provider = Gtk.CssProvider()
            Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), self.app.provider,
                                                      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.app.provider.load_from_string(css)
        settings = Gtk.Settings.get_default()
        if settings:
            try:   # GTK 4.20+
                settings.set_property("gtk-interface-color-scheme",
                                      Gtk.InterfaceColorScheme.DARK if ctx["variant"] == "dark" else Gtk.InterfaceColorScheme.LIGHT)
            except (AttributeError, TypeError):
                settings.set_property("gtk-application-prefer-dark-theme", ctx["variant"] == "dark")

    def toast(self, msg, kind="ok"):
        self.toast_label.set_text(msg)
        (self.toast_label.add_css_class if kind == "err" else self.toast_label.remove_css_class)("err")
        self.revealer.set_reveal_child(True)
        if self._toast_timer:
            GLib.source_remove(self._toast_timer)
        self._toast_timer = GLib.timeout_add(4500 if kind == "err" else 3000, self.hide_toast)

    def hide_toast(self):
        self._toast_timer = None
        self.revealer.set_reveal_child(False)
        return False

    def build_help(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, visible=False)
        box.add_css_class("help")
        t = Gtk.Label(label="Keys", xalign=0)
        t.add_css_class("page-title")
        box.append(t)
        grid = Gtk.Grid(column_spacing=24, row_spacing=6)
        for i, (k, d) in enumerate(KEYS):
            kl = Gtk.Label(label=k, xalign=0)
            kl.add_css_class("help-key")
            grid.attach(kl, 0, i, 1, 1)
            grid.attach(Gtk.Label(label=d, xalign=0), 1, i, 1, 1)
        box.append(grid)
        foot = Gtk.Label(label="? or Esc closes this", xalign=0)
        foot.add_css_class("setting-subtitle")
        box.append(foot)
        return box

    # ------------------------------------------------------------ navigation
    def filter_row(self, row):
        q = self.search.get_text().strip().lower()
        if not q:
            return True
        if row.page is None:   # a group header shows if any of its pages match
            return any(self.matches(r.page, q) for r in self.rows if r.group == row.group)
        return self.matches(row.page, q)

    @staticmethod
    def matches(page, q):
        text = page.search_text().lower()
        return all(w in text for w in q.split())

    def on_search(self):
        self.listbox.invalidate_filter()
        q = self.search.get_text().strip().lower()
        hits = [r for r in self.rows if not q or self.matches(r.page, q)]
        self.nothing.set_visible(not hits)
        if hits and self.listbox.get_selected_row() not in hits:   # show the first match while typing
            self.listbox.select_row(hits[0])

    def open_first_match(self):
        for r in self.rows:
            if r.get_child_visible() and self.filter_row(r):
                self.listbox.select_row(r)
                self.focus_page()
                return

    def on_row(self, _lb, row):
        if row is None or row.page is None:
            return
        self.stack.set_visible_child_name(row.page.title)
        try:
            row.page.refresh()
        except Exception as e:
            self.toast(f"{row.page.title}: {e}", "err")

    def visible_rows(self):
        return [r for r in self.rows if self.filter_row(r)]

    def move_page(self, step):
        rows = self.visible_rows()
        cur = self.listbox.get_selected_row()
        i = rows.index(cur) if cur in rows else -1
        nxt = rows[max(0, min(len(rows) - 1, i + step))] if rows else None
        if nxt:
            self.listbox.select_row(nxt)
            nxt.grab_focus()

    def move_in_page(self, step):
        """j / k in a page: down / up a row in a grid of cards, else the next / previous control."""
        f = self.get_focus()
        grid = f
        while grid is not None and not isinstance(grid, Gtk.FlowBox):
            grid = grid.get_parent()
        if grid is not None:
            before = self.get_focus()
            grid.emit("move-cursor", Gtk.MovementStep.DISPLAY_LINES, step, False, False)
            if self.get_focus() is not before:
                return
        self.child_focus(Gtk.DirectionType.TAB_FORWARD if step > 0 else Gtk.DirectionType.TAB_BACKWARD)

    def focus_page(self):
        page = self.stack.get_visible_child()
        if page:
            page.child_focus(Gtk.DirectionType.TAB_FORWARD)

    def in_sidebar(self):
        f = self.get_focus()
        while f is not None:
            if f is self.listbox:
                return True
            f = f.get_parent()
        return False

    def typing(self):
        f = self.get_focus()
        return isinstance(f, (Gtk.Text, Gtk.Editable)) or (f is not None and isinstance(f.get_parent(), (Gtk.SpinButton, Gtk.SearchEntry)))

    def on_key(self, _ctl, keyval, _code, state):
        name = Gdk.keyval_name(keyval) or ""
        ctrl = state & Gdk.ModifierType.CONTROL_MASK
        if DEBUG:
            print(f"key {name} focus={type(self.get_focus()).__name__} sidebar={self.in_sidebar()}", flush=True)
        if ctrl and name == "q":
            self.close()
            return True
        if self.help.get_visible():
            if name in ("question", "Escape", "q"):
                self.help.set_visible(False)
            return True
        if self.typing():
            if name == "Escape":
                self.search.set_text("")
                self.listbox.grab_focus()
                return True
            return False
        if ctrl:
            return False
        g, self.pending_g = self.pending_g, False
        if name == "g":
            if g:
                rows = self.visible_rows()
                if rows:
                    self.listbox.select_row(rows[0])
                    rows[0].grab_focus()
            else:
                self.pending_g = True
            return True
        if name == "G":
            rows = self.visible_rows()
            if rows:
                self.listbox.select_row(rows[-1])
                rows[-1].grab_focus()
            return True
        if name in ("j", "k"):
            if self.in_sidebar():
                self.move_page(1 if name == "j" else -1)
            else:
                self.move_in_page(1 if name == "j" else -1)
            return True
        if name == "l" or (name in ("Return", "Right") and self.in_sidebar()):
            if name == "l" or self.in_sidebar():
                self.focus_page()
                return True
            return False
        if name in ("Return", "KP_Enter", "space"):
            f = self.get_focus()
            if isinstance(f, Gtk.FlowBoxChild) and isinstance(f.get_parent(), Gtk.FlowBox):
                f.get_parent().emit("child-activated", f)   # a theme card or wallpaper: pick it
                return True
            return False
        if name == "h":
            sel = self.listbox.get_selected_row()
            (sel or self.listbox).grab_focus()
            return True
        if name == "slash":
            self.search.grab_focus()
            return True
        if name == "question":
            self.help.set_visible(True)
            return True
        if name in ("q", "Escape"):
            self.close()
            return True
        return False


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="dev.vayu.Vinyasa")
        self.core = bridge.load()
        self.provider = None
        self.page = None

    def do_activate(self):
        win = self.get_active_window()
        if not win:
            win = Window(self)
        if self.page:
            want = self.page.lower()
            hit = next((r for r in win.rows if r.page.title.lower() == want), None) or \
                next((r for r in win.rows if r.page.title.lower().startswith(want)), None) or \
                next((r for r in win.rows if want in r.page.title.lower()), None)
            if hit:
                win.listbox.select_row(hit)
        win.present()

        def focus():   # after the window maps: the selected page row takes the keyboard
            row = win.listbox.get_selected_row()
            (row or win.listbox).grab_focus()
            return False
        GLib.idle_add(focus)


def main(argv):
    import sys
    page = None
    rest = [a for a in argv if not a.startswith("--page=")]
    for a in argv:
        if a.startswith("--page="):
            page = a.split("=", 1)[1]
    if rest and rest[0] in ("-h", "--help"):
        print("vinyasa: Vayu's settings.\n\n  vinyasa                 open settings\n  vinyasa --page=wallpaper  open on a page "
              "(theme, editor, fonts, wallpaper, windows, tools, about)\n  vinyasa --version\n\nThemes from the command line: varna help")
        return 0
    if rest and rest[0] in ("-V", "--version"):
        print(f"vinyasa {VERSION}")
        return 0
    try:
        app = App()
    except ImportError as e:
        print(f"vinyasa: {e}", file=sys.stderr)
        return 1
    app.page = page
    return app.run([sys.argv[0]])
