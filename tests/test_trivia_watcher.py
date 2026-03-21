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
