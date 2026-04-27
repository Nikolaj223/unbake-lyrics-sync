from evaluation.metrics import (
    aggregate,
    char_error_rate,
    timestamp_metrics,
    word_error_rate,
    TimestampedToken,
)


def test_word_error_rate_exact_match() -> None:
    metrics = word_error_rate("hello from the other side", "hello from the other side", "en")
    assert metrics["wer"] == 0
    assert metrics["hallucination_rate"] == 0


def test_word_error_rate_with_insertion() -> None:
    metrics = word_error_rate("hello world", "hello brave world", "en")
    assert metrics["wer"] > 0
    assert metrics["insertions"] == 1


def test_char_error_rate_for_japanese() -> None:
    metrics = char_error_rate("こんにちは", "こんにちわ", "ja")
    assert metrics["cer"] > 0


def test_timestamp_metrics_returns_mae() -> None:
    reference = [
        TimestampedToken(text="hello", start_ms=100, end_ms=300),
        TimestampedToken(text="world", start_ms=320, end_ms=520),
    ]
    prediction = [
        TimestampedToken(text="hello", start_ms=120, end_ms=310),
        TimestampedToken(text="world", start_ms=340, end_ms=500),
    ]
    metrics = timestamp_metrics(reference, prediction, "en")
    assert metrics["matched_tokens"] == 2
    assert metrics["timestamp_mae_ms"] is not None


def test_aggregate_summary() -> None:
    rows = [
        {"wer": 0.1, "cer": 0.05, "hallucination_rate": 0.0, "timestamp_mae_ms": 40, "timestamp_p90_ms": 80, "mean_iou": 0.8},
        {"wer": 0.2, "cer": 0.1, "hallucination_rate": 0.1, "timestamp_mae_ms": 60, "timestamp_p90_ms": 120, "mean_iou": 0.7},
    ]
    summary = aggregate(rows)
    assert summary["samples"] == 2
    assert summary["mean_wer"] > 0
