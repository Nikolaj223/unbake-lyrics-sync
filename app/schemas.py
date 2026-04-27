from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


def to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.capitalize() for part in tail)


class APIModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class CreateLyricsJobRequest(APIModel):
    audio_url: HttpUrl
    language_hint: str | None = Field(default=None, description="ISO language hint, e.g. en/ru/es/ja")
    track_name: str | None = None
    artist_name: str | None = None
    album_name: str | None = None
    duration_ms: int | None = None
    shazam_track_id: str | None = None
    is_custom_cover: bool = False


class WordTimestamp(APIModel):
    text: str
    start_ms: int
    end_ms: int
    confidence: float | None = None


class LyricsPayload(APIModel):
    language: str
    source: Literal["asr_baseline", "catalog_reference", "hybrid_reference_alignment"]
    plain_lyrics: str
    synced_lyrics: str
    words: list[WordTimestamp]
    cost_estimate_usd: float | None = None
    debug: dict[str, object] = Field(default_factory=dict)


class LyricsJobAcceptedResponse(APIModel):
    job_id: str
    status: Literal["queued"]
    status_url: str


class LyricsJobStatusResponse(APIModel):
    job_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    created_at: datetime
    updated_at: datetime
    result: LyricsPayload | None = None
    error: str | None = None
