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
