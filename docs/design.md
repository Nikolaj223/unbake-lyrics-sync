# Design doc

## 1. Goal

Build an API that:

- accepts an `S3 presigned URL` to an isolated vocal stem
- returns song lyrics with timestamps
- prefers word-level timestamps over line-level timestamps
- stays cheap enough for an early product stage

Input today is `m4a 256 kbps` after `Demucs v4`.

## 2. Main decision

I would ship an **async job API** with a **self-hosted WhisperX baseline**.

Why:

- good multilingual quality
- word-level timestamps through forced alignment
- much cheaper than hosted transcription APIs
- easy to evaluate offline on the requested dataset

## 3. API design

### `POST /v1/lyrics/jobs`

Request:

```json
{
  "audioUrl": "https://bucket.example.com/presigned-url",
  "languageHint": "en",
  "trackName": "Someone Like You",
  "artistName": "Adele",
  "durationMs": 285000,
  "shazamTrackId": "optional",
  "isCustomCover": false
}
```

Response:

```json
{
  "jobId": "c3a5...",
  "status": "queued",
  "statusUrl": "/v1/lyrics/jobs/c3a5..."
}
```

### `GET /v1/lyrics/jobs/{job_id}`

Completed response:

```json
{
  "jobId": "c3a5...",
  "status": "completed",
  "result": {
    "language": "en",
    "source": "asr_baseline",
    "plainLyrics": "Hello from the other side\nI must have called a thousand times",
    "syncedLyrics": "[00:00.12] Hello from the other side\n[00:03.44] I must have called a thousand times",
    "words": [
      { "text": "Hello", "startMs": 120, "endMs": 480, "confidence": 0.97 }
    ],
    "costEstimateUsd": 0.0032
  }
}
```

## 4. Why async and not sync

Sync looks simpler, but here it is the wrong default:

- presigned URL download takes time
- audio normalization takes time
- transcription + alignment takes time
- mobile clients should not hold a request open for 20-60 seconds

For an iOS app, polling a job is a safer first version.

## 5. Audio format decision

### Accept at API boundary

- keep `m4a`, because that is what the upstream already produces

### Convert internally

- `wav`
- `16 kHz`
- `mono`
- `pcm_s16le`

Why:

- less codec noise during ASR/alignment
- most alignment pipelines assume PCM audio
- deterministic preprocessing
- easier offline evaluation

## 6. Proposed pipeline

### Baseline shipped first

1. download stem from presigned URL
2. transcode to `wav 16k mono`
3. run `WhisperX` with `faster-whisper` backend
4. run forced alignment
5. emit:
   - `plainLyrics`
   - `syncedLyrics`
   - `words[]`

### Product direction after baseline

Use a **hybrid path**:

1. if client sends strong catalog hint from `ShazamKit`, try to retrieve canonical lyrics
2. if retrieved lyrics match the stem well enough, align reference lyrics to audio
3. else fall back to direct ASR

Why this is interesting:

- lower hallucination risk on known songs
- lower compute if reference lyrics are available
- still handles custom covers because fallback is always direct ASR

I would not ship the reference-only path first, because custom covers are explicitly in scope.

## 7. Model choice

### Recommended baseline

- ASR: `WhisperX` with `faster-whisper` backend
- model: `large-v3`
- alignment: WhisperX forced alignment model per language
- settings:
  - `beam_size=5`
  - disable previous-context conditioning when the installed WhisperX/faster-whisper version exposes that option
  - VAD enabled

Why:

- WhisperX gives word-level timestamps and documents forced alignment on top of Whisper
- faster-whisper is more efficient than openai/whisper and uses less memory

## 8. Alternatives considered

### A. Hosted OpenAI / cloud speech API

Pros:

- fastest to launch
- no GPU ops

Cons:

- cost is harder to keep under the target at scale
- less control over timestamp behavior
- weaker offline reproducibility
- harder to tune for stem artifacts

Verdict:

- good emergency prototype, not my first production choice here

### B. faster-whisper only, no alignment

Pros:

- simple
- cheap

Cons:

- worse timestamp precision
- more drift for karaoke-like UX

Verdict:

- acceptable fallback, not final answer

### C. WhisperX self-hosted baseline

Pros:

- best baseline tradeoff across accuracy / cost / timestamp precision
- multilingual
- cheap enough for early stage

Cons:

- more moving pieces than plain ASR
- GPU dependency

Verdict:

- recommended first production version

### D. Reference lyrics only

Pros:

- lowest hallucination risk if exact song is known
- can be extremely precise after alignment

Cons:

- breaks on custom covers
- breaks on lyric changes
- not enough on its own

Verdict:

- useful as phase 2 hybrid optimization, not the only path

## 9. Cost per request

I would start with `Runpod Serverless` style economics for bursty traffic.

Relevant public pricing pages today:

- Runpod serverless docs show `A4000/A4500/RTX 4000` flex workers at `$0.00016 / second`
- Runpod GPU pages show low-cost pod options such as `RTX A4000`

Conservative estimate:

- 3 minute track
- end-to-end GPU time for ASR + alignment: `20-25 sec`
- compute cost: `25 * 0.00016 = $0.004`
- the benchmark runner records actual `elapsed_seconds` and `cost_estimate_usd` per clip, so this estimate is checked against the real run instead of staying a spreadsheet guess

Add CPU, storage, transfer margin:

- target estimate: `~$0.005 - $0.01 / request`

That is comfortably below the stated `>$0.05 unacceptable` threshold.

At `100 requests/day`:

- compute only: roughly `$15-$30 / month`
- plus API node, storage, logs: still realistic to stay near the requested `$100/month`

Important nuance:

- an always-on GPU pod can exceed the early monthly budget
- for the first stage I prefer **serverless/burst GPU** or an aggressively auto-suspended single worker

## 10. Hardware choice

### Early stage

- 1 small CPU API node
- 1 burst GPU worker
- object storage for temporary artifacts

Concrete shape:

- API: 2-4 vCPU, 4-8 GB RAM
- worker: `A4000 / L4 class GPU`

Why:

- enough VRAM for WhisperX baseline
- cheaper than larger cards
- good fit for 100 requests/day

## 11. What can go wrong

### Hallucinated text

Mitigation:

- avoid previous-context conditioning where supported by the installed ASR backend
- VAD before transcription
- language hint if available
- reject very low-confidence tails
- compare against catalog lyrics only as a hint, never blindly overwrite custom covers

### Bad timestamps

Mitigation:

- force alignment after ASR
- evaluate timestamp MAE/P90 on manually aligned subset
- emit both words and lines, not just lines

### Backing vocals / chorus stacks

Mitigation:

- accept that v1 is single mixed vocal stem
- evaluate specifically on hard chorus-heavy clips
- later add confidence-based downranking for overlapping vocal regions

### Wrong language

Mitigation:

- accept client hint
- keep automatic language detection
- monitor language confusion matrix by dataset split

### Presigned URL failures

Mitigation:

- retry download once
- validate content type / ffmpeg decode
- explicit `failed` job state

## 12. How I would evaluate quality automatically

I would not trust one metric.

Need at least:

- `WER` for transcript quality
- `CER` for languages where tokenization is trickier
- `hallucination_rate`
- `timestamp_mae_ms`
- `timestamp_p90_ms`
- `mean_iou` of token intervals

The repo has two evaluation steps:

1. `python -m evaluation.run_asr --manifest ./datasets/benchmark_manifest.jsonl --output ./results/predictions.jsonl --metrics-output ./results/metrics.json --markdown-output ./docs/evaluation-results.md`
2. `python -m evaluation.cli --manifest ./results/predictions.jsonl --output ./results/metrics.json --markdown-output ./docs/evaluation-results.md`

The first command runs the real WhisperX baseline on `htdemucs v4` clips and stores exact predictions. The second command re-scores those predictions without paying GPU cost again.

The benchmark manifest should contain at least one checked sample for each required language: `fr`, `it`, `ru`, `en`, `pt`, `es`, `ja`, `pl`. Word-level references can be smaller than text references, but they are necessary to make timestamp claims.

## 13. What success looks like

For v1 I optimize in this order:

1. no random hallucinated lines
2. strong word timestamps on common cases
3. low enough cost to stay under early budget
4. reasonable latency for mobile polling UX

## 14. Why this is not generic LLM slop

The important non-generic decisions are:

- async jobs instead of sync request
- internal conversion to `wav 16k mono`
- WhisperX baseline instead of plain hosted STT
- evaluation on Demucs stems, not regular speech datasets
- future hybrid path using `ShazamKit` hints without trusting catalog lyrics blindly

## Sources

- WhisperX repository: https://github.com/m-bain/whisperX
- faster-whisper repository: https://github.com/SYSTRAN/faster-whisper
- LRCLib response shape examples: https://lrclib.js.org/
- Runpod serverless pricing: https://docs.runpod.io/serverless/pricing
