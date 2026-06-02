#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from interview_core import (
    build_resume_prep,
    build_consistency_summary,
    build_screening_summary,
    QuestionResult,
    build_interview_plan,
    build_persona_configs,
    build_profiles,
    build_round_scorecards,
    build_round_summaries,
    build_round_deliberations,
    build_session_id,
    decision_reason,
    decide_result,
    finalize_interview_plan,
    filter_questions_by_mode,
    final_decision,
    load_answers,
    parse_question_target_overrides,
    parse_round_language_overrides,
    parse_round_persona_overrides,
    planned_language_for_round,
    read_text,
    render_failure_summary,
    render_reject_mail,
    render_report,
    render_resume_prep,
    render_pass_summary,
    render_screening_summary,
    render_transcript,
    score_answer,
    score_payload,
    select_questions,
    session_payload,
    synthesize_summary_artifacts,
    resolve_persona_name,
    write_json,
)
from question_bank import load_question_bank, validate_question_bank, write_question_bank_validation_artifacts
from tts_support import edge_tts_available
from ai_client import AIClientError
from ai_schemas import AIConfig
from ai_services import InterviewAIServices


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an Android interview batch session.")
    parser.add_argument("--jd", required=True, help="Path to JD text or Markdown.")
    parser.add_argument("--resume", required=True, help="Path to resume text or Markdown.")
    parser.add_argument("--question-bank", required=True, help="Markdown question bank path.")
    parser.add_argument("--answers", required=True, help="Path to scripted answers JSON.")
    parser.add_argument("--output-dir", required=True, help="Session output directory.")
    parser.add_argument("--session-id", default="", help="Optional fixed session ID.")
    parser.add_argument("--mode", default="simulate", choices=["simulate", "screening", "round1", "round2", "round3", "hr"])
    parser.add_argument("--level", default="senior", choices=["mid", "senior", "tl"])
    parser.add_argument("--language", default="en", choices=["zh", "en", "bilingual"])
    parser.add_argument("--enable-tts", action="store_true")
    parser.add_argument("--voice", default="en-US-AndrewNeural")
    parser.add_argument("--default-persona", default="", help="Default interviewer persona preset for all rounds.")
    parser.add_argument("--round-persona-overrides", default="", help="Comma-separated round=persona overrides, e.g. round2=technical-deep-diver.")
    parser.add_argument("--round-language-overrides", default="", help="Comma-separated round=language overrides, e.g. round2=bilingual,hr=zh.")
    parser.add_argument("--question-target-overrides", default="", help="Comma-separated round=count overrides, e.g. round1=1,round2=2.")
    parser.add_argument("--ai-mode", default="off", choices=["off", "assist", "required"], help="AI runtime mode. off isolates the deterministic fallback; assist uses AI with fallback; required fails if AI is unavailable.")
    parser.add_argument("--ai-provider", default="auto", choices=["auto", "openai-compatible", "fixture", "none"], help="AI provider adapter.")
    parser.add_argument("--model", default="", help="AI model name for provider-backed modes.")
    parser.add_argument("--ai-timeout-seconds", type=int, default=45, help="Timeout for each AI call.")
    parser.add_argument("--ai-cache-dir", default="", help="Reserved cache directory for AI calls.")
    parser.add_argument("--ai-fixture-dir", default="", help="Fixture directory for provider=fixture.")
    return parser.parse_args()


def evaluate_question_batch(question, answer_item, turn_index: int, persona_name: str, persona_dimensions: dict[str, int], ai_services: InterviewAIServices) -> QuestionResult:
    answer = str(answer_item.get("answer", "")).strip()
    candidate_follow_ups = list(answer_item.get("follow_up_answers", []) or [])
    follow_up_chain: list[dict[str, str]] = []
    prompts = question.follow_ups[: question.follow_up_limit]
    for idx, prompt in enumerate(prompts):
        reply = candidate_follow_ups[idx] if idx < len(candidate_follow_ups) else ""
        follow_up_chain.append({"question": prompt, "answer": reply})
    follow_up_answers = [item["answer"] for item in follow_up_chain if item["answer"]]
    score, confidence, strengths, risks, missing, question_alignment = ai_services.evaluate_answer(answer, follow_up_answers, question, score_answer)
    decision_result = ai_services.decide_result(score, confidence, missing, risks, question.round, question_alignment, decide_result)
    return QuestionResult(
        id=question.id,
        title=question.title,
        round=question.round,
        question=question.question,
        answer=answer,
        follow_up_chain=follow_up_chain,
        score=score,
        confidence=confidence,
        strength_evidence=strengths,
        risk_evidence=risks,
        missing_evidence=missing,
        source_path=question.source_path,
        decision_result=decision_result,
        turn_index=turn_index,
        direction=question.direction,
        competencies=question.competencies,
        persona=persona_name,
        persona_dimensions=persona_dimensions,
        decision_reason=decision_reason(decision_result, score, confidence, missing, risks),
        round_focus=list(question.competencies or ([question.direction] if question.direction else [])),
        question_source=question.source,
        matched_good_signals=question_alignment["matched_good_signals"],
        matched_red_flags=question_alignment["matched_red_flags"],
        expected_signal_hit=bool(question_alignment["expected_signal_hit"]),
        question_bank_alignment=question_alignment["question_bank_alignment"],
    )


def main() -> int:
    args = parse_args()
    jd_text = read_text(args.jd)
    resume_text = read_text(args.resume)
    answers = load_answers(args.answers)
    resolved_default_persona = resolve_persona_name(args.default_persona) if args.default_persona else ""
    round_persona_overrides = parse_round_persona_overrides(args.round_persona_overrides)
    round_language_overrides = parse_round_language_overrides(args.round_language_overrides)
    question_target_overrides = parse_question_target_overrides(args.question_target_overrides)
    session_id = build_session_id(args.session_id, answers.get("_meta", {}).get("candidate_name", "candidate"), "mvp")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ai_config = AIConfig(
        mode=args.ai_mode,
        provider=args.ai_provider,
        model=args.model,
        timeout_seconds=args.ai_timeout_seconds,
        cache_dir=args.ai_cache_dir,
        fixture_dir=args.ai_fixture_dir,
    )
    ai_services = InterviewAIServices(ai_config, output_dir)
    all_questions = load_question_bank(args.question_bank)
    question_bank_validation = validate_question_bank(args.question_bank, all_questions)
    write_question_bank_validation_artifacts(output_dir, question_bank_validation)
    print(f"question_bank_status={question_bank_validation['status']}")
    print(f"question_bank_errors={question_bank_validation['error_count']}")
    if question_bank_validation["error_count"]:
        raise SystemExit("Question bank validation failed; fix the Markdown bank before running the interview.")

    interview_plan = build_interview_plan(
        jd_text,
        resume_text,
        args.level,
        args.language,
        args.mode,
        question_target_overrides=question_target_overrides,
        round_language_overrides=round_language_overrides,
    )
    selected_questions = filter_questions_by_mode(
        select_questions(all_questions, jd_text, resume_text, args.level, args.language, interview_plan),
        args.mode,
    )
    interview_plan = finalize_interview_plan(interview_plan, selected_questions)
    persona_configs = build_persona_configs(
        args.language,
        [question.round for question in selected_questions],
        default_persona=resolved_default_persona,
        round_persona_overrides=round_persona_overrides,
        round_language_overrides=round_language_overrides,
    )
    persona_by_round = {item.round: item for item in persona_configs}

    results = []
    for index, question in enumerate(selected_questions, start=1):
        persona = persona_by_round[question.round]
        try:
            results.append(
                evaluate_question_batch(
                    question,
                    answers.get(question.id, {}),
                    turn_index=index,
                    persona_name=persona.persona,
                    persona_dimensions={
                        "pressure_level": persona.pressure_level,
                        "guidance_level": persona.guidance_level,
                        "skepticism_level": persona.skepticism_level,
                        "depth_threshold": persona.depth_threshold,
                        "business_focus": persona.business_focus,
                        "leadership_focus": persona.leadership_focus,
                    },
                    ai_services=ai_services,
                )
            )
        except AIClientError as exc:
            raise SystemExit(f"AI runtime failed in required mode: {exc}") from exc

    round_summaries = build_round_summaries(results, args.level, interview_plan)
    round_scorecards = build_round_scorecards(results, round_summaries, interview_plan, args.level)
    round_deliberations = build_round_deliberations(results, args.level, interview_plan)
    decision, hard_fail_flags = final_decision(results, round_scorecards)
    job_profile, candidate_profile = build_profiles(jd_text, resume_text, args.level, args.language)
    screening_summary = build_screening_summary(
        jd_text,
        resume_text,
        args.level,
        args.language,
        interview_plan,
        job_profile=job_profile,
        candidate_profile=candidate_profile,
    )
    consistency_summary = build_consistency_summary(results, screening_summary)
    resume_prep = build_resume_prep(
        jd_text,
        resume_text,
        args.level,
        args.language,
        screening_summary,
        interview_plan=interview_plan,
        job_profile=job_profile,
        candidate_profile=candidate_profile,
    )

    tts_files: list[str] = []
    tts_status = "disabled"
    if args.enable_tts:
        if edge_tts_available():
            tts_files = synthesize_summary_artifacts(output_dir, results, decision, args.voice)
            tts_status = "generated"
        else:
            tts_status = "edge-tts-not-installed"

    session_data = session_payload(
        session_id=session_id,
        level=args.level,
        language=args.language,
        enable_tts=args.enable_tts,
        voice=args.voice,
        job_profile=job_profile,
        candidate_profile=candidate_profile,
        results=results,
        turn_events=[],
        tts_status=tts_status,
        tts_files=tts_files,
        question_sources=sorted({result.source_path for result in results}),
        hard_fail_flags=hard_fail_flags,
        mode=args.mode,
        interactive_mode=False,
        round_summaries=round_summaries,
        round_deliberations=round_deliberations,
        persona_configs=persona_configs,
        session_state_history=["intake", "planning", "round_review", "reporting", "completed"],
        final_decision_value=decision,
        interview_plan=interview_plan,
        terminated_early=False,
        round_scorecards=round_scorecards,
        screening_summary=screening_summary,
        consistency_summary=consistency_summary,
        resume_prep=resume_prep,
        extra_input_config={
            "default_persona": resolved_default_persona,
            "round_persona_overrides": round_persona_overrides,
            "round_language_overrides": round_language_overrides,
            "question_target_overrides": question_target_overrides,
            **ai_services.metadata(),
        },
        question_bank_validation=question_bank_validation,
    )
    score_data = score_payload(results, hard_fail_flags, decision, round_summaries, round_scorecards, consistency_summary, round_deliberations)
    score_data["ai_runtime"] = ai_services.metadata()

    write_json(output_dir / "session.json", session_data)
    write_json(output_dir / "ai-runtime.json", ai_services.trace_payload())
    write_json(output_dir / "score.json", score_data)
    write_json(output_dir / "interview-plan.json", interview_plan)
    write_json(output_dir / "screening-summary.json", screening_summary)
    write_json(output_dir / "resume-prep.json", resume_prep)
    render_screening_summary(output_dir / "screening-summary.md", session_id, screening_summary)
    render_resume_prep(output_dir / "resume-prep.md", session_id, resume_prep)
    render_transcript(output_dir / "transcript.md", session_id, results, round_summaries, round_deliberations, [])
    render_report(output_dir / "report.html", session_data, score_data)
    if decision == "fail":
        render_reject_mail(output_dir / "mail-reject.html", session_id, hard_fail_flags, round_summaries)
        render_failure_summary(output_dir / "fail-summary.md", session_data, score_data)
    elif decision == "pass":
        render_pass_summary(output_dir / "pass-summary.md", session_id, session_data, score_data)

    print(f"session_id={session_id}")
    print(f"output_dir={output_dir}")
    print(f"decision={decision}")
    print(f"tts_status={tts_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
