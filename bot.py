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
CHANNEL            = "rifftrax"
TRIGGERS           = ("!cmd edit movie", "!cmd edit !movie")  # Admin commands that change the movie
STREAMELEMENTS_BOT  = "streamelements"       # Bot that replies to !movie / !film queries
RIFFTRAX_URL_MARKER = "rifftrax.com/"       # Present in all StreamElements movie replies
NICK               = "justinfan70"       # Twitch requires justinfan* prefix for anonymous read-only access
NOW_PLAYING_FILE   = os.path.expanduser("~/.rifftrax_now_playing.txt")
# ─────────────────────────────────────────────────────────────────────────────

HOST = "irc.chat.twitch.tv"
PORT = 6667


def notify(title: str, message: str) -> None:
    script = f'display notification "{message}" with title "RiffTrax" subtitle "{title}"'
    subprocess.run(["osascript", "-e", script], check=False)


def extract_title(text: str, trigger: str) -> str:
    """Return the movie title from a trigger command line, stripping the trigger prefix and URL."""
    rest = text[len(trigger):].strip()
    parts = rest.split()
    title_parts = [p for p in parts if not p.startswith("http")]
    title = " ".join(title_parts).strip()
    return title if title else "New RiffTrax presentation starting!"


def strip_url(text: str) -> str:
    """Strip trailing URL from a message, return just the title portion."""
    parts = text.split()
    title_parts = [p for p in parts if not p.startswith("http")]
    return " ".join(title_parts).strip()


def read_now_playing() -> str:
    """Return the currently stored title, or empty string if not set."""
    try:
        with open(NOW_PLAYING_FILE) as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


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


MOVIE_QUERY_COMMANDS = {"!movie", "!film"}
MOVIE_QUERY_WINDOW   = 30  # seconds to wait for streamelements reply after a query


def run() -> None:
    last_query_time = 0.0

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

                matched_trigger = next((t for t in TRIGGERS if message.startswith(t)), None)
                if matched_trigger:
                    title = extract_title(message, matched_trigger)
                    print(f"[rifftrax-bot] *** TRIGGER detected! Notifying: {title!r}")
                    notify("Now Starting", title)
                    with open(NOW_PLAYING_FILE, "w") as f:
                        f.write(title)

                elif message.strip().lower() in MOVIE_QUERY_COMMANDS:
                    last_query_time = time.time()

                elif username == STREAMELEMENTS_BOT and RIFFTRAX_URL_MARKER in message:
                    if time.time() - last_query_time <= MOVIE_QUERY_WINDOW:
                        # Preceded by !movie / !film — sync if we missed the change command
                        last_query_time = 0.0
                        title = strip_url(message)
                        current = read_now_playing()
                        if title and title != current:
                            print(f"[rifftrax-bot] *** SYNC: stored title mismatch, updating to: {title!r}")
                            notify("Now Playing", title)
                            with open(NOW_PLAYING_FILE, "w") as f:
                                f.write(title)

        except KeyboardInterrupt:
            print("\n[rifftrax-bot] Stopped.")
            return
        except Exception as e:
            print(f"[rifftrax-bot] Connection lost ({e}). Reconnecting in 5s...")
            time.sleep(5)


if __name__ == "__main__":
    run()
