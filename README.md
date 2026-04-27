# Unbake Lyrics Sync

Take-home solution for timestamped lyrics from `htdemucs v4` vocal stems.

## What is inside

- design doc: [docs/design.md](./docs/design.md)
- benchmark protocol and result table: [docs/evaluation-results.md](./docs/evaluation-results.md)
- FastAPI async job API: [app/main.py](./app/main.py)
- WhisperX/faster-whisper baseline: [app/pipeline/transcription.py](./app/pipeline/transcription.py)
- real ASR benchmark runner: [evaluation/run_asr.py](./evaluation/run_asr.py)
- scoring code: [evaluation/metrics.py](./evaluation/metrics.py)
- dataset manifest format: [datasets/README.md](./datasets/README.md)
- production Postgres sketch: [docs/postgres-schema.sql](./docs/postgres-schema.sql)

## API shape

- `POST /v1/lyrics/jobs`
- `GET /v1/lyrics/jobs/{jobId}`
- `GET /healthz`

Request fields accept camelCase and snake_case. Responses use camelCase to stay close to LRCLib naming:

```json
{
  "jobId": "c3a5...",
  "status": "completed",
  "result": {
    "language": "en",
    "source": "asr_baseline",
    "plainLyrics": "Hello from the other side",
    "syncedLyrics": "[00:00.12] Hello from the other side",
    "words": [
      { "text": "Hello", "startMs": 120, "endMs": 480, "confidence": 0.97 }
    ],
    "costEstimateUsd": 0.004
  }
}
```

## Pipeline

1. Accept `m4a 256 kbps` from an S3 presigned URL.
2. Normalize internally to `wav 16 kHz mono pcm_s16le`.
3. Run WhisperX with faster-whisper and forced alignment.
4. Return `plainLyrics`, `syncedLyrics`, and word timestamps.
5. Score real outputs with `WER`, `CER`, hallucination rate, timestamp MAE/P90, IoU, latency, and estimated cost.

## Setup

Requirements:

- Python 3.11 or 3.12
- ffmpeg and ffprobe in `PATH`
- CUDA GPU for the recommended `large-v3` benchmark

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev,asr]"
cp .env.example .env
pytest -q
```

Run the API:

```bash
uvicorn app.main:app --reload
```

## Benchmark

Create `datasets/benchmark_manifest.jsonl` from the provided Yandex Disk vocals or your own clips separated with `htdemucs v4`, not `ft`. Keep at least one sample per required language: `fr`, `it`, `ru`, `en`, `pt`, `es`, `ja`, `pl`.

Run the actual ASR baseline:

```bash
python -m evaluation.run_asr \
  --manifest ./datasets/benchmark_manifest.jsonl \
  --output ./results/predictions.jsonl \
  --metrics-output ./results/metrics.json \
  --markdown-output ./docs/evaluation-results.md \
  --device cuda \
  --model large-v3
```

Re-score existing predictions:

```bash
python -m evaluation.cli \
  --manifest ./results/predictions.jsonl \
  --output ./results/metrics.json \
  --markdown-output ./docs/evaluation-results.md
```

The design is intentionally tied to this run: without measured rows in [docs/evaluation-results.md](./docs/evaluation-results.md), the cost/accuracy claims are not defensible.
