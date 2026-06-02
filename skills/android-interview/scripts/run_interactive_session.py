#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from interview_core import (
    QuestionResult,
    PersonaConfig,
    TurnEvent,
    build_consistency_summary,
    build_dynamic_question,
    build_interview_plan,
    build_intro_question,
    build_screening_summary,
    build_persona_configs,
    build_profiles,
    build_round_scorecards,
    build_round_summaries,
    build_round_deliberations,
    build_resume_prep,
    build_session_id,
    compose_main_prompt,
    compose_round_intro,
    decision_reason,
    decide_result,
    finalize_interview_plan,
    filter_questions_by_mode,
    final_decision,
    language_text,
    load_answers,
    parse_question_target_overrides,
    parse_round_language_overrides,
    parse_round_persona_overrides,
    planned_language_for_round,
    question_difficulty_rank,
    question_focuses,
    choose_adaptive_next_question,
    read_text,
    render_failure_summary,
    render_pass_summary,
    render_reject_mail,
    render_report,
    render_resume_prep,
    render_screening_summary,
    render_transcript,
    score_answer,
    score_payload,
    select_questions,
    session_payload,
    signal_tags,
    synthesize_summary_artifacts,
    synthesize_turn_prompt,
    resolve_persona_name,
    write_json,
)
from question_bank import Question, load_question_bank, validate_question_bank, write_question_bank_validation_artifacts
from tts_support import edge_tts_available
from ai_client import AIClientError
from ai_schemas import AIConfig
from ai_services import InterviewAIServices


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an interactive Android interview session.")
    parser.add_argument("--jd", required=True, help="Path to JD text or Markdown.")
    parser.add_argument("--resume", required=True, help="Path to resume text or Markdown.")
    parser.add_argument("--question-bank", required=True, help="Markdown question bank path.")
    parser.add_argument("--output-dir", required=True, help="Session output directory.")
    parser.add_argument("--session-id", default="", help="Optional fixed session ID.")
    parser.add_argument("--mode", default="simulate", choices=["simulate", "screening", "round1", "round2", "round3", "hr"])
    parser.add_argument("--level", default="senior", choices=["mid", "senior", "tl"])
    parser.add_argument("--language", default="en", choices=["zh", "en", "bilingual"])
    parser.add_argument("--enable-tts", action="store_true")
    parser.add_argument("--voice", default="en-US-AndrewNeural")
    parser.add_argument("--disable-early-termination", action="store_true")
    parser.add_argument("--resume-state", help="Path to a previous session-checkpoint.json to resume.")
    parser.add_argument("--stop-after-questions", type=int, default=0, help="Pause after N completed questions to create a resumable checkpoint.")
    parser.add_argument("--no-live-feedback", action="store_true", help="Disable automatic feedback after each answered question.")
    parser.add_argument("--adaptive-runtime-routing", action="store_true", help="Enable runtime reordering of the remaining questions based on the last answer.")
    parser.add_argument("--deliberation-bridge-probes", action="store_true", help="Allow round deliberation to hold the round for one extra targeted probe before advancing.")
    parser.add_argument("--default-persona", default="", help="Default interviewer persona preset for all rounds.")
    parser.add_argument("--round-persona-overrides", default="", help="Comma-separated round=persona overrides, e.g. round2=technical-deep-diver,hr=leadership-evaluator.")
    parser.add_argument("--round-language-overrides", default="", help="Comma-separated round=language overrides, e.g. round2=bilingual,hr=zh.")
    parser.add_argument("--question-target-overrides", default="", help="Comma-separated round=count overrides, e.g. round1=1,round2=2.")
    parser.add_argument("--scripted-answers", help="Optional JSON file for scripted interactive testing.")
    parser.add_argument("--ai-mode", default="off", choices=["off", "assist", "required"], help="AI runtime mode. off isolates the deterministic fallback; assist uses AI with fallback; required fails if AI is unavailable.")
    parser.add_argument("--ai-provider", default="auto", choices=["auto", "openai-compatible", "fixture", "none"], help="AI provider adapter.")
    parser.add_argument("--model", default="", help="AI model name for provider-backed modes.")
    parser.add_argument("--ai-timeout-seconds", type=int, default=45, help="Timeout for each AI call.")
    parser.add_argument("--ai-cache-dir", default="", help="Reserved cache directory for AI calls.")
    parser.add_argument("--ai-fixture-dir", default="", help="Fixture directory for provider=fixture.")
    return parser.parse_args()


class ScriptedAnswerProvider:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.follow_up_offsets: dict[str, int] = {}

    def candidate_name(self) -> str:
        return str(self.payload.get("_meta", {}).get("candidate_name", "candidate"))

    def answer(self, question_id: str) -> str:
        return str(self.payload.get(question_id, {}).get("answer", "")).strip()

    def follow_up_answer(self, question_id: str) -> str:
        item = self.payload.get(question_id, {})
        arr = list(item.get("follow_up_answers", []) or [])
        offset = self.follow_up_offsets.get(question_id, 0)
        self.follow_up_offsets[question_id] = offset + 1
        return str(arr[offset]).strip() if offset < len(arr) else ""


class UserAbort(Exception):
    pass


def question_from_payload(payload: dict[str, Any]) -> Question:
    return Question(**payload)


def persona_from_payload(payload: dict[str, Any]) -> PersonaConfig:
    return PersonaConfig(**payload)


def question_result_from_payload(payload: dict[str, Any]) -> QuestionResult:
    return QuestionResult(**payload)


def turn_event_from_payload(payload: dict[str, Any]) -> TurnEvent:
    return TurnEvent(**payload)


def load_checkpoint(path: str | Path) -> dict[str, Any]:
    return load_answers(path)


def build_checkpoint_hint(round_order: list[str], round_questions: dict[str, list[Question]], next_round_index: int, next_question_index: int) -> dict[str, Any]:
    next_round = round_order[next_round_index] if next_round_index < len(round_order) else ""
    next_question_id = ""
    if next_round and next_question_index < len(round_questions.get(next_round, [])):
        next_question_id = round_questions[next_round][next_question_index].id
    return {
        "next_round": next_round,
        "next_question_id": next_question_id,
    }


def write_session_checkpoint(
    output_dir: Path,
    session_id: str,
    session_status: str,
    checkpoint_status: str,
    checkpoint_reason: str,
    input_paths: dict[str, str],
    level: str,
    language: str,
    mode: str,
    enable_tts: bool,
    voice: str,
    interview_plan: dict[str, Any],
    selected_questions: list[Question],
    persona_configs: list[PersonaConfig],
    results: list[QuestionResult],
    turn_events: list[TurnEvent],
    session_state_history: list[str],
    hard_fail_flags: list[str],
    terminated_early: bool,
    turn_index_next: int,
    next_round_index: int,
    next_question_index: int,
    resume_context: dict[str, Any],
    extra_input_config: dict[str, Any] | None = None,
) -> None:
    payload = {
        "schema_version": 1,
        "session_id": session_id,
        "updated_at": datetime.now().isoformat(),
        "output_dir": str(output_dir),
        "session_status": session_status,
        "checkpoint_status": checkpoint_status,
        "checkpoint_reason": checkpoint_reason,
        "input_paths": input_paths,
        "input_config": {
            "level": level,
            "language": language,
            "mode": mode,
            "enable_tts": enable_tts,
            "voice": voice,
            **(extra_input_config or {}),
        },
        "interview_plan": interview_plan,
        "selected_questions": [asdict(item) for item in selected_questions],
        "persona_configs": [asdict(item) for item in persona_configs],
        "results": [asdict(item) for item in results],
        "turn_events": [asdict(item) for item in turn_events],
        "session_state_history": session_state_history,
        "hard_fail_flags": hard_fail_flags,
        "terminated_early": terminated_early,
        "turn_index_next": turn_index_next,
        "next_round_index": next_round_index,
        "next_question_index": next_question_index,
        "completed_question_count": len(results),
        "resume_context": resume_context,
        "checkpoint_resume_hint": build_checkpoint_hint(
            [round_name for round_name in dict.fromkeys(question.round for question in selected_questions if question.round)],
            {
                round_name: [question for question in selected_questions if question.round == round_name]
                for round_name in dict.fromkeys(question.round for question in selected_questions if question.round)
            },
            next_round_index,
            next_question_index,
        ),
    }
    write_json(output_dir / "session-checkpoint.json", payload)


def latest_feedback_payload(results: list[QuestionResult]) -> dict[str, Any]:
    if not results:
        return {}
    latest = results[-1]
    return {
        "question_id": latest.id,
        "title": latest.title,
        "round": latest.round,
        "score": latest.score,
        "confidence": latest.confidence,
        "decision_result": latest.decision_result,
        "decision_reason": latest.decision_reason,
        "strength_evidence": latest.strength_evidence,
        "risk_evidence": latest.risk_evidence,
        "missing_evidence": latest.missing_evidence,
        "persona": latest.persona,
    }


def write_session_progress(
    output_dir: Path,
    session_id: str,
    session_status: str,
    current_round: str,
    current_question_id: str,
    results: list[QuestionResult],
    turn_events: list[TurnEvent],
    hard_fail_flags: list[str],
    interview_plan: dict[str, Any],
    level: str,
    decision: str,
    resume_context: dict[str, Any],
) -> None:
    round_summaries = build_round_summaries(results, level, interview_plan) if results else []
    round_scorecards = build_round_scorecards(results, round_summaries, interview_plan, level) if results else []
    round_deliberations = build_round_deliberations(results, level, interview_plan) if results else []
    payload = {
        "schema_version": 1,
        "session_id": session_id,
        "updated_at": datetime.now().isoformat(),
        "session_status": session_status,
        "current_round": current_round,
        "current_question_id": current_question_id,
        "completed_question_count": len(results),
        "turn_count": len(turn_events),
        "current_decision": decision,
        "hard_fail_flags": hard_fail_flags,
        "latest_question_feedback": latest_feedback_payload(results),
        "round_summaries": [asdict(item) for item in round_summaries],
        "round_scorecards": round_scorecards,
        "round_deliberations": round_deliberations,
        "resume_context": resume_context,
    }
    write_json(output_dir / "session-progress.json", payload)


def format_latest_feedback(results: list[QuestionResult]) -> str:
    if not results:
        return "No completed question yet."
    latest = results[-1]
    lines = [
        f"Latest feedback: {latest.round} / {latest.title}",
        f"  score={latest.score} confidence={latest.confidence} decision={latest.decision_result}",
    ]
    if latest.strength_evidence:
        lines.append(f"  strengths: {', '.join(latest.strength_evidence[:3])}")
    if latest.risk_evidence:
        lines.append(f"  risks: {', '.join(latest.risk_evidence[:3])}")
    if latest.missing_evidence:
        lines.append(f"  missing: {', '.join(latest.missing_evidence[:3])}")
    return "\n".join(lines)


def format_scorecards(results: list[QuestionResult], level: str, interview_plan: dict[str, Any]) -> str:
    if not results:
        return "No scorecard yet. Complete at least one question first."
    round_summaries = build_round_summaries(results, level, interview_plan)
    round_scorecards = build_round_scorecards(results, round_summaries, interview_plan, level)
    lines = ["Current scorecards:"]
    for item in round_scorecards[-3:]:
        lines.append(f"  {item['round']}: {item['round_verdict']} | {item['verdict_reason']}")
    return "\n".join(lines)


def format_turn_feedback(result: QuestionResult) -> str:
    lines = [
        f"[live feedback] {result.round} / {result.title}",
        f"score={result.score} confidence={result.confidence} decision={result.decision_result}",
    ]
    if result.strength_evidence:
        lines.append(f"strengths: {', '.join(result.strength_evidence[:2])}")
    if result.risk_evidence:
        lines.append(f"risks: {', '.join(result.risk_evidence[:2])}")
    if result.missing_evidence:
        lines.append(f"missing: {', '.join(result.missing_evidence[:2])}")
    return "\n".join(lines)


class InteractiveConsole:
    def __init__(self, enabled: bool, session_id: str, output_dir: Path, interview_plan: dict[str, Any]) -> None:
        self.enabled = enabled
        self.session_id = session_id
        self.output_dir = output_dir
        self.interview_plan = interview_plan

    def print_banner(self) -> None:
        if not self.enabled:
            return
        print()
        print("=" * 72)
        print("Android Interview Live Session")
        print(f"session_id={self.session_id}")
        print(f"output_dir={self.output_dir}")
        print("Commands: /help /status /plan /feedback /scorecard /checkpoint /repeat /skip /quit")
        print("=" * 72)

    def _print_help(self) -> None:
        print("Commands:")
        print("  /help   show the command list")
        print("  /status show current round and progress")
        print("  /plan   show current round focus and planned topics")
        print("  /feedback show the latest completed-question feedback")
        print("  /scorecard show the current round scorecards")
        print("  /checkpoint write a resumable checkpoint without exiting")
        print("  /repeat show the current question again")
        print("  /skip   submit a skip placeholder for the current answer")
        print("  /quit   end the session early and write partial artifacts")

    def _print_status(self, context: dict[str, Any]) -> None:
        print(
            "Status:"
            f" round={context['round_name']} ({context['round_index']}/{context['round_total']})"
            f" question={context['question_index']}/{context['question_total']}"
            f" completed_questions={context['completed_questions']}"
            f" current_decision={context.get('last_decision', 'n/a')}"
        )
        if context.get("latest_risks"):
            print("Latest risks:")
            for item in context["latest_risks"]:
                print(f"  - {item}")

    def _print_plan(self, context: dict[str, Any]) -> None:
        round_name = context["round_name"]
        item = next((entry for entry in self.interview_plan.get("rounds", []) if entry.get("round") == round_name), None)
        if not item:
            print("No round plan available.")
            return
        print(f"Round plan for {item['label']}:")
        print(f"  target questions: {item['question_target']}")
        print(f"  priority focuses: {', '.join(item.get('priority_focuses', [])) or 'n/a'}")
        for reason in item.get("selection_reasons", []):
            print(f"  - {reason['focus']}: {reason['reason']}")

    def prompt(self, prompt: str, context: dict[str, Any]) -> str:
        if not self.enabled:
            raise RuntimeError("InteractiveConsole.prompt should only be used in live mode.")
        print()
        print(prompt)
        while True:
            raw = input("> ").strip()
            if not raw.startswith("/"):
                return raw
            command = raw.split()[0].lower()
            if command == "/help":
                self._print_help()
            elif command == "/status":
                self._print_status(context)
            elif command == "/plan":
                self._print_plan(context)
            elif command == "/feedback":
                printer = context.get("feedback_printer")
                print(printer() if callable(printer) else "No feedback available.")
            elif command == "/scorecard":
                printer = context.get("scorecard_printer")
                print(printer() if callable(printer) else "No scorecard available.")
            elif command == "/checkpoint":
                saver = context.get("checkpoint_saver")
                print(saver() if callable(saver) else "Checkpoint saver is not available.")
            elif command == "/repeat":
                print(prompt)
            elif command == "/skip":
                return "[candidate skipped answer]"
            elif command == "/quit":
                raise UserAbort("user_requested_exit")
            else:
                print("Unknown command. Use /help to see the available commands.")


def maybe_tts(output_dir: Path, turn_index: int, prompt: str, enable_tts: bool, voice: str) -> str:
    if not enable_tts or not edge_tts_available():
        return ""
    return synthesize_turn_prompt(output_dir, turn_index, prompt, voice)


def result_evidence_text(result: QuestionResult) -> str:
    parts = [
        result.answer,
        *[item.get("answer", "") for item in result.follow_up_chain],
        *result.strength_evidence,
        *result.risk_evidence,
        *result.missing_evidence,
    ]
    return " ".join(item for item in parts if item)


def latest_result_with_signal(previous_results: list[QuestionResult], signal_name: str) -> QuestionResult | None:
    for result in reversed(previous_results):
        if signal_name in signal_tags(result_evidence_text(result)):
            return result
    return None


def runtime_consistency_candidate(
    question,
    persona,
    language: str,
    previous_results: list[QuestionResult],
    current_text: str,
) -> dict[str, Any] | None:
    if persona.skepticism_level < 3 or not previous_results:
        return None

    lowered = current_text.lower()
    ownership_history = latest_result_with_signal(previous_results, "ownership")
    ownership_conflict = any(
        token in lowered
        for token in [
            "mostly coordinated",
            "coordination role",
            "supporting role",
            "team owned",
            "backend team owned",
            "qa owned",
            "i was not the owner",
            "not the primary owner",
            "not my decision",
        ]
    )
    if ownership_history and ownership_conflict:
        prompt = language_text(
            language,
            f"前面聊到《{ownership_history.title}》时，你给人的感觉是明确 owner；但这次回答里你更像是在做协调。请把这两个案例的职责边界重新对齐，并非常具体地说明这一次你亲自负责了什么。",
            f"Earlier, when we discussed {ownership_history.title}, you sounded like the direct owner. In this example you sound more like a coordinator. Reconcile the two and be very explicit about what you personally owned here.",
            f"Earlier, when we discussed {ownership_history.title}, you sounded like the direct owner. In this example you sound more like a coordinator. Reconcile the two and be very explicit about what you personally owned here. 如有必要可补充中文，但请先用英文说清职责边界。",
        )
        return {
            "category": "runtime_consistency_ownership",
            "stage": "consistency_challenge",
            "prompt": prompt,
            "notes": ["consistency_challenge", "ownership_consistency", ownership_history.id],
        }

    metrics_history = latest_result_with_signal(previous_results, "metrics")
    metrics_conflict = any(
        token in lowered
        for token in [
            "do not remember the exact",
            "don't remember the exact",
            "cannot recall the exact",
            "can't recall the exact",
            "not sure about the metric",
            "not sure about the baseline",
            "we did not really track",
            "i no longer remember the numbers",
        ]
    )
    if metrics_history and metrics_conflict:
        prompt = language_text(
            language,
            f"前面聊到《{metrics_history.title}》时，你能给出比较具体的指标；但这个案例里你又说自己记不清数字。请解释这是否是项目属性不同，还是当时其实没有建立稳定指标，并给出你现在还能负责的最近似口径。",
            f"Earlier, when we discussed {metrics_history.title}, you were comfortable with concrete metrics. In this example you say you do not remember the numbers. Explain whether this project had a different measurement setup or whether the metrics were never tracked well, and give me the closest baseline and outcome you can still defend.",
            f"Earlier, when we discussed {metrics_history.title}, you were comfortable with concrete metrics. In this example you say you do not remember the numbers. Explain whether this project had a different measurement setup or whether the metrics were never tracked well, and give me the closest baseline and outcome you can still defend. 如有必要可补充中文解释。",
        )
        return {
            "category": "runtime_consistency_metrics",
            "stage": "consistency_challenge",
            "prompt": prompt,
            "notes": ["consistency_challenge", "metrics_consistency", metrics_history.id],
        }

    tradeoff_history = latest_result_with_signal(previous_results, "tradeoff")
    tradeoff_conflict = any(
        token in lowered
        for token in [
            "there was not really a tradeoff",
            "there was no real tradeoff",
            "we just followed the default",
            "we did not compare alternatives",
            "i just followed the existing pattern",
            "no real alternative",
        ]
    )
    if tradeoff_history and tradeoff_conflict:
        prompt = language_text(
            language,
            f"前面聊到《{tradeoff_history.title}》时，你能讲清方案权衡；但这个案例里你又像是在说几乎没有比较过替代方案。请解释这是不是因为场景本身更简单，还是当时其实没有做过严肃权衡，并把你排除过的方案讲清楚。",
            f"Earlier, when we discussed {tradeoff_history.title}, you showed clear tradeoff reasoning. In this example you now sound like there was barely any alternative analysis. Explain whether this case was genuinely simpler or whether the tradeoffs were never examined rigorously, and walk me through the option you rejected.",
            f"Earlier, when we discussed {tradeoff_history.title}, you showed clear tradeoff reasoning. In this example you now sound like there was barely any alternative analysis. Explain whether this case was genuinely simpler or whether the tradeoffs were never examined rigorously, and walk me through the option you rejected. 如有必要可补充中文解释。",
        )
        return {
            "category": "runtime_consistency_tradeoff",
            "stage": "consistency_challenge",
            "prompt": prompt,
            "notes": ["consistency_challenge", "tradeoff_consistency", tradeoff_history.id],
        }

    leadership_history = latest_result_with_signal(previous_results, "leadership")
    leadership_conflict = any(
        token in lowered
        for token in [
            "my manager handled the alignment",
            "i just followed the decision",
            "i was not really influencing",
            "i was not involved in the conflict",
            "product decided everything",
            "i mostly executed the plan",
        ]
    )
    if leadership_history and leadership_conflict:
        prompt = language_text(
            language,
            f"前面聊到《{leadership_history.title}》时，你给人的感觉是能推动团队达成一致；但这个案例里你又像是在被动执行。请把这两种状态区分清楚，并说明这一次你具体影响了什么、没有影响什么。",
            f"Earlier, when we discussed {leadership_history.title}, you sounded like someone who could drive alignment. In this example you now sound much more passive. Separate those two situations clearly and tell me exactly what you influenced here and what you did not control.",
            f"Earlier, when we discussed {leadership_history.title}, you sounded like someone who could drive alignment. In this example you now sound much more passive. Separate those two situations clearly and tell me exactly what you influenced here and what you did not control. 如有必要可补充中文。",
        )
        return {
            "category": "runtime_consistency_leadership",
            "stage": "consistency_challenge",
            "prompt": prompt,
            "notes": ["consistency_challenge", "leadership_consistency", leadership_history.id],
        }

    return None


def follow_up_candidates(
    question,
    persona,
    language: str,
    missing_evidence: list[str],
    risk_evidence: list[str],
    previous_results: list[QuestionResult] | None = None,
    current_text: str = "",
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    def add_candidate(category: str, stage: str, prompt: str, notes: list[str]) -> None:
        if prompt and all(item["prompt"] != prompt for item in candidates):
            candidates.append({"category": category, "stage": stage, "prompt": prompt, "notes": notes})

    consistency_candidate = runtime_consistency_candidate(
        question,
        persona,
        language,
        list(previous_results or []),
        current_text,
    )
    if consistency_candidate is not None:
        add_candidate(
            consistency_candidate["category"],
            consistency_candidate["stage"],
            consistency_candidate["prompt"],
            consistency_candidate["notes"],
        )

    if any("职责边界" in risk for risk in risk_evidence) or persona.skepticism_level >= 4:
        add_candidate(
            "ownership_challenge",
            "challenge",
            language_text(
                language,
                "请你非常具体地说明，你亲自负责了哪一部分，团队其他人分别负责什么。",
                "Be very precise about what you personally owned, and what was handled by the rest of the team.",
                "Be very precise about what you personally owned, and what was handled by the rest of the team. 如有必要可补充中文，但核心回答请保持英文。",
            ),
            ["ownership", "skepticism"],
        )

    if any("量化结果" in item or "指标" in item for item in risk_evidence + missing_evidence) or persona.business_focus >= 4:
        add_candidate(
            "metrics_probe",
            "follow_up",
            language_text(
                language,
                "这件事最后的结果是如何量化的？请给我指标口径、基线和变化结果。",
                "How was the outcome measured? Give me the metric definition, baseline, and the observed change.",
                "How was the outcome measured? Give me the metric definition, baseline, and the observed change. 如果需要，可补充中文解释指标口径。",
            ),
            ["metrics", "business"],
        )

    if any("权衡" in item for item in missing_evidence) or persona.depth_threshold >= 4:
        add_candidate(
            "tradeoff_probe",
            "follow_up",
            language_text(
                language,
                "这里最关键的技术权衡是什么？你为什么选择这个方案，而不是另一个更直接的方案？",
                "What was the key tradeoff here, and why did you choose this approach instead of a more direct alternative?",
                "What was the key tradeoff here, and why did you choose this approach instead of a more direct alternative? 需要时可补充中文术语说明。",
            ),
            ["tradeoff", "depth"],
        )

    if any("失败" in item or "回滚" in item for item in missing_evidence) or persona.skepticism_level >= 4:
        add_candidate(
            "failure_probe",
            "challenge",
            language_text(
                language,
                "给我一个你们差点失败、回滚，或者发现关键问题的具体时刻。你当时是怎么处理的？",
                "Give me one specific moment where the project almost failed, needed rollback, or exposed a critical issue. How did you handle it?",
                "Give me one specific moment where the project almost failed, needed rollback, or exposed a critical issue. How did you handle it? 必要时可补充中文背景。",
            ),
            ["failure", "skepticism"],
        )

    if persona.leadership_focus >= 4 and question.round in {"round3", "hr"}:
        add_candidate(
            "leadership_probe",
            "follow_up",
            language_text(
                language,
                "当团队里有人不同意你的方案时，你具体是怎么推进到最终一致的？",
                "When someone on the team disagreed with your approach, how exactly did you drive the discussion to a final alignment?",
                "When someone on the team disagreed with your approach, how exactly did you drive the discussion to a final alignment? 必要时可补充中文背景。",
            ),
            ["leadership"],
        )

    if persona.business_focus >= 4 and question.round in {"round3", "hr"}:
        add_candidate(
            "business_probe",
            "follow_up",
            language_text(
                language,
                "如果从业务结果角度复盘，这件事最值得保留和最应该重做的部分分别是什么？",
                "From a business outcome perspective, what would you absolutely keep, and what would you redesign today?",
                "From a business outcome perspective, what would you absolutely keep, and what would you redesign today? 如有必要可补充中文。",
            ),
            ["business"],
        )

    for prompt in question.follow_ups[: question.follow_up_limit]:
        add_candidate("question_bank", "follow_up", prompt, ["question_bank"])

    return candidates


def max_follow_up_count(question, persona) -> int:
    persona_limit = 1 + max(0, persona.depth_threshold - 3)
    return max(1, min(question.follow_up_limit, persona_limit))


def build_console_context(
    round_name: str,
    round_index: int,
    round_total: int,
    question_index: int,
    question_total: int,
    results: list[QuestionResult],
    hard_fail_flags: list[str],
    last_decision: str = "",
    feedback_printer: Any = None,
    scorecard_printer: Any = None,
    checkpoint_saver: Any = None,
) -> dict[str, Any]:
    latest_risks = results[-1].risk_evidence if results else []
    return {
        "round_name": round_name,
        "round_index": round_index,
        "round_total": round_total,
        "question_index": question_index,
        "question_total": question_total,
        "completed_questions": len(results),
        "latest_risks": latest_risks or hard_fail_flags[-2:],
        "last_decision": last_decision,
        "feedback_printer": feedback_printer,
        "scorecard_printer": scorecard_printer,
        "checkpoint_saver": checkpoint_saver,
    }


def should_switch_topic(
    result: QuestionResult,
    remaining_questions: list[Any],
    planned_focuses: list[str],
    covered_focuses: set[str],
) -> bool:
    if not remaining_questions:
        return False
    if result.decision_result not in {"advance_same_round", "increase_difficulty", "complete_round_pass", "switch_topic"}:
        return False
    remaining_focuses = {focus for question in remaining_questions for focus in question_focuses(question)}
    uncovered_planned = [focus for focus in planned_focuses if focus not in covered_focuses]
    if uncovered_planned and any(focus in remaining_focuses for focus in uncovered_planned):
        return True
    current_focuses = set(question_focuses(result))
    return any(not current_focuses.intersection(question_focuses(question)) for question in remaining_questions)


def clamp_persona_level(value: int) -> int:
    return max(1, min(5, int(value)))


def build_round_transition_state(
    round_summary: dict[str, Any] | Any,
    round_deliberation: dict[str, Any],
    next_round_name: str,
) -> dict[str, Any]:
    next_action = str(round_deliberation.get("next_action", ""))
    failed_focuses = [str(item) for item in round_deliberation.get("failed_focuses", []) if item]
    missing_focuses = [str(item) for item in round_deliberation.get("missing_focuses", []) if item]
    risk_focuses = failed_focuses or missing_focuses
    state = {
        "from_round": str(round_deliberation.get("round", "")),
        "from_label": str(round_deliberation.get("label", "")),
        "next_round": next_round_name,
        "next_action": next_action,
        "mode": "steady_transition",
        "focuses": risk_focuses[:3],
        "pressure_delta": 0,
        "guidance_delta": 0,
        "skepticism_delta": 0,
        "depth_delta": 0,
        "business_delta": 0,
        "leadership_delta": 0,
        "score": float(getattr(round_summary, "score", round_deliberation.get("score", 0.0))),
        "confidence": float(getattr(round_summary, "confidence", round_deliberation.get("confidence", 0.0))),
    }
    if next_action == "continue_with_targeted_probe":
        state["mode"] = "carry_risk_forward"
        state["pressure_delta"] = 1
        state["skepticism_delta"] = 1
        state["guidance_delta"] = -1
    elif next_action == "seek_more_evidence":
        state["mode"] = "evidence_recovery"
        state["guidance_delta"] = 1
        state["depth_delta"] = 1
    elif next_action == "advance_to_next_round":
        state["mode"] = "clean_advance"
    elif next_action == "stop_session":
        state["mode"] = "termination_path"
        state["pressure_delta"] = 1
        state["skepticism_delta"] = 1

    if next_round_name in {"round2", "round3"} and any(
        focus in {"architecture", "performance", "tradeoff_reasoning", "problem_solving", "technical_influence"}
        for focus in risk_focuses
    ):
        state["depth_delta"] += 1
    if next_round_name in {"round3", "hr"} and any(
        focus in {"leadership", "cross_team_execution", "conflict_handling", "technical_influence"}
        for focus in risk_focuses
    ):
        state["leadership_delta"] += 1
    if next_round_name in {"round3", "hr"} and any(
        focus in {"business_understanding", "motivation", "stability"}
        for focus in risk_focuses
    ):
        state["business_delta"] += 1
    return state


def apply_round_transition_persona(persona: PersonaConfig, transition_state: dict[str, Any] | None) -> PersonaConfig:
    if not transition_state:
        return persona
    return PersonaConfig(
        round=persona.round,
        persona=persona.persona,
        pressure_level=clamp_persona_level(persona.pressure_level + int(transition_state.get("pressure_delta", 0))),
        guidance_level=clamp_persona_level(persona.guidance_level + int(transition_state.get("guidance_delta", 0))),
        skepticism_level=clamp_persona_level(persona.skepticism_level + int(transition_state.get("skepticism_delta", 0))),
        depth_threshold=clamp_persona_level(persona.depth_threshold + int(transition_state.get("depth_delta", 0))),
        business_focus=clamp_persona_level(persona.business_focus + int(transition_state.get("business_delta", 0))),
        leadership_focus=clamp_persona_level(persona.leadership_focus + int(transition_state.get("leadership_delta", 0))),
        interviewer_brief=persona.interviewer_brief,
    )


def build_round_transition_notice(transition_state: dict[str, Any], language: str) -> str:
    from_label = str(transition_state.get("from_label", "the previous round"))
    focus_text = ", ".join(str(item) for item in transition_state.get("focuses", []) if item) or "the remaining risk areas"
    mode = str(transition_state.get("mode", "steady_transition"))
    if mode == "carry_risk_forward":
        return language_text(
            language,
            f"上一轮 {from_label} 还留下了 {focus_text} 这些风险点。本轮我会继续带着这些疑点往下追，不会按默认宽松节奏放过去。",
            f"The previous round, {from_label}, still left risk around {focus_text}. I will carry that pressure forward instead of treating this round as a clean reset.",
            f"The previous round, {from_label}, still left risk around {focus_text}. I will carry that pressure forward instead of treating this round as a clean reset. 如有必要我会补充中文，但核心追问仍会按英文面试推进。",
        )
    if mode == "evidence_recovery":
        return language_text(
            language,
            f"上一轮 {from_label} 的证据还不够完整，尤其是 {focus_text}。本轮我会优先确认这些缺口是否能被补齐。",
            f"The previous round, {from_label}, still lacked enough evidence, especially around {focus_text}. I will use this round to recover those missing signals early.",
            f"The previous round, {from_label}, still lacked enough evidence, especially around {focus_text}. I will use this round to recover those missing signals early. 必要时可补充中文说明。",
        )
    if mode == "clean_advance":
        return language_text(
            language,
            f"上一轮 {from_label} 的核心证据已经比较完整。本轮我会自然提高层次，继续验证更高阶的判断力。",
            f"The previous round, {from_label}, collected enough evidence cleanly. I will raise the bar and move to the next layer of judgment.",
            f"The previous round, {from_label}, collected enough evidence cleanly. I will raise the bar and move to the next layer of judgment. 如有必要可补充中文背景。",
        )
    return language_text(
        language,
        f"上一轮 {from_label} 的结论会继续影响本轮的提问节奏。",
        f"The outcome of {from_label} will continue to shape the pace and pressure of this round.",
        f"The outcome of {from_label} will continue to shape the pace and pressure of this round. 必要时可补充中文说明。",
    )


def choose_deliberation_probe_focus(
    round_deliberation: dict[str, Any],
    planned_focuses: list[str],
    covered_focuses: set[str],
) -> str:
    candidates: list[str] = []
    for key in ("failed_focuses", "missing_focuses", "critical_focuses"):
        for item in round_deliberation.get(key, []) or []:
            focus = str(item).strip().lower().replace("-", "_").replace(" ", "_")
            if focus and focus not in candidates and focus not in covered_focuses:
                candidates.append(focus)
    for item in planned_focuses:
        focus = str(item).strip().lower().replace("-", "_").replace(" ", "_")
        if focus and focus not in candidates and focus not in covered_focuses:
                candidates.append(focus)
    return candidates[0] if candidates else ""


def rank_handoff_question(
    question: Question,
    transition_state: dict[str, Any] | None,
    planned_focuses: list[str],
    covered_focuses: set[str],
) -> tuple[int, int, int, int, str]:
    q_focuses = set(question_focuses(question))
    transition_focuses = {str(item).strip().lower().replace("-", "_").replace(" ", "_") for item in (transition_state or {}).get("focuses", []) if item}
    planned_hits = len(set(planned_focuses) & q_focuses)
    transition_hits = len(transition_focuses & q_focuses)
    covered_penalty = 1 if q_focuses and q_focuses.issubset(covered_focuses) else 0
    difficulty = question_difficulty_rank(question)
    return (
        transition_hits,
        planned_hits,
        -covered_penalty,
        -difficulty,
        question.title,
    )


def interactive_run(args: argparse.Namespace) -> tuple[str, list[QuestionResult], list[TurnEvent], str, list[str], dict[str, Any], dict[str, Any]]:
    jd_text = read_text(args.jd)
    resume_text = read_text(args.resume)
    scripted = ScriptedAnswerProvider(load_answers(args.scripted_answers)) if args.scripted_answers else None
    show_live_feedback = not args.no_live_feedback
    resolved_default_persona = resolve_persona_name(args.default_persona) if args.default_persona else ""
    round_persona_overrides = parse_round_persona_overrides(args.round_persona_overrides)
    round_language_overrides = parse_round_language_overrides(args.round_language_overrides)
    question_target_overrides = parse_question_target_overrides(args.question_target_overrides)
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
    extra_input_config = {
        "default_persona": resolved_default_persona,
        "round_persona_overrides": round_persona_overrides,
        "round_language_overrides": round_language_overrides,
        "question_target_overrides": question_target_overrides,
        "live_feedback": show_live_feedback,
        "adaptive_runtime_routing": bool(args.adaptive_runtime_routing),
        **ai_services.metadata(),
    }

    input_paths = {
        "jd": str(Path(args.jd)),
        "resume": str(Path(args.resume)),
        "question_bank": str(Path(args.question_bank)),
        "scripted_answers": str(Path(args.scripted_answers)) if args.scripted_answers else "",
    }
    all_questions = load_question_bank(args.question_bank)
    question_bank_validation = validate_question_bank(args.question_bank, all_questions)
    write_question_bank_validation_artifacts(output_dir, question_bank_validation)
    print(f"question_bank_status={question_bank_validation['status']}")
    print(f"question_bank_errors={question_bank_validation['error_count']}")
    if question_bank_validation["error_count"]:
        raise SystemExit("Question bank validation failed; fix the Markdown bank before running the interview.")

    resume_state = load_checkpoint(args.resume_state) if args.resume_state else {}
    resume_context: dict[str, Any] = {"resumed": False}
    controlled_pause = False
    pause_reason = ""
    session_status = "completed"
    start_round_index = 0
    start_question_index = 0

    if resume_state:
        saved_input_config = dict(resume_state.get("input_config", {}))
        if not extra_input_config.get("default_persona") and saved_input_config.get("default_persona"):
            extra_input_config["default_persona"] = saved_input_config.get("default_persona")
        if not extra_input_config.get("round_persona_overrides") and saved_input_config.get("round_persona_overrides"):
            extra_input_config["round_persona_overrides"] = saved_input_config.get("round_persona_overrides")
        if not extra_input_config.get("round_language_overrides") and saved_input_config.get("round_language_overrides"):
            extra_input_config["round_language_overrides"] = saved_input_config.get("round_language_overrides")
        if not extra_input_config.get("question_target_overrides") and saved_input_config.get("question_target_overrides"):
            extra_input_config["question_target_overrides"] = saved_input_config.get("question_target_overrides")
        if not args.no_live_feedback and "live_feedback" in saved_input_config:
            extra_input_config["live_feedback"] = saved_input_config.get("live_feedback")
        if not args.adaptive_runtime_routing and saved_input_config.get("adaptive_runtime_routing"):
            extra_input_config["adaptive_runtime_routing"] = True
        if str(output_dir) != str(Path(resume_state.get("output_dir", output_dir))):
            raise SystemExit("Resume state output_dir does not match the requested output-dir.")
        if resume_state.get("checkpoint_status") == "completed":
            raise SystemExit("Resume state is already completed and cannot be resumed.")
        if args.session_id and args.session_id != str(resume_state.get("session_id", "")):
            raise SystemExit("Session ID mismatch between --session-id and --resume-state.")
        for key in ("jd", "resume", "question_bank"):
            stored = str(resume_state.get("input_paths", {}).get(key, ""))
            if stored and input_paths.get(key) != stored:
                raise SystemExit(f"Resume state input mismatch for {key}.")

        session_id = str(resume_state.get("session_id") or build_session_id(args.session_id, "interactive-candidate", "interactive"))
        selected_questions = [question_from_payload(item) for item in resume_state.get("selected_questions", [])]
        if not selected_questions:
            raise SystemExit("Resume state does not contain selected questions.")
        interview_plan = resume_state.get("interview_plan", {"rounds": []})
        persona_configs = [persona_from_payload(item) for item in resume_state.get("persona_configs", [])]
        if not persona_configs:
            persona_configs = build_persona_configs(
                args.language,
                [question.round for question in selected_questions],
                round_language_overrides=dict(extra_input_config.get("round_language_overrides", round_language_overrides) or {}),
            )
        results = [question_result_from_payload(item) for item in resume_state.get("results", [])]
        turn_events = [turn_event_from_payload(item) for item in resume_state.get("turn_events", [])]
        session_state_history = list(resume_state.get("session_state_history", ["intake", "planning"]))
        hard_fail_flags = list(resume_state.get("hard_fail_flags", []))
        terminated_early = bool(resume_state.get("terminated_early", False))
        turn_index = int(resume_state.get("turn_index_next", max((event.turn_index for event in turn_events), default=0) + 1))
        start_round_index = int(resume_state.get("next_round_index", 0))
        start_question_index = int(resume_state.get("next_question_index", 0))
        resume_context = {
            "resumed": True,
            "checkpoint_path": str(Path(args.resume_state).resolve()),
            "previous_session_status": str(resume_state.get("session_status", "session_paused")),
            "previous_checkpoint_status": str(resume_state.get("checkpoint_status", "paused")),
            "completed_question_count_before_resume": len(results),
            "turn_count_before_resume": len(turn_events),
            "resume_round": str(resume_state.get("checkpoint_resume_hint", {}).get("next_round", "")),
            "resume_question_id": str(resume_state.get("checkpoint_resume_hint", {}).get("next_question_id", "")),
        }
    else:
        candidate_name = scripted.candidate_name() if scripted else "interactive-candidate"
        session_id = build_session_id(args.session_id, candidate_name, "interactive")
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
        intro_language = planned_language_for_round(interview_plan, "intro", args.language)
        selected_questions = [build_intro_question(args.level, intro_language)] + selected_questions
        interview_plan = finalize_interview_plan(interview_plan, [question for question in selected_questions if question.round != "intro"])
        persona_configs = build_persona_configs(
            args.language,
            [question.round for question in selected_questions],
            default_persona=resolved_default_persona,
            round_persona_overrides=round_persona_overrides,
            round_language_overrides=round_language_overrides,
        )
        results = []
        turn_events = []
        session_state_history = ["intake", "planning"]
        hard_fail_flags = []
        terminated_early = False
        turn_index = 1

    show_live_feedback = bool(extra_input_config.get("live_feedback", show_live_feedback))
    console = InteractiveConsole(scripted is None, session_id, output_dir, interview_plan)
    adaptive_runtime_routing_enabled = bool(extra_input_config.get("adaptive_runtime_routing", False))
    console.print_banner()
    if resume_context.get("resumed"):
        print(f"Resuming from {resume_context['checkpoint_path']}")
        print(f"Resume point: round={resume_context['resume_round']} question_id={resume_context['resume_question_id']}")

    persona_by_round = {item.round: item for item in persona_configs}
    round_order: list[str] = []
    round_questions: dict[str, list[Question]] = {}
    for question in selected_questions:
        if question.round not in round_questions:
            round_questions[question.round] = []
            round_order.append(question.round)
        round_questions[question.round].append(question)

    def sync_selected_question_order() -> None:
        selected_questions[:] = [question for round_name in round_order for question in round_questions.get(round_name, [])]

    if start_round_index >= len(round_order):
        start_round_index = len(round_order) - 1 if round_order else 0
    if start_round_index < 0:
        start_round_index = 0

    resume_next_round_index = start_round_index
    resume_next_question_index = start_question_index
    user_aborted = False

    def refresh_progress(current_round: str, current_question_id: str, current_decision: str, status: str) -> None:
        write_session_progress(
            output_dir=output_dir,
            session_id=session_id,
            session_status=status,
            current_round=current_round,
            current_question_id=current_question_id,
            results=results,
            turn_events=turn_events,
            hard_fail_flags=hard_fail_flags,
            interview_plan=interview_plan,
            level=args.level,
            decision=current_decision,
            resume_context=resume_context,
        )

    def manual_checkpoint_message(round_idx_for_checkpoint: int, question_idx_for_checkpoint: int) -> str:
        write_session_checkpoint(
            output_dir=output_dir,
            session_id=session_id,
            session_status="in_progress",
            checkpoint_status="in_progress",
            checkpoint_reason="manual_checkpoint",
            input_paths=input_paths,
            level=args.level,
            language=args.language,
            mode=args.mode,
            enable_tts=args.enable_tts,
            voice=args.voice,
            interview_plan=interview_plan,
            selected_questions=selected_questions,
            persona_configs=persona_configs,
            results=results,
            turn_events=turn_events,
            session_state_history=session_state_history,
            hard_fail_flags=hard_fail_flags,
            terminated_early=False,
            turn_index_next=turn_index,
            next_round_index=round_idx_for_checkpoint,
            next_question_index=question_idx_for_checkpoint,
            resume_context=resume_context,
            extra_input_config=extra_input_config,
        )
        refresh_progress(
            current_round=round_order[round_idx_for_checkpoint] if round_idx_for_checkpoint < len(round_order) else "",
            current_question_id=round_questions[round_order[round_idx_for_checkpoint]][question_idx_for_checkpoint].id
            if round_idx_for_checkpoint < len(round_order)
            and question_idx_for_checkpoint < len(round_questions[round_order[round_idx_for_checkpoint]])
            else "",
            current_decision="in_progress",
            status="in_progress",
        )
        return f"Checkpoint saved: {output_dir / 'session-checkpoint.json'}"

    round_transition_state_by_round: dict[str, dict[str, Any]] = {}
    round_probe_counts: dict[str, int] = {}
    panel_memos: list[dict[str, Any]] = []

    def run_question_flow(
        round_name: str,
        round_idx: int,
        question_offset: int,
        question: Question,
        persona: PersonaConfig,
        round_language: str,
        questions_in_round: list[Question],
        planned_focuses: list[str],
        covered_focuses: set[str],
        *,
        allow_adaptive: bool = True,
        allow_switch_topic: bool = True,
    ) -> dict[str, Any]:
        nonlocal turn_index, controlled_pause, pause_reason, resume_next_round_index, resume_next_question_index

        round_failed_local = False
        pause_after_round_local = False
        round_pause_reason_local = ""
        resume_next_round_index = round_idx
        resume_next_question_index = question_offset

        prompt = compose_main_prompt(question, persona, round_language)
        tts_file = maybe_tts(output_dir, turn_index, prompt, args.enable_tts, args.voice)
        if scripted:
            answer = scripted.answer(question.id)
        else:
            answer = console.prompt(
                prompt,
                build_console_context(
                    round_name,
                    round_idx + 1,
                    len(round_order),
                    question_offset + 1,
                    len(questions_in_round),
                    results,
                    hard_fail_flags,
                    feedback_printer=lambda: format_latest_feedback(results),
                    scorecard_printer=lambda: format_scorecards(results, args.level, interview_plan),
                    checkpoint_saver=lambda ridx=round_idx, qidx=question_offset: manual_checkpoint_message(ridx, qidx),
                ),
            )
        turn_events.append(
            TurnEvent(
                turn_index=turn_index,
                round=question.round,
                stage="questioning",
                prompt=prompt,
                response=answer,
                decision_result="pending",
                tts_file=tts_file,
                persona=persona.persona,
                question_id=question.id,
                question_title=question.title,
                notes=["main_question"],
            )
        )
        main_turn_index = turn_index

        follow_up_answers: list[str] = []
        follow_up_chain: list[dict[str, str]] = []
        score, confidence, strengths, risks, missing, question_alignment = ai_services.evaluate_answer(answer, follow_up_answers, question, score_answer)
        candidates = ai_services.follow_up_candidates(
            question=question,
            persona=persona,
            language=round_language,
            missing_evidence=missing,
            risk_evidence=risks,
            previous_results=results,
            current_text=" ".join([answer, *follow_up_answers]),
            fallback=follow_up_candidates,
        )
        max_follow_ups = max_follow_up_count(question, persona)
        follow_up_count = 0

        while follow_up_count < max_follow_ups and candidates:
            decision_preview = ai_services.decide_result(score, confidence, missing, risks, question.round, question_alignment, decide_result)
            if follow_up_answers and decision_preview in {"switch_topic", "complete_round_pass", "advance_same_round"} and (score >= 3 or not missing):
                break
            candidate = candidates.pop(0)
            turn_index += 1
            follow_prompt = candidate["prompt"]
            tts_file = maybe_tts(output_dir, turn_index, follow_prompt, args.enable_tts, args.voice)
            if scripted:
                reply = scripted.follow_up_answer(question.id)
            else:
                reply = console.prompt(
                    follow_prompt,
                    build_console_context(
                        round_name,
                        round_idx + 1,
                        len(round_order),
                        question_offset + 1,
                        len(questions_in_round),
                        results,
                        hard_fail_flags,
                        last_decision=decision_preview,
                        feedback_printer=lambda: format_latest_feedback(results),
                        scorecard_printer=lambda: format_scorecards(results, args.level, interview_plan),
                        checkpoint_saver=lambda ridx=round_idx, qidx=question_offset: manual_checkpoint_message(ridx, qidx),
                    ),
                )
            follow_up_chain.append({"question": follow_prompt, "answer": reply})
            follow_up_answers.append(reply)
            follow_up_count += 1
            turn_events.append(
                TurnEvent(
                    turn_index=turn_index,
                    round=question.round,
                    stage=candidate["stage"],
                    prompt=follow_prompt,
                    response=reply,
                    decision_result="pending",
                    tts_file=tts_file,
                    persona=persona.persona,
                    question_id=question.id,
                    question_title=question.title,
                    parent_question_id=question.id,
                    parent_question_title=question.title,
                    parent_turn_index=main_turn_index,
                    follow_up_index=follow_up_count,
                    notes=candidate["notes"],
                )
            )
            score, confidence, strengths, risks, missing, question_alignment = ai_services.evaluate_answer(answer, follow_up_answers, question, score_answer)
            if score >= 4 and confidence >= 0.78 and not missing:
                break

        result_decision = ai_services.decide_result(score, confidence, missing, risks, question.round, question_alignment, decide_result)
        result_reason = decision_reason(result_decision, score, confidence, missing, risks)
        result = QuestionResult(
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
            decision_result=result_decision,
            turn_index=turn_index,
            direction=question.direction,
            competencies=question.competencies,
            persona=persona.persona,
            persona_dimensions={
                "pressure_level": persona.pressure_level,
                "guidance_level": persona.guidance_level,
                "skepticism_level": persona.skepticism_level,
                "depth_threshold": persona.depth_threshold,
                "business_focus": persona.business_focus,
                "leadership_focus": persona.leadership_focus,
            },
            decision_reason=result_reason,
            round_focus=list(question.competencies or ([question.direction] if question.direction else [])),
            question_source=question.source,
            matched_good_signals=question_alignment["matched_good_signals"],
            matched_red_flags=question_alignment["matched_red_flags"],
            expected_signal_hit=bool(question_alignment["expected_signal_hit"]),
            question_bank_alignment=question_alignment["question_bank_alignment"],
        )
        results.append(result)
        covered_focuses.update(question_focuses(question))
        if show_live_feedback:
            print(format_turn_feedback(result))
        refresh_progress(
            current_round=round_name,
            current_question_id=question.id,
            current_decision=result_decision,
            status="in_progress",
        )
        if show_live_feedback:
            turn_index += 1
            turn_events.append(
                TurnEvent(
                    turn_index=turn_index,
                    round=question.round,
                    stage="feedback",
                    prompt=f"Live feedback for {question.id}",
                    response=format_turn_feedback(result),
                    decision_result=result_decision,
                    score=score,
                    confidence=confidence,
                    persona=persona.persona,
                    notes=["live_feedback"],
                )
            )
            turn_index += 1

        for event in reversed(turn_events):
            if event.round == question.round and event.decision_result == "pending":
                event.decision_result = result_decision
                event.score = score
                event.confidence = confidence
            elif event.round != question.round:
                break

        remaining_questions = questions_in_round[question_offset + 1 :]
        if allow_adaptive and adaptive_runtime_routing_enabled and remaining_questions:
            adaptive_choice = choose_adaptive_next_question(result, remaining_questions, planned_focuses, covered_focuses)
            if adaptive_choice and int(adaptive_choice.get("selected_index", 0)) > 0:
                selected_index = int(adaptive_choice["selected_index"])
                selected_question = remaining_questions.pop(selected_index)
                remaining_questions.insert(0, selected_question)
                questions_in_round[question_offset + 1 :] = remaining_questions
                sync_selected_question_order()
                turn_index += 1
                turn_events.append(
                    TurnEvent(
                        turn_index=turn_index,
                        round=round_name,
                        stage="adaptive_route",
                        prompt=f"Adaptive runtime routing for {round_name}",
                        response=f"{adaptive_choice['reason']} Next question routed to {selected_question.id}.",
                        decision_result=result_decision,
                        score=result.score,
                        confidence=result.confidence,
                        persona=persona.persona,
                        notes=["adaptive_route", str(adaptive_choice["action"]), selected_question.id],
                    )
                )

        if result_decision == "terminate_round_fail":
            round_failed_local = True

        remaining_questions = questions_in_round[question_offset + 1 :]
        if allow_switch_topic and should_switch_topic(result, remaining_questions, planned_focuses, covered_focuses):
            turn_index += 1
            next_focuses = ", ".join(question_focuses(remaining_questions[0])) if remaining_questions else "next topic"
            turn_events.append(
                TurnEvent(
                    turn_index=turn_index,
                    round=round_name,
                    stage="switch_topic",
                    prompt=f"Switch topic within {round_name}",
                    response=f"Current topic evidence is sufficient. Switching to {next_focuses}.",
                    decision_result="switch_topic",
                    score=result.score,
                    confidence=result.confidence,
                    persona=persona.persona,
                    notes=["switch_topic", *question_focuses(remaining_questions[0])],
                )
            )
        turn_index += 1

        if args.stop_after_questions and len(results) >= args.stop_after_questions:
            if remaining_questions or round_idx < len(round_order) - 1:
                controlled_pause = True
                pause_reason = f"Paused after {len(results)} completed questions at the configured checkpoint."
                if remaining_questions:
                    resume_next_round_index = round_idx
                    resume_next_question_index = question_offset + 1
                else:
                    resume_next_round_index = round_idx + 1
                    resume_next_question_index = 0
                session_state_history.append("session_paused")
                write_session_checkpoint(
                    output_dir=output_dir,
                    session_id=session_id,
                    session_status="session_paused",
                    checkpoint_status="paused",
                    checkpoint_reason="stop_after_questions",
                    input_paths=input_paths,
                    level=args.level,
                    language=args.language,
                    mode=args.mode,
                    enable_tts=args.enable_tts,
                    voice=args.voice,
                    interview_plan=interview_plan,
                    selected_questions=selected_questions,
                    persona_configs=persona_configs,
                    results=results,
                    turn_events=turn_events,
                    session_state_history=session_state_history,
                    hard_fail_flags=hard_fail_flags,
                    terminated_early=False,
                    turn_index_next=turn_index,
                    next_round_index=resume_next_round_index,
                    next_question_index=resume_next_question_index,
                    resume_context=resume_context,
                    extra_input_config=extra_input_config,
                )
                refresh_progress(
                    current_round=round_name,
                    current_question_id=question.id,
                    current_decision="paused",
                    status="session_paused",
                )
                return {
                    "round_failed": round_failed_local,
                    "pause_after_round": False,
                    "round_pause_reason": pause_reason,
                    "covered_focuses": covered_focuses,
                    "result": result,
                    "controlled_pause": True,
                }
            pause_after_round_local = True
            round_pause_reason_local = f"Paused after {len(results)} completed questions at the configured checkpoint."

        return {
            "round_failed": round_failed_local,
            "pause_after_round": pause_after_round_local,
            "round_pause_reason": round_pause_reason_local,
            "covered_focuses": covered_focuses,
            "result": result,
            "controlled_pause": False,
        }

    refresh_progress(
        current_round=round_order[start_round_index] if round_order else "",
        current_question_id=(
            round_questions[round_order[start_round_index]][start_question_index].id
            if round_order
            and start_round_index < len(round_order)
            and start_question_index < len(round_questions[round_order[start_round_index]])
            else ""
        ),
        current_decision="in_progress",
        status="in_progress",
    )

    try:
        for round_idx in range(start_round_index, len(round_order)):
            round_name = round_order[round_idx]
            base_persona = persona_by_round[round_name]
            transition_state = round_transition_state_by_round.get(round_name)
            persona = apply_round_transition_persona(base_persona, transition_state)
            round_language = planned_language_for_round(interview_plan, round_name, args.language)
            questions_in_round = round_questions[round_name]
            local_start_question_index = start_question_index if round_idx == start_round_index else 0
            existing_round_results = [result for result in results if result.round == round_name]
            round_failed = False
            pause_after_round = False
            round_pause_reason = ""
            if round_idx == start_round_index and local_start_question_index > 0 and existing_round_results:
                session_state_history.append("round_active")
            else:
                session_state_history.append("round_active")

            if transition_state and not (resume_context.get("resumed") and round_idx == start_round_index and local_start_question_index > 0):
                transition_notice = build_round_transition_notice(transition_state, round_language)
                turn_events.append(
                    TurnEvent(
                        turn_index=turn_index,
                        round=round_name,
                        stage="round_transition",
                        prompt=f"Transition into {round_name}",
                        response=transition_notice,
                        decision_result=str(transition_state.get("next_action", "")),
                        score=float(transition_state.get("score", 0.0)),
                        confidence=float(transition_state.get("confidence", 0.0)),
                        persona=persona.persona,
                        notes=["round_transition", str(transition_state.get("mode", "")), *list(transition_state.get("focuses", []))[:2]],
                    )
                )
                turn_index += 1

            if not (resume_context.get("resumed") and round_idx == start_round_index and local_start_question_index > 0):
                intro_prompt = compose_round_intro(round_name, persona, round_language)
                if transition_state:
                    intro_prompt = f"{intro_prompt}\n\n{build_round_transition_notice(transition_state, round_language)}"
                intro_tts = maybe_tts(output_dir, turn_index, intro_prompt, args.enable_tts, args.voice)
                turn_events.append(
                    TurnEvent(
                        turn_index=turn_index,
                        round=round_name,
                        stage="intro",
                        prompt=intro_prompt,
                        response="",
                        decision_result="pending",
                        tts_file=intro_tts,
                        persona=persona.persona,
                        notes=["round_intro", *( [transition_state["mode"]] if transition_state else [] )],
                    )
                )
                turn_index += 1

            planned_focuses = [
                str(item).strip().lower().replace("-", "_").replace(" ", "_")
                for item in next((entry.get("priority_focuses", []) for entry in interview_plan.get("rounds", []) if entry.get("round") == round_name), [])
            ]
            covered_focuses: set[str] = {focus for result in existing_round_results for focus in question_focuses(result)}

            if transition_state and local_start_question_index == 0 and questions_in_round:
                before_order = [question.id for question in questions_in_round]
                ordered_questions = sorted(questions_in_round, key=lambda item: rank_handoff_question(item, transition_state, planned_focuses, covered_focuses), reverse=True)
                route_changed = bool(ordered_questions and ordered_questions[0].id != questions_in_round[0].id)
                if route_changed:
                    round_questions[round_name] = ordered_questions
                    questions_in_round = round_questions[round_name]
                    sync_selected_question_order()
                after_order = [question.id for question in questions_in_round]
                handoff_response = (
                    f"Reordered first questions from {before_order[0]} to {after_order[0]} based on panel carry-over focus."
                    if route_changed
                    else f"Reviewed carry-over focus and kept {after_order[0]} as the first question for {round_name}."
                )
                panel_memos.append(
                    {
                        "round": round_name,
                        "next_round": round_name,
                        "source_round": str(transition_state.get("from_round", "")),
                        "mode": str(transition_state.get("mode", "")),
                        "focuses": list(transition_state.get("focuses", [])),
                        "before_order": before_order,
                        "after_order": after_order,
                        "decision": str(transition_state.get("next_action", "")),
                        "reason": build_round_transition_notice(transition_state, round_language),
                        "route_applied": route_changed,
                    }
                )
                turn_events.append(
                    TurnEvent(
                        turn_index=turn_index,
                        round=round_name,
                        stage="handoff_route",
                        prompt=f"Handoff routing for {round_name}",
                        response=handoff_response,
                        decision_result=str(transition_state.get("next_action", "")),
                        score=float(transition_state.get("score", 0.0)),
                        confidence=float(transition_state.get("confidence", 0.0)),
                        persona=persona.persona,
                        notes=["handoff_route", "route_changed" if route_changed else "route_unchanged", str(transition_state.get("mode", "")), *list(transition_state.get("focuses", []))[:2]],
                    )
                )
                turn_index += 1

            for question_offset in range(local_start_question_index, len(questions_in_round)):
                question = questions_in_round[question_offset]
                flow = run_question_flow(
                    round_name,
                    round_idx,
                    question_offset,
                    question,
                    persona,
                    round_language,
                    questions_in_round,
                    planned_focuses,
                    covered_focuses,
                )
                if flow["controlled_pause"]:
                    break
                if flow["round_failed"]:
                    round_failed = True
                    break
                if flow["pause_after_round"]:
                    pause_after_round = True
                    round_pause_reason = flow["round_pause_reason"]
                    break

            if controlled_pause and not pause_after_round:
                break

            if len(results) == len(existing_round_results):
                continue

            round_summary = build_round_summaries(results, args.level, interview_plan)[-1]
            round_deliberation = build_round_deliberations(results, args.level, interview_plan)[-1]
            turn_index += 1
            turn_events.append(
                TurnEvent(
                    turn_index=turn_index,
                    round=round_name,
                    stage="summary",
                    prompt=f"{round_summary.label} summary",
                    response=round_summary.decision_reason,
                    decision_result=results[-1].decision_result,
                    score=round_summary.score,
                    confidence=round_summary.confidence,
                    persona=persona.persona,
                    notes=["round_summary"],
                )
            )

            turn_index += 1
            turn_events.append(
                TurnEvent(
                    turn_index=turn_index,
                    round=round_name,
                    stage="deliberation",
                    prompt=f"{round_summary.label} panel deliberation",
                    response=round_deliberation["panel_reason"],
                    decision_result=round_summary.decision,
                    score=round_summary.score,
                    confidence=round_summary.confidence,
                    persona=persona.persona,
                    notes=["round_review", round_deliberation["review_mode"], round_deliberation["next_action"], *round_deliberation["failed_focuses"][:2]],
                )
            )

            if (
                args.deliberation_bridge_probes
                and round_name in {"round2", "round3", "hr"}
                and not round_failed
                and not controlled_pause
                and not pause_after_round
                and round_probe_counts.get(round_name, 0) < 1
            ):
                probe_focus = choose_deliberation_probe_focus(round_deliberation, planned_focuses, covered_focuses)
                if probe_focus:
                    round_probe_counts[round_name] = round_probe_counts.get(round_name, 0) + 1
                    turn_index += 1
                    turn_events.append(
                        TurnEvent(
                            turn_index=turn_index,
                            round=round_name,
                            stage="hold",
                            prompt=f"{round_summary.label} hold for targeted probe",
                            response=f"Hold before advancing. Need one more probe on {probe_focus}.",
                            decision_result=round_summary.decision,
                            score=round_summary.score,
                            confidence=round_summary.confidence,
                            persona=persona.persona,
                            notes=["round_hold", round_deliberation["next_action"], probe_focus],
                        )
                    )
                    probe_question = build_dynamic_question(
                        round_name,
                        probe_focus,
                        args.level,
                        round_language,
                        jd_text,
                        resume_text,
                        len(questions_in_round) + 1,
                    )
                    questions_in_round.append(probe_question)
                    sync_selected_question_order()
                    probe_flow = run_question_flow(
                        round_name,
                        round_idx,
                        len(questions_in_round) - 1,
                        probe_question,
                        persona,
                        round_language,
                        questions_in_round,
                        planned_focuses,
                        covered_focuses,
                        allow_adaptive=False,
                        allow_switch_topic=False,
                    )
                    if probe_flow["controlled_pause"]:
                        break
                    if probe_flow["round_failed"]:
                        round_failed = True
                    if probe_flow["pause_after_round"]:
                        pause_after_round = True
                        round_pause_reason = probe_flow["round_pause_reason"]
                    round_summary = build_round_summaries(results, args.level, interview_plan)[-1]
                    round_deliberation = build_round_deliberations(results, args.level, interview_plan)[-1]
                    turn_index += 1
                    turn_events.append(
                        TurnEvent(
                            turn_index=turn_index,
                            round=round_name,
                            stage="summary",
                            prompt=f"{round_summary.label} post-probe summary",
                            response=round_summary.decision_reason,
                            decision_result=results[-1].decision_result,
                            score=round_summary.score,
                            confidence=round_summary.confidence,
                            persona=persona.persona,
                            notes=["round_summary", "post_probe"],
                        )
                    )
                    turn_index += 1
                    turn_events.append(
                        TurnEvent(
                            turn_index=turn_index,
                            round=round_name,
                            stage="deliberation",
                            prompt=f"{round_summary.label} post-probe panel deliberation",
                            response=round_deliberation["panel_reason"],
                            decision_result=round_summary.decision,
                            score=round_summary.score,
                            confidence=round_summary.confidence,
                            persona=persona.persona,
                            notes=["round_review", "post_probe", round_deliberation["review_mode"], round_deliberation["next_action"], *round_deliberation["failed_focuses"][:2]],
                        )
                    )

            decision_stage = "reject" if round_summary.decision == "reject" else "advance"
            turn_index += 1
            turn_events.append(
                TurnEvent(
                    turn_index=turn_index,
                    round=round_name,
                    stage=decision_stage,
                    prompt=f"{round_summary.label} decision",
                    response=round_summary.decision_reason,
                    decision_result=results[-1].decision_result,
                    score=round_summary.score,
                    confidence=round_summary.confidence,
                    persona=persona.persona,
                    notes=["round_decision", round_summary.decision],
                )
            )
            session_state_history.append("round_review")

            if round_idx + 1 < len(round_order):
                next_round_name = round_order[round_idx + 1]
                round_transition_state_by_round[next_round_name] = build_round_transition_state(round_summary, round_deliberation, next_round_name)
                panel_memos.append(
                    {
                        "round": round_name,
                        "next_round": next_round_name,
                        "source_round": round_name,
                        "decision": round_deliberation["next_action"],
                        "review_mode": round_deliberation["review_mode"],
                        "focuses": round_deliberation["critical_focuses"],
                        "failed_focuses": round_deliberation["failed_focuses"],
                        "missing_focuses": round_deliberation["missing_focuses"],
                        "panel_reason": round_deliberation["panel_reason"],
                    }
                )

            if round_summary.decision == "reject" or round_failed:
                hard_fail_flags.append(f"{results[-1].id}: {round_summary.decision_reason}")
                if not args.disable_early_termination:
                    terminated_early = True
                    resume_next_round_index = round_idx + 1
                    resume_next_question_index = 0
                    session_state_history.append("session_terminated")
                    write_session_checkpoint(
                        output_dir=output_dir,
                        session_id=session_id,
                        session_status="session_terminated",
                        checkpoint_status="session_terminated",
                        checkpoint_reason="round_reject",
                        input_paths=input_paths,
                        level=args.level,
                        language=args.language,
                        mode=args.mode,
                        enable_tts=args.enable_tts,
                        voice=args.voice,
                        interview_plan=interview_plan,
                        selected_questions=selected_questions,
                        persona_configs=persona_configs,
                        results=results,
                        turn_events=turn_events,
                        session_state_history=session_state_history,
                        hard_fail_flags=hard_fail_flags,
                        terminated_early=True,
                        turn_index_next=turn_index,
                        next_round_index=resume_next_round_index,
                        next_question_index=resume_next_question_index,
                        resume_context=resume_context,
                        extra_input_config=extra_input_config,
                    )
                    refresh_progress(
                        current_round=round_name,
                        current_question_id=results[-1].id,
                        current_decision="fail",
                        status="session_terminated",
                    )
                    break

            if pause_after_round:
                controlled_pause = True
                pause_reason = round_pause_reason
                resume_next_round_index = round_idx + 1
                resume_next_question_index = 0
                session_state_history.append("session_paused")
                write_session_checkpoint(
                    output_dir=output_dir,
                    session_id=session_id,
                    session_status="session_paused",
                    checkpoint_status="paused",
                    checkpoint_reason="stop_after_questions",
                    input_paths=input_paths,
                    level=args.level,
                    language=args.language,
                    mode=args.mode,
                    enable_tts=args.enable_tts,
                    voice=args.voice,
                    interview_plan=interview_plan,
                    selected_questions=selected_questions,
                    persona_configs=persona_configs,
                    results=results,
                    turn_events=turn_events,
                    session_state_history=session_state_history,
                    hard_fail_flags=hard_fail_flags,
                    terminated_early=False,
                    turn_index_next=turn_index,
                    next_round_index=resume_next_round_index,
                    next_question_index=resume_next_question_index,
                    resume_context=resume_context,
                    extra_input_config=extra_input_config,
                )
                refresh_progress(
                    current_round=round_name,
                    current_question_id=results[-1].id,
                    current_decision="paused",
                    status="session_paused",
                )
                break

            resume_next_round_index = round_idx + 1
            resume_next_question_index = 0
            write_session_checkpoint(
                output_dir=output_dir,
                session_id=session_id,
                session_status="in_progress",
                checkpoint_status="in_progress",
                checkpoint_reason="round_completed",
                input_paths=input_paths,
                level=args.level,
                language=args.language,
                mode=args.mode,
                enable_tts=args.enable_tts,
                voice=args.voice,
                interview_plan=interview_plan,
                selected_questions=selected_questions,
                persona_configs=persona_configs,
                results=results,
                turn_events=turn_events,
                session_state_history=session_state_history,
                hard_fail_flags=hard_fail_flags,
                terminated_early=False,
                turn_index_next=turn_index,
                next_round_index=resume_next_round_index,
                next_question_index=resume_next_question_index,
                resume_context=resume_context,
                extra_input_config=extra_input_config,
            )
            refresh_progress(
                current_round=round_name,
                current_question_id=results[-1].id,
                current_decision=round_summary.decision,
                status="in_progress",
            )
    except UserAbort:
        user_aborted = True
        pause_reason = "The candidate paused the session manually from the CLI."
        session_state_history.append("session_paused")
        write_session_checkpoint(
            output_dir=output_dir,
            session_id=session_id,
            session_status="session_paused",
            checkpoint_status="paused",
            checkpoint_reason="user_requested_exit",
            input_paths=input_paths,
            level=args.level,
            language=args.language,
            mode=args.mode,
            enable_tts=args.enable_tts,
            voice=args.voice,
            interview_plan=interview_plan,
            selected_questions=selected_questions,
            persona_configs=persona_configs,
            results=results,
            turn_events=turn_events,
            session_state_history=session_state_history,
            hard_fail_flags=hard_fail_flags,
            terminated_early=False,
            turn_index_next=turn_index,
            next_round_index=resume_next_round_index,
            next_question_index=resume_next_question_index,
            resume_context=resume_context,
            extra_input_config=extra_input_config,
        )
        refresh_progress(
            current_round=round_order[resume_next_round_index] if resume_next_round_index < len(round_order) else "",
            current_question_id="",
            current_decision="paused",
            status="session_paused",
        )

    round_summaries = build_round_summaries(results, args.level, interview_plan)
    round_scorecards = build_round_scorecards(results, round_summaries, interview_plan, args.level)
    round_deliberations = build_round_deliberations(results, args.level, interview_plan)

    if controlled_pause or user_aborted:
        decision = "paused"
        session_status = "session_paused"
    else:
        decision, final_flags = final_decision(results, round_scorecards)
        for item in final_flags:
            if item not in hard_fail_flags:
                hard_fail_flags.append(item)
        if terminated_early and decision == "pass":
            decision = "fail"
        session_status = "session_terminated" if terminated_early else "completed"

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
    consistency_summary = build_consistency_summary(results, screening_summary)

    tts_files: list[str] = []
    tts_status = "disabled"
    if args.enable_tts:
        if edge_tts_available():
            tts_files = synthesize_summary_artifacts(output_dir, results, decision, args.voice)
            tts_status = "generated"
        else:
            tts_status = "edge-tts-not-installed"

    session_state_history.extend(["reporting", "completed"])
    extra_input_config.update(ai_services.metadata())
    session_data = session_payload(
        session_id=session_id,
        level=args.level,
        language=args.language,
        enable_tts=args.enable_tts,
        voice=args.voice,
        job_profile=job_profile,
        candidate_profile=candidate_profile,
        results=results,
        turn_events=turn_events,
        tts_status=tts_status,
        tts_files=tts_files,
        question_sources=sorted({result.source_path for result in results}),
        hard_fail_flags=hard_fail_flags,
        mode=args.mode,
        interactive_mode=True,
        round_summaries=round_summaries,
        round_deliberations=round_deliberations,
        persona_configs=persona_configs,
        session_state_history=session_state_history,
        session_status=session_status,
        final_decision_value=decision,
        interview_plan=interview_plan,
        terminated_early=terminated_early,
        round_scorecards=round_scorecards,
        pause_reason=pause_reason,
        resume_context=resume_context,
        extra_input_config=extra_input_config,
        screening_summary=screening_summary,
        consistency_summary=consistency_summary,
        panel_memos=panel_memos,
        question_bank_validation=question_bank_validation,
        resume_prep=resume_prep,
    )
    score_data = score_payload(results, hard_fail_flags, decision, round_summaries, round_scorecards, consistency_summary, round_deliberations)
    score_data["interactive_mode"] = True
    score_data["ai_runtime"] = ai_services.metadata()

    write_json(output_dir / "session.json", session_data)
    write_json(output_dir / "ai-runtime.json", ai_services.trace_payload())
    write_json(output_dir / "panel-notes.json", {"panel_memos": panel_memos})
    panel_notes_lines = [f"# Panel Notes - {session_id}", ""]
    if panel_memos:
        for item in panel_memos:
            source_round = str(item.get("source_round", item.get("round", "")))
            target_round = str(item.get("next_round", item.get("round", "")))
            if source_round and target_round and source_round != target_round:
                panel_notes_lines.append(f"- **{source_round} -> {target_round}** -> `{item.get('decision', '')}`")
            else:
                panel_notes_lines.append(f"- **{item.get('round', '')}** -> `{item.get('decision', '')}`")
            if item.get("focuses"):
                panel_notes_lines.append(f"  - Focuses: {', '.join(item['focuses'])}")
            if item.get("reason"):
                panel_notes_lines.append(f"  - Reason: {item['reason']}")
            if item.get("before_order") and item.get("after_order"):
                panel_notes_lines.append(f"  - Route: {' -> '.join(item['before_order'])} -> {' -> '.join(item['after_order'])}")
            if "route_applied" in item:
                panel_notes_lines.append(f"  - Route changed: {'yes' if item.get('route_applied') else 'no'}")
    else:
        panel_notes_lines.append("- none")
    (output_dir / "panel-notes.md").write_text("\n".join(panel_notes_lines).strip() + "\n", encoding="utf-8")
    write_json(output_dir / "score.json", score_data)
    write_json(output_dir / "interview-plan.json", interview_plan)
    write_json(output_dir / "screening-summary.json", screening_summary)
    write_json(output_dir / "resume-prep.json", resume_prep)
    render_screening_summary(output_dir / "screening-summary.md", session_id, screening_summary)
    render_resume_prep(output_dir / "resume-prep.md", session_id, resume_prep)
    write_json(output_dir / "turn-events.json", {"turn_events": [event.__dict__ for event in turn_events]})
    render_transcript(output_dir / "transcript.md", session_id, results, round_summaries, round_deliberations, turn_events)
    render_report(output_dir / "report.html", session_data, score_data)
    refresh_progress(
        current_round="",
        current_question_id="",
        current_decision=decision,
        status=session_status,
    )
    if decision == "fail":
        render_reject_mail(output_dir / "mail-reject.html", session_id, hard_fail_flags, round_summaries)
        render_failure_summary(output_dir / "fail-summary.md", session_data, score_data)
    elif decision == "paused":
        render_failure_summary(output_dir / "fail-summary.md", session_data, score_data)
    elif decision == "pass":
        render_pass_summary(output_dir / "pass-summary.md", session_id, session_data, score_data)

    write_session_checkpoint(
        output_dir=output_dir,
        session_id=session_id,
        session_status=session_status,
        checkpoint_status="completed" if decision != "paused" else "paused",
        checkpoint_reason=decision,
        input_paths=input_paths,
        level=args.level,
        language=args.language,
        mode=args.mode,
        enable_tts=args.enable_tts,
        voice=args.voice,
        interview_plan=interview_plan,
        selected_questions=selected_questions,
        persona_configs=persona_configs,
        results=results,
        turn_events=turn_events,
        session_state_history=session_state_history,
        hard_fail_flags=hard_fail_flags,
        terminated_early=terminated_early,
        turn_index_next=turn_index,
        next_round_index=resume_next_round_index if decision == "paused" else len(round_order),
        next_question_index=resume_next_question_index if decision == "paused" else 0,
        resume_context=resume_context,
        extra_input_config=extra_input_config,
    )

    print(f"session_id={session_id}")
    print(f"output_dir={output_dir}")
    print(f"decision={decision}")
    print(f"tts_status={tts_status}")
    print(f"turn_count={len(turn_events)}")
    print(f"checkpoint_file={output_dir / 'session-checkpoint.json'}")
    print(f"resumed={'true' if resume_context.get('resumed') else 'false'}")
    return session_id, results, turn_events, decision, hard_fail_flags, session_data, score_data


def main() -> int:
    args = parse_args()
    try:
        interactive_run(args)
    except AIClientError as exc:
        raise SystemExit(f"AI runtime failed in required mode: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
