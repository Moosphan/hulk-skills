#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ai_schemas import AIConfig
from ai_services import InterviewAIServices
from interview_core import build_intro_question
from question_bank import Question, load_question_bank
from tts_support import contains_cjk


def export_languages(target_language: str) -> list[str]:
    return ["zh", "en"] if target_language == "bilingual" else [target_language]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a speech-overrides JSON by reusing existing spoken text, copying display text, or AI-translating missing prompts."
    )
    parser.add_argument("--question-bank", required=True, help="Markdown question bank path.")
    parser.add_argument("--output", required=True, help="Path to write the speech-overrides JSON.")
    parser.add_argument("--language", default="zh", choices=["zh", "en", "bilingual"], help="Target speech language(s). bilingual generates both zh and en entries.")
    parser.add_argument("--level", default="senior", choices=["mid", "senior", "tl"], help="Built-in intro question level.")
    parser.add_argument("--include-intro", action="store_true", help="Include the built-in intro prompt.")
    parser.add_argument(
        "--fill-mode",
        default="auto",
        choices=["auto", "existing-only", "copy-display", "ai-translate"],
        help="How to populate missing spoken text. auto uses AI when enabled, otherwise copies display text.",
    )
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Regenerate even when spoken_question/spoken_follow_ups already exist for the target language.",
    )
    parser.add_argument("--ai-mode", default="off", choices=["off", "assist", "required"], help="AI runtime mode for ai-translate/auto.")
    parser.add_argument("--ai-provider", default="auto", choices=["auto", "openai-compatible", "fixture", "none"], help="AI provider adapter.")
    parser.add_argument("--model", default="", help="AI model name for provider-backed modes.")
    parser.add_argument("--ai-timeout-seconds", type=int, default=45, help="Timeout for each AI call.")
    parser.add_argument("--ai-cache-dir", default="", help="Reserved cache directory for AI calls.")
    parser.add_argument("--ai-fixture-dir", default="", help="Fixture directory for provider=fixture.")
    return parser.parse_args()


def source_language_for(text: str) -> str:
    return "zh" if contains_cjk(str(text or "")) else "en"


def resolve_fill_mode(requested_mode: str, ai_config: AIConfig) -> str:
    if requested_mode != "auto":
        return requested_mode
    return "ai-translate" if ai_config.enabled else "copy-display"


def localize_text(
    raw_text: str,
    existing_text: str,
    target_language: str,
    fill_mode: str,
    ai_services: InterviewAIServices,
    *,
    replace_existing: bool = False,
) -> tuple[str, str]:
    current_existing = str(existing_text or "").strip()
    display_text = str(raw_text or "").strip()
    if current_existing and not replace_existing:
        return current_existing, "existing"
    if not display_text:
        return "", "empty"

    source_language = source_language_for(display_text)
    if fill_mode == "existing-only":
        return current_existing if replace_existing else "", "blank"
    if source_language == target_language:
        return display_text, "copied_display_same_language"
    if fill_mode == "copy-display":
        return display_text, "copied_display_cross_language"

    translated = ai_services.translate_text(
        display_text,
        source_language=source_language,
        target_language=target_language,
    ).strip()
    if not translated:
        return display_text, "fallback_display_empty_translation"
    if translated == display_text:
        return display_text, "fallback_display_same_text"
    return translated, "ai_translated"


def question_entry(
    question: Question,
    target_languages: list[str],
    fill_mode: str,
    ai_services: InterviewAIServices,
    *,
    replace_existing: bool = False,
    strategy_counts: dict[str, int] | None = None,
) -> dict[str, Any]:
    spoken_question: dict[str, str] = {}
    spoken_follow_ups: dict[str, list[str]] = {}

    for language in target_languages:
        localized_question, question_strategy = localize_text(
            question.question,
            question.spoken_question.get(language, ""),
            language,
            fill_mode,
            ai_services,
            replace_existing=replace_existing,
        )
        spoken_question[language] = localized_question
        if strategy_counts is not None:
            strategy_counts[question_strategy] = strategy_counts.get(question_strategy, 0) + 1

        localized_follow_ups: list[str] = []
        existing_follow_ups = list(question.spoken_follow_ups.get(language, []) or [])
        for idx, follow_up in enumerate(question.follow_ups):
            existing_follow_up = existing_follow_ups[idx] if idx < len(existing_follow_ups) else ""
            localized_follow_up, follow_up_strategy = localize_text(
                follow_up,
                existing_follow_up,
                language,
                fill_mode,
                ai_services,
                replace_existing=replace_existing,
            )
            localized_follow_ups.append(localized_follow_up)
            if strategy_counts is not None:
                strategy_counts[follow_up_strategy] = strategy_counts.get(follow_up_strategy, 0) + 1
        spoken_follow_ups[language] = localized_follow_ups

    return {
        "title": question.title,
        "round": question.round,
        "source_path": question.source_path,
        "display_question": question.question,
        "display_follow_ups": list(question.follow_ups),
        "spoken_question": spoken_question,
        "spoken_follow_ups": spoken_follow_ups,
    }


def main() -> int:
    args = parse_args()
    questions = load_question_bank(args.question_bank)
    export_questions = list(questions)
    if args.include_intro:
        export_questions = [build_intro_question(args.level, "en"), *export_questions]

    ai_config = AIConfig(
        mode=args.ai_mode,
        provider=args.ai_provider,
        model=args.model,
        timeout_seconds=args.ai_timeout_seconds,
        cache_dir=args.ai_cache_dir,
        fixture_dir=args.ai_fixture_dir,
    )
    resolved_fill_mode = resolve_fill_mode(args.fill_mode, ai_config)
    ai_services = InterviewAIServices(ai_config, Path(args.output).resolve().parent)
    languages = export_languages(args.language)
    strategy_counts: dict[str, int] = {}

    payload = {
        "meta": {
            "question_bank": str(Path(args.question_bank).resolve()),
            "target_language": args.language,
            "target_languages": languages,
            "question_count": len(export_questions),
            "fill_mode_requested": args.fill_mode,
            "fill_mode_resolved": resolved_fill_mode,
            "replace_existing": args.replace_existing,
            "note": "Generated for speech-only localization. Display text remains unchanged in the runtime UI.",
        },
        "questions": {
            question.id: question_entry(
                question,
                languages,
                resolved_fill_mode,
                ai_services,
                replace_existing=args.replace_existing,
                strategy_counts=strategy_counts,
            )
            for question in export_questions
        },
        "follow_up_categories": {},
    }
    payload["meta"]["strategy_counts"] = strategy_counts
    payload["meta"]["ai_runtime"] = ai_services.metadata()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"output={output_path}")
    print(f"question_count={len(export_questions)}")
    print(f"target_languages={','.join(languages)}")
    print(f"fill_mode={resolved_fill_mode}")
    print(f"strategy_counts={json.dumps(strategy_counts, ensure_ascii=False, sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
