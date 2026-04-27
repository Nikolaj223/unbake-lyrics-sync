from __future__ import annotations

import json
import statistics
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


CHARACTER_TOKEN_LANGUAGES = {"ja", "jp"}


@dataclass(slots=True)
class TimestampedToken:
    text: str
    start_ms: int
    end_ms: int


@dataclass(slots=True)
class AlignmentOp:
    op: str
    ref: str | None
    hyp: str | None
    ref_index: int | None
    hyp_index: int | None


def normalize_text(text: str, language: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    if language in CHARACTER_TOKEN_LANGUAGES:
        return "".join(char for char in normalized if _is_content_char(char))
    lowered = normalized.casefold()
    cleaned = "".join(char if _is_content_char(char) or char.isspace() else " " for char in lowered)
    return " ".join(cleaned.split())


def tokenize(text: str, language: str) -> list[str]:
    normalized = normalize_text(text, language)
    if language in CHARACTER_TOKEN_LANGUAGES:
        return [char for char in normalized if not char.isspace()]
    return normalized.split()


def word_error_rate(reference: str, hypothesis: str, language: str) -> dict[str, float]:
    ref_tokens = tokenize(reference, language)
    hyp_tokens = tokenize(hypothesis, language)
    ops = align_sequences(ref_tokens, hyp_tokens)
    substitutions = sum(1 for op in ops if op.op == "sub")
    insertions = sum(1 for op in ops if op.op == "ins")
    deletions = sum(1 for op in ops if op.op == "del")
    denominator = max(len(ref_tokens), 1)
    return {
        "wer": (substitutions + insertions + deletions) / denominator,
        "substitutions": substitutions,
        "insertions": insertions,
        "deletions": deletions,
        "reference_tokens": len(ref_tokens),
        "hypothesis_tokens": len(hyp_tokens),
        "hallucination_rate": insertions / max(len(hyp_tokens), 1),
    }


def char_error_rate(reference: str, hypothesis: str, language: str) -> dict[str, float]:
    ref_tokens = list(normalize_text(reference, language))
    hyp_tokens = list(normalize_text(hypothesis, language))
    ops = align_sequences(ref_tokens, hyp_tokens)
    substitutions = sum(1 for op in ops if op.op == "sub")
    insertions = sum(1 for op in ops if op.op == "ins")
    deletions = sum(1 for op in ops if op.op == "del")
    denominator = max(len(ref_tokens), 1)
    return {
        "cer": (substitutions + insertions + deletions) / denominator,
        "reference_chars": len(ref_tokens),
        "hypothesis_chars": len(hyp_tokens),
    }


def timestamp_metrics(
    reference_tokens: list[TimestampedToken],
    hypothesis_tokens: list[TimestampedToken],
    language: str,
) -> dict[str, float | int | None]:
    ref_words = [normalize_text(token.text, language) for token in reference_tokens]
    hyp_words = [normalize_text(token.text, language) for token in hypothesis_tokens]
    ops = align_sequences(ref_words, hyp_words)

    start_deltas: list[int] = []
    end_deltas: list[int] = []
    ious: list[float] = []

    for op in ops:
        if op.op != "eq":
            continue
        ref_token = reference_tokens[op.ref_index]  # type: ignore[index]
        hyp_token = hypothesis_tokens[op.hyp_index]  # type: ignore[index]
        start_deltas.append(abs(ref_token.start_ms - hyp_token.start_ms))
        end_deltas.append(abs(ref_token.end_ms - hyp_token.end_ms))
        ious.append(interval_iou(ref_token.start_ms, ref_token.end_ms, hyp_token.start_ms, hyp_token.end_ms))

    matched = len(start_deltas)
    if matched == 0:
        return {
            "matched_tokens": 0,
            "timestamp_mae_ms": None,
            "timestamp_p90_ms": None,
            "mean_iou": None,
        }

    merged_deltas = [*start_deltas, *end_deltas]
    return {
        "matched_tokens": matched,
        "timestamp_mae_ms": statistics.fmean(merged_deltas),
        "timestamp_p90_ms": percentile(merged_deltas, 90),
        "mean_iou": statistics.fmean(ious),
    }


def evaluate_record(record: dict[str, object]) -> dict[str, object]:
    language = str(record["language"])
    reference = dict(record["reference"])
    prediction = dict(record["prediction"])
    ref_text = str(reference["text"])
    hyp_text = str(prediction["text"])

    text_metrics = word_error_rate(ref_text, hyp_text, language)
    cer_metrics = char_error_rate(ref_text, hyp_text, language)

    output: dict[str, object] = {
        "id": record["id"],
        "language": language,
        **text_metrics,
        **cer_metrics,
    }

    runtime = record.get("runtime")
    if isinstance(runtime, dict):
        if runtime.get("elapsed_seconds") is not None:
            output["elapsed_seconds"] = float(runtime["elapsed_seconds"])
        if runtime.get("cost_estimate_usd") is not None:
            output["cost_estimate_usd"] = float(runtime["cost_estimate_usd"])

    if reference.get("words") and prediction.get("words"):
        ref_words = parse_timestamped_tokens(reference["words"])
        hyp_words = parse_timestamped_tokens(prediction["words"])
        output.update(timestamp_metrics(ref_words, hyp_words, language))

    return output


def parse_timestamped_tokens(tokens: object) -> list[TimestampedToken]:
    parsed: list[TimestampedToken] = []
    for token in tokens:  # type: ignore[union-attr]
        item = dict(token)
        parsed.append(
            TimestampedToken(
                text=str(item["text"]),
                start_ms=int(item.get("start_ms", item.get("startMs"))),
                end_ms=int(item.get("end_ms", item.get("endMs"))),
            )
        )
    return parsed


def aggregate(records: Iterable[dict[str, object]]) -> dict[str, object]:
    rows = list(records)
    if not rows:
        return {"samples": 0}

    def collect_numeric(key: str) -> list[float]:
        return [float(row[key]) for row in rows if row.get(key) is not None]

    summary = {
        "samples": len(rows),
        "mean_wer": statistics.fmean(collect_numeric("wer")),
        "mean_cer": statistics.fmean(collect_numeric("cer")),
        "mean_hallucination_rate": statistics.fmean(collect_numeric("hallucination_rate")),
    }

    timestamp_mae_values = collect_numeric("timestamp_mae_ms")
    if timestamp_mae_values:
        summary["mean_timestamp_mae_ms"] = statistics.fmean(timestamp_mae_values)
    timestamp_p90_values = collect_numeric("timestamp_p90_ms")
    if timestamp_p90_values:
        summary["mean_timestamp_p90_ms"] = statistics.fmean(timestamp_p90_values)
    mean_iou_values = collect_numeric("mean_iou")
    if mean_iou_values:
        summary["mean_iou"] = statistics.fmean(mean_iou_values)
    elapsed_values = collect_numeric("elapsed_seconds")
    if elapsed_values:
        summary["mean_elapsed_seconds"] = statistics.fmean(elapsed_values)
        summary["p90_elapsed_seconds"] = percentile(elapsed_values, 90)
    cost_values = collect_numeric("cost_estimate_usd")
    if cost_values:
        summary["mean_cost_estimate_usd"] = statistics.fmean(cost_values)
        summary["total_cost_estimate_usd"] = sum(cost_values)

    return summary


def aggregate_by_language(records: Iterable[dict[str, object]]) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in records:
        grouped.setdefault(str(row["language"]), []).append(row)
    return {language: aggregate(rows) for language, rows in sorted(grouped.items())}


def load_manifest(path: str | Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with Path(path).open("r", encoding="utf-8-sig") as file_handle:
        for line in file_handle:
            stripped = line.strip()
            if not stripped:
                continue
            rows.append(json.loads(stripped))
    return rows


def align_sequences(reference: list[str], hypothesis: list[str]) -> list[AlignmentOp]:
    rows = len(reference) + 1
    cols = len(hypothesis) + 1
    dp = [[0] * cols for _ in range(rows)]
    backtrack: list[list[str | None]] = [[None] * cols for _ in range(rows)]

    for row in range(1, rows):
        dp[row][0] = row
        backtrack[row][0] = "del"
    for col in range(1, cols):
        dp[0][col] = col
        backtrack[0][col] = "ins"

    for row in range(1, rows):
        for col in range(1, cols):
            substitution_cost = 0 if reference[row - 1] == hypothesis[col - 1] else 1
            candidates = [
                (dp[row - 1][col] + 1, "del"),
                (dp[row][col - 1] + 1, "ins"),
                (dp[row - 1][col - 1] + substitution_cost, "eq" if substitution_cost == 0 else "sub"),
            ]
            dp[row][col], backtrack[row][col] = min(candidates, key=lambda item: item[0])

    aligned: list[AlignmentOp] = []
    row = len(reference)
    col = len(hypothesis)
    while row > 0 or col > 0:
        op = backtrack[row][col]
        if op in {"eq", "sub"}:
            aligned.append(
                AlignmentOp(op=op, ref=reference[row - 1], hyp=hypothesis[col - 1], ref_index=row - 1, hyp_index=col - 1)
            )
            row -= 1
            col -= 1
        elif op == "del":
            aligned.append(
                AlignmentOp(op="del", ref=reference[row - 1], hyp=None, ref_index=row - 1, hyp_index=None)
            )
            row -= 1
        elif op == "ins":
            aligned.append(
                AlignmentOp(op="ins", ref=None, hyp=hypothesis[col - 1], ref_index=None, hyp_index=col - 1)
            )
            col -= 1
        else:
            break

    aligned.reverse()
    return aligned


def interval_iou(start_a: int, end_a: int, start_b: int, end_b: int) -> float:
    intersection = max(0, min(end_a, end_b) - max(start_a, start_b))
    union = max(end_a, end_b) - min(start_a, start_b)
    return intersection / union if union else 0.0


def percentile(values: list[float] | list[int], p: int) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    rank = (len(ordered) - 1) * (p / 100)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _is_content_char(char: str) -> bool:
    category = unicodedata.category(char)
    return category[0] in {"L", "N"} or char in {"'", "-"}
