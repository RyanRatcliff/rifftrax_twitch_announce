# RiffTrax Twitch Notifier — Design Spec

**Date:** 2026-03-21
**Status:** Approved

---

## Overview

A locally-running Python script (`bot.py`) that connects anonymously to the RiffTrax Twitch chat, watches for a specific bot command indicating a new movie or short is starting, and fires a native macOS system notification containing the title from the message.

---

## Architecture

Single-file Python script. No external dependencies — stdlib only.

```
bot.py
  ├── Config block (channel, trigger command, notification template)
  ├── IRC connection (anonymous justinfan login)
  ├── Message loop (PING/PONG keepalive, message parsing)
  ├── Trigger detection (matches command pattern in PRIVMSG)
  ├── Title extraction (parses title from message text)
  └── macOS notification (osascript display notification)
```

---

## Components

### IRC Connection
- Connects to `irc.chat.twitch.tv:6667` (plaintext IRC — port Twitch currently supports for anonymous bots) as `rifferfan70` using anonymous auth (`PASS SCHMOOPIIE`)
- Joins `#rifftrax`
- Uses `socket.makefile('r')` for proper line buffering (`\r\n` line endings per IRC spec)
- Handles `PING` → `PONG` to maintain connection
- Auto-reconnects on socket drop: re-sends NICK, PASS, and JOIN after a 5-second delay; loops indefinitely

### Message Loop
- Reads IRC lines via the buffered file handle (handles partial reads and multi-line reads correctly)
- Parses `PRIVMSG` lines for the trigger command (placeholder: `!newmovie`)
- Logs only `PRIVMSG` lines to the terminal (suppresses PING/PONG and server notices) so the user can monitor chat and spot the real trigger command

### Trigger Detection
- Matches messages that **start with** the configured trigger command (e.g. `!newmovie Movie Title Here`)
- Command placeholder can be updated in the config block at the top of the file

### Title Extraction
- Expected message format: `<TRIGGER> <title>` — title is everything after the first space
- Falls back to `"New RiffTrax presentation starting!"` if no title is found in the message

### macOS Notification
- Fires via `osascript -e 'display notification "..." with title "RiffTrax" subtitle "..."'`
- No external dependencies

---

## Config

At the top of `bot.py`:

```python
CHANNEL = "rifftrax"    # no # prefix — code prepends it
TRIGGER = "!newmovie"   # ← placeholder, update when real command is known
NICK = "rifferfan70"    # arbitrary username; Twitch accepts any nick for anonymous read-only
```

---

## Operation

- **Start:** `python3 bot.py`
- **Stop:** `Ctrl+C` (clean shutdown)
- **Output:** Prints received messages to terminal so the user can monitor chat and spot the real command

---

## Error Handling

- Socket disconnect → reconnect after 5-second delay, loop indefinitely
- Malformed message lines → skip silently
- `osascript` failure → log to terminal, continue running

---

## Out of Scope

- Discord integration
- Scheduling or cron behavior
- Twitch OAuth / API credentials
- Multiple channel support
