#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FIXTURE_ROOT = ROOT / "tests" / "skills" / "android-interview" / "fixtures"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Android interview MVP demo.")
    parser.add_argument("--output-dir", default=str(ROOT / "dist" / "interview-reports" / "mvp-demo"))
    parser.add_argument("--session-id", default="mvp-demo")
    parser.add_argument("--enable-tts", action="store_true", default=True)
    parser.add_argument("--voice", default="en-US-AndrewNeural")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cmd = [
        "python3",
        str(ROOT / "skills" / "android-interview" / "scripts" / "run_interview_session.py"),
        "--jd",
        str(FIXTURE_ROOT / "jd.md"),
        "--resume",
        str(FIXTURE_ROOT / "resume.md"),
        "--question-bank",
        str(FIXTURE_ROOT / "question-bank"),
        "--answers",
        str(FIXTURE_ROOT / "answers.json"),
        "--output-dir",
        args.output_dir,
        "--session-id",
        args.session_id,
        "--voice",
        args.voice,
    ]
    if args.enable_tts:
        cmd.append("--enable-tts")
    return subprocess.call(cmd, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
