from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class AudioAsset:
    source_url: str
    downloaded_path: str
    normalized_path: str
    original_format: str
    duration_ms: int | None
    sample_rate_hz: int = 16_000
    channels: int = 1


@dataclass(slots=True)
class WordTiming:
    text: str
    start_ms: int
    end_ms: int
    confidence: float | None = None


@dataclass(slots=True)
class LineTiming:
    text: str
    start_ms: int


@dataclass(slots=True)
class TranscriptWordsResult:
    language: str
    words: list[WordTiming]
    debug: dict[str, object] = field(default_factory=dict)
    cost_estimate_usd: float | None = None


@dataclass(slots=True)
class ReferenceLyricsCandidate:
    track_name: str
    artist_name: str
    plain_lyrics: str
    synced_lyrics: str | None
