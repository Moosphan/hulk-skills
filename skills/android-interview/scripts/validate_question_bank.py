#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from question_bank import (
    configure_question_bank_template,
    validate_question_bank,
    write_question_bank_validation_artifacts,
)
from template_resolver import resolve_template


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an external Markdown question bank.")
    parser.add_argument("--question-bank", required=True, help="Markdown question bank path.")
    parser.add_argument("--output-dir", default="", help="Optional output directory for validation artifacts.")
    parser.add_argument("--fail-on-warnings", action="store_true", help="Return a non-zero exit code when warnings exist.")
    parser.add_argument("--template", default="", help="Explicit template ID to use for validation rules.")
    parser.add_argument("--target-role", default="", help="Natural-language target role used to resolve a template.")
    parser.add_argument("--role-family", default="", help="Optional role family hint used for template resolution.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    template_match = resolve_template(
        template_id=args.template,
        query=args.target_role,
        target_role=args.target_role,
        role_family=args.role_family,
    )
    configure_question_bank_template(template_match.template)
    report = validate_question_bank(args.question_bank)

    if args.output_dir:
        write_question_bank_validation_artifacts(args.output_dir, report)

    print(f"question_bank_status={report['status']}")
    print(f"template_id={template_match.template.template_id}")
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
