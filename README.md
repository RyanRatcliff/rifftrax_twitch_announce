# RiffTrax Twitch Notifier

A lightweight, locally-running bot that watches the [RiffTrax Twitch channel](https://www.twitch.tv/rifftrax) chat for the command that announces a new movie or short starting, then fires a **macOS system notification** and updates an optional **desktop widget** with the title.

No Twitch account, API keys, or OAuth tokens required.

---

![RiffTrax widgets showing Now Riffing and Trivia on a dark desktop](docs/assets/screenshot.png)

## Features

- Connects anonymously to Twitch IRC — no credentials needed
- Fires a native macOS notification with the movie/short title
- Optional [Übersicht](https://tracesof.net/uebersicht/) desktop widget that shows what's currently playing
- Auto-reconnects if the connection drops
- All chat messages printed to the terminal for visibility

---

## Requirements

- macOS (notifications use `osascript`)
- Python 3.8+
- [Übersicht](https://tracesof.net/uebersicht/) *(optional, for desktop widgets)*
- An [Anthropic API key](https://console.anthropic.com/) *(optional, for the trivia widget)*

---

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/rifftrax_twitch_announce.git
cd rifftrax_twitch_announce
```

For the trivia widget only, install the `anthropic` SDK:

```bash
pip install -r requirements.txt
```

---

## Usage

### Start the bot

```bash
python3 bot.py
```

Press `Ctrl+C` to stop.

The bot will print all chat messages to the terminal. When the trigger command is detected, a macOS notification will pop up and `~/.rifftrax_now_playing.txt` will be updated with the current title.

---

## Desktop Widgets (optional)

Two Übersicht widgets are included. Both require [Übersicht](https://tracesof.net/uebersicht/) to be installed.

### Now Playing widget

Displays the current movie/short title on your desktop and disappears when nothing is playing.

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

### Trivia widget

Displays a scrolling ticker of Claude-generated RiffTrax-flavored trivia about whatever is currently playing. Requires an Anthropic API key.

**Setup:**

1. Create an API key file (one line, just the key):

```bash
echo "your-anthropic-api-key" > ~/.rifftrax_anthropic_key
chmod 600 ~/.rifftrax_anthropic_key
```

2. Copy the widget:

```bash
cp -r widget/rifftrax-trivia.widget ~/Library/Application\ Support/Übersicht/widgets/
```

3. Start the trivia watcher alongside the bot:

```bash
python3 trivia_watcher.py
```

The watcher polls `~/.rifftrax_now_playing.txt` every 5 seconds. When the title changes it calls Claude, writes the trivia to `~/.rifftrax_trivia.txt`, and the widget picks it up automatically. The widget appears below the now-playing widget and hides itself when nothing is playing.

> **Note:** If your Übersicht widgets directory is not the default, substitute your actual path in the `cp` commands above.

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
