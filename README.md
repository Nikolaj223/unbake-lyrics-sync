# Unbake Lyrics Sync

Take-home solution for `timestamped lyrics from isolated vocals`.

## What is inside

- short design doc: [docs/design.md](./docs/design.md)
- reviewer checklist: [docs/reviewer-checklist.md](./docs/reviewer-checklist.md)
- production Postgres sketch: [docs/postgres-schema.sql](./docs/postgres-schema.sql)
- FastAPI skeleton for async job API: [app/main.py](./app/main.py)
- ASR pipeline baseline with `WhisperX + faster-whisper`: [app/pipeline/transcription.py](./app/pipeline/transcription.py)
- evaluation code for text and timestamp quality: [evaluation/metrics.py](./evaluation/metrics.py)
- dataset manifest format and curation notes: [datasets/README.md](./datasets/README.md)

## Proposed API shape

- `POST /v1/lyrics/jobs`
- `GET /v1/lyrics/jobs/{job_id}`
- `GET /healthz`

The API is asynchronous on purpose: mobile clients should not wait on a long request while audio is downloaded, normalized, transcribed and aligned.

For the take-home code the repository is intentionally in-memory, but the Postgres schema I would use in production is included separately.

## Core idea

The production recommendation in the design doc is:

1. accept `m4a` presigned URL
2. normalize internally to `wav 16 kHz mono pcm_s16le`
3. run `WhisperX` for multilingual ASR + word alignment
4. format output into `plainLyrics`, `syncedLyrics` and `words[]`
5. measure quality with `WER/CER + timestamp MAE/P90 + hallucination rate`

There is also a product direction for a hybrid path with catalog hints, but the baseline code here intentionally stays simple and reliable.

## Why convert away from M4A

Keep `m4a` at the API boundary because that is what the client already has after Demucs.

Convert internally to `wav` because:

- alignment tools work more predictably on PCM audio
- it removes codec ambiguity during evaluation
- it gives deterministic preprocessing for all languages

## Quick start

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
```

Optional ASR extras:

```bash
pip install -e ".[dev,asr]"
```

## Evaluate predictions

Input format is `jsonl` with one sample per line.

```bash
python -m evaluation.cli --manifest ./datasets/manifest.example.jsonl
```

## Important note

In this working environment `python` is not available in `PATH`, so the project files and tests were prepared carefully but not executed here locally. The deliverable is structured so it can be run on a normal Python 3.11+ machine.
