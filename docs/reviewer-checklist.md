# Reviewer checklist

## What to read first

1. [docs/design.md](./design.md)
2. [docs/evaluation-results.md](./evaluation-results.md)
3. [evaluation/run_asr.py](../evaluation/run_asr.py)
4. [evaluation/metrics.py](../evaluation/metrics.py)
5. [app/pipeline/transcription.py](../app/pipeline/transcription.py)

## What is implemented

- clear API contract
- async job flow
- baseline preprocessing/transcription/alignment architecture
- output formatter for `plainLyrics + syncedLyrics + words[]`
- real ASR benchmark runner that produces `predictions.jsonl`
- automatic evaluation code for transcript and timestamp quality

## What is intentionally lightweight

- storage is in-memory in this take-home code
- production Postgres schema is included in [`docs/postgres-schema.sql`](./postgres-schema.sql), but not fully wired into the demo code
- hybrid catalog-reference alignment is described as the next product step, while code stays on the reliable ASR baseline

## What I would ask on follow-up

- why async API instead of sync
- why `wav 16k mono` internally
- why `WhisperX` over plain Whisper or hosted APIs
- how hallucination risk is measured
- how the reported cost was computed from actual runtime
- why Shazam/catalog hints should be advisory, not authoritative
