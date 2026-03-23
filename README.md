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

## Desktop Widget (optional)

An [Übersicht](https://tracesof.net/uebersicht/) widget is included that shows the current movie title, start time, and a scrolling trivia ticker in a single overlay card. Each section hides itself independently when its data isn't available, and the whole card hides when nothing is playing.

### Setup

1. Copy the widget:

```bash
cp -r widget/rifftrax-combined.widget ~/Library/Application\ Support/Übersicht/widgets/
```

2. For trivia, create an Anthropic API key file (one line, just the key):

```bash
echo "your-anthropic-api-key" > ~/.rifftrax_anthropic_key
chmod 600 ~/.rifftrax_anthropic_key
```

The bot detects the key file on startup and runs the trivia watcher automatically. When the title changes it calls Claude and writes trivia to `~/.rifftrax_trivia.txt`, which the widget picks up automatically. If no key file is found, trivia is silently skipped.

To test without waiting for a stream:

```bash
echo "Plan 9 from Outer Space" > ~/.rifftrax_now_playing.txt
```

To clear it:

```bash
rm ~/.rifftrax_now_playing.txt
```

> **Note:** If your Übersicht widgets directory is not the default, substitute your actual path in the `cp` command above.

---

## Configuration

Edit the config block at the top of `bot.py`:

```python
CHANNEL            = "rifftrax"                        # Twitch channel to watch
TRIGGERS           = ("!cmd edit movie", "!cmd edit !movie")  # Commands that signal a new movie
RIFFTRAX_URL_MARKER = "rifftrax.com/"                 # Substring present in StreamElements movie replies
NICK               = "justinfan70"                    # Any justinfan* username works for anonymous access
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
