from __future__ import annotations

from ..schemas import CreateLyricsJobRequest, LyricsPayload, WordTimestamp

from .formatting import build_lines_from_words, format_plain_lyrics, format_synced_lyrics
from .preprocessing import AudioPreprocessor
from .retrieval import LRCLibRetriever
from .transcription import WhisperXTranscriber


class LyricsSyncOrchestrator:
    def __init__(
        self,
        preprocessor: AudioPreprocessor,
        transcriber: WhisperXTranscriber,
        retriever: LRCLibRetriever,
    ) -> None:
        self.preprocessor = preprocessor
        self.transcriber = transcriber
        self.retriever = retriever

    def run(self, request: CreateLyricsJobRequest) -> LyricsPayload:
        audio = self.preprocessor.prepare(str(request.audio_url))
        reference_candidate = None

        try:
            reference_candidate = self.retriever.find(
                track_name=request.track_name,
                artist_name=request.artist_name,
                duration_ms=request.duration_ms,
            )

            transcript = self.transcriber.transcribe(audio, request.language_hint)
            lines = build_lines_from_words(transcript.words)

            return LyricsPayload(
                language=transcript.language,
                source="asr_baseline",
                plain_lyrics=format_plain_lyrics(lines),
                synced_lyrics=format_synced_lyrics(lines),
                words=[
                    WordTimestamp(
                        text=word.text,
                        start_ms=word.start_ms,
                        end_ms=word.end_ms,
                        confidence=word.confidence,
                    )
                    for word in transcript.words
                ],
                cost_estimate_usd=transcript.cost_estimate_usd,
                debug={
                    **transcript.debug,
                    "reference_candidate_found": reference_candidate is not None,
                    "reference_candidate_artist": (
                        reference_candidate.artist_name if reference_candidate else None
                    ),
                },
            )
        finally:
            self.preprocessor.cleanup(audio)
