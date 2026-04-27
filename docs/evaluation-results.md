# Evaluation Results

This page is generated from the same metrics JSON used for scoring.

## Command

```bash
C:\postal-max-go\unbake-lyrics-sync\evaluation\cli.py --manifest .\results\predictions.jsonl --output .\results\metrics.json --markdown-output .\docs\evaluation-results.md
```

## Result Table

| split | samples | mean WER | mean CER | hallucination | timestamp MAE, ms | timestamp P90, ms | mean IoU | mean latency, s | mean cost, $ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 2 | 0.915 | 0.345 | 0.324 | - | - | - | 131.7 | 0.021067 |
| ru | 1 | 0.330 | 0.173 | 0.114 | - | - | - | 125.1 | 0.020011 |
| en | 1 | 1.500 | 0.517 | 0.533 | - | - | - | 138.3 | 0.022122 |

## What To Inspect Manually

- high insertion rate: hallucinated lines or repeated chorus tails
- high CER with low WER: tokenization or punctuation issue
- high timestamp P90: drift, long instrumental gaps, backing-vocal overlap
- low IoU with good text: alignment failure rather than ASR failure
- language-level outliers: weak language detection or missing alignment model

## Submission Rule

Do not use design-only numbers here. The table should come from `results/metrics.json`, and `results/predictions.jsonl` should contain the exact model outputs used for scoring.
