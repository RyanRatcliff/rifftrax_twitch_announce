#!/usr/bin/env python3
"""
RiffTrax Trivia Watcher
Watches ~/.rifftrax_now_playing.txt and fetches Claude-generated trivia
when the title changes. Writes to ~/.rifftrax_trivia.txt.

Usage:
    python3 trivia_watcher.py
    Ctrl+C to stop
"""

import os
import sys
import time


# ── Paths ─────────────────────────────────────────────────────────────────────
NOW_PLAYING_FILE = os.path.expanduser("~/.rifftrax_now_playing.txt")
TRIVIA_FILE      = os.path.expanduser("~/.rifftrax_trivia.txt")
API_KEY_FILE     = os.path.expanduser("~/.rifftrax_anthropic_key")

POLL_INTERVAL    = 5  # seconds
MODEL            = "claude-haiku-4-5-20251001"
FALLBACK_QUIP    = "Even our robots couldn't find anything nice to say about this one."
# ─────────────────────────────────────────────────────────────────────────────


def read_file(path: str) -> str:
    """Read a file and return stripped contents, or '' if absent."""
    try:
        with open(path) as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def write_file(path: str, content: str) -> None:
    """Write content to a file, overwriting if it exists."""
    with open(path, "w") as f:
        f.write(content)
