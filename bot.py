#!/usr/bin/env python3
"""
RiffTrax Twitch Notifier
Watches #rifftrax chat for a trigger command and fires a macOS notification.

Usage:
    python3 bot.py
    Ctrl+C to stop
"""

import os
import socket
import subprocess
import time

# ── Config ────────────────────────────────────────────────────────────────────
CHANNEL = "rifftrax"
TRIGGER = "!cmd edit movie"
NICK    = "justinfan70"  # Twitch requires justinfan* prefix for anonymous read-only access
# ─────────────────────────────────────────────────────────────────────────────

HOST = "irc.chat.twitch.tv"
PORT = 6667


def notify(title: str, message: str) -> None:
    script = f'display notification "{message}" with title "RiffTrax" subtitle "{title}"'
    subprocess.run(["osascript", "-e", script], check=False)


def extract_title(text: str) -> str:
    """Return the movie title from '!cmd edit movie <title> <url>', stripping the URL."""
    rest = text[len(TRIGGER):].strip()
    # Drop trailing URL (anything starting with http)
    parts = rest.split()
    title_parts = [p for p in parts if not p.startswith("http")]
    title = " ".join(title_parts).strip()
    return title if title else "New RiffTrax presentation starting!"


def parse_privmsg(line: str):
    """
    Parse a Twitch IRC PRIVMSG line.
    Returns (username, message) or None if it's not a PRIVMSG.

    Format: :nick!nick@nick.tmi.twitch.tv PRIVMSG #channel :message text
    """
    if "PRIVMSG" not in line:
        return None
    try:
        prefix, _, rest = line.partition(" PRIVMSG ")
        username = prefix.lstrip(":").split("!")[0]
        _, _, message = rest.partition(":")
        return username, message.strip()
    except Exception:
        return None


def connect() -> tuple[socket.socket, object]:
    sock = socket.socket()
    sock.connect((HOST, PORT))
    sock.send(f"NICK {NICK}\r\n".encode())
    sock.send(f"JOIN #{CHANNEL}\r\n".encode())
    reader = sock.makefile("r", encoding="utf-8", errors="ignore")
    print(f"[rifftrax-bot] Connected to #{CHANNEL} as {NICK}")
    return sock, reader


def run() -> None:
    while True:
        try:
            sock, reader = connect()
            for line in reader:
                line = line.rstrip("\r\n")

                if line.startswith("PING"):
                    sock.send(b"PONG :tmi.twitch.tv\r\n")
                    continue

                parsed = parse_privmsg(line)
                if parsed is None:
                    if line:
                        print(f"[server]: {line}")
                    continue

                username, message = parsed
                print(f"[{username}]: {message}")

                if message.startswith(TRIGGER):
                    title = extract_title(message)
                    print(f"[rifftrax-bot] *** TRIGGER detected! Notifying: {title!r}")
                    notify("Now Starting", title)
                    with open(os.path.expanduser("~/.rifftrax_now_playing.txt"), "w") as f:
                        f.write(title)

        except KeyboardInterrupt:
            print("\n[rifftrax-bot] Stopped.")
            return
        except Exception as e:
            print(f"[rifftrax-bot] Connection lost ({e}). Reconnecting in 5s...")
            time.sleep(5)


if __name__ == "__main__":
    run()
