# Reviewer checklist

## What to read first

1. [docs/design.md](./design.md)
2. [evaluation/metrics.py](../evaluation/metrics.py)
3. [app/pipeline/transcription.py](../app/pipeline/transcription.py)

## What is implemented

- clear API contract
- async job flow
- baseline preprocessing/transcription/alignment architecture
- output formatter for `plainLyrics + syncedLyrics + words[]`
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
- why Shazam/catalog hints should be advisory, not authoritative
