#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from interview_core import build_intro_question
from question_bank import Question, load_question_bank


def export_languages(target_language: str) -> list[str]:
    return ["zh", "en"] if target_language == "bilingual" else [target_language]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export a speech-overrides template JSON for localized spoken prompts."
    )
    parser.add_argument("--question-bank", required=True, help="Markdown question bank path.")
    parser.add_argument("--output", required=True, help="Path to write the template JSON.")
    parser.add_argument("--language", default="zh", choices=["zh", "en", "bilingual"], help="Target speech language placeholder to generate.")
    parser.add_argument("--level", default="senior", choices=["mid", "senior", "tl"], help="Built-in intro question level.")
    parser.add_argument("--include-intro", action="store_true", help="Include the built-in intro prompt template.")
    return parser.parse_args()


def question_entry(question: Question, target_language: str) -> dict[str, Any]:
    languages = export_languages(target_language)
    return {
        "title": question.title,
        "round": question.round,
        "source_path": question.source_path,
        "display_question": question.question,
        "display_follow_ups": list(question.follow_ups),
        "spoken_question": {language: question.spoken_question.get(language, "") for language in languages},
        "spoken_follow_ups": {
            language: (
                list(question.spoken_follow_ups.get(language, []))
                if question.spoken_follow_ups.get(language)
                else ["" for _ in question.follow_ups]
            )
            for language in languages
        },
    }


def main() -> int:
    args = parse_args()
    questions = load_question_bank(args.question_bank)
    export_questions = list(questions)
    if args.include_intro:
        export_questions = [build_intro_question(args.level, "en"), *export_questions]

    payload = {
        "meta": {
            "question_bank": str(Path(args.question_bank).resolve()),
            "target_language": args.language,
            "question_count": len(export_questions),
            "note": "Fill spoken_question/spoken_follow_ups only. Display text remains unchanged in the runtime UI.",
        },
        "questions": {
            question.id: question_entry(question, args.language)
            for question in export_questions
        },
        "follow_up_categories": {},
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"output={output_path}")
    print(f"question_count={len(export_questions)}")
    print(f"target_language={args.language}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
