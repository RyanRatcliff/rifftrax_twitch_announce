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


def should_fetch_on_startup(title: str, existing_trivia: str) -> bool:
    """Return True if we should fetch trivia on startup."""
    if not title:
        return False
    return not existing_trivia


def build_prompt(title: str) -> str:
    return (
        f'You are a writer for RiffTrax, the comedy riffing show. Write 2-3 short, punchy '
        f'sentences of trivia about "{title}" in the RiffTrax voice — dry wit, affectionate '
        f'mockery, genuine facts wrapped in a joke. If you don\'t recognize the title, write '
        f'something generically funny about low-budget cinema. No bullet points, no lists, '
        f'just flowing sentences.'
    )


def fetch_trivia(title: str, client) -> str:
    """Call Claude API and return trivia text. Returns fallback quip on error."""
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=200,
            messages=[{"role": "user", "content": build_prompt(title)}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        print(f"[trivia-watcher] API error: {e}")
        return FALLBACK_QUIP
