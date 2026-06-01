#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from question_bank import (
    validate_question_bank,
    write_question_bank_validation_artifacts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an external Markdown question bank.")
    parser.add_argument("--question-bank", required=True, help="Markdown question bank path.")
    parser.add_argument("--output-dir", default="", help="Optional output directory for validation artifacts.")
    parser.add_argument("--fail-on-warnings", action="store_true", help="Return a non-zero exit code when warnings exist.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = validate_question_bank(args.question_bank)

    if args.output_dir:
        write_question_bank_validation_artifacts(args.output_dir, report)

    print(f"question_bank_status={report['status']}")
    print(f"question_count={report['question_count']}")
    print(f"file_count={report['file_count']}")
    print(f"error_count={report['error_count']}")
    print(f"warning_count={report['warning_count']}")

    if report["status"] == "invalid":
        return 2
    if args.fail_on_warnings and report["warning_count"]:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
