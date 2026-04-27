from app.schemas import CreateLyricsJobRequest, LyricsPayload, WordTimestamp


def test_request_accepts_lrclib_style_camel_case() -> None:
    request = CreateLyricsJobRequest.model_validate(
        {
            "audioUrl": "https://bucket.example.com/vocals.m4a",
            "languageHint": "en",
            "trackName": "Custom Cover",
            "artistName": "Singer",
            "durationMs": 180000,
            "shazamTrackId": "shazam-123",
            "isCustomCover": True,
        }
    )
    assert str(request.audio_url) == "https://bucket.example.com/vocals.m4a"
    assert request.track_name == "Custom Cover"
    assert request.is_custom_cover is True


def test_payload_serializes_plain_and_synced_lyrics_like_lrclib() -> None:
    payload = LyricsPayload(
        language="en",
        source="asr_baseline",
        plain_lyrics="hello world",
        synced_lyrics="[00:00.00] hello world",
        words=[WordTimestamp(text="hello", start_ms=0, end_ms=250, confidence=0.9)],
        cost_estimate_usd=0.004,
    )
    serialized = payload.model_dump(by_alias=True)
    assert serialized["plainLyrics"] == "hello world"
    assert serialized["syncedLyrics"] == "[00:00.00] hello world"
    assert serialized["words"][0]["startMs"] == 0
    assert serialized["costEstimateUsd"] == 0.004
