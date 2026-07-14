"""Runtime platform detection kept independent from rendering backends."""

import os
import sys


def is_web() -> bool:
    """Return whether Arepy is running inside its browser runtime."""

    return sys.platform == "emscripten" or os.getenv("AREPY_PLATFORM") == "web"
