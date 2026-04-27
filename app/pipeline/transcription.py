from __future__ import annotations

import time

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

    def transcribe(self, audio: AudioAsset, language_hint: str | None) -> TranscriptWordsResult:
        start_time = time.perf_counter()

        import whisperx

        asr_options = {
            "beam_size": 5,
            "condition_on_prev_text": False,
        }
        model = whisperx.load_model(
            self.settings.transcriber_model,
            self.settings.transcriber_device,
            compute_type=self.settings.transcriber_compute_type,
            language=language_hint,
            asr_options=asr_options,
        )
        audio_array = whisperx.load_audio(audio.normalized_path)
        initial_result = model.transcribe(audio_array, batch_size=self.settings.batch_size, language=language_hint)

        align_model, metadata = whisperx.load_align_model(
            language_code=initial_result["language"],
            device=self.settings.transcriber_device,
        )
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
