import pytest
from unittest.mock import MagicMock
from bot import (
    extract_title,
    parse_privmsg,
    build_prompt,
    strip_url,
    read_file,
    write_file,
    should_fetch_on_startup,
    fetch_trivia,
    load_api_key,
    FALLBACK_QUIP,
    MODEL,
    TRIGGERS,
)


# ── File I/O ──────────────────────────────────────────────────────────────────

def test_read_title_returns_stripped_content(tmp_path):
    f = tmp_path / "now_playing.txt"
    f.write_text("Plan 9 from Outer Space\n")
    assert read_file(str(f)) == "Plan 9 from Outer Space"


def test_read_title_returns_empty_string_when_file_missing(tmp_path):
    assert read_file(str(tmp_path / "nonexistent.txt")) == ""


def test_write_trivia_creates_file(tmp_path):
    f = tmp_path / "trivia.txt"
    write_file(str(f), "This film was shot in four days.")
    assert f.read_text() == "This film was shot in four days."


def test_write_trivia_overwrites_existing(tmp_path):
    f = tmp_path / "trivia.txt"
    f.write_text("old content")
    write_file(str(f), "new content")
    assert f.read_text() == "new content"


def test_write_trivia_empty_string(tmp_path):
    f = tmp_path / "trivia.txt"
    write_file(str(f), "")
    assert f.read_text() == ""


# ── extract_title ─────────────────────────────────────────────────────────────

def test_extract_title_strips_trigger_and_returns_title():
    trigger = TRIGGERS[0]  # "!cmd edit movie"
    assert extract_title(f"{trigger} Manos: The Hands of Fate", trigger) == "Manos: The Hands of Fate"


def test_extract_title_strips_trailing_url():
    trigger = TRIGGERS[0]
    assert extract_title(f"{trigger} Plan 9 from Outer Space https://rifftrax.com/plan9", trigger) == "Plan 9 from Outer Space"


def test_extract_title_returns_fallback_when_only_url():
    trigger = TRIGGERS[0]
    assert extract_title(f"{trigger} https://rifftrax.com/plan9", trigger) == "New RiffTrax presentation starting!"


def test_extract_title_returns_fallback_when_empty():
    trigger = TRIGGERS[0]
    assert extract_title(f"{trigger} ", trigger) == "New RiffTrax presentation starting!"


def test_extract_title_works_with_second_trigger_variant():
    trigger = TRIGGERS[1]  # "!cmd edit !movie"
    assert extract_title(f"{trigger} Santa Claus Conquers the Martians", trigger) == "Santa Claus Conquers the Martians"


def test_extract_title_strips_url_mid_title_tokens():
    # Only http-prefixed tokens are filtered; non-URL words are kept
    trigger = TRIGGERS[0]
    assert extract_title(f"{trigger} The Film https://example.com", trigger) == "The Film"


# ── parse_privmsg ─────────────────────────────────────────────────────────────

def test_parse_privmsg_returns_username_and_message():
    line = ":rifferfan!rifferfan@rifferfan.tmi.twitch.tv PRIVMSG #rifftrax :Hello there!"
    result = parse_privmsg(line)
    assert result == ("rifferfan", "Hello there!")


def test_parse_privmsg_returns_none_for_non_privmsg():
    assert parse_privmsg("PING :tmi.twitch.tv") is None


def test_parse_privmsg_returns_none_for_server_join():
    assert parse_privmsg(":rifferfan!rifferfan@rifferfan.tmi.twitch.tv JOIN #rifftrax") is None


def test_parse_privmsg_returns_none_for_empty_line():
    assert parse_privmsg("") is None


def test_parse_privmsg_extracts_trigger_command():
    line = ":streamadmin!streamadmin@streamadmin.tmi.twitch.tv PRIVMSG #rifftrax :!cmd edit movie Plan 9"
    username, message = parse_privmsg(line)
    assert username == "streamadmin"
    assert message == "!cmd edit movie Plan 9"


def test_parse_privmsg_handles_message_with_colon():
    line = ":user!user@user.tmi.twitch.tv PRIVMSG #rifftrax :This: has colons: in it"
    username, message = parse_privmsg(line)
    assert username == "user"
    assert message == "This: has colons: in it"


# ── strip_url ─────────────────────────────────────────────────────────────────

def test_strip_url_removes_trailing_url():
    assert strip_url("Plan 9 from Outer Space https://rifftrax.com/plan9") == "Plan 9 from Outer Space"


def test_strip_url_returns_text_unchanged_when_no_url():
    assert strip_url("Plan 9 from Outer Space") == "Plan 9 from Outer Space"


# ── build_prompt ──────────────────────────────────────────────────────────────

def test_build_prompt_contains_title():
    prompt = build_prompt("Manos: The Hands of Fate")
    assert "Manos: The Hands of Fate" in prompt


def test_build_prompt_contains_rifftrax_voice_instructions():
    prompt = build_prompt("Plan 9")
    assert "RiffTrax" in prompt
    assert "dry wit" in prompt


def test_build_prompt_wraps_title_in_delimiters():
    # Title should be isolated in XML delimiters to reduce prompt injection surface
    prompt = build_prompt("Some Title")
    assert "<title>Some Title</title>" in prompt


# ── should_fetch_on_startup ───────────────────────────────────────────────────

def test_should_fetch_when_title_present_trivia_absent():
    assert should_fetch_on_startup(title="Manos: The Hands of Fate", existing_trivia="") is True


def test_should_not_fetch_when_title_present_trivia_present():
    assert should_fetch_on_startup(
        title="Manos: The Hands of Fate",
        existing_trivia="Filmed in El Paso by a fertilizer salesman."
    ) is False


def test_should_not_fetch_when_title_absent():
    assert should_fetch_on_startup(title="", existing_trivia="") is False


def test_should_not_fetch_when_title_absent_even_if_trivia_present():
    assert should_fetch_on_startup(title="", existing_trivia="stale trivia") is False


# ── fetch_trivia ──────────────────────────────────────────────────────────────

def test_fetch_trivia_returns_api_text():
    mock_client = MagicMock()
    mock_client.messages.create.return_value.content = [
        MagicMock(text="This film was made for $7,000 and a prayer.")
    ]
    result = fetch_trivia("Plan 9 from Outer Space", mock_client)
    assert result == "This film was made for $7,000 and a prayer."


def test_fetch_trivia_calls_correct_model():
    mock_client = MagicMock()
    mock_client.messages.create.return_value.content = [MagicMock(text="trivia")]
    fetch_trivia("Plan 9", mock_client)
    assert mock_client.messages.create.call_args.kwargs["model"] == MODEL


def test_fetch_trivia_includes_title_in_prompt():
    mock_client = MagicMock()
    mock_client.messages.create.return_value.content = [MagicMock(text="trivia")]
    fetch_trivia("Santa Claus Conquers the Martians", mock_client)
    prompt_text = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "Santa Claus Conquers the Martians" in prompt_text


def test_fetch_trivia_returns_fallback_on_api_error():
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("API down")
    result = fetch_trivia("Plan 9", mock_client)
    assert result == FALLBACK_QUIP


def test_fetch_trivia_logs_error_on_api_failure(capsys):
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("timeout")
    fetch_trivia("Plan 9", mock_client)
    captured = capsys.readouterr()
    assert "timeout" in captured.out


# ── load_api_key ──────────────────────────────────────────────────────────────

def test_load_api_key_reads_key_from_file(tmp_path):
    key_file = tmp_path / "key"
    key_file.write_text("sk-ant-test123\n")
    assert load_api_key(str(key_file)) == "sk-ant-test123"


def test_load_api_key_returns_none_if_file_missing(tmp_path):
    assert load_api_key(str(tmp_path / "missing.txt")) is None
