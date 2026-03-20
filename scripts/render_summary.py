#!/usr/bin/env python3
"""Render a Markdown summary from the JSON analysis output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    # This script stays file-based so it can be chained easily in CI.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-file", required=True, help="Path to the JSON report.")
    parser.add_argument(
        "--output-file",
        required=True,
        help="Where to write the Markdown summary.",
    )
    return parser.parse_args()


def load_report(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def render_markdown(report: dict) -> str:
    evidence_lines = "\n".join(f"- {item}" for item in report.get("evidence", []))
    action_lines = "\n".join(
        f"- {item}" for item in report.get("recommended_actions", [])
    )

    # The summary format is intentionally plain so it works well in GitHub job summaries and PR comments.
    return f"""# CI/CD Debug Summary

## Summary
{report.get("summary", "No summary available.")}

## Root Cause
{report.get("root_cause", "Unknown")}

## Category
{report.get("category", "unknown")}

## Confidence Score
{report.get("confidence_score", "unknown")}

## Evidence
{evidence_lines or "- No evidence captured."}

## Recommended Actions
{action_lines or "- No recommendations provided."}
"""


def main() -> int:
    args = parse_args()
    report = load_report(Path(args.input_file))

    output_file = Path(args.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(render_markdown(report), encoding="utf-8")

    print(f"Markdown summary written to {args.output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
