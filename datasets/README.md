# Dataset Notes

The benchmark must use vocals separated with `htdemucs v4`, not `htdemucs_ft`. Regular speech audio is not representative because the real input contains music bleed, reverb, doubled vocals, and Demucs artifacts.

## Benchmark manifest

`evaluation.run_asr` expects one JSON object per line:

```json
{
  "id": "en-001",
  "language": "en",
  "audioPath": "./datasets/benchmark/en-001/vocals.m4a",
  "trackName": "optional title",
  "artistName": "optional artist",
  "durationMs": 45000,
  "reference": {
    "text": "hello from the other side",
    "words": [
      { "text": "hello", "start_ms": 120, "end_ms": 480 },
      { "text": "from", "start_ms": 500, "end_ms": 680 }
    ]
  }
}
```

Use `audioUrl` instead of `audioPath` when the clip is reachable by presigned URL.

## Scored predictions manifest

`evaluation.run_asr` writes the format consumed by `evaluation.cli`:

```json
{
  "id": "en-001",
  "language": "en",
  "reference": {
    "text": "hello from the other side",
    "words": [
      { "text": "hello", "start_ms": 120, "end_ms": 480 }
    ]
  },
  "prediction": {
    "text": "hello from the other side",
    "syncedLyrics": "[00:00.12] hello from the other side",
    "words": [
      { "text": "hello", "start_ms": 100, "end_ms": 470, "confidence": 0.97 }
    ]
  },
  "runtime": {
    "elapsed_seconds": 22.4,
    "cost_estimate_usd": 0.003584,
    "model": "large-v3",
    "device": "cuda",
    "duration_ms": 45000
  }
}
```

## Minimum split

Use at least one short clip per required language:

- `fr`
- `it`
- `ru`
- `en`
- `pt`
- `es`
- `ja`
- `pl`

For the first pass, 30-60 second clips are enough. They keep annotation cheap while still exposing the hard parts: chorus stacks, reverbs, bleed, missing consonants, and language detection mistakes.

## References

Build references in two layers:

- `reference.text` from manually checked lyrics for transcript quality
- `reference.words[]` for a smaller manually aligned subset

For Japanese, score CER/character tokens by default. Add word segmentation only if the annotation tooling already gives consistent word boundaries.
