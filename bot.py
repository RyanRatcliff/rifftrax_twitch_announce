#!/usr/bin/env python3
"""
RiffTrax Twitch Notifier
Watches #rifftrax chat for a trigger command and fires a macOS notification.
Optionally generates Claude-powered trivia when the title changes.

Usage:
    python3 bot.py
    Ctrl+C to stop
"""

import os
import socket
import subprocess
import threading
import time

# ── IRC Config ────────────────────────────────────────────────────────────────
CHANNEL             = "rifftrax"
TRIGGERS            = ("!cmd edit movie", "!cmd edit !movie")  # Admin commands that change the movie
STREAMELEMENTS_BOT  = "streamelements"    # Bot that replies to !movie / !film queries
RIFFTRAX_URL_MARKER = "rifftrax.com/"    # Present in all StreamElements movie replies
NICK                = "justinfan70"      # Twitch requires justinfan* prefix for anonymous read-only access
NOW_PLAYING_FILE    = os.path.expanduser("~/.rifftrax_now_playing.txt")

# ── Trivia Config ─────────────────────────────────────────────────────────────
TRIVIA_FILE    = os.path.expanduser("~/.rifftrax_trivia.txt")
API_KEY_FILE   = os.path.expanduser("~/.rifftrax_anthropic_key")
POLL_INTERVAL  = 5   # seconds between now-playing checks
MODEL          = "claude-haiku-4-5-20251001"
FALLBACK_QUIP  = "Even our robots couldn't find anything nice to say about this one."
# ─────────────────────────────────────────────────────────────────────────────

HOST = "irc.chat.twitch.tv"
PORT = 6667


# ── Shared helpers ────────────────────────────────────────────────────────────

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


# ── IRC bot ───────────────────────────────────────────────────────────────────

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


def bot_loop() -> None:
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
                    write_file(NOW_PLAYING_FILE, title)

                elif message.strip().lower() in MOVIE_QUERY_COMMANDS:
                    last_query_time = time.time()

                elif username == STREAMELEMENTS_BOT and RIFFTRAX_URL_MARKER in message:
                    if time.time() - last_query_time <= MOVIE_QUERY_WINDOW:
                        last_query_time = 0.0
                        title = strip_url(message)
                        current = read_file(NOW_PLAYING_FILE)
                        if title and title != current:
                            print(f"[rifftrax-bot] *** SYNC: stored title mismatch, updating to: {title!r}")
                            notify("Now Playing", title)
                            write_file(NOW_PLAYING_FILE, title)

        except Exception as e:
            print(f"[rifftrax-bot] Connection lost ({e}). Reconnecting in 5s...")
            time.sleep(5)


# ── Trivia watcher ────────────────────────────────────────────────────────────

def load_api_key(path: str) -> str | None:
    """Read API key from file. Returns None if absent."""
    try:
        with open(path) as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


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
        print(f"[trivia] API error: {e}")
        return FALLBACK_QUIP


def trivia_loop(client) -> None:
    title           = read_file(NOW_PLAYING_FILE)
    existing_trivia = read_file(TRIVIA_FILE)
    last_title      = title

    if not title:
        write_file(TRIVIA_FILE, "")
    elif should_fetch_on_startup(title, existing_trivia):
        print(f"[trivia] Startup fetch for: {title!r}")
        write_file(TRIVIA_FILE, fetch_trivia(title, client))
    else:
        print(f"[trivia] Startup: trivia already present for {title!r}, skipping fetch")

    print(f"[trivia] Watching {NOW_PLAYING_FILE} ...")

    while True:
        try:
            time.sleep(POLL_INTERVAL)
            current_title = read_file(NOW_PLAYING_FILE)

            if current_title == last_title:
                continue

            last_title = current_title

            if not current_title:
                print("[trivia] Title cleared, hiding trivia")
                write_file(TRIVIA_FILE, "")
            else:
                print(f"[trivia] New title: {current_title!r}, fetching trivia...")
                write_file(TRIVIA_FILE, fetch_trivia(current_title, client))

        except Exception as e:
            print(f"[trivia] Unexpected error: {e}")


# ── Entry point ───────────────────────────────────────────────────────────────

def run() -> None:
    import anthropic  # deferred so tests can import this module without the SDK installed

    api_key = load_api_key(API_KEY_FILE)
    if api_key:
        client = anthropic.Anthropic(api_key=api_key)
        t = threading.Thread(target=trivia_loop, args=(client,), daemon=True)
        t.start()
    else:
        print("[trivia] No API key found at ~/.rifftrax_anthropic_key — trivia disabled")

    try:
        bot_loop()
    except KeyboardInterrupt:
        print("\n[rifftrax-bot] Stopped.")


if __name__ == "__main__":
    run()
