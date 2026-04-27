from __future__ import annotations

import time
from typing import Any

from ..config import Settings

from .types import AudioAsset, TranscriptWordsResult, WordTiming


class WhisperXTranscriber:
    """
    Concrete baseline:
    - ASR: faster-whisper backend through WhisperX
    - alignment: WhisperX forced alignment
    - output: word-level timestamps

    The code is intentionally dependency-light at import time:
    heavy ASR libraries are imported only inside transcribe().
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._models: dict[tuple[str, str, str, str | None], Any] = {}
        self._align_models: dict[tuple[str, str], tuple[Any, Any]] = {}

    def transcribe(self, audio: AudioAsset, language_hint: str | None) -> TranscriptWordsResult:
        start_time = time.perf_counter()

        import whisperx

        model = self._load_model(whisperx, language_hint)
        audio_array = whisperx.load_audio(audio.normalized_path)
        initial_result = model.transcribe(audio_array, batch_size=self.settings.batch_size, language=language_hint)

        align_model, metadata = self._load_align_model(whisperx, str(initial_result["language"]))
        aligned_result = whisperx.align(
            initial_result["segments"],
            align_model,
            metadata,
            audio_array,
            self.settings.transcriber_device,
            return_char_alignments=False,
        )

        words: list[WordTiming] = []
        for segment in aligned_result["segments"]:
            for word in segment.get("words", []):
                if word.get("start") is None or word.get("end") is None:
                    continue
                words.append(
                    WordTiming(
                        text=str(word["word"]).strip(),
                        start_ms=round(float(word["start"]) * 1000),
                        end_ms=round(float(word["end"]) * 1000),
                        confidence=float(word["score"]) if word.get("score") is not None else None,
                    )
                )

        elapsed_seconds = time.perf_counter() - start_time
        cost_estimate_usd = round(elapsed_seconds * self.settings.gpu_price_per_second, 6)
        return TranscriptWordsResult(
            language=initial_result["language"],
            words=words,
            cost_estimate_usd=cost_estimate_usd,
            debug={
                "segments_before_alignment": len(initial_result.get("segments", [])),
                "aligned_segments": len(aligned_result.get("segments", [])),
                "elapsed_seconds": round(elapsed_seconds, 3),
                "model": self.settings.transcriber_model,
                "device": self.settings.transcriber_device,
                "reference_candidate_used": False,
            },
        )

    def _load_model(self, whisperx: Any, language_hint: str | None) -> Any:
        key = (
            self.settings.transcriber_model,
            self.settings.transcriber_device,
            self.settings.transcriber_compute_type,
            language_hint,
        )
        if key not in self._models:
            asr_options = {
                "beam_size": 5,
            }
            self._models[key] = whisperx.load_model(
                self.settings.transcriber_model,
                self.settings.transcriber_device,
                compute_type=self.settings.transcriber_compute_type,
                language=language_hint,
                asr_options=asr_options,
            )
        return self._models[key]

    def _load_align_model(self, whisperx: Any, language: str) -> tuple[Any, Any]:
        key = (language, self.settings.transcriber_device)
        if key not in self._align_models:
            self._align_models[key] = whisperx.load_align_model(
                language_code=language,
                device=self.settings.transcriber_device,
            )
        return self._align_models[key]
