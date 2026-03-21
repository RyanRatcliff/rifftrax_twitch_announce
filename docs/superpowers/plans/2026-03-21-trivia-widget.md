# RiffTrax Trivia Widget Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Claude-powered trivia watcher script and a matching scrolling Übersicht desktop widget that displays RiffTrax-flavored trivia about whatever movie is currently playing.

**Architecture:** A polling Python script (`trivia_watcher.py`) watches `~/.rifftrax_now_playing.txt` for changes, calls the Claude API when the title changes, and writes the result to `~/.rifftrax_trivia.txt`. A new Übersicht widget (`widget/rifftrax-trivia.widget/index.coffee`) reads that file every 5s and displays the trivia as a CSS marquee ticker, matching the style of the existing now-playing widget.

**Tech Stack:** Python 3 + `anthropic` SDK, CoffeeScript + CSS (Übersicht), pytest + `unittest.mock`

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `trivia_watcher.py` | Create | Polls now-playing file, calls Claude, writes trivia file |
| `widget/rifftrax-trivia.widget/index.coffee` | Create | Übersicht widget: reads trivia file, CSS marquee display |
| `requirements.txt` | Create | Pin `anthropic` SDK version |
| `tests/test_trivia_watcher.py` | Create | Unit tests for watcher logic |

---

## Task 1: Dependencies

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: Create requirements.txt**

```
anthropic>=0.25.0
```

- [ ] **Step 2: Install**

```bash
pip install -r requirements.txt
```

Expected: installs without errors.

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "feat: add anthropic SDK dependency"
```

---

## Task 2: Watcher — file I/O helpers

Write and test the pure file-reading/writing functions that have no external dependencies.

**Files:**
- Create: `trivia_watcher.py` (skeleton + I/O helpers)
- Create: `tests/test_trivia_watcher.py`

- [ ] **Step 1: Write failing tests for file helpers**

Create `tests/test_trivia_watcher.py`:

```python
import os
import tempfile
import pytest


def test_read_title_returns_stripped_content(tmp_path):
    f = tmp_path / "now_playing.txt"
    f.write_text("Plan 9 from Outer Space\n")
    from trivia_watcher import read_file
    assert read_file(str(f)) == "Plan 9 from Outer Space"


def test_read_title_returns_empty_string_when_file_missing(tmp_path):
    from trivia_watcher import read_file
    assert read_file(str(tmp_path / "nonexistent.txt")) == ""


def test_write_trivia_creates_file(tmp_path):
    f = tmp_path / "trivia.txt"
    from trivia_watcher import write_file
    write_file(str(f), "This film was shot in four days.")
    assert f.read_text() == "This film was shot in four days."


def test_write_trivia_overwrites_existing(tmp_path):
    f = tmp_path / "trivia.txt"
    f.write_text("old content")
    from trivia_watcher import write_file
    write_file(str(f), "new content")
    assert f.read_text() == "new content"


def test_write_trivia_empty_string(tmp_path):
    f = tmp_path / "trivia.txt"
    from trivia_watcher import write_file
    write_file(str(f), "")
    assert f.read_text() == ""
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_trivia_watcher.py -v
```

Expected: `ModuleNotFoundError: No module named 'trivia_watcher'`

- [ ] **Step 3: Create trivia_watcher.py with file helpers**

```python
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_trivia_watcher.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add trivia_watcher.py tests/test_trivia_watcher.py
git commit -m "feat: trivia watcher skeleton with file I/O helpers"
```

---

## Task 3: Watcher — startup logic

Test and implement the startup decision: should we fetch trivia on startup, or skip because we already have it?

**Files:**
- Modify: `tests/test_trivia_watcher.py` (add tests)
- Modify: `trivia_watcher.py` (add `should_fetch_on_startup`)

- [ ] **Step 1: Write failing tests**

Append to `tests/test_trivia_watcher.py`:

```python
def test_should_fetch_when_title_present_trivia_absent():
    from trivia_watcher import should_fetch_on_startup
    assert should_fetch_on_startup(title="Manos: The Hands of Fate", existing_trivia="") is True


def test_should_not_fetch_when_title_present_trivia_present():
    from trivia_watcher import should_fetch_on_startup
    assert should_fetch_on_startup(
        title="Manos: The Hands of Fate",
        existing_trivia="Filmed in El Paso by a fertilizer salesman."
    ) is False


def test_should_not_fetch_when_title_absent():
    from trivia_watcher import should_fetch_on_startup
    assert should_fetch_on_startup(title="", existing_trivia="") is False


def test_should_not_fetch_when_title_absent_even_if_trivia_present():
    from trivia_watcher import should_fetch_on_startup
    assert should_fetch_on_startup(title="", existing_trivia="stale trivia") is False
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_trivia_watcher.py -v -k "should_fetch"
```

Expected: `ImportError` or `AttributeError`.

- [ ] **Step 3: Implement `should_fetch_on_startup`**

Add to `trivia_watcher.py`:

```python
def should_fetch_on_startup(title: str, existing_trivia: str) -> bool:
    """Return True if we should fetch trivia on startup."""
    if not title:
        return False
    return not existing_trivia
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_trivia_watcher.py -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add trivia_watcher.py tests/test_trivia_watcher.py
git commit -m "feat: trivia watcher startup fetch decision logic"
```

---

## Task 4: Watcher — Claude API integration

Test and implement the `fetch_trivia` function that calls Claude.

**Files:**
- Modify: `tests/test_trivia_watcher.py` (add tests)
- Modify: `trivia_watcher.py` (add `fetch_trivia`, `build_prompt`)

- [ ] **Step 1: Write failing tests**

Append to `tests/test_trivia_watcher.py`:

```python
from unittest.mock import MagicMock, patch


def test_fetch_trivia_returns_api_text():
    from trivia_watcher import fetch_trivia
    mock_client = MagicMock()
    mock_client.messages.create.return_value.content = [
        MagicMock(text="This film was made for $7,000 and a prayer.")
    ]
    result = fetch_trivia("Plan 9 from Outer Space", mock_client)
    assert result == "This film was made for $7,000 and a prayer."


def test_fetch_trivia_calls_correct_model():
    from trivia_watcher import fetch_trivia, MODEL
    mock_client = MagicMock()
    mock_client.messages.create.return_value.content = [MagicMock(text="trivia")]
    fetch_trivia("Plan 9", mock_client)
    call_kwargs = mock_client.messages.create.call_args[1]
    assert call_kwargs["model"] == MODEL


def test_fetch_trivia_includes_title_in_prompt():
    from trivia_watcher import fetch_trivia
    mock_client = MagicMock()
    mock_client.messages.create.return_value.content = [MagicMock(text="trivia")]
    fetch_trivia("Santa Claus Conquers the Martians", mock_client)
    call_kwargs = mock_client.messages.create.call_args[1]
    prompt_text = call_kwargs["messages"][0]["content"]
    assert "Santa Claus Conquers the Martians" in prompt_text


def test_fetch_trivia_returns_fallback_on_api_error():
    from trivia_watcher import fetch_trivia, FALLBACK_QUIP
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("API down")
    result = fetch_trivia("Plan 9", mock_client)
    assert result == FALLBACK_QUIP


def test_fetch_trivia_logs_error_on_api_failure(capsys):
    from trivia_watcher import fetch_trivia
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("timeout")
    fetch_trivia("Plan 9", mock_client)
    captured = capsys.readouterr()
    assert "timeout" in captured.out
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_trivia_watcher.py -v -k "fetch_trivia"
```

Expected: `ImportError`.

- [ ] **Step 3: Implement `build_prompt` and `fetch_trivia`**

Add to `trivia_watcher.py`:

```python
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_trivia_watcher.py -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add trivia_watcher.py tests/test_trivia_watcher.py
git commit -m "feat: trivia watcher Claude API integration"
```

---

## Task 5: Watcher — main loop and entry point

Wire everything together: API key loading, startup behavior, poll loop, and `run()`.

**Files:**
- Modify: `tests/test_trivia_watcher.py` (add tests)
- Modify: `trivia_watcher.py` (add `load_api_key`, `run`)

- [ ] **Step 1: Write failing tests**

Append to `tests/test_trivia_watcher.py`:

```python
def test_load_api_key_reads_key_from_file(tmp_path):
    key_file = tmp_path / "key"
    key_file.write_text("sk-ant-test123\n")
    from trivia_watcher import load_api_key
    assert load_api_key(str(key_file)) == "sk-ant-test123"


def test_load_api_key_exits_if_file_missing(tmp_path):
    from trivia_watcher import load_api_key
    with pytest.raises(SystemExit):
        load_api_key(str(tmp_path / "missing.txt"))


def test_load_api_key_exit_message_is_descriptive(tmp_path, capsys):
    from trivia_watcher import load_api_key
    try:
        load_api_key(str(tmp_path / "missing.txt"))
    except SystemExit:
        pass
    captured = capsys.readouterr()
    assert "~/.rifftrax_anthropic_key" in captured.out
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_trivia_watcher.py -v -k "load_api_key"
```

Expected: `ImportError`.

- [ ] **Step 3: Implement `load_api_key` and `run`**

Add to `trivia_watcher.py`:

```python
def load_api_key(path: str) -> str:
    """Read API key from file. Exits with clear message if missing."""
    try:
        with open(path) as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"[trivia-watcher] Error: API key file not found at ~/.rifftrax_anthropic_key")
        print(f"[trivia-watcher] Create it with your Anthropic API key as the only content.")
        sys.exit(1)


def run() -> None:
    import anthropic

    api_key = load_api_key(API_KEY_FILE)
    client  = anthropic.Anthropic(api_key=api_key)

    # Startup: decide whether to fetch immediately
    title          = read_file(NOW_PLAYING_FILE)
    existing_trivia = read_file(TRIVIA_FILE)
    last_title     = title  # initialize so first poll doesn't re-trigger

    if not title:
        write_file(TRIVIA_FILE, "")
    elif should_fetch_on_startup(title, existing_trivia):
        print(f"[trivia-watcher] Startup fetch for: {title!r}")
        write_file(TRIVIA_FILE, fetch_trivia(title, client))
    else:
        print(f"[trivia-watcher] Startup: trivia already present for {title!r}, skipping fetch")

    print(f"[trivia-watcher] Watching {NOW_PLAYING_FILE} ...")

    while True:
        try:
            time.sleep(POLL_INTERVAL)
            current_title = read_file(NOW_PLAYING_FILE)

            if current_title == last_title:
                continue

            last_title = current_title

            if not current_title:
                print("[trivia-watcher] Title cleared, hiding trivia")
                write_file(TRIVIA_FILE, "")
            else:
                print(f"[trivia-watcher] New title: {current_title!r}, fetching trivia...")
                write_file(TRIVIA_FILE, fetch_trivia(current_title, client))

        except KeyboardInterrupt:
            print("\n[trivia-watcher] Stopped.")
            return
        except Exception as e:
            print(f"[trivia-watcher] Unexpected error: {e}")


if __name__ == "__main__":
    run()
```

- [ ] **Step 4: Run all tests**

```bash
pytest tests/test_trivia_watcher.py -v
```

Expected: all pass.

- [ ] **Step 5: Smoke test manually**

```bash
# In one terminal:
echo "Manos: The Hands of Fate" > ~/.rifftrax_now_playing.txt
python3 trivia_watcher.py
```

Expected: watcher prints a startup fetch message, writes trivia to `~/.rifftrax_trivia.txt`.

```bash
# In another terminal — verify output:
cat ~/.rifftrax_trivia.txt
```

Expected: 2-3 sentences of RiffTrax-flavored trivia.

```bash
# Test title change:
echo "Santa Claus Conquers the Martians" > ~/.rifftrax_now_playing.txt
# Wait 5s — watcher should detect change and fetch new trivia
cat ~/.rifftrax_trivia.txt
```

```bash
# Test clear:
echo -n "" > ~/.rifftrax_now_playing.txt
# Wait 5s
cat ~/.rifftrax_trivia.txt
# Expected: empty file
```

- [ ] **Step 6: Commit**

```bash
git add trivia_watcher.py tests/test_trivia_watcher.py
git commit -m "feat: trivia watcher main loop and entry point"
```

---

## Task 6: Übersicht widget

Create the trivia widget. This is visual — no unit tests. Verify by loading in Übersicht.

**Files:**
- Create: `widget/rifftrax-trivia.widget/index.coffee`

- [ ] **Step 1: Create the widget directory and file**

```bash
mkdir -p widget/rifftrax-trivia.widget
```

Create `widget/rifftrax-trivia.widget/index.coffee`:

```coffeescript
command: "cat ~/.rifftrax_trivia.txt 2>/dev/null"

refreshFrequency: 5000

style: """
  top: 160px
  left: 40px
  font-family: -apple-system, BlinkMacSystemFont, sans-serif
  color: white
  background: rgba(0,0,0,0.75)
  border-left: 4px solid #e50914
  border-radius: 4px
  padding: 15px 22px
  max-width: 525px
  overflow: hidden
  display: none

  &.visible
    display: block

  .label
    font-size: 13px
    font-weight: 600
    letter-spacing: 0.12em
    text-transform: uppercase
    color: #e50914
    margin-bottom: 6px

  .ticker-wrap
    overflow: hidden
    width: 100%

  .ticker
    display: inline-block
    white-space: nowrap
    animation: marquee 25s linear infinite

  @keyframes marquee
    from
      transform: translateX(100vw)
    to
      transform: translateX(-100vw)
"""

render: (output) -> """
  <div class='label'>🎬 Trivia</div>
  <div class='ticker-wrap'>
    <span class='ticker'>#{output.trim()}</span>
  </div>
"""

update: (output, domEl) ->
  trivia = output.trim()
  $el = $(domEl)

  if trivia
    $ticker = $el.find('.ticker')
    if $ticker.text() != trivia
      $ticker.text(trivia)
    $el.addClass('visible')
  else
    $el.removeClass('visible')
```

- [ ] **Step 2: Verify widget loads in Übersicht**

Open Übersicht → Refresh All Widgets. The trivia widget should appear below the now-playing widget when `~/.rifftrax_trivia.txt` is non-empty.

```bash
echo "Test trivia line here." > ~/.rifftrax_trivia.txt
```

Expected: widget appears at roughly `top: 160px` with scrolling text. Adjust `top` value in the widget if it overlaps the now-playing widget on your screen.

- [ ] **Step 3: Verify hide behavior**

```bash
echo -n "" > ~/.rifftrax_trivia.txt
```

Wait up to 5s. Expected: widget disappears.

- [ ] **Step 4: Verify scroll animation doesn't restart on unchanged content**

Leave a non-empty trivia file in place. Watch the widget for 15+ seconds — the animation should scroll continuously without snapping back to the start on each 5s poll.

- [ ] **Step 5: Commit**

```bash
git add widget/rifftrax-trivia.widget/index.coffee
git commit -m "feat: add trivia scrolling widget"
```

---

## Task 7: End-to-end smoke test

Verify the full pipeline works together.

- [ ] **Step 1: Start the watcher**

```bash
python3 trivia_watcher.py &
```

- [ ] **Step 2: Simulate a title change**

```bash
echo "Pod People" > ~/.rifftrax_now_playing.txt
```

- [ ] **Step 3: Verify trivia appears**

Wait ~3s for the API call, then check:

```bash
cat ~/.rifftrax_trivia.txt
```

Expected: non-empty trivia text. Übersicht widget should show it scrolling.

- [ ] **Step 4: Simulate a title clear**

```bash
echo -n "" > ~/.rifftrax_now_playing.txt
```

Wait 5s. Expected: `~/.rifftrax_trivia.txt` is empty, widget is hidden.

- [ ] **Step 5: Stop the watcher**

```bash
kill %1
```

- [ ] **Step 6: Final commit if any adjustments made**

```bash
git add -A
git commit -m "chore: end-to-end verified, adjust trivia widget position if needed"
```

---

## Running Tests

```bash
# All tests:
pytest tests/ -v

# Watcher only:
pytest tests/test_trivia_watcher.py -v
```

No external services are called in tests — all Claude API calls are mocked.
