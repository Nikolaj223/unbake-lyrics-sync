from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

from app.config import Settings
from app.pipeline.formatting import build_lines_from_words, format_plain_lyrics, format_synced_lyrics
from app.pipeline.preprocessing import AudioPreprocessor
from app.pipeline.transcription import WhisperXTranscriber
from evaluation.metrics import aggregate, aggregate_by_language, evaluate_record, load_manifest
from evaluation.reporting import render_markdown_report


LANGUAGE_HINT_ALIASES = {
    "jp": "ja",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the real WhisperX baseline and write prediction JSONL.")
    parser.add_argument("--manifest", required=True, help="JSONL with audioPath/audioUrl and reference fields")
    parser.add_argument("--output", required=True, help="Where to write prediction JSONL")
    parser.add_argument("--metrics-output", help="Optional path to write metrics JSON")
    parser.add_argument("--markdown-output", help="Optional path to write a markdown report")
    parser.add_argument("--tmp-dir", default="./tmp/eval", help="Temporary directory for normalized audio")
    parser.add_argument("--model", default="large-v3", help="WhisperX/faster-whisper model name")
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu"], help="Inference device")
    parser.add_argument("--compute-type", default="float16", help="faster-whisper compute type")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-duration-sec", type=int, default=600)
    parser.add_argument("--gpu-price-per-second", type=float, default=0.00016)
    parser.add_argument("--only-id", action="append", help="Run only selected sample id; can be passed multiple times")
    parser.add_argument("--limit", type=int, help="Optional number of samples to run")
    parser.add_argument("--continue-on-error", action="store_true", help="Write failed rows and continue")
    args = parser.parse_args()

    settings = Settings(
        tmp_dir=args.tmp_dir,
        max_audio_duration_sec=args.max_duration_sec,
        transcriber_model=args.model,
        transcriber_device=args.device,
        transcriber_compute_type=args.compute_type,
        batch_size=args.batch_size,
        gpu_price_per_second=args.gpu_price_per_second,
    )
    preprocessor = AudioPreprocessor(
        tmp_dir=settings.tmp_dir,
        max_audio_duration_sec=settings.max_audio_duration_sec,
    )
    transcriber = WhisperXTranscriber(settings)

    manifest = load_manifest(args.manifest)
    if args.only_id:
        selected_ids = set(args.only_id)
        manifest = [record for record in manifest if record.get("id") in selected_ids]
    if args.limit:
        manifest = manifest[: args.limit]

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    metric_rows: list[dict[str, object]] = []
    with output_path.open("w", encoding="utf-8") as file_handle:
        for record in manifest:
            try:
                prediction_record = run_record(record, preprocessor, transcriber)
                if has_reference_and_prediction(prediction_record):
                    metric_rows.append(evaluate_record(prediction_record))
            except Exception as error:
                if not args.continue_on_error:
                    raise
                prediction_record = {
                    "id": record.get("id"),
                    "language": normalize_language(str(record.get("language", ""))),
                    "error": str(error),
                    "reference": record.get("reference"),
                }
            file_handle.write(json.dumps(prediction_record, ensure_ascii=False) + "\n")

    report = {
        "summary": aggregate(metric_rows),
        "by_language": aggregate_by_language(metric_rows),
        "rows": metric_rows,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.metrics_output:
        metrics_path = Path(args.metrics_output)
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_path.write_text(rendered + "\n", encoding="utf-8")
    if args.markdown_output:
        markdown_path = Path(args.markdown_output)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(render_markdown_report(report, " ".join(sys.argv)), encoding="utf-8")
    print(rendered)


def run_record(
    record: dict[str, object],
    preprocessor: AudioPreprocessor,
    transcriber: WhisperXTranscriber,
) -> dict[str, object]:
    source = get_audio_source(record)
    language = normalize_language(str(record["language"]))
    language_hint = LANGUAGE_HINT_ALIASES.get(language, language)

    audio = preprocessor.prepare(source) if is_url(source) else preprocessor.prepare_local_file(source)
    try:
        transcript = transcriber.transcribe(audio, language_hint)
    finally:
        preprocessor.cleanup(audio)

    lines = build_lines_from_words(transcript.words)
    prediction = {
        "text": format_plain_lyrics(lines),
        "syncedLyrics": format_synced_lyrics(lines),
        "words": [
            {
                "text": word.text,
                "start_ms": word.start_ms,
                "end_ms": word.end_ms,
                "confidence": word.confidence,
            }
            for word in transcript.words
        ],
    }
    return {
        "id": record["id"],
        "language": language,
        "audioPath": record.get("audioPath") or record.get("audio_path"),
        "audioUrl": record.get("audioUrl") or record.get("audio_url"),
        "reference": record.get("reference"),
        "prediction": prediction,
        "runtime": {
            "elapsed_seconds": transcript.debug.get("elapsed_seconds"),
            "cost_estimate_usd": transcript.cost_estimate_usd,
            "model": transcript.debug.get("model"),
            "device": transcript.debug.get("device"),
            "duration_ms": audio.duration_ms,
        },
    }


def get_audio_source(record: dict[str, object]) -> str:
    source = record.get("audioPath") or record.get("audio_path") or record.get("audioUrl") or record.get("audio_url")
    if not source:
        raise ValueError(f"Record {record.get('id')} has no audioPath/audioUrl")
    return str(source)


def has_reference_and_prediction(record: dict[str, object]) -> bool:
    return bool(record.get("reference")) and bool(record.get("prediction")) and not record.get("error")


def normalize_language(language: str) -> str:
    return language.strip().lower()


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"}


if __name__ == "__main__":
    main()
