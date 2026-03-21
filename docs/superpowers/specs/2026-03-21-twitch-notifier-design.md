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
- Connects to `irc.chat.twitch.tv:6667` as `rifferfan70` using anonymous auth (`PASS SCHMOOPIIE`)
- Joins `#rifftrax`
- Handles `PING` → `PONG` to maintain connection
- Auto-reconnects with a short delay if the socket drops

### Message Loop
- Reads incoming IRC lines in a loop
- Parses `PRIVMSG` lines for the trigger command (placeholder: `!newmovie`)
- Logs all received messages to the terminal for visibility

### Trigger Detection
- Matches messages that start with (or contain) the configured trigger command
- Command placeholder can be updated in the config block at the top of the file

### Title Extraction
- Extracts the movie/short title from the portion of the message after the command keyword
- Falls back to a generic notification if no title is found

### macOS Notification
- Fires via `osascript -e 'display notification "..." with title "RiffTrax" subtitle "..."'`
- No external dependencies

---

## Config

At the top of `bot.py`:

```python
CHANNEL = "rifftrax"
TRIGGER = "!newmovie"   # ← placeholder, update when real command is known
NICK = "rifferfan70"
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
