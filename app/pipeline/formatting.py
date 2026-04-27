from __future__ import annotations

from .types import LineTiming, WordTiming


def build_lines_from_words(
    words: list[WordTiming],
    max_chars_per_line: int = 42,
    gap_threshold_ms: int = 650,
) -> list[LineTiming]:
    if not words:
        return []

    lines: list[LineTiming] = []
    current_words: list[str] = []
    current_start_ms = words[0].start_ms
    previous_end_ms = words[0].start_ms

    for word in words:
        gap = word.start_ms - previous_end_ms
        candidate_text = " ".join([*current_words, word.text]).strip()
        should_split = bool(current_words) and (
            gap >= gap_threshold_ms or len(candidate_text) > max_chars_per_line
        )

        if should_split:
            lines.append(LineTiming(text=" ".join(current_words), start_ms=current_start_ms))
            current_words = [word.text]
            current_start_ms = word.start_ms
        else:
            current_words.append(word.text)

        previous_end_ms = word.end_ms

    if current_words:
        lines.append(LineTiming(text=" ".join(current_words), start_ms=current_start_ms))

    return lines


def format_synced_lyrics(lines: list[LineTiming]) -> str:
    return "\n".join(f"[{format_lrc_timestamp(line.start_ms)}] {line.text}" for line in lines)


def format_plain_lyrics(lines: list[LineTiming]) -> str:
    return "\n".join(line.text for line in lines)


def format_lrc_timestamp(milliseconds: int) -> str:
    total_centiseconds = round(milliseconds / 10)
    minutes, centiseconds = divmod(total_centiseconds, 6000)
    seconds, centiseconds = divmod(centiseconds, 100)
    return f"{minutes:02d}:{seconds:02d}.{centiseconds:02d}"
