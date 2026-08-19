from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


DEFAULT_ALLOWED_LANGUAGES = {"zh", "en", "bilingual"}
DEFAULT_ALLOWED_DIFFICULTIES = {"L1", "L2", "L3", "L4", "L5"}
DEFAULT_ALLOWED_LEVELS = {"mid", "senior", "tl"}
DEFAULT_TEMPLATE_ID = "android_senior"


def _string(value: Any, default: str = "") -> str:
    return str(value).strip() if value is not None else default


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _label_map(value: Any, fallback: str) -> dict[str, str]:
    if isinstance(value, dict):
        payload = {str(key).strip(): str(item).strip() for key, item in value.items() if str(item).strip()}
        if payload:
            return payload
    return {"en": fallback}


@dataclass
class RoundDefinition:
    round_id: str
    label: dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    order: int = 0
    goal: str = ""
    default_language: str = "auto"
    target_question_count: int = 1
    focuses: list[str] = field(default_factory=list)
    persona: str = ""

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RoundDefinition":
        round_id = _string(payload.get("round_id"))
        fallback_label = round_id.replace("_", " ").title() if round_id else ""
        return cls(
            round_id=round_id,
            label=_label_map(payload.get("label"), fallback_label),
            enabled=bool(payload.get("enabled", True)),
            order=int(payload.get("order", 0) or 0),
            goal=_string(payload.get("goal")),
            default_language=_string(payload.get("default_language"), "auto") or "auto",
            target_question_count=max(0, int(payload.get("target_question_count", 1) or 0)),
            focuses=_string_list(payload.get("focuses")),
            persona=_string(payload.get("persona")),
        )


@dataclass
class PersonaDefaults:
    default_persona: str = ""
    round_overrides: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "PersonaDefaults":
        data = payload if isinstance(payload, dict) else {}
        round_overrides = data.get("round_overrides", {})
        normalized = {
            str(key).strip(): str(value).strip()
            for key, value in dict(round_overrides).items()
            if str(key).strip() and str(value).strip()
        } if isinstance(round_overrides, dict) else {}
        return cls(
            default_persona=_string(data.get("default_persona")),
            round_overrides=normalized,
        )


@dataclass
class QuestionBankRules:
    allowed_rounds: list[str] = field(default_factory=list)
    allowed_levels: list[str] = field(default_factory=list)
    allowed_languages: list[str] = field(default_factory=lambda: sorted(DEFAULT_ALLOWED_LANGUAGES))
    allowed_difficulties: list[str] = field(default_factory=lambda: sorted(DEFAULT_ALLOWED_DIFFICULTIES))
    blocked_tags: list[str] = field(default_factory=list)
    blocked_keywords: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any] | None,
        *,
        fallback_rounds: list[str],
        fallback_levels: list[str],
    ) -> "QuestionBankRules":
        data = payload if isinstance(payload, dict) else {}
        return cls(
            allowed_rounds=_string_list(data.get("allowed_rounds")) or list(fallback_rounds),
            allowed_levels=_string_list(data.get("allowed_levels")) or list(fallback_levels),
            allowed_languages=_string_list(data.get("allowed_languages")) or sorted(DEFAULT_ALLOWED_LANGUAGES),
            allowed_difficulties=_string_list(data.get("allowed_difficulties")) or sorted(DEFAULT_ALLOWED_DIFFICULTIES),
            blocked_tags=_string_list(data.get("blocked_tags")),
            blocked_keywords=_string_list(data.get("blocked_keywords")),
        )


@dataclass
class InterviewTemplate:
    template_id: str
    display_name: str
    template_type: str
    target_role: str
    role_family: str
    version: int = 1
    enabled: bool = True
    aliases: list[str] = field(default_factory=list)
    inherits_from: str = ""
    candidate_level: str = "senior"
    supported_levels: list[str] = field(default_factory=lambda: sorted(DEFAULT_ALLOWED_LEVELS))
    default_language: str = "en"
    default_speech_language: str = "auto"
    rounds: list[RoundDefinition] = field(default_factory=list)
    persona_defaults: PersonaDefaults = field(default_factory=PersonaDefaults)
    question_bank_rules: QuestionBankRules = field(default_factory=QuestionBankRules)
    source_path: str = ""

    @classmethod
    def from_dict(cls, payload: dict[str, Any], *, source_path: str = "") -> "InterviewTemplate":
        rounds_payload = payload.get("rounds", [])
        rounds = [RoundDefinition.from_dict(item) for item in rounds_payload if isinstance(item, dict)]
        rounds = [item for item in rounds if item.round_id]
        rounds.sort(key=lambda item: (item.order, item.round_id))

        supported_levels = _string_list(payload.get("supported_levels")) or sorted(DEFAULT_ALLOWED_LEVELS)
        question_bank_rules = QuestionBankRules.from_dict(
            payload.get("question_bank_rules") if isinstance(payload.get("question_bank_rules"), dict) else None,
            fallback_rounds=[item.round_id for item in rounds],
            fallback_levels=supported_levels,
        )
        template_id = _string(payload.get("template_id"), DEFAULT_TEMPLATE_ID) or DEFAULT_TEMPLATE_ID
        return cls(
            template_id=template_id,
            display_name=_string(payload.get("display_name"), template_id) or template_id,
            template_type=_string(payload.get("template_type"), "preset") or "preset",
            target_role=_string(payload.get("target_role"), template_id) or template_id,
            role_family=_string(payload.get("role_family"), "general") or "general",
            version=int(payload.get("version", 1) or 1),
            enabled=bool(payload.get("enabled", True)),
            aliases=_string_list(payload.get("aliases")),
            inherits_from=_string(payload.get("inherits_from")),
            candidate_level=_string(payload.get("candidate_level"), "senior") or "senior",
            supported_levels=supported_levels,
            default_language=_string(payload.get("default_language"), "en") or "en",
            default_speech_language=_string(payload.get("default_speech_language"), "auto") or "auto",
            rounds=rounds,
            persona_defaults=PersonaDefaults.from_dict(
                payload.get("persona_defaults") if isinstance(payload.get("persona_defaults"), dict) else None
            ),
            question_bank_rules=question_bank_rules,
            source_path=source_path,
        )

    @property
    def round_ids(self) -> list[str]:
        return [item.round_id for item in self.rounds if item.enabled]

    def round_labels(self, preferred_language: str = "en") -> dict[str, str]:
        labels: dict[str, str] = {}
        for item in self.rounds:
            if not item.enabled:
                continue
            labels[item.round_id] = item.label.get(preferred_language) or item.label.get("en") or item.round_id
        return labels

    def round_focus_map(self) -> dict[str, list[str]]:
        return {item.round_id: list(item.focuses) for item in self.rounds if item.enabled}

    def round_persona_map(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for item in self.rounds:
            if not item.enabled:
                continue
            persona = self.persona_defaults.round_overrides.get(item.round_id) or item.persona or self.persona_defaults.default_persona
            if persona:
                result[item.round_id] = persona
        return result

    def round_question_targets(self) -> dict[str, int]:
        return {
            item.round_id: item.target_question_count
            for item in self.rounds
            if item.enabled and item.target_question_count >= 0
        }
