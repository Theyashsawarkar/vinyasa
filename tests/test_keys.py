"""The settings window's keys: the table is consistent and the annotations match it."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from vinyasa import app, keys  # noqa: E402


class Keys(unittest.TestCase):
    def test_annotations_are_generated(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "keybinds.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_every_page_has_a_space_t_key(self):
        from vinyasa.pages import PAGES
        self.assertEqual({P.title for P in PAGES}, set(app.PAGE_KEYS))
        self.assertEqual(len(set(app.PAGE_KEYS.values())), len(app.PAGE_KEYS))

    def test_leader_keys_are_in_reserved_groups(self):
        for b in app.BINDS:
            if b.seq.startswith(" ") and len(b.seq) > 1:
                self.assertIn(b.seq[:2], keys.GROUPS, b.seq)

    def test_no_key_hides_another(self):
        table = {b.seq for b in app.BINDS}
        for seq in table:
            self.assertFalse([s for s in table if s != seq and s.startswith(seq)], seq)

    def test_sequences(self):
        km = keys.Keymap(app.BINDS)
        m = keys.Machine()
        m.feed(km, "5")
        r = m.feed(km, "l")
        self.assertEqual((r.bind.action, r.count), ("right", 5))
        for tok in (" ", "t"):
            self.assertEqual(m.feed(km, tok).kind, "pending")
        self.assertEqual(m.feed(km, "f").bind.action, "goto:Fonts")


if __name__ == "__main__":
    unittest.main()
