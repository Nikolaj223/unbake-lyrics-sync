from evaluation.reporting import render_markdown_report


def test_render_markdown_report_includes_summary_row() -> None:
    report = {
        "summary": {
            "samples": 2,
            "mean_wer": 0.1,
            "mean_cer": 0.05,
            "mean_hallucination_rate": 0.0,
            "mean_cost_estimate_usd": 0.004,
        },
        "by_language": {},
    }
    rendered = render_markdown_report(report, "python -m evaluation.cli")
    assert "| all | 2 | 0.100 | 0.050 | 0.000 |" in rendered
    assert "python -m evaluation.cli" in rendered
