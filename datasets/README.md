# Dataset Notes

The take-home explicitly asks for evaluation on vocals separated with `htdemucs v4` (not `ft`), because the stem still contains artifacts and backing vocals.

## Recommended manifest schema

Each line in `manifest.jsonl` should look like:

```json
{
  "id": "sample-en-001",
  "language": "en",
  "reference": {
    "text": "hello from the other side",
    "words": [
      { "text": "hello", "start_ms": 120, "end_ms": 480 },
      { "text": "from", "start_ms": 500, "end_ms": 680 }
    ]
  },
  "prediction": {
    "text": "hello from the other side",
    "words": [
      { "text": "hello", "start_ms": 100, "end_ms": 470 },
      { "text": "from", "start_ms": 515, "end_ms": 700 }
    ]
  }
}
```

## Practical curation plan

1. Take the provided vocals split with `htdemucs v4`.
2. Keep language-balanced slices for:
   - `FR`
   - `IT`
   - `RU`
   - `EN`
   - `PT`
   - `ES`
   - `JP`
   - `PL`
3. Prefer 30-60 second clips first, because they are faster to annotate and compare.
4. Build references in two layers:
   - `reference.text` for transcript quality
   - `reference.words[]` for timestamp quality
5. For Japanese, evaluate both:
   - character-level quality by default
   - optional word segmentation if the annotation tooling already provides it

## Why the dataset matters

This problem is not regular speech-to-text. Demucs stems contain:

- musical bleed
- chorus stacks
- reverbs
- compression artifacts
- partially missing consonants

So offline evaluation on ordinary speech datasets would give misleadingly optimistic numbers.
