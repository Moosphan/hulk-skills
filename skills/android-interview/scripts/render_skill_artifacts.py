#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from interview_core import (
    QuestionResult,
    RoundSummary,
    render_failure_summary,
    render_pass_summary,
    render_reject_mail,
    render_report,
    render_resume_prep,
    render_screening_summary,
    render_transcript,
    write_json,
)
from question_bank import write_question_bank_validation_artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render Android interview local artifacts from structured session and score payloads."
    )
    parser.add_argument("--session-json", help="Path to a structured session.json payload.")
    parser.add_argument("--score-json", help="Path to a structured score.json payload.")
    parser.add_argument(
        "--bundle-json",
        help="Optional path to a bundle JSON containing session/score or session_data/score_data.",
    )
    parser.add_argument("--output-dir", required=True, help="Directory where artifacts should be written.")
    return parser.parse_args()


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def resolve_payloads(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    if args.bundle_json:
        bundle = load_json(args.bundle_json)
        session_data = bundle.get("session") or bundle.get("session_data")
        score_data = bundle.get("score") or bundle.get("score_data")
        if not isinstance(session_data, dict) or not isinstance(score_data, dict):
            raise SystemExit("bundle-json must contain session/score or session_data/score_data mappings.")
        return session_data, score_data

    if not args.session_json or not args.score_json:
        raise SystemExit("Provide either --bundle-json, or both --session-json and --score-json.")
    return load_json(args.session_json), load_json(args.score_json)


def results_from_score(score_data: dict[str, Any]) -> list[QuestionResult]:
    return [QuestionResult(**item) for item in score_data.get("questions", [])]


def round_summaries_from_session(session_data: dict[str, Any]) -> list[RoundSummary]:
    return [RoundSummary(**item) for item in session_data.get("round_summaries", [])]


def main() -> int:
    args = parse_args()
    session_data, score_data = resolve_payloads(args)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    session_id = str(session_data.get("session_id", "android-interview-session"))
    results = results_from_score(score_data)
    round_summaries = round_summaries_from_session(session_data)
    round_deliberations = list(session_data.get("round_deliberations", []))
    decision = str(score_data.get("final_decision", session_data.get("final_decision", "completed")))

    write_json(output_dir / "session.json", session_data)
    write_json(output_dir / "score.json", score_data)

    screening_summary = session_data.get("screening_summary") or {}
    if screening_summary:
        write_json(output_dir / "screening-summary.json", screening_summary)
        render_screening_summary(output_dir / "screening-summary.md", session_id, screening_summary)

    resume_prep = session_data.get("resume_prep") or {}
    if resume_prep:
        write_json(output_dir / "resume-prep.json", resume_prep)
        render_resume_prep(output_dir / "resume-prep.md", session_id, resume_prep)

    question_bank_validation = session_data.get("question_bank_validation") or {}
    if question_bank_validation:
        write_question_bank_validation_artifacts(output_dir, question_bank_validation)

    turn_events = session_data.get("turn_events") or []
    if turn_events:
        write_json(output_dir / "turn-events.json", {"turn_events": turn_events})

    panel_memos = session_data.get("panel_memos") or []
    if panel_memos:
        write_json(output_dir / "panel-notes.json", {"panel_memos": panel_memos})

    render_transcript(
        output_dir / "transcript.md",
        session_id,
        results,
        round_summaries,
        round_deliberations,
    )
    render_report(output_dir / "report.html", session_data, score_data)

    if decision == "fail":
        hard_fail_flags = list(score_data.get("hard_fail_flags", []))
        render_reject_mail(output_dir / "mail-reject.html", session_id, hard_fail_flags, round_summaries)
        render_failure_summary(output_dir / "fail-summary.md", session_data, score_data)
    elif decision == "pass":
        render_pass_summary(output_dir / "pass-summary.md", session_id, session_data, score_data)
    elif decision == "paused":
        render_failure_summary(output_dir / "fail-summary.md", session_data, score_data)

    print(f"session_id={session_id}")
    print(f"output_dir={output_dir}")
    print(f"decision={decision}")
    print("artifacts_rendered=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
