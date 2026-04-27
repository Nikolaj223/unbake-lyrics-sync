from __future__ import annotations

import httpx

from .types import ReferenceLyricsCandidate


class LRCLibRetriever:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def find(self, track_name: str | None, artist_name: str | None, duration_ms: int | None) -> ReferenceLyricsCandidate | None:
        if not track_name or not artist_name:
            return None

        params = {
            "track_name": track_name,
            "artist_name": artist_name,
        }
        if duration_ms:
            params["duration"] = round(duration_ms / 1000)

        response = httpx.get(f"{self.base_url}/api/get", params=params, timeout=10.0)
        if response.status_code != 200:
            return None

        payload = response.json()
        plain_lyrics = payload.get("plainLyrics")
        if not plain_lyrics:
            return None

        return ReferenceLyricsCandidate(
            track_name=payload.get("trackName", track_name),
            artist_name=payload.get("artistName", artist_name),
            plain_lyrics=plain_lyrics,
            synced_lyrics=payload.get("syncedLyrics"),
        )
