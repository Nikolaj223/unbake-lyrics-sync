from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, HttpUrl


class CreateLyricsJobRequest(BaseModel):
    audio_url: HttpUrl
    language_hint: str | None = Field(default=None, description="ISO language hint, e.g. en/ru/es/ja")
    track_name: str | None = None
    artist_name: str | None = None
    album_name: str | None = None
    duration_ms: int | None = None
    shazam_track_id: str | None = None
    is_custom_cover: bool = False


class WordTimestamp(BaseModel):
    text: str
    start_ms: int
    end_ms: int
    confidence: float | None = None


class LyricsPayload(BaseModel):
    language: str
    source: Literal["asr_baseline", "catalog_reference", "hybrid_reference_alignment"]
    plain_lyrics: str
    synced_lyrics: str
    words: list[WordTimestamp]
    cost_estimate_usd: float | None = None
    debug: dict[str, object] = Field(default_factory=dict)


class LyricsJobAcceptedResponse(BaseModel):
    job_id: str
    status: Literal["queued"]
    status_url: str


class LyricsJobStatusResponse(BaseModel):
    job_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    created_at: datetime
    updated_at: datetime
    result: LyricsPayload | None = None
    error: str | None = None
