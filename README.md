# RiffTrax Twitch Notifier

A lightweight, locally-running bot that watches the [RiffTrax Twitch channel](https://www.twitch.tv/rifftrax) chat for the command that announces a new movie or short starting, then fires a **macOS system notification** and updates an optional **desktop widget** with the title.

No Twitch account, API keys, or OAuth tokens required.

---

## Features

- Connects anonymously to Twitch IRC — no credentials needed
- Fires a native macOS notification with the movie/short title
- Optional [Übersicht](https://tracesof.net/uebersicht/) desktop widget that shows what's currently playing
- Auto-reconnects if the connection drops
- All chat messages printed to the terminal for visibility

---

## Requirements

- macOS (notifications use `osascript`)
- Python 3.8+ (stdlib only — no pip installs needed)
- [Übersicht](https://tracesof.net/uebersicht/) *(optional, for the desktop widget)*

---

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/rifftrax_twitch_announce.git
cd rifftrax_twitch_announce
```

That's it. No virtual environment or dependencies to install.

---

## Usage

### Start the bot

```bash
python3 bot.py
```

Press `Ctrl+C` to stop.

The bot will print all chat messages to the terminal. When the trigger command is detected, a macOS notification will pop up and `~/.rifftrax_now_playing.txt` will be updated with the current title.

---

## Desktop Widget (optional)

The widget displays the current movie/short title on your desktop and disappears when nothing is playing.

**Setup:**

1. Install [Übersicht](https://tracesof.net/uebersicht/)
2. Copy the widget folder into your Übersicht widgets directory:

```bash
cp -r widget/rifftrax.widget ~/Library/Application\ Support/Übersicht/widgets/
```

The widget reads `~/.rifftrax_now_playing.txt` every 5 seconds and updates automatically.

To test it without waiting for a stream:

```bash
echo "Plan 9 from Outer Space" > ~/.rifftrax_now_playing.txt
```

To clear it:

```bash
rm ~/.rifftrax_now_playing.txt
```

---

## Configuration

Edit the config block at the top of `bot.py`:

```python
CHANNEL = "rifftrax"       # Twitch channel to watch
TRIGGER = "!cmd edit movie" # Chat command that signals a new movie
NICK    = "justinfan70"    # Any justinfan* username works for anonymous access
```

> **Note:** The `justinfan` prefix is required by Twitch for anonymous read-only IRC connections. You can change the number but must keep the `justinfan` prefix.

---

## How It Works

Twitch chat is accessible over standard IRC. This bot connects anonymously using Twitch's `justinfan` protocol, joins the channel, and watches for a specific command posted by stream admins when a new title starts. When matched, it extracts the movie/short title from the message and triggers a macOS notification via `osascript`.

---

## Contributing

PRs welcome! Some ideas for extensions:

- Support for other streaming platforms
- Linux notification support (`notify-send`)
- A menu bar app alternative to the Übersicht widget
- Logging history of what's been played
