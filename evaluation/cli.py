from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .metrics import aggregate, aggregate_by_language, evaluate_record, load_manifest
from .reporting import render_markdown_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate lyrics recognition quality and timestamp alignment.")
    parser.add_argument("--manifest", required=True, help="Path to JSONL manifest with reference/prediction pairs")
    parser.add_argument("--output", help="Optional path to write the metrics JSON report")
    parser.add_argument("--markdown-output", help="Optional path to write a markdown report")
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    rows = [evaluate_record(record) for record in manifest]
    report = {
        "summary": aggregate(rows),
        "by_language": aggregate_by_language(rows),
        "rows": rows,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
    if args.markdown_output:
        markdown_path = Path(args.markdown_output)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(render_markdown_report(report, " ".join(sys.argv)), encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
