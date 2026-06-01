from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from ai_client import AIClientError, build_ai_client
from ai_schemas import AIConfig, AIEvaluation, AIFollowUp, AITraceEvent


class InterviewAIServices:
    def __init__(self, config: AIConfig, output_dir: Path | None = None) -> None:
        self.config = config
        self.output_dir = output_dir
        self.trace_events: list[AITraceEvent] = []
        self.client = build_ai_client(config)

    @property
    def provider_name(self) -> str:
        return getattr(self.client, "provider_name", self.config.provider)

    def metadata(self) -> dict[str, Any]:
        fallback_available = self.config.mode in {"off", "assist"}
        return {
            **self.config.metadata(),
            "ai_active_provider": self.provider_name,
            "deterministic_fallback_available": fallback_available,
            "hot_swap_modes": ["off", "assist", "required"],
            "ai_trace_event_count": len(self.trace_events),
        }

    def trace_payload(self) -> dict[str, Any]:
        return {
            "metadata": self.metadata(),
            "events": [event.to_dict() for event in self.trace_events],
        }

    def _record(self, event: AITraceEvent) -> None:
        self.trace_events.append(event)

    def _audit(self, role: str, action: str, payload: dict[str, Any], response: dict[str, Any] | None, error: str = "") -> None:
        if not self.output_dir:
            return
        audit_dir = self.output_dir / "ai-calls"
        audit_dir.mkdir(parents=True, exist_ok=True)
        index = len(list(audit_dir.glob("*.json"))) + 1
        audit_payload = {
            "created_at": datetime.now().isoformat(),
            "role": role,
            "action": action,
            "provider": self.provider_name,
            "model": self.config.model,
            "request": payload,
            "response": response or {},
            "error": error,
        }
        (audit_dir / f"{index:03d}-{role}-{action}.json").write_text(json.dumps(audit_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _call_json(self, role: str, action: str, system_prompt: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = self.client.complete_json(role=role, action=action, system_prompt=system_prompt, payload=payload)
        self._audit(role, action, payload, response)
        self._record(AITraceEvent(role=role, action=action, status="ai_used", provider=self.provider_name, model=self.config.model))
        return response

    def _handle_failure(self, role: str, action: str, payload: dict[str, Any], error: Exception) -> None:
        message = str(error)
        self._audit(role, action, payload, None, message)
        if self.config.required:
            self._record(
                AITraceEvent(
                    role=role,
                    action=action,
                    status="failed",
                    provider=self.provider_name,
                    model=self.config.model,
                    error=message,
                )
            )
            raise AIClientError(message) from error
        self._record(
            AITraceEvent(
                role=role,
                action=action,
                status="fallback_used",
                provider=self.provider_name,
                model=self.config.model,
                fallback_used=True,
                error=message,
            )
        )

    @staticmethod
    def _question_payload(question: Any | None) -> dict[str, Any]:
        if question is None:
            return {}
        fields = [
            "id",
            "title",
            "round",
            "direction",
            "level",
            "difficulty",
            "language",
            "competencies",
            "expected_signal",
            "intent",
            "question",
            "follow_ups",
            "scoring_notes",
            "red_flags",
            "good_signals",
        ]
        return {field: getattr(question, field, None) for field in fields}

    def evaluate_answer(
        self,
        answer: str,
        follow_up_answers: list[str],
        question: Any | None,
        fallback: Callable[[str, list[str], Any | None], tuple[int, float, list[str], list[str], list[str], dict[str, Any]]],
    ) -> tuple[int, float, list[str], list[str], list[str], dict[str, Any]]:
        if not self.config.enabled:
            return fallback(answer, follow_up_answers, question)

        role = "evaluator"
        action = "evaluate-answer"
        payload = {
            "question": self._question_payload(question),
            "answer": answer,
            "follow_up_answers": follow_up_answers,
            "required_json_shape": {
                "score": "integer 1-5",
                "confidence": "number 0-1",
                "strength_evidence": ["answer-specific evidence"],
                "risk_evidence": ["answer-specific risk"],
                "missing_evidence": ["missing evidence"],
                "recommended_next_action": "advance_same_round|follow_up_same_topic|switch_topic|increase_difficulty|decrease_difficulty|mark_risk|terminate_round_fail|complete_round_pass",
                "hard_fail_flags": ["optional"],
            },
        }
        system_prompt = (
            "You are the evaluator in a structured Android interview. "
            "Score only from answer evidence. Return strict JSON only. "
            "Do not reward vague claims without ownership, metrics, tradeoffs, or verification evidence."
        )
        try:
            data = self._call_json(role, action, system_prompt, payload)
            evaluation = self._parse_evaluation(data)
        except Exception as exc:  # noqa: BLE001
            self._handle_failure(role, action, payload, exc)
            return fallback(answer, follow_up_answers, question)

        alignment = {
            "matched_good_signals": [],
            "matched_red_flags": [],
            "expected_signal_hit": bool(evaluation.strength_evidence),
            "question_bank_alignment": "ai_evaluated",
            "ai_raw": evaluation.raw,
            "recommended_next_action": evaluation.recommended_next_action,
            "hard_fail_flags": evaluation.hard_fail_flags,
        }
        return (
            evaluation.score,
            evaluation.confidence,
            evaluation.strength_evidence,
            evaluation.risk_evidence,
            evaluation.missing_evidence,
            alignment,
        )

    @staticmethod
    def _parse_evaluation(data: dict[str, Any]) -> AIEvaluation:
        score = max(1, min(5, int(data.get("score", 3))))
        confidence = max(0.0, min(1.0, float(data.get("confidence", 0.5))))
        return AIEvaluation(
            score=score,
            confidence=round(confidence, 2),
            strength_evidence=[str(item) for item in data.get("strength_evidence", []) if str(item).strip()][:6],
            risk_evidence=[str(item) for item in data.get("risk_evidence", []) if str(item).strip()][:6],
            missing_evidence=[str(item) for item in data.get("missing_evidence", []) if str(item).strip()][:6],
            recommended_next_action=str(data.get("recommended_next_action", "")),
            hard_fail_flags=[str(item) for item in data.get("hard_fail_flags", []) if str(item).strip()][:4],
            raw=data,
        )

    def decide_result(
        self,
        score: int,
        confidence: float,
        missing_evidence: list[str],
        risk_evidence: list[str],
        round_name: str,
        question_alignment: dict[str, Any],
        fallback: Callable[[int, float, list[str], list[str], str], str],
    ) -> str:
        recommended = str(question_alignment.get("recommended_next_action", "")).strip()
        allowed = {
            "advance_same_round",
            "follow_up_same_topic",
            "switch_topic",
            "increase_difficulty",
            "decrease_difficulty",
            "mark_risk",
            "terminate_round_fail",
            "complete_round_pass",
        }
        if self.config.enabled and recommended in allowed:
            return recommended
        return fallback(score, confidence, missing_evidence, risk_evidence, round_name)

    def follow_up_candidates(
        self,
        *,
        question: Any,
        persona: Any,
        language: str,
        missing_evidence: list[str],
        risk_evidence: list[str],
        previous_results: list[Any] | None,
        current_text: str,
        fallback: Callable[..., list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        if not self.config.enabled:
            return fallback(question, persona, language, missing_evidence, risk_evidence, previous_results, current_text)

        role = "interviewer"
        action = "generate-follow-up"
        payload = {
            "question": self._question_payload(question),
            "persona": asdict(persona) if hasattr(persona, "__dataclass_fields__") else dict(persona),
            "language": language,
            "missing_evidence": missing_evidence,
            "risk_evidence": risk_evidence,
            "current_answer_text": current_text,
            "previous_results": [
                {
                    "id": getattr(item, "id", ""),
                    "round": getattr(item, "round", ""),
                    "title": getattr(item, "title", ""),
                    "score": getattr(item, "score", None),
                    "risk_evidence": getattr(item, "risk_evidence", []),
                    "missing_evidence": getattr(item, "missing_evidence", []),
                }
                for item in list(previous_results or [])[-5:]
            ],
            "required_json_shape": {
                "action": "clarify|deepen|challenge|switch_topic|stop",
                "probe_type": "ownership|metrics|tradeoff|failure|depth|business|leadership|consistency|none",
                "prompt": "single follow-up prompt, or empty when action=stop",
                "rationale": "short reason",
                "stop_condition": "what evidence would end this chain",
            },
        }
        system_prompt = (
            "You are the interviewer in a structured Android interview. "
            "Generate at most one grounded follow-up from the candidate's exact answer. "
            "Do not ask generic template questions if a more specific evidence probe is possible. "
            "Return strict JSON only."
        )
        try:
            data = self._call_json(role, action, system_prompt, payload)
            follow_up = self._parse_follow_up(data)
        except Exception as exc:  # noqa: BLE001
            self._handle_failure(role, action, payload, exc)
            return fallback(question, persona, language, missing_evidence, risk_evidence, previous_results, current_text)

        if follow_up.action == "stop" or not follow_up.prompt:
            return []
        stage = "challenge" if follow_up.action == "challenge" else "follow_up"
        return [
            {
                "category": f"ai_{follow_up.probe_type or 'probe'}",
                "stage": stage,
                "prompt": follow_up.prompt,
                "notes": ["ai_generated", follow_up.action, follow_up.probe_type],
            }
        ]

    @staticmethod
    def _parse_follow_up(data: dict[str, Any]) -> AIFollowUp:
        return AIFollowUp(
            action=str(data.get("action", "deepen")),
            probe_type=str(data.get("probe_type", "depth")),
            prompt=str(data.get("prompt", "")).strip(),
            rationale=str(data.get("rationale", "")),
            stop_condition=str(data.get("stop_condition", "")),
            raw=data,
        )
