"""Finds varna (the theme engine vinyasa drives) and imports its core:
the `varna` on PATH (kosha's install), ~/.local/share/varna, or $VARNA_HOME."""
import os
import shutil
import sys


def _candidates():
    if os.environ.get("VARNA_HOME"):
        yield os.environ["VARNA_HOME"]
    exe = shutil.which("varna")
    if exe:
        yield os.path.dirname(os.path.dirname(os.path.realpath(exe)))
    yield os.path.join(os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share"), "varna")


def load():
    for d in _candidates():
        if os.path.isfile(os.path.join(d, "varna", "core.py")):
            if d not in sys.path:
                sys.path.insert(0, d)
            from varna import core
            return core
    raise ImportError("vinyasa needs varna (Vayu's theme engine): kosha install varna")
