#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a pause-and-resume interactive Android interview demo.")
    parser.add_argument("--jd", required=True, help="Path to JD text or Markdown.")
    parser.add_argument("--resume", required=True, help="Path to resume text or Markdown.")
    parser.add_argument("--question-bank", required=True, help="Markdown question bank path.")
    parser.add_argument("--scripted-answers", required=True, help="JSON answer fixture for deterministic resume validation.")
    parser.add_argument("--output-dir", required=True, help="Session output directory.")
    parser.add_argument("--session-id", default="", help="Optional fixed session ID.")
    parser.add_argument("--mode", default="simulate", choices=["simulate", "screening", "round1", "round2", "round3", "hr"])
    parser.add_argument("--level", default="senior", choices=["mid", "senior", "tl"])
    parser.add_argument("--language", default="en", choices=["zh", "en", "bilingual"])
    parser.add_argument("--pause-after-questions", type=int, default=3, help="Pause after N completed questions in the first run.")
    parser.add_argument("--default-persona", default="", help="Default interviewer persona preset for all rounds.")
    parser.add_argument("--round-persona-overrides", default="", help="Comma-separated round=persona overrides.")
    parser.add_argument("--round-language-overrides", default="", help="Comma-separated round=language overrides.")
    parser.add_argument("--question-target-overrides", default="", help="Comma-separated round=count overrides.")
    parser.add_argument("--no-live-feedback", action="store_true", help="Disable automatic per-question live feedback.")
    parser.add_argument("--keep-existing-output", action="store_true", help="Do not clean the output directory before the first run.")
    return parser.parse_args()


def run_command(command: list[str], cwd: Path) -> int:
    proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if proc.stdout.strip():
        print(proc.stdout.strip())
    if proc.stderr.strip():
        print(proc.stderr.strip(), file=sys.stderr)
    return proc.returncode


def main() -> int:
    args = parse_args()
    script_path = Path(__file__).with_name("run_interactive_session.py")
    output_dir = Path(args.output_dir)
    checkpoint_path = output_dir / "session-checkpoint.json"

    if not args.keep_existing_output and output_dir.exists():
        shutil.rmtree(output_dir)

    base_args = [
        sys.executable,
        str(script_path),
        "--jd",
        args.jd,
        "--resume",
        args.resume,
        "--question-bank",
        args.question_bank,
        "--scripted-answers",
        args.scripted_answers,
        "--output-dir",
        str(output_dir),
        "--mode",
        args.mode,
        "--level",
        args.level,
        "--language",
        args.language,
    ]
    if args.session_id:
        base_args.extend(["--session-id", args.session_id])
    if args.default_persona:
        base_args.extend(["--default-persona", args.default_persona])
    if args.round_persona_overrides:
        base_args.extend(["--round-persona-overrides", args.round_persona_overrides])
    if args.round_language_overrides:
        base_args.extend(["--round-language-overrides", args.round_language_overrides])
    if args.question_target_overrides:
        base_args.extend(["--question-target-overrides", args.question_target_overrides])
    if args.no_live_feedback:
        base_args.append("--no-live-feedback")

    print("=== pause run ===")
    pause_cmd = [*base_args, "--stop-after-questions", str(args.pause_after_questions)]
    if run_command(pause_cmd, cwd=Path(__file__).resolve().parents[3]) != 0:
        return 1

    if not checkpoint_path.exists():
        print(f"Missing checkpoint: {checkpoint_path}", file=sys.stderr)
        return 1

    print("=== resume run ===")
    resume_cmd = [*base_args, "--resume-state", str(checkpoint_path)]
    return run_command(resume_cmd, cwd=Path(__file__).resolve().parents[3])


if __name__ == "__main__":
    raise SystemExit(main())
