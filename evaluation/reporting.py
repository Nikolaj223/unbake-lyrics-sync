from __future__ import annotations


LANGUAGE_ORDER = ["all", "fr", "it", "ru", "en", "pt", "es", "ja", "pl"]


def render_markdown_report(report: dict[str, object], command: str | None = None) -> str:
    lines = [
        "# Evaluation Results",
        "",
        "This page is generated from the same metrics JSON used for scoring.",
        "",
    ]
    if command:
        lines.extend(["## Command", "", "```bash", command, "```", ""])

    lines.extend(
        [
            "## Result Table",
            "",
            "| split | samples | mean WER | mean CER | hallucination | timestamp MAE, ms | timestamp P90, ms | mean IoU | mean latency, s | mean cost, $ |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    summary = dict(report.get("summary", {}))
    by_language = dict(report.get("by_language", {}))
    rows = {"all": summary, **by_language}
    for language in LANGUAGE_ORDER:
        if language not in rows:
            continue
        lines.append(format_metric_row(language, dict(rows[language])))

    lines.extend(
        [
            "",
            "## What To Inspect Manually",
            "",
            "- high insertion rate: hallucinated lines or repeated chorus tails",
            "- high CER with low WER: tokenization or punctuation issue",
            "- high timestamp P90: drift, long instrumental gaps, backing-vocal overlap",
            "- low IoU with good text: alignment failure rather than ASR failure",
            "- language-level outliers: weak language detection or missing alignment model",
            "",
            "## Submission Rule",
            "",
            "Do not use design-only numbers here. The table should come from `results/metrics.json`, and `results/predictions.jsonl` should contain the exact model outputs used for scoring.",
        ]
    )
    return "\n".join(lines) + "\n"


def format_metric_row(name: str, row: dict[str, object]) -> str:
    return (
        f"| {name} "
        f"| {format_int(row.get('samples'))} "
        f"| {format_float(row.get('mean_wer'))} "
        f"| {format_float(row.get('mean_cer'))} "
        f"| {format_float(row.get('mean_hallucination_rate'))} "
        f"| {format_float(row.get('mean_timestamp_mae_ms'), digits=1)} "
        f"| {format_float(row.get('mean_timestamp_p90_ms'), digits=1)} "
        f"| {format_float(row.get('mean_iou'))} "
        f"| {format_float(row.get('mean_elapsed_seconds'), digits=1)} "
        f"| {format_float(row.get('mean_cost_estimate_usd'), digits=6)} |"
    )


def format_int(value: object) -> str:
    return str(int(value)) if value is not None else "-"


def format_float(value: object, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}" if value is not None else "-"
