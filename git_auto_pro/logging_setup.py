"""Logging setup for Git-Auto Pro.

Enables debug logging when the ``GIT_AUTO_DEBUG`` environment variable is set
(documented in docs/troubleshooting.md). Debug output is written to
``~/.git-auto.log`` (and to stderr). Without the flag, logging is silent at
WARNING and above — the normal CLI output is unaffected.

Usage:
    from .logging_setup import setup_logging, get_logger
    setup_logging()           # call once at CLI startup
    logger = get_logger(__name__)
    logger.debug("...")
"""

import logging
import os
from pathlib import Path

_LOG_FILE = Path.home() / ".git-auto.log"
_CONFIGURED = False


def setup_logging() -> None:
    """Configure the root logger based on GIT_AUTO_DEBUG.

    Idempotent: safe to call more than once.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    debug = os.environ.get("GIT_AUTO_DEBUG", "").strip().lower() in ("1", "true", "yes")
    root = logging.getLogger("git_auto_pro")

    if debug:
        root.setLevel(logging.DEBUG)
        fmt = logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s")

        # File handler — the documented ~/.git-auto.log
        try:
            file_handler = logging.FileHandler(_LOG_FILE)
            file_handler.setFormatter(fmt)
            file_handler.setLevel(logging.DEBUG)
            root.addHandler(file_handler)
        except OSError:
            # Can't write the log file (read-only home, etc.) — fall back to
            # stderr only.
            pass

        # Also mirror to stderr so `GIT_AUTO_DEBUG=1 git-auto ...` shows
        # debug output inline during a run.
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(fmt)
        stream_handler.setLevel(logging.DEBUG)
        root.addHandler(stream_handler)
    else:
        # Silent by default: nothing below WARNING propagates.
        root.setLevel(logging.WARNING)
        # Attach a no-op-ish handler so library code never emits "No handlers
        # could be found" warnings; WARNING+ still surface if something truly
        # goes wrong.
        if not root.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.WARNING)
            root.addHandler(handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module logger under the 'git_auto_pro' namespace."""
    if not name.startswith("git_auto_pro"):
        name = f"git_auto_pro.{name}"
    return logging.getLogger(name)


def log_file_path() -> Path:
    """Return the path debug logs are written to (for `doctor` / docs)."""
    return _LOG_FILE
