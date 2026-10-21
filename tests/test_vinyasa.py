import os
import sys
import tempfile
import unittest

ROOT = tempfile.mkdtemp()
os.environ.update(HOME=ROOT, XDG_CONFIG_HOME=os.path.join(ROOT, ".config"), XDG_STATE_HOME=os.path.join(ROOT, ".local", "state"),
                  GSETTINGS_BACKEND="memory")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
# varna: a checkout next to this one (CI clones it there), or $VARNA_HOME
os.environ.setdefault("VARNA_HOME", os.path.join(os.path.dirname(HERE), "varna"))

from vinyasa import bridge  # noqa: E402

core = bridge.load()
DISPLAY = bool(os.environ.get("WAYLAND_DISPLAY") or os.environ.get("DISPLAY"))


class Logic(unittest.TestCase):
    def test_bridge_finds_varna(self):
        self.assertTrue(core.theme_paths())

    def test_wallpapers_skip_current(self):
        from vinyasa import pages
        d = os.path.join(ROOT, "walls")
        os.makedirs(os.path.join(d, "Active"))
        for name in ("Active/a.jpg", "b.png", "current.jpg", "notes.txt"):
            open(os.path.join(d, name), "w").close()
        old = pages.WALL_DIR
        pages.WALL_DIR = d
        try:
            got = sorted(os.path.basename(p) for p in pages.wallpapers())
        finally:
            pages.WALL_DIR = old
        self.assertEqual(got, ["a.jpg", "b.png"])


@unittest.skipUnless(DISPLAY, "needs a display")
class Gui(unittest.TestCase):
    def test_every_page_builds_and_the_editor_saves(self):
        import gi
        gi.require_version("Gtk", "4.0")
        from gi.repository import Gtk

        from vinyasa.app import Window

        class FakeApp(Gtk.Application):
            pass
        app = FakeApp(application_id="dev.vayu.VinyasaTest")
        app.core = core
        app.provider = None
        app.register(None)
        win = Window(app)
        for page in win.pages:
            page.refresh()
        editor = next(p for p in win.pages if p.title == "Theme editor")
        editor.name.set_text("Test Dusk")
        editor.save(new=True)
        self.assertIn("test-dusk", core.theme_paths())
        self.assertTrue(core.load_theme("test-dusk")["user"])
        # search: theme names and tool names find their pages
        theme_page = next(p for p in win.pages if p.title == "Theme")
        self.assertTrue(win.matches(theme_page, "nord"))
        tools = next(p for p in win.pages if p.title == "Tools")
        self.assertTrue(win.matches(tools, "kitty"))
        self.assertFalse(win.matches(tools, "wallpaper"))
        win.destroy()


if __name__ == "__main__":
    unittest.main()
