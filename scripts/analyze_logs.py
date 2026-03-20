#!/usr/bin/env python3
"""Analyze CI/CD logs with Azure OpenAI and emit structured JSON."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


# Keep the payload bounded for predictable cost and lower risk of sending noisy logs.
MAX_LOG_CHARS = 12_000


# The result contract is intentionally compact so downstream automation can rely on it.
ANALYSIS_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "summary": {"type": "string"},
        "root_cause": {"type": "string"},
        "category": {
            "type": "string",
            "enum": [
                "dependency_error",
                "version_mismatch",
                "yaml_syntax_issue",
                "authentication_failure",
                "unknown",
            ],
        },
        "recommended_actions": {
            "type": "array",
            "items": {"type": "string"},
        },
        "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
        "evidence": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "summary",
        "root_cause",
        "category",
        "recommended_actions",
        "confidence_score",
        "evidence",
    ],
}


# Local patterns provide a first-pass classification before the model sees the log.
ISSUE_RULES = {
    "dependency_error": {
        "patterns": [
            r"No module named",
            r"ModuleNotFoundError",
            r"Could not resolve dependencies",
            r"Unable to locate package",
            r"npm ERR! code ERESOLVE",
            r"pip .* No matching distribution found",
            r"Could not find a version that satisfies the requirement",
            r"error: failed to solve:.*not found",
        ],
        "actions": [
            "Verify the dependency name and version exist in the package registry.",
            "Regenerate the lockfile or dependency manifest if it is stale.",
            "Check whether the CI environment has access to the required package source.",
        ],
    },
    "version_mismatch": {
        "patterns": [
            r"requires Python ['\"]?[><=].*",
            r"Unsupported engine",
            r"Expected version",
            r"version .* does not satisfy",
            r"RuntimeError: .*version",
            r"because no versions of .* match",
            r"found .* but expected",
        ],
        "actions": [
            "Align the CI runtime version with the application's declared requirements.",
            "Pin compatible dependency versions and update the lockfile.",
            "Review recent version bumps in the workflow, Dockerfile, or build image.",
        ],
    },
    "yaml_syntax_issue": {
        "patterns": [
            r"yaml\.scanner\.ScannerError",
            r"mapping values are not allowed here",
            r"did not find expected key",
            r"found character that cannot start any token",
            r"while parsing a block mapping",
            r"error converting YAML to JSON",
        ],
        "actions": [
            "Validate the YAML file with a linter before running the pipeline.",
            "Inspect indentation, quoting, and colon placement near the reported line.",
            "Compare the changed YAML against a known-good version.",
        ],
    },
    "authentication_failure": {
        "patterns": [
            r"401 Unauthorized",
            r"403 Forbidden",
            r"AccessDenied",
            r"authentication failed",
            r"permission denied",
            r"invalid token",
            r"could not read Username",
            r"login failed",
            r"not authorized",
        ],
        "actions": [
            "Verify the CI secret or token is present and not expired.",
            "Check the service account, IAM role, or registry permissions used by the job.",
            "Confirm the workflow is exposing the secret to the failing step or environment.",
        ],
    },
}


SECRET_PATTERNS = [
    re.compile(r"(?i)(authorization:\s*bearer\s+)[^\s]+"),
    re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)[^\s]+"),
    re.compile(r"(?i)(token\s*[=:]\s*)[^\s]+"),
    re.compile(r"(?i)(password\s*[=:]\s*)[^\s]+"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
]


def parse_args() -> argparse.Namespace:
    # CLI flags stay explicit so the script is easy to wire into GitHub Actions.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-file", required=True, help="Path to the CI/CD log file.")
    parser.add_argument(
        "--output-file",
        required=True,
        help="Where to write the JSON analysis report.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini"),
        help="Azure OpenAI deployment name. Defaults to AZURE_OPENAI_DEPLOYMENT.",
    )
    parser.add_argument(
        "--max-log-chars",
        type=int,
        default=MAX_LOG_CHARS,
        help="Maximum number of sanitized log characters sent to the model.",
    )
    return parser.parse_args()


def build_client() -> Any:
    # Azure OpenAI uses the standard OpenAI client pointed at the Azure v1 endpoint.
    from openai import OpenAI

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")

    if not endpoint or not api_key:
        raise RuntimeError(
            "Missing Azure OpenAI configuration. Set AZURE_OPENAI_ENDPOINT and "
            "AZURE_OPENAI_API_KEY."
        )

    base_url = endpoint.rstrip("/") + "/openai/v1/"
    return OpenAI(api_key=api_key, base_url=base_url)


def read_log(log_file: Path) -> str:
    if not log_file.exists():
        raise FileNotFoundError(f"Log file not found: {log_file}")
    return log_file.read_text(encoding="utf-8")


def redact_secrets(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(r"\1[REDACTED]" if pattern.groups else "[REDACTED]", redacted)
    return redacted


def limit_log_size(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text

    head_size = max_chars // 2
    tail_size = max_chars - head_size
    return (
        text[:head_size]
        + "\n\n... [TRUNCATED FOR SIZE] ...\n\n"
        + text[-tail_size:]
    )


def extract_evidence(log_text: str, patterns: list[str]) -> list[str]:
    evidence: list[str] = []
    for line in log_text.splitlines():
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns):
            evidence.append(line.strip())
        if len(evidence) >= 3:
            break
    return evidence


def detect_known_issue(log_text: str) -> dict:
    for category, rule in ISSUE_RULES.items():
        evidence = extract_evidence(log_text, rule["patterns"])
        if evidence:
            return {
                "summary": f"Detected likely {category.replace('_', ' ')} in the CI/CD log.",
                "root_cause": evidence[0],
                "category": category,
                "recommended_actions": rule["actions"],
                "confidence_score": 0.88,
                "evidence": evidence,
            }

    return {
        "summary": "No known CI/CD error pattern matched the log.",
        "root_cause": "Unable to determine a specific issue from local rules alone.",
        "category": "unknown",
        "recommended_actions": [
            "Review the failing step and nearby log lines for the first explicit error.",
            "Add more step-level logging or artifact capture if the failure remains ambiguous.",
            "Use the structured output to route the failure to the most likely owning team.",
        ],
        "confidence_score": 0.35,
        "evidence": [],
    }


def validate_analysis(data: dict) -> dict:
    # A tiny validator keeps the script dependency-light while still failing fast on malformed output.
    required_keys = set(ANALYSIS_SCHEMA["required"])
    missing = sorted(required_keys - set(data))
    if missing:
        raise ValueError(f"Model response is missing required keys: {', '.join(missing)}")
    return data


def analyze_log(
    client: Any, model: str, log_text: str, heuristic_result: dict
) -> dict:
    prompt = f"""
You are an SRE assistant analyzing CI/CD logs.
Return only JSON that matches the provided schema.

Required behavior:
- Focus on the single most likely root cause.
- Prefer one of these categories when it fits: dependency_error, version_mismatch,
  yaml_syntax_issue, authentication_failure.
- Keep the summary concise and operational.
- Do not repeat or expose secrets even if they appear in the log.
- Confidence score must be between 0 and 1.

Local rule-based hint:
{json.dumps(heuristic_result, indent=2)}

Sanitized CI/CD log:
{log_text}
""".strip()

    response = client.responses.create(
        model=model,
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "cicd_debug_report",
                "strict": True,
                "schema": ANALYSIS_SCHEMA,
            }
        },
    )

    # `output_text` is the simplest way to read the JSON body returned by the model.
    payload = json.loads(response.output_text)
    return validate_analysis(payload)


def write_output(output_file: Path, data: dict) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()

    try:
        client = build_client()
        raw_log_text = read_log(Path(args.log_file))
        redacted_log_text = redact_secrets(raw_log_text)
        heuristic_result = detect_known_issue(redacted_log_text)
        safe_log_text = limit_log_size(redacted_log_text, args.max_log_chars)
        analysis = analyze_log(client, args.model, safe_log_text, heuristic_result)
        write_output(Path(args.output_file), analysis)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Analysis written to {args.output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
