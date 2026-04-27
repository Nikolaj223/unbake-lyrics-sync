from app.pipeline.formatting import build_lines_from_words, format_lrc_timestamp, format_synced_lyrics
from app.pipeline.types import WordTiming


def test_build_lines_from_words_splits_on_gap() -> None:
    words = [
        WordTiming(text="hello", start_ms=100, end_ms=300),
        WordTiming(text="world", start_ms=320, end_ms=520),
        WordTiming(text="again", start_ms=1400, end_ms=1700),
    ]
    lines = build_lines_from_words(words, gap_threshold_ms=600)
    assert len(lines) == 2
    assert lines[0].text == "hello world"
    assert lines[1].text == "again"


def test_format_lrc_timestamp() -> None:
    assert format_lrc_timestamp(12340) == "00:12.34"


def test_format_synced_lyrics() -> None:
    words = [
        WordTiming(text="hello", start_ms=0, end_ms=200),
        WordTiming(text="world", start_ms=220, end_ms=400),
    ]
    lines = build_lines_from_words(words)
    synced = format_synced_lyrics(lines)
    assert synced.startswith("[00:00.00] hello world")
