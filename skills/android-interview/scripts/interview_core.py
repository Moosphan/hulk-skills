from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from jinja2 import Template

from question_bank import Question
from tts_support import synthesize_text


ROUND_LABELS = {
    "intro": "Self Introduction",
    "screening": "Screening",
    "round1": "Round 1",
    "round2": "Round 2",
    "round3": "Round 3",
    "hr": "HR Interview",
}

ROUND_FOCUS = {
    "intro": ["communication", "project_authenticity", "english_interview"],
    "screening": ["ownership", "resume_authenticity", "delivery_scope"],
    "round1": ["android_core", "problem_solving", "implementation_detail"],
    "round2": ["architecture", "performance", "tradeoff_reasoning"],
    "round3": ["business_understanding", "technical_influence", "cross_team_execution"],
    "hr": ["motivation", "conflict_handling", "leadership", "stability"],
}

ROUND_SEQUENCE = ["intro", "screening", "round1", "round2", "round3", "hr"]

TURN_STAGE_LABELS = {
    "intro": "阶段介绍",
    "question": "主问题",
    "questioning": "主问题",
    "follow_up": "追问",
    "challenge": "追问挑战",
    "consistency_challenge": "一致性挑战",
    "feedback": "即时反馈",
    "adaptive_route": "自适应路由",
    "switch_topic": "切换题型/主题",
    "round_transition": "轮次过渡",
    "handoff_route": "承接路由",
    "summary": "阶段总结",
    "deliberation": "阶段评审",
    "hold": "阶段暂缓",
    "advance": "阶段晋级",
    "reject": "阶段终止",
}

COMPETENCY_FAMILY_MAP = {
    "technical_depth": "technical_depth",
    "android_core": "technical_depth",
    "architecture": "architecture_and_system_thinking",
    "engineering_execution": "engineering_execution",
    "problem_solving": "problem_solving",
    "communication": "communication",
    "leadership": "leadership_and_management_potential",
    "business": "business_understanding",
    "business_understanding": "business_understanding",
    "project_authenticity": "communication",
    "english_interview": "english_interview",
    "resume_authenticity": "communication",
    "ownership": "engineering_execution",
    "delivery_scope": "engineering_execution",
    "motivation": "career_maturity_and_stability",
    "stability": "career_maturity_and_stability",
    "conflict_handling": "leadership_and_management_potential",
}

PERSONA_LIBRARY = {
    "严厉审查型": {
        "pressure_level": 5,
        "guidance_level": 1,
        "skepticism_level": 5,
        "depth_threshold": 4,
        "business_focus": 2,
        "leadership_focus": 2,
        "interviewer_brief": "Direct, skeptical, and low-tolerance for vague statements.",
    },
    "连环拷问型": {
        "pressure_level": 4,
        "guidance_level": 1,
        "skepticism_level": 5,
        "depth_threshold": 5,
        "business_focus": 2,
        "leadership_focus": 1,
        "interviewer_brief": "Stay on one point until the ownership, metrics, and tradeoffs are clear.",
    },
    "引导教练型": {
        "pressure_level": 2,
        "guidance_level": 5,
        "skepticism_level": 3,
        "depth_threshold": 4,
        "business_focus": 2,
        "leadership_focus": 3,
        "interviewer_brief": "Warm but structured. Offer clarification room without lowering the bar.",
    },
    "业务结果型": {
        "pressure_level": 3,
        "guidance_level": 2,
        "skepticism_level": 4,
        "depth_threshold": 3,
        "business_focus": 5,
        "leadership_focus": 2,
        "interviewer_brief": "Anchor the discussion to metrics, impact, and product outcomes.",
    },
    "技术深挖型": {
        "pressure_level": 3,
        "guidance_level": 2,
        "skepticism_level": 4,
        "depth_threshold": 5,
        "business_focus": 1,
        "leadership_focus": 1,
        "interviewer_brief": "Probe implementation detail, diagnosis path, and tradeoff depth.",
    },
    "领导力评估型": {
        "pressure_level": 3,
        "guidance_level": 2,
        "skepticism_level": 3,
        "depth_threshold": 3,
        "business_focus": 3,
        "leadership_focus": 5,
        "interviewer_brief": "Focus on influence, prioritization, conflict handling, and people impact.",
    },
}

PERSONA_ALIASES = {
    "harsh-reviewer": "严厉审查型",
    "cross-examiner": "连环拷问型",
    "guided-coach": "引导教练型",
    "business-outcome": "业务结果型",
    "technical-deep-diver": "技术深挖型",
    "leadership-evaluator": "领导力评估型",
}

ROUND_PERSONA_DEFAULTS = {
    "intro": "引导教练型",
    "screening": "引导教练型",
    "round1": "技术深挖型",
    "round2": "连环拷问型",
    "round3": "业务结果型",
    "hr": "领导力评估型",
}

MODE_ROUNDS = {
    "simulate": ["intro", "screening", "round1", "round2", "round3", "hr"],
    "screening": ["intro", "screening"],
    "round1": ["intro", "screening", "round1"],
    "round2": ["intro", "round2"],
    "round3": ["intro", "round3"],
    "hr": ["intro", "hr"],
}

ROUND_QUESTION_TARGETS = {
    "screening": 1,
    "round1": 2,
    "round2": 2,
    "round3": 2,
    "hr": 2,
}

ROUND_THRESHOLD_DEFAULTS = {
    "intro": {"min_round_score": 3.0, "min_confidence": 0.45, "critical_focuses": ["communication", "project_authenticity"], "critical_min_score": 3.0},
    "screening": {"min_round_score": 3.0, "min_confidence": 0.45, "critical_focuses": ["ownership"], "critical_min_score": 3.0},
    "round1": {"min_round_score": 3.0, "min_confidence": 0.45, "critical_focuses": ["android_core", "problem_solving"], "critical_min_score": 3.0},
    "round2": {"min_round_score": 3.4, "min_confidence": 0.5, "critical_focuses": ["architecture", "performance", "tradeoff_reasoning"], "critical_min_score": 3.0},
    "round3": {"min_round_score": 3.2, "min_confidence": 0.48, "critical_focuses": ["business_understanding", "technical_influence"], "critical_min_score": 3.0},
    "hr": {"min_round_score": 3.0, "min_confidence": 0.45, "critical_focuses": ["leadership", "motivation"], "critical_min_score": 3.0},
}

LEVEL_THRESHOLD_OVERRIDES = {
    "mid": {
        "round2": {"min_round_score": 3.0, "critical_min_score": 2.8},
        "round3": {"min_round_score": 3.0, "critical_min_score": 2.8},
        "hr": {"critical_focuses": ["motivation", "communication"]},
    },
    "senior": {},
    "tl": {
        "round2": {"min_round_score": 3.5, "critical_min_score": 3.2, "critical_focuses": ["architecture", "performance", "tradeoff_reasoning"]},
        "round3": {"min_round_score": 3.4, "critical_min_score": 3.1, "critical_focuses": ["business_understanding", "technical_influence", "cross_team_execution"]},
        "hr": {"min_round_score": 3.2, "critical_min_score": 3.0, "critical_focuses": ["leadership", "motivation", "conflict_handling"]},
    },
}


@dataclass
class PersonaConfig:
    round: str
    persona: str
    pressure_level: int
    guidance_level: int
    skepticism_level: int
    depth_threshold: int
    business_focus: int
    leadership_focus: int
    interviewer_brief: str = ""


@dataclass
class QuestionResult:
    id: str
    title: str
    round: str
    question: str
    answer: str
    follow_up_chain: list[dict[str, str]]
    score: int
    confidence: float
    strength_evidence: list[str]
    risk_evidence: list[str]
    missing_evidence: list[str]
    source_path: str
    decision_result: str = ""
    turn_index: int = 0
    direction: str = ""
    competencies: list[str] = field(default_factory=list)
    persona: str = ""
    persona_dimensions: dict[str, int] = field(default_factory=dict)
    decision_reason: str = ""
    round_focus: list[str] = field(default_factory=list)
    question_source: str = ""
    matched_good_signals: list[str] = field(default_factory=list)
    matched_red_flags: list[str] = field(default_factory=list)
    expected_signal_hit: bool = False
    question_bank_alignment: str = ""
    spoken_question: str = ""


@dataclass
class TurnEvent:
    turn_index: int
    round: str
    stage: str
    prompt: str
    response: str
    decision_result: str
    spoken_text: str = ""
    score: int | None = None
    confidence: float | None = None
    tts_file: str = ""
    persona: str = ""
    question_id: str = ""
    question_title: str = ""
    parent_question_id: str = ""
    parent_question_title: str = ""
    parent_turn_index: int | None = None
    follow_up_index: int | None = None
    notes: list[str] = field(default_factory=list)


@dataclass
class RoundSummary:
    round: str
    label: str
    persona: str
    focus: list[str]
    score: float
    confidence: float
    decision: str
    decision_reason: str
    strengths: list[str]
    risks: list[str]
    missing: list[str]
    question_ids: list[str]
    terminated: bool = False
    threshold_summary: dict[str, Any] = field(default_factory=dict)


def round_sort_index(round_name: str) -> int:
    try:
        return ROUND_SEQUENCE.index(str(round_name))
    except ValueError:
        return len(ROUND_SEQUENCE)


def stage_label(stage: str) -> str:
    return TURN_STAGE_LABELS.get(str(stage or "").strip(), str(stage or "").strip() or "未知阶段")


MAIN_QUESTION_STAGES = {"question", "questioning"}
FOLLOW_UP_STAGES = {"follow_up", "challenge", "consistency_challenge"}


def normalize_turn_event(raw_event: TurnEvent | dict[str, Any]) -> dict[str, Any]:
    if isinstance(raw_event, TurnEvent):
        payload = asdict(raw_event)
    else:
        payload = dict(raw_event or {})
    payload.setdefault("turn_index", 0)
    payload.setdefault("round", "")
    payload.setdefault("stage", "")
    payload.setdefault("prompt", "")
    payload.setdefault("spoken_text", "")
    payload.setdefault("response", "")
    payload.setdefault("decision_result", "")
    payload.setdefault("score", None)
    payload.setdefault("confidence", None)
    payload.setdefault("tts_file", "")
    payload.setdefault("persona", "")
    payload.setdefault("question_id", "")
    payload.setdefault("question_title", "")
    payload.setdefault("parent_question_id", "")
    payload.setdefault("parent_question_title", "")
    payload.setdefault("parent_turn_index", None)
    payload.setdefault("follow_up_index", None)
    payload.setdefault("notes", [])
    return payload


def serialize_question_record(raw_result: QuestionResult | dict[str, Any]) -> dict[str, Any]:
    payload = asdict(raw_result) if isinstance(raw_result, QuestionResult) else dict(raw_result or {})
    payload.setdefault("id", "")
    payload.setdefault("title", "")
    payload.setdefault("round", "")
    payload.setdefault("turn_index", 0)
    payload.setdefault("question", "")
    payload.setdefault("spoken_question", "")
    payload.setdefault("answer", "")
    payload.setdefault("follow_up_chain", [])
    payload.setdefault("score", 0)
    payload.setdefault("confidence", 0.0)
    payload.setdefault("strength_evidence", [])
    payload.setdefault("risk_evidence", [])
    payload.setdefault("missing_evidence", [])
    payload.setdefault("decision_result", "")
    payload.setdefault("decision_reason", "")
    payload.setdefault("persona", "")
    payload.setdefault("persona_dimensions", {})
    payload.setdefault("competencies", [])
    payload.setdefault("round_focus", [])
    payload.setdefault("question_source", "")
    payload.setdefault("matched_good_signals", [])
    payload.setdefault("matched_red_flags", [])
    payload.setdefault("expected_signal_hit", False)
    payload.setdefault("question_bank_alignment", "")
    payload.setdefault("source_path", "")
    return payload


def build_timeline_records(
    turn_events: list[TurnEvent] | list[dict[str, Any]] | None,
    question_records: list[QuestionResult] | list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    ordered_questions = sorted(
        [serialize_question_record(item) for item in (question_records or [])],
        key=lambda item: (
            round_sort_index(str(item.get("round", ""))),
            int(item.get("turn_index", 0) or 0),
            str(item.get("id", "")),
        ),
    )
    raw_events = sorted(
        [normalize_turn_event(item) for item in (turn_events or [])],
        key=lambda item: int(item.get("turn_index", 0) or 0),
    )

    question_by_turn = {
        int(item.get("turn_index", 0) or 0): item
        for item in ordered_questions
        if int(item.get("turn_index", 0) or 0) > 0
    }
    question_by_id = {
        str(item.get("id", "")): item
        for item in ordered_questions
        if str(item.get("id", ""))
    }
    prompt_to_question: dict[tuple[str, str], dict[str, Any]] = {}
    for item in ordered_questions:
        prompt = str(item.get("question", "") or "").strip()
        round_name = str(item.get("round", "") or "").strip()
        if prompt and round_name:
            prompt_to_question[(round_name, prompt)] = item

    last_main_turn_by_round: dict[str, int] = {}
    existing_follow_ups_by_parent: dict[int, set[tuple[str, str]]] = defaultdict(set)
    inferred_follow_up_index: dict[int, int] = defaultdict(int)
    timeline_records: list[dict[str, Any]] = []

    for seq, event in enumerate(raw_events):
        round_name = str(event.get("round", "") or "")
        stage = str(event.get("stage", "") or "")
        turn_index = int(event.get("turn_index", 0) or 0)

        question = None
        question_id = str(event.get("question_id", "") or "")
        if question_id:
            question = question_by_id.get(question_id)
        if question is None and turn_index in question_by_turn:
            question = question_by_turn.get(turn_index)
        if question is None:
            question = prompt_to_question.get((round_name, str(event.get("prompt", "") or "").strip()))

        resolved_question_id = str(event.get("question_id", "") or (question.get("id", "") if question else ""))
        resolved_question_title = str(event.get("question_title", "") or (question.get("title", "") if question else ""))

        parent_turn_index = event.get("parent_turn_index")
        if parent_turn_index is None and stage in FOLLOW_UP_STAGES:
            parent_turn_index = last_main_turn_by_round.get(round_name)
        if parent_turn_index is not None:
            parent_turn_index = int(parent_turn_index)

        if stage in MAIN_QUESTION_STAGES:
            last_main_turn_by_round[round_name] = turn_index
            timeline_records.append(
                {
                    **event,
                    "question_id": resolved_question_id,
                    "question_title": resolved_question_title,
                    "parent_question_id": "",
                    "parent_question_title": "",
                    "parent_turn_index": None,
                    "follow_up_index": None,
                    "display_turn_index": f"#{turn_index}",
                    "group_label": "主问题",
                    "parent_display": "",
                    "is_synthetic": False,
                    "timeline_sort": (turn_index, 0, seq),
                }
            )
            continue

        if stage in FOLLOW_UP_STAGES:
            if not parent_turn_index and resolved_question_id:
                question_item = question_by_id.get(resolved_question_id)
                if question_item:
                    parent_turn_index = int(question_item.get("turn_index", 0) or 0) or None
            parent_question = question_by_turn.get(int(parent_turn_index or 0)) if parent_turn_index else None
            parent_question_id = str(event.get("parent_question_id", "") or resolved_question_id or (parent_question.get("id", "") if parent_question else ""))
            parent_question_title = str(
                event.get("parent_question_title", "")
                or resolved_question_title
                or (parent_question.get("title", "") if parent_question else "")
            )
            if parent_turn_index:
                inferred_follow_up_index[parent_turn_index] += 1
            follow_up_index = int(event.get("follow_up_index") or inferred_follow_up_index.get(int(parent_turn_index or 0), 0) or 1)
            existing_follow_ups_by_parent[int(parent_turn_index or 0)].add(
                (str(event.get("prompt", "") or ""), str(event.get("response", "") or ""))
            )
            parent_display = (
                f"归属主问题 #{parent_turn_index} {parent_question_title}".strip()
                if parent_turn_index
                else (f"归属主问题 {parent_question_title}" if parent_question_title else "")
            )
            timeline_records.append(
                {
                    **event,
                    "question_id": resolved_question_id or parent_question_id,
                    "question_title": resolved_question_title or parent_question_title,
                    "parent_question_id": parent_question_id,
                    "parent_question_title": parent_question_title,
                    "parent_turn_index": parent_turn_index,
                    "follow_up_index": follow_up_index,
                    "display_turn_index": f"#{turn_index}",
                    "group_label": f"追问 {follow_up_index}",
                    "parent_display": parent_display,
                    "is_synthetic": False,
                    "timeline_sort": (turn_index, 1, seq),
                }
            )
            continue

        timeline_records.append(
            {
                **event,
                "question_id": resolved_question_id,
                "question_title": resolved_question_title,
                "display_turn_index": f"#{turn_index}",
                "group_label": stage_label(stage),
                "parent_display": "",
                "is_synthetic": False,
                "timeline_sort": (turn_index, 2, seq),
            }
        )

    for question in ordered_questions:
        parent_turn_index = int(question.get("turn_index", 0) or 0)
        if parent_turn_index <= 0:
            continue
        for idx, item in enumerate(question.get("follow_up_chain", []) or [], start=1):
            signature = (str(item.get("question", "") or ""), str(item.get("answer", "") or ""))
            if signature in existing_follow_ups_by_parent.get(parent_turn_index, set()):
                continue
            timeline_records.append(
                {
                    "turn_index": parent_turn_index,
                    "round": str(question.get("round", "") or ""),
                    "stage": "follow_up",
                    "prompt": signature[0],
                    "spoken_text": "",
                    "response": signature[1],
                    "decision_result": "",
                    "score": None,
                    "confidence": None,
                    "tts_file": "",
                    "persona": str(question.get("persona", "") or ""),
                    "question_id": str(question.get("id", "") or ""),
                    "question_title": str(question.get("title", "") or ""),
                    "parent_question_id": str(question.get("id", "") or ""),
                    "parent_question_title": str(question.get("title", "") or ""),
                    "parent_turn_index": parent_turn_index,
                    "follow_up_index": idx,
                    "notes": ["synthetic_follow_up_from_score"],
                    "display_turn_index": f"#{parent_turn_index}.{idx}",
                    "group_label": f"追问 {idx}",
                    "parent_display": f"归属主问题 #{parent_turn_index} {question.get('title', '')}".strip(),
                    "is_synthetic": True,
                    "timeline_sort": (parent_turn_index, idx, 1000 + idx),
                }
            )

    return sorted(timeline_records, key=lambda item: item["timeline_sort"])


def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8").strip()


def load_answers(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def slugify(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip()).strip("-")
    return text.lower() or "candidate"


def keywords(text: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[A-Za-z][A-Za-z0-9.+_-]{2,}", text)}


def language_text(language: str, zh: str, en: str, bilingual: str | None = None) -> str:
    if language == "zh":
        return zh
    if language == "bilingual":
        return bilingual or f"{en}\n\n{zh}"
    return en


def build_session_id(session_id: str, candidate_name: str, suffix: str) -> str:
    if session_id:
        return session_id
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{ts}-{slugify(candidate_name)}-{suffix}"


def filter_questions_by_mode(questions: list[Question], mode: str) -> list[Question]:
    allowed_rounds = set(MODE_ROUNDS.get(mode, MODE_ROUNDS["simulate"]))
    return [question for question in questions if question.round in allowed_rounds]


def normalize_dimension_name(name: str) -> str:
    return name.strip().lower().replace("-", "_").replace(" ", "_")


def normalize_cli_key(name: str) -> str:
    return name.strip().lower().replace("_", "-").replace(" ", "-")


def resolve_persona_name(name: str) -> str:
    raw = str(name or "").strip()
    if not raw:
        return ""
    if raw in PERSONA_LIBRARY:
        return raw
    alias = PERSONA_ALIASES.get(normalize_cli_key(raw), "")
    if alias:
        return alias
    raise ValueError(f"Unknown persona preset: {name}")


def parse_round_persona_overrides(value: str) -> dict[str, str]:
    if not value.strip():
        return {}
    overrides: dict[str, str] = {}
    for item in value.split(","):
        if not item.strip():
            continue
        if "=" not in item:
            raise ValueError(f"Invalid round persona override: {item}")
        round_name, persona_name = item.split("=", 1)
        round_key = round_name.strip()
        if round_key not in ROUND_LABELS:
            raise ValueError(f"Unknown round in persona override: {round_name}")
        overrides[round_key] = resolve_persona_name(persona_name)
    return overrides


def parse_persona_voice_overrides(value: str) -> dict[str, str]:
    if not value.strip():
        return {}
    overrides: dict[str, str] = {}
    for item in value.split(","):
        if not item.strip():
            continue
        if "=" not in item:
            raise ValueError(f"Invalid persona voice override: {item}")
        persona_name, voice_name = item.split("=", 1)
        resolved_persona = resolve_persona_name(persona_name)
        resolved_voice = str(voice_name).strip()
        if not resolved_voice:
            raise ValueError(f"Voice name cannot be empty in persona voice override: {item}")
        overrides[resolved_persona] = resolved_voice
    return overrides


def parse_question_target_overrides(value: str) -> dict[str, int]:
    if not value.strip():
        return {}
    overrides: dict[str, int] = {}
    for item in value.split(","):
        if not item.strip():
            continue
        if "=" not in item:
            raise ValueError(f"Invalid question target override: {item}")
        round_name, target_value = item.split("=", 1)
        round_key = round_name.strip()
        if round_key not in ROUND_LABELS:
            raise ValueError(f"Unknown round in question target override: {round_name}")
        target = int(target_value.strip())
        if target < 1:
            raise ValueError(f"Question target must be >= 1 for round {round_name}")
        overrides[round_key] = target
    return overrides


def parse_round_language_overrides(value: str) -> dict[str, str]:
    if not value.strip():
        return {}
    overrides: dict[str, str] = {}
    allowed = {"zh", "en", "bilingual"}
    for item in value.split(","):
        if not item.strip():
            continue
        if "=" not in item:
            raise ValueError(f"Invalid round language override: {item}")
        round_name, language_value = item.split("=", 1)
        round_key = round_name.strip()
        if round_key not in ROUND_LABELS:
            raise ValueError(f"Unknown round in language override: {round_name}")
        language_mode = language_value.strip()
        if language_mode not in allowed:
            raise ValueError(f"Unknown language mode in override: {language_value}")
        overrides[round_key] = language_mode
    return overrides


def rank_question(question: Question, jd_tokens: set[str], resume_tokens: set[str], level: str, language: str) -> float:
    score = question.weight
    if question.level == level:
        score += 2.0
    if question.language in {"", language}:
        score += 1.0
    hits = sum(1 for tag in question.tags if tag.lower() in jd_tokens or tag.lower() in resume_tokens)
    score += hits * 0.35
    if question.direction and question.direction.lower() in jd_tokens:
        score += 0.6
    if question.must_ask:
        score += 1.5
    if question.difficulty in {"L4", "L5"} and level in {"senior", "tl"}:
        score += 0.3
    return score


def coverage_dimensions(question: Question) -> set[str]:
    dimensions = {normalize_dimension_name(item) for item in question.competencies}
    if question.direction:
        dimensions.add(normalize_dimension_name(question.direction))
    return {item for item in dimensions if item}


def question_focuses(question: Any) -> list[str]:
    focuses = [normalize_dimension_name(item) for item in getattr(question, "competencies", []) if item]
    direction = getattr(question, "direction", "")
    if direction:
        focuses.append(normalize_dimension_name(direction))
    normalized: list[str] = []
    for item in focuses:
        if item and item not in normalized:
            normalized.append(item)
    return normalized


def top_keywords_for_prompt(jd_text: str, resume_text: str, limit: int = 4) -> list[str]:
    merged = sorted(list(keywords(jd_text) | keywords(resume_text)))
    return merged[:limit]


def question_target_count(round_name: str, overrides: dict[str, int] | None = None) -> int:
    if overrides and round_name in overrides:
        return overrides[round_name]
    return ROUND_QUESTION_TARGETS.get(round_name, 1)


def question_difficulty_rank(question: Any) -> int:
    difficulty = str(getattr(question, "difficulty", "") or "").upper().strip()
    match = re.search(r"L([1-5])", difficulty)
    if match:
        return int(match.group(1))
    return 3


def choose_adaptive_next_question(
    current_result: QuestionResult,
    remaining_questions: list[Any],
    planned_focuses: list[str],
    covered_focuses: set[str],
) -> dict[str, Any] | None:
    if not remaining_questions:
        return None

    current_focuses = set(question_focuses(current_result))
    planned_remaining = [focus for focus in planned_focuses if focus not in covered_focuses]

    def candidate_score(question: Any) -> tuple[Any, ...]:
        q_focuses = set(question_focuses(question))
        overlap = len(current_focuses & q_focuses)
        planned_hits = len(set(planned_remaining) & q_focuses)
        difficulty = question_difficulty_rank(question)
        return (
            overlap,
            planned_hits,
            difficulty,
            -len(q_focuses),
            question.title,
        )

    def easier_candidate_score(question: Any) -> tuple[Any, ...]:
        q_focuses = set(question_focuses(question))
        overlap = len(current_focuses & q_focuses)
        planned_hits = len(set(planned_remaining) & q_focuses)
        difficulty = question_difficulty_rank(question)
        return (
            -overlap,
            planned_hits,
            difficulty,
            question.title,
        )

    action = current_result.decision_result
    candidates = list(enumerate(remaining_questions))

    if action == "increase_difficulty":
        ranked = sorted(candidates, key=lambda item: (-question_difficulty_rank(item[1]), -candidate_score(item[1])[1], -candidate_score(item[1])[0], item[0]))
        selected_index, selected_question = ranked[0]
        return {
            "action": "promote_harder_question",
            "reason": "Current answer is strong enough to justify a harder follow-up question.",
            "selected_index": selected_index,
            "selected_question_id": getattr(selected_question, "id", ""),
        }

    if action == "decrease_difficulty":
        ranked = sorted(candidates, key=lambda item: (question_difficulty_rank(item[1]), easier_candidate_score(item[1])[0], -easier_candidate_score(item[1])[1], item[0]))
        selected_index, selected_question = ranked[0]
        return {
            "action": "promote_easier_question",
            "reason": "Current answer is weak enough to lower the next question’s difficulty and recover evidence.",
            "selected_index": selected_index,
            "selected_question_id": getattr(selected_question, "id", ""),
        }

    if action == "follow_up_same_topic":
        topical = [item for item in candidates if current_focuses.intersection(question_focuses(item[1]))]
        if not topical:
            return None
        ranked = sorted(topical, key=lambda item: (-len(current_focuses & set(question_focuses(item[1]))), question_difficulty_rank(item[1]), item[0]))
        selected_index, selected_question = ranked[0]
        return {
            "action": "stay_on_topic",
            "reason": "The current answer still has a gap, so the next question should stay on the same topic.",
            "selected_index": selected_index,
            "selected_question_id": getattr(selected_question, "id", ""),
        }

    if action in {"switch_topic", "complete_round_pass", "advance_same_round"}:
        topical = [item for item in candidates if not current_focuses.intersection(question_focuses(item[1]))]
        if planned_remaining:
            topical = [item for item in topical if set(planned_remaining).intersection(question_focuses(item[1]))] or topical
        if not topical:
            return None
        ranked = sorted(topical, key=lambda item: (-len(set(planned_remaining) & set(question_focuses(item[1]))), question_difficulty_rank(item[1]), item[0]))
        selected_index, selected_question = ranked[0]
        return {
            "action": "switch_to_new_focus",
            "reason": "The current topic is sufficiently covered, so the next question should move to a different focus area.",
            "selected_index": selected_index,
            "selected_question_id": getattr(selected_question, "id", ""),
        }

    return None


def detect_jd_priority_signals(jd_text: str) -> dict[str, bool]:
    lowered = jd_text.lower()
    return {
        "performance_heavy": any(token in lowered for token in ["performance", "startup", "latency", "anr", "oom", "render"]),
        "architecture_heavy": any(token in lowered for token in ["architecture", "modular", "module", "design", "scalability", "system"]),
        "leadership_heavy": any(token in lowered for token in ["lead", "mentoring", "manager", "stakeholder", "cross-team", "ownership"]),
        "business_heavy": any(token in lowered for token in ["business", "growth", "consumer", "metric", "impact", "product"]),
        "english_required": "english" in lowered,
    }


def detect_resume_gap_signals(resume_text: str, candidate_profile: dict[str, Any] | None = None, language: str = "en") -> list[str]:
    lowered = resume_text.lower()
    profile_signals = (candidate_profile or {}).get("signals", {})
    gaps: list[str] = []
    if not profile_signals.get("contains_metrics", False):
        gaps.append("metrics_evidence")
    if not profile_signals.get("contains_ownership", False):
        gaps.append("ownership_evidence")
    if not any(token in lowered for token in ["lead", "mentor", "stakeholder", "align", "priority", "conflict"]):
        gaps.append("leadership_signal")
    if not any(token in lowered for token in ["tradeoff", "rollback", "regression", "baseline", "trace", "monitor"]):
        gaps.append("tradeoff_signal")
    if language != "zh" and not any(token in lowered for token in ["english", "global", "international"]):
        gaps.append("english_signal")
    return gaps


def plan_round_focuses(
    round_name: str,
    level: str,
    language: str,
    jd_signals: dict[str, bool],
    resume_gaps: list[str],
) -> list[str]:
    base = list(ROUND_FOCUS.get(round_name, []))
    extra: list[str] = []
    if round_name == "screening":
        if "ownership_evidence" in resume_gaps:
            extra.append("ownership")
        if "metrics_evidence" in resume_gaps:
            extra.append("delivery_scope")
    elif round_name == "round1":
        if "tradeoff_signal" in resume_gaps:
            extra.append("implementation_detail")
    elif round_name == "round2":
        if jd_signals.get("architecture_heavy"):
            extra.insert(0, "architecture")
        if jd_signals.get("performance_heavy"):
            extra.insert(0, "performance")
        if "metrics_evidence" in resume_gaps:
            extra.append("tradeoff_reasoning")
    elif round_name == "round3":
        if jd_signals.get("business_heavy"):
            extra.insert(0, "business_understanding")
        if jd_signals.get("leadership_heavy") or level == "tl":
            extra.append("technical_influence")
            extra.append("cross_team_execution")
    elif round_name == "hr":
        if jd_signals.get("leadership_heavy") or "leadership_signal" in resume_gaps:
            extra.insert(0, "leadership")
        if "english_signal" in resume_gaps and language != "zh":
            extra.append("english_interview")
    ordered: list[str] = []
    for item in extra + base:
        norm = normalize_dimension_name(item)
        if norm and norm not in ordered:
            ordered.append(norm)
    return ordered


def focus_selection_reason(focus: str, jd_signals: dict[str, bool], resume_gaps: list[str]) -> str:
    reasons: list[str] = []
    if focus in {"performance", "tradeoff_reasoning"} and jd_signals.get("performance_heavy"):
        reasons.append("JD 对性能或稳定性有明确要求")
    if focus in {"architecture", "implementation_detail"} and jd_signals.get("architecture_heavy"):
        reasons.append("JD 强调架构、模块化或系统设计")
    if focus in {"leadership", "technical_influence", "cross_team_execution"} and jd_signals.get("leadership_heavy"):
        reasons.append("JD 强调带人、跨团队推进或 ownership")
    if focus in {"business_understanding"} and jd_signals.get("business_heavy"):
        reasons.append("JD 强调业务结果与指标意识")
    if focus in {"ownership", "delivery_scope"} and "ownership_evidence" in resume_gaps:
        reasons.append("简历中 ownership 证据偏弱，需要优先验证")
    if focus in {"tradeoff_reasoning", "performance"} and "metrics_evidence" in resume_gaps:
        reasons.append("简历中量化指标信号偏弱，需要补充结果证据")
    if focus in {"leadership", "technical_influence"} and "leadership_signal" in resume_gaps:
        reasons.append("简历中领导力/影响力信号不足，需要面试中补证")
    return "；".join(reasons) or "作为本轮默认核心能力点进行验证"


def build_interview_plan(
    jd_text: str,
    resume_text: str,
    level: str,
    language: str,
    mode: str,
    question_target_overrides: dict[str, int] | None = None,
    round_language_overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    candidate_profile = build_profiles(jd_text, resume_text, level, language)[1]
    jd_signals = detect_jd_priority_signals(jd_text)
    resume_gaps = detect_resume_gap_signals(resume_text, candidate_profile, language)
    allowed_rounds = MODE_ROUNDS.get(mode, MODE_ROUNDS["simulate"])
    rounds: list[dict[str, Any]] = []
    round_language_overrides = round_language_overrides or {}
    for round_name in allowed_rounds:
        if round_name == "intro":
            priority_focuses = ["communication", "project_authenticity"] + (["english_interview"] if language != "zh" else [])
        else:
            priority_focuses = plan_round_focuses(round_name, level, language, jd_signals, resume_gaps)
        round_language = round_language_overrides.get(round_name, language)
        rounds.append(
            {
                "round": round_name,
                "label": ROUND_LABELS.get(round_name, round_name),
                "question_target": 1 if round_name == "intro" else question_target_count(round_name, question_target_overrides),
                "priority_focuses": priority_focuses,
                "selection_reasons": [
                    {"focus": focus, "reason": focus_selection_reason(focus, jd_signals, resume_gaps)}
                    for focus in priority_focuses
                ],
                "language_mode": round_language,
            }
        )
    return {
        "mode": mode,
        "target_level": level,
        "language_mode": language,
        "question_target_overrides": question_target_overrides or {},
        "round_language_overrides": round_language_overrides,
        "jd_priority_signals": jd_signals,
        "resume_gap_signals": resume_gaps,
        "rounds": rounds,
    }


def threshold_policy(level: str, round_name: str) -> dict[str, Any]:
    base = dict(ROUND_THRESHOLD_DEFAULTS.get(round_name, {"min_round_score": 3.0, "min_confidence": 0.45, "critical_focuses": [], "critical_min_score": 3.0}))
    override = LEVEL_THRESHOLD_OVERRIDES.get(level, {}).get(round_name, {})
    merged = {**base, **override}
    merged["critical_focuses"] = [normalize_dimension_name(item) for item in merged.get("critical_focuses", [])]
    return merged


def build_round_scorecards(
    results: list[QuestionResult],
    round_summaries: list[RoundSummary],
    interview_plan: dict[str, Any] | None,
    level: str,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[QuestionResult]] = defaultdict(list)
    for result in results:
        grouped[result.round].append(result)

    scorecards: list[dict[str, Any]] = []
    for summary in round_summaries:
        items = grouped.get(summary.round, [])
        policy = threshold_policy(level, summary.round)
        planned_focuses = planned_focuses_for_round(interview_plan, summary.round)
        critical_focuses = critical_focuses_for_round(policy, planned_focuses)
        competency_checks: list[dict[str, Any]] = []
        failed_focuses: list[str] = []
        for focus in critical_focuses:
            focus_scores = [item.score for item in items if focus in question_focuses(item)]
            focus_confidences = [item.confidence for item in items if focus in question_focuses(item)]
            if focus_scores:
                actual_score = round(sum(focus_scores) / len(focus_scores), 2)
                actual_confidence = round(sum(focus_confidences) / len(focus_confidences), 2)
                verdict = "pass" if actual_score >= policy["critical_min_score"] else "fail"
            else:
                actual_score = None
                actual_confidence = None
                verdict = "missing"
            competency_checks.append(
                {
                    "focus": focus,
                    "expected_min_score": policy["critical_min_score"],
                    "actual_score": actual_score,
                    "actual_confidence": actual_confidence,
                    "verdict": verdict,
                }
            )
            if verdict == "fail":
                failed_focuses.append(focus)

        round_verdict = "pass"
        verdict_reason = "Round evidence meets the configured threshold."
        if summary.terminated:
            round_verdict = "fail"
            verdict_reason = "Round terminated early because a critical answer failed."
        elif summary.score < policy["min_round_score"] or summary.confidence < policy["min_confidence"]:
            round_verdict = "risk"
            verdict_reason = "Round average score or confidence did not fully meet the target threshold."
        if failed_focuses:
            round_verdict = "fail"
            verdict_reason = f"Critical focus below threshold: {', '.join(failed_focuses)}."

        scorecards.append(
            {
                "round": summary.round,
                "label": summary.label,
                "threshold": {
                    "min_round_score": policy["min_round_score"],
                    "min_confidence": policy["min_confidence"],
                    "critical_min_score": policy["critical_min_score"],
                },
                "critical_focuses": critical_focuses,
                "competency_checks": competency_checks,
                "round_verdict": round_verdict,
                "verdict_reason": verdict_reason,
            }
        )
    return scorecards


def scorecard_map(scorecards: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["round"]: item for item in scorecards}


def planned_focuses_for_round(interview_plan: dict[str, Any] | None, round_name: str) -> list[str]:
    if not interview_plan:
        return []
    for item in interview_plan.get("rounds", []):
        if item.get("round") == round_name:
            return [normalize_dimension_name(focus) for focus in item.get("priority_focuses", [])]
    return []


def planned_question_target_for_round(interview_plan: dict[str, Any] | None, round_name: str) -> int | None:
    if not interview_plan:
        return None
    for item in interview_plan.get("rounds", []):
        if item.get("round") == round_name:
            value = item.get("question_target")
            return int(value) if value else None
    return None


def planned_language_for_round(interview_plan: dict[str, Any] | None, round_name: str, default_language: str) -> str:
    if not interview_plan:
        return default_language
    for item in interview_plan.get("rounds", []):
        if item.get("round") == round_name:
            return str(item.get("language_mode") or default_language)
    return default_language


def critical_focuses_for_round(policy: dict[str, Any], planned_focuses: list[str]) -> list[str]:
    critical = [focus for focus in policy.get("critical_focuses", []) if focus]
    if planned_focuses:
        overlapping = [focus for focus in critical if focus in planned_focuses]
        if overlapping:
            return overlapping
        return planned_focuses[:2]
    return critical


def finalize_interview_plan(interview_plan: dict[str, Any], selected_questions: list[Question]) -> dict[str, Any]:
    questions_by_round: dict[str, list[Question]] = defaultdict(list)
    for question in selected_questions:
        questions_by_round[question.round].append(question)

    rounds: list[dict[str, Any]] = []
    for round_item in interview_plan.get("rounds", []):
        round_name = round_item["round"]
        selected = questions_by_round.get(round_name, [])
        planned = [normalize_dimension_name(item) for item in round_item.get("priority_focuses", [])]
        covered = sorted({item for question in selected for item in coverage_dimensions(question)})
        missing = [item for item in planned if item not in covered]
        rounds.append(
            {
                **round_item,
                "selected_questions": [
                    {
                        "id": question.id,
                        "title": question.title,
                        "source": question.source or ("generated-fallback" if question.source_path.startswith("generated:") else "question-bank"),
                        "direction": question.direction,
                        "competencies": question.competencies,
                    }
                    for question in selected
                ],
                "covered_focuses": covered,
                "missing_focuses_after_selection": missing,
            }
        )
    return {**interview_plan, "rounds": rounds}


def build_improvement_suggestions(results: list[QuestionResult]) -> list[str]:
    risk_counter: dict[str, int] = defaultdict(int)
    for result in results:
        for risk in result.risk_evidence:
            risk_counter[risk] += 1
        for missing in result.missing_evidence:
            risk_counter[missing] += 1

    suggestions: list[str] = []
    if risk_counter.get("缺少量化结果或关键指标", 0):
        suggestions.append("准备每个核心项目的基线、指标口径、优化结果和上线后的监控表现。")
    if risk_counter.get("团队表述较多，但个人职责边界不够清晰", 0):
        suggestions.append("用“背景-我的职责-我的动作-结果”模板重写项目叙述，明确个人 ownership。")
    if risk_counter.get("缺少明确的方案权衡说明", 0):
        suggestions.append("为每个重点项目补齐至少一个技术权衡案例，说明为什么选这个方案以及放弃了什么。")
    if risk_counter.get("缺少失败、问题或回滚相关说明", 0):
        suggestions.append("准备真实失败或回滚案例，说明问题定位、止损动作和后续复盘。")
    if not suggestions:
        suggestions.append("继续保持证据化回答习惯，确保每道题都包含职责、指标、权衡和复盘。")
    return suggestions[:4]


def generated_question_blueprint(round_name: str, focus: str, language: str, jd_text: str, resume_text: str) -> tuple[str, list[str], str, str]:
    keyword_text = ", ".join(top_keywords_for_prompt(jd_text, resume_text, limit=4))
    normalized_focus = normalize_dimension_name(focus)

    prompt_map = {
        "implementation_detail": (
            language_text(
                language,
                f"请结合你做过的 Android 功能，讲一个你亲自落地的实现细节案例。重点说明关键实现、边界条件，以及它与 {keyword_text} 这类要求的关系。",
                f"Take one Android feature you personally implemented and walk me through the concrete implementation detail. Focus on the key mechanism, edge cases, and how it connects to requirements like {keyword_text}.",
                f"Take one Android feature you personally implemented and walk me through the concrete implementation detail. Focus on the key mechanism, edge cases, and how it connects to requirements like {keyword_text}. 如有必要可补充中文术语说明。",
            ),
            [
                language_text(language, "这个实现里最容易出错的边界条件是什么？", "What was the easiest edge case to get wrong here?"),
                language_text(language, "你如何验证这个实现在线上是稳定的？", "How did you validate that this implementation was stable in production?"),
            ],
            "Probe whether the candidate can move from architecture words to actual implementation detail.",
            "Candidate can explain concrete implementation detail, edge cases, and verification path.",
        ),
        "tradeoff_reasoning": (
            language_text(
                language,
                "请讲一个你在 Android 项目里做过的重要技术权衡。重点说清楚候选方案、你最终的选择、被你放弃的方案，以及为什么。",
                "Tell me about one meaningful Android tradeoff you had to make. Be explicit about the options you considered, the option you chose, the option you rejected, and why.",
                "Tell me about one meaningful Android tradeoff you had to make. Be explicit about the options you considered, the option you chose, the option you rejected, and why. 需要时可补充中文术语说明。",
            ),
            [
                language_text(language, "如果现在重做，你还会做同样的选择吗？", "If you had to do it again today, would you make the same choice?"),
                language_text(language, "你怎么控制这个权衡带来的风险？", "How did you control the risks introduced by that tradeoff?"),
            ],
            "Verify tradeoff quality beyond tool or framework name-dropping.",
            "Candidate can explain tradeoffs, rejected alternatives, and risk control.",
        ),
        "technical_influence": (
            language_text(
                language,
                "讲一个你不是靠职位权力，而是靠技术判断和影响力推动团队改变做法的例子。",
                "Tell me about a time you changed the team’s direction through technical judgment and influence rather than positional authority.",
                "Tell me about a time you changed the team’s direction through technical judgment and influence rather than positional authority. 如有必要可补充中文背景。",
            ),
            [
                language_text(language, "一开始别人为什么不认同？", "Why did people disagree with you at first?"),
                language_text(language, "最后团队为什么愿意跟进？", "Why did the team finally align with you?"),
            ],
            "Check senior/TL influence signal without defaulting to people management only.",
            "Candidate can explain technical influence, resistance, and alignment path.",
        ),
        "motivation": (
            language_text(
                language,
                "如果你真的加入这个岗位，你最看重的三件事是什么？同时说清楚哪些情况会让你判断这个机会不适合你。",
                "If you were to take this role, what are the top three things you would care about, and what conditions would make you decide it is not the right fit?",
                "If you were to take this role, what are the top three things you would care about, and what conditions would make you decide it is not the right fit? 如有必要可补充中文说明。",
            ),
            [
                language_text(language, "你如何判断一家公司和团队是否值得长期投入？", "How do you decide whether a company and team are worth a long-term commitment?"),
                language_text(language, "你下一阶段最想强化的能力是什么？", "What capability do you most want to strengthen in your next step?"),
            ],
            "Evaluate motivation, stability, and career maturity.",
            "Candidate can explain motivation, constraints, and career judgment with maturity.",
        ),
        "business_understanding": (
            language_text(
                language,
                f"选一个你参与过的 Android 项目，从业务结果视角复盘。重点说清楚这个项目服务了什么目标，以及它和 {keyword_text} 这类要求的关系。",
                f"Pick one Android project you worked on and review it from a business outcome perspective. Explain the business goal it served and how it connected to expectations like {keyword_text}.",
                f"Pick one Android project you worked on and review it from a business outcome perspective. Explain the business goal it served and how it connected to expectations like {keyword_text}. 如有必要可补充中文业务背景。",
            ),
            [
                language_text(language, "你最关注的业务指标是什么？", "Which business metric mattered the most to you?"),
                language_text(language, "如果业务目标变了，你会先动哪一部分方案？", "If the business goal changed, what part of the solution would you change first?"),
            ],
            "Check whether the candidate can connect engineering work to business outcomes.",
            "Candidate can link technical decisions to metrics, priorities, and user value.",
        ),
    }

    default_prompt = (
        language_text(
            language,
            f"请围绕 {focus} 这个主题，结合你的真实项目经历回答：你亲自做过什么，结果如何，风险如何控制？",
            f"Answer this around the theme of {focus}: what did you personally do, what outcome did it drive, and how did you control the risk?",
            f"Answer this around the theme of {focus}: what did you personally do, what outcome did it drive, and how did you control the risk? 如有必要可补充中文。",
        ),
        [
            language_text(language, "你如何证明这不是团队平均贡献，而是你的关键贡献？", "How do you prove this was your key contribution rather than generic team output?"),
            language_text(language, "这件事最关键的风险点是什么？", "What was the key risk in that situation?"),
        ],
        f"Probe the candidate on {focus}.",
        f"Candidate can provide evidence-based detail for {focus}.",
    )
    return prompt_map.get(normalized_focus, default_prompt)


def build_dynamic_question(round_name: str, focus: str, level: str, language: str, jd_text: str, resume_text: str, slot: int) -> Question:
    question_text, follow_ups, intent, expected_signal = generated_question_blueprint(round_name, focus, language, jd_text, resume_text)
    focus_key = normalize_dimension_name(focus)
    question_id = f"generated-{round_name}-{focus_key.replace('_', '-')}-{slot:03d}"
    return Question(
        id=question_id,
        title=f"Generated {round_name.title()} {focus_key.replace('_', ' ').title()}",
        direction=focus_key,
        round=round_name,
        level=level,
        difficulty="L4" if round_name in {"round2", "round3"} else "L3",
        language=language,
        tags=[round_name, focus_key, "generated", "dynamic-fallback"],
        weight=0.72,
        source="generated-fallback",
        competencies=[focus_key],
        persona_fit=[],
        must_ask=False,
        follow_up_limit=min(2, len(follow_ups)),
        expected_signal=expected_signal,
        question=question_text,
        intent=intent,
        follow_ups=follow_ups,
        source_path=f"generated:{question_id}",
    )


def select_round_questions(
    round_name: str,
    questions: list[Question],
    jd_text: str,
    resume_text: str,
    level: str,
    language: str,
    planned_focuses: list[str] | None = None,
    target_count: int | None = None,
) -> list[Question]:
    jd_tokens = keywords(jd_text)
    resume_tokens = keywords(resume_text)
    target_count = target_count or question_target_count(round_name)
    pool = [question for question in questions if question.round == round_name]
    ranked = sorted(
        pool,
        key=lambda q: rank_question(q, jd_tokens, resume_tokens, level, language),
        reverse=True,
    )
    selected: list[Question] = []
    used_ids: set[str] = set()
    focus_priorities = [normalize_dimension_name(item) for item in (planned_focuses or [])]
    for focus in focus_priorities:
        match = next((question for question in ranked if question.id not in used_ids and focus in coverage_dimensions(question)), None)
        if match is not None:
            selected.append(match)
            used_ids.add(match.id)
        if len(selected) >= target_count:
            break
    for question in ranked:
        if len(selected) >= target_count:
            break
        if question.id in used_ids:
            continue
        selected.append(question)
        used_ids.add(question.id)
    covered = {item for question in selected for item in coverage_dimensions(question)}

    if len(selected) < target_count:
        round_focus = focus_priorities or [normalize_dimension_name(item) for item in ROUND_FOCUS.get(round_name, [])]
        focus_candidates = [focus for focus in round_focus if normalize_dimension_name(focus) not in covered]
        if not focus_candidates:
            focus_candidates = round_focus or [round_name]
        while len(selected) < target_count and focus_candidates:
            focus = focus_candidates.pop(0)
            generated = build_dynamic_question(round_name, focus, level, language, jd_text, resume_text, len(selected) + 1)
            selected.append(generated)
            covered.update(coverage_dimensions(generated))
        while len(selected) < target_count:
            fallback_focus = ROUND_FOCUS.get(round_name, [round_name])[(len(selected) - 1) % max(1, len(ROUND_FOCUS.get(round_name, [round_name])))]
            generated = build_dynamic_question(round_name, fallback_focus, level, language, jd_text, resume_text, len(selected) + 1)
            selected.append(generated)
    return selected


def select_questions(
    questions: list[Question],
    jd_text: str,
    resume_text: str,
    level: str,
    language: str,
    interview_plan: dict[str, Any] | None = None,
) -> list[Question]:
    desired_rounds = ["screening", "round1", "round2", "round3", "hr"]
    selected: list[Question] = []
    for target_round in desired_rounds:
        round_language = planned_language_for_round(interview_plan, target_round, language)
        selected.extend(
            select_round_questions(
                target_round,
                questions,
                jd_text,
                resume_text,
                level,
                round_language,
                planned_focuses=planned_focuses_for_round(interview_plan, target_round),
                target_count=planned_question_target_for_round(interview_plan, target_round),
            )
        )
    return selected or questions[: min(5, len(questions))]


def build_intro_question(level: str, language: str) -> Question:
    return Question(
        id="intro-self-001",
        title="Self Introduction and Career Narrative",
        direction="communication",
        round="intro",
        level=level,
        difficulty="L2",
        language=language,
        tags=["intro", "self-introduction", "resume"],
        weight=1.0,
        source="builtin",
        competencies=["communication", "project_authenticity", "english_interview"],
        persona_fit=["guided_mentor"],
        must_ask=True,
        follow_up_limit=2,
        expected_signal="Candidate can give a concise, role-relevant narrative with clear strongest project anchors.",
        question=language_text(
            language,
            "请你先做一个 1 到 2 分钟的自我介绍，重点讲清楚你的 Android 核心经历、最有代表性的项目，以及为什么你适合这个岗位。",
            "Please give me a one to two minute self-introduction. Focus on your Android experience, your strongest project, and why you fit this role.",
            "Please give me a one to two minute self-introduction in English. You may add a short Chinese clarification only if necessary. Focus on your Android experience, strongest project, and fit for this role.\n\n请先用英文做 1 到 2 分钟自我介绍，必要时可补充简短中文说明。",
        ),
        follow_ups=[
            language_text(
                language,
                "你提到的项目里，哪一部分是你亲自负责的？",
                "Which part of that project did you personally own?",
                "Which part of that project did you personally own? 如果需要，也可以补充中文说明。",
            ),
            language_text(
                language,
                "这个项目最能体现你资深度的结果指标是什么？",
                "What result or metric from that project best demonstrates your seniority?",
                "What result or metric from that project best demonstrates your seniority? 你也可以补充中文指标定义。",
            ),
        ],
        source_path="builtin:intro-self-001",
    )


def build_persona_configs(
    language: str,
    rounds: Iterable[str] | None = None,
    default_persona: str = "",
    round_persona_overrides: dict[str, str] | None = None,
    round_language_overrides: dict[str, str] | None = None,
) -> list[PersonaConfig]:
    selected_rounds = list(rounds or ROUND_PERSONA_DEFAULTS.keys())
    seen_rounds: set[str] = set()
    configs: list[PersonaConfig] = []
    resolved_default_persona = resolve_persona_name(default_persona) if default_persona else ""
    persona_overrides = dict(round_persona_overrides or {})
    language_overrides = dict(round_language_overrides or {})
    for round_name in selected_rounds:
        if round_name in seen_rounds:
            continue
        seen_rounds.add(round_name)
        persona_name = persona_overrides.get(round_name) or resolved_default_persona or ROUND_PERSONA_DEFAULTS.get(round_name, "引导教练型")
        preset = PERSONA_LIBRARY[persona_name]
        brief = preset["interviewer_brief"]
        round_language = language_overrides.get(round_name, language)
        if round_language == "en":
            brief = f"{brief} Keep the entire round in English."
        elif round_language == "bilingual":
            brief = f"{brief} Guide in Chinese when needed, but push the candidate to answer core parts in English."
        configs.append(
            PersonaConfig(
                round=round_name,
                persona=persona_name,
                pressure_level=int(preset["pressure_level"]),
                guidance_level=int(preset["guidance_level"]),
                skepticism_level=int(preset["skepticism_level"]),
                depth_threshold=int(preset["depth_threshold"]),
                business_focus=int(preset["business_focus"]),
                leadership_focus=int(preset["leadership_focus"]),
                interviewer_brief=brief,
            )
        )
    return configs


def persona_plan(language: str = "en", rounds: Iterable[str] | None = None) -> list[dict[str, Any]]:
    return [asdict(item) for item in build_persona_configs(language, rounds)]


def persona_dimensions(persona: PersonaConfig) -> dict[str, int]:
    return {
        "pressure_level": persona.pressure_level,
        "guidance_level": persona.guidance_level,
        "skepticism_level": persona.skepticism_level,
        "depth_threshold": persona.depth_threshold,
        "business_focus": persona.business_focus,
        "leadership_focus": persona.leadership_focus,
    }


def compose_round_intro(round_name: str, persona: PersonaConfig, language: str) -> str:
    label = ROUND_LABELS.get(round_name, round_name)
    focus = ", ".join(ROUND_FOCUS.get(round_name, []))
    return language_text(
        language,
        f"接下来进入 {label}。当前面试官风格为“{persona.persona}”。本轮重点考察：{focus}。",
        f"We are moving into {label}. My interviewer style for this round is {persona.persona}. I will focus on: {focus}.",
        f"We are moving into {label}. My interviewer style for this round is {persona.persona}. I will focus on: {focus}. If needed I can briefly clarify in Chinese, but please keep your core answer in English.\n\n接下来进入 {label}，重点考察：{focus}。",
    )


def compose_main_prompt(question: Question, persona: PersonaConfig, language: str) -> str:
    guidance_hint = ""
    if persona.guidance_level >= 4:
        guidance_hint = language_text(
            language,
            "你可以按背景、行动、结果来组织回答。",
            "You can structure your answer as context, action, and result.",
            "You can structure your answer as context, action, and result. 你也可以按背景、行动、结果来组织。",
        )
    pressure_hint = ""
    if persona.pressure_level >= 4:
        pressure_hint = language_text(
            language,
            "请回答得具体，不要只停留在概念层。",
            "Be precise and avoid staying at the concept level.",
            "Be precise and avoid staying at the concept level. 请尽量具体。",
        )
    round_label = ROUND_LABELS.get(question.round, question.round)
    focus_tags = " / ".join(question_focuses(question)[:3])
    stage_hint = language_text(
        language,
        f"当前阶段：{round_label}" + (f"；本题类型：{focus_tags}" if focus_tags else ""),
        f"Current stage: {round_label}" + (f"; question type: {focus_tags}" if focus_tags else ""),
        f"Current stage: {round_label}" + (f"; question type: {focus_tags}" if focus_tags else "") + f"\n当前阶段：{round_label}" + (f"；本题类型：{focus_tags}" if focus_tags else ""),
    )
    parts = [stage_hint, question.question]
    if guidance_hint:
        parts.append(guidance_hint)
    if pressure_hint:
        parts.append(pressure_hint)
    return "\n".join(parts)


def detect_strengths(text: str) -> list[str]:
    signals: list[str] = []
    lowered = text.lower()
    if re.search(r"\b\d+(\.\d+)?%|\b\d+ms\b|\b\d+x\b", lowered):
        signals.append("提供了量化指标或性能结果")
    if any(token in lowered for token in ["i led", "i owned", "i designed", "i implemented", "i drove", "my role"]):
        signals.append("能够明确说明个人职责与 ownership")
    if any(token in lowered for token in ["because", "trade", "instead of", "rollback", "regression", "tradeoff"]):
        signals.append("体现出方案权衡与风险控制意识")
    if any(token in lowered for token in ["trace", "profil", "metric", "monitor", "baseline", "macrobenchmark", "dashboard"]):
        signals.append("体现出诊断、度量或可观测性意识")
    if any(token in lowered for token in ["stakeholder", "align", "scope", "priority", "mentoring", "coach"]):
        signals.append("体现出跨团队协作或领导力信号")
    if any(token in lowered for token in ["customer", "revenue", "retention", "conversion", "adoption"]):
        signals.append("体现出业务结果意识")
    return sorted(set(signals))


def detect_risks(text: str) -> list[str]:
    risks: list[str] = []
    lowered = text.lower()
    if len(text.split()) < 18:
        risks.append("回答过短，证据密度不足")
    if "we" in lowered and not any(token in lowered for token in ["i owned", "my role", "i was responsible", "i led"]):
        risks.append("团队表述较多，但个人职责边界不够清晰")
    if not re.search(r"\b\d+(\.\d+)?%|\b\d+ms\b|\b\d+x\b", lowered):
        risks.append("缺少量化结果或关键指标")
    if any(token in lowered for token in ["maybe", "probably", "i think"]):
        risks.append("表述存在不确定语气，结论不够扎实")
    return sorted(set(risks))


def detect_missing(text: str) -> list[str]:
    missing: list[str] = []
    lowered = text.lower()
    if not any(token in lowered for token in ["because", "trade", "instead of", "tradeoff"]):
        missing.append("缺少明确的方案权衡说明")
    if not any(token in lowered for token in ["failed", "issue", "problem", "regression", "rollback", "lesson"]):
        missing.append("缺少失败、问题或回滚相关说明")
    if not any(token in lowered for token in ["metric", "monitor", "latency", "startup", "anr", "oom", "crash", "dashboard"]):
        missing.append("缺少可观测指标或问题定位信息")
    return sorted(set(missing))


def signal_tags(text: str) -> set[str]:
    lowered = text.lower()
    tags: set[str] = set()
    mapping = {
        "ownership": ["ownership", "owner", "owned", "responsible", "boundary", "contribution", "personally", "my role"],
        "metrics": ["metric", "result", "latency", "startup", "anr", "oom", "dashboard", "baseline", "monitor", "ms", "%", "measur"],
        "tradeoff": ["tradeoff", "trade", "rollback", "regression", "risk", "alternative", "option"],
        "verification": ["verify", "validation", "reproduction", "recreate", "duplicate", "log", "trace", "stable", "testing"],
        "lifecycle": ["lifecycle", "viewmodel", "state", "effect", "recreation", "duplicate work"],
        "leadership": ["stakeholder", "align", "mentor", "coach", "influence", "priority", "conflict", "team"],
        "business": ["business", "product", "launch", "customer", "revenue", "retention", "conversion", "adoption", "outcome"],
        "motivation": ["motivation", "fit", "career", "commitment", "long-term", "next step"],
        "english": ["english", "global", "international", "bilingual"],
    }
    for tag, keywords_list in mapping.items():
        if any(keyword in lowered for keyword in keywords_list):
            tags.add(tag)
    return tags


def align_question_bank_signals(
    question: Question | None,
    combined_text: str,
    strengths: list[str],
    risks: list[str],
    missing: list[str],
) -> dict[str, Any]:
    if question is None:
        return {
            "matched_good_signals": [],
            "matched_red_flags": [],
            "expected_signal_hit": False,
            "question_bank_alignment": "",
            "confidence_adjustment": 0.0,
        }

    strength_tags = signal_tags(" ".join(strengths))
    risk_tags = signal_tags(" ".join(risks + missing))
    answer_tags = signal_tags(combined_text)
    positive_tags = strength_tags | answer_tags
    negative_tags = risk_tags | answer_tags

    matched_good_signals = [
        phrase for phrase in question.good_signals if signal_tags(phrase) and signal_tags(phrase).intersection(positive_tags)
    ]
    matched_red_flags = [
        phrase for phrase in question.red_flags if signal_tags(phrase) and signal_tags(phrase).intersection(negative_tags) and risk_tags
    ]
    expected_tags = signal_tags(question.expected_signal)
    expected_signal_hit = not expected_tags or bool(expected_tags.intersection(positive_tags))

    confidence_adjustment = 0.0
    if matched_good_signals:
        confidence_adjustment += min(0.04, 0.02 * len(matched_good_signals))
    if matched_red_flags:
        confidence_adjustment -= min(0.06, 0.03 * len(matched_red_flags))
    if question.expected_signal and not expected_signal_hit:
        confidence_adjustment -= 0.03

    if matched_good_signals and expected_signal_hit and not matched_red_flags:
        question_bank_alignment = "strong_match"
    elif matched_good_signals or expected_signal_hit:
        question_bank_alignment = "partial_match"
    elif matched_red_flags:
        question_bank_alignment = "risk_match"
    else:
        question_bank_alignment = "no_match"

    return {
        "matched_good_signals": matched_good_signals[:4],
        "matched_red_flags": matched_red_flags[:4],
        "expected_signal_hit": expected_signal_hit,
        "question_bank_alignment": question_bank_alignment,
        "confidence_adjustment": confidence_adjustment,
    }


def score_answer(answer: str, follow_up_answers: list[str], question: Question | None = None) -> tuple[int, float, list[str], list[str], list[str], dict[str, Any]]:
    combined = " ".join([answer] + follow_up_answers).strip()
    strengths = detect_strengths(combined)
    risks = detect_risks(combined)
    missing = detect_missing(combined)
    base = 2
    base += min(len(strengths), 3)
    if len(risks) >= 3:
        base -= 1
    if len(missing) == 0:
        base += 1
    score = max(1, min(5, base))
    question_alignment = align_question_bank_signals(question, combined, strengths, risks, missing)
    if question_alignment["matched_good_signals"]:
        strengths = sorted(set(strengths + [f"题库命中正向信号: {item}" for item in question_alignment["matched_good_signals"]]))
    if question_alignment["matched_red_flags"]:
        risks = sorted(set(risks + [f"题库命中风险信号: {item}" for item in question_alignment["matched_red_flags"]]))
    if question and question.expected_signal and not question_alignment["expected_signal_hit"]:
        missing = sorted(set(missing + [f"未充分体现题库期望信号: {question.expected_signal}"]))
    confidence = round(
        max(
            0.3,
            min(
                0.95,
                0.52
                + len(strengths) * 0.08
                - len(missing) * 0.04
                - (0.03 if len(risks) >= 3 else 0.0)
                + float(question_alignment["confidence_adjustment"]),
            ),
        ),
        2,
    )
    return score, confidence, strengths, risks, missing, question_alignment


def decide_result(score: int, confidence: float, missing_evidence: list[str], risk_evidence: list[str], round_name: str) -> str:
    if round_name == "round2" and score <= 2:
        return "terminate_round_fail"
    if score <= 2 and any("职责边界" in item for item in risk_evidence):
        return "mark_risk"
    if score >= 4 and confidence >= 0.8 and not missing_evidence:
        return "complete_round_pass"
    if score >= 4 and confidence >= 0.72:
        return "increase_difficulty"
    if missing_evidence and score <= 3:
        return "follow_up_same_topic"
    if confidence >= 0.68 and not missing_evidence:
        return "switch_topic"
    if score <= 2:
        return "decrease_difficulty"
    return "advance_same_round"


def decision_reason(decision_result: str, score: int, confidence: float, missing_evidence: list[str], risk_evidence: list[str]) -> str:
    reasons = {
        "advance_same_round": "当前题目已收集到基本可用证据，但还不属于强信号通过。",
        "follow_up_same_topic": "当前题目仍存在关键证据缺口，需要围绕同一主题继续深挖。",
        "switch_topic": "当前主题已基本覆盖，适合切换到同轮其他能力点。",
        "increase_difficulty": "当前回答较强，可以提高后续验证难度。",
        "decrease_difficulty": "当前回答偏弱，适合降维收集更多基础证据。",
        "mark_risk": "当前回答暴露出明确风险，需要后续持续核验。",
        "terminate_round_fail": "当前轮次已达到提前淘汰阈值。",
        "complete_round_pass": "当前轮次目标已获得较充分证据，可结束本轮并进入下一轮。",
    }
    details: list[str] = [f"score={score}", f"confidence={confidence}"]
    if missing_evidence:
        details.append(f"missing={missing_evidence[0]}")
    if risk_evidence:
        details.append(f"risk={risk_evidence[0]}")
    return f"{reasons.get(decision_result, '流程决策已更新。')} ({', '.join(details)})"


def final_decision(results: list[QuestionResult], round_scorecards: list[dict[str, Any]] | None = None) -> tuple[str, list[str]]:
    hard_fail_flags: list[str] = []
    avg = sum(result.score for result in results) / max(1, len(results))
    for result in results:
        if result.score <= 2 and any("职责边界" in risk for risk in result.risk_evidence):
            hard_fail_flags.append(f"{result.id}: 项目归属表达存在明显风险")
        if result.round == "round2" and result.score <= 2:
            hard_fail_flags.append(f"{result.id}: 架构或深度能力未达到资深/TL 预期")
        if result.round == "intro" and result.score <= 2:
            hard_fail_flags.append(f"{result.id}: 自我介绍未能建立岗位匹配与项目真实性")
    if round_scorecards:
        for item in round_scorecards:
            if item["round_verdict"] == "fail":
                hard_fail_flags.append(f"{item['round']}: {item['verdict_reason']}")
    if hard_fail_flags:
        return "fail", sorted(set(hard_fail_flags))
    if avg >= 3.6:
        return "pass", []
    return ("borderline" if avg >= 3.0 else "fail"), []


def build_profiles(jd_text: str, resume_text: str, level: str, language: str) -> tuple[dict[str, Any], dict[str, Any]]:
    jd_signals = detect_jd_priority_signals(jd_text)
    focus_areas: list[str] = []
    if jd_signals.get("architecture_heavy"):
        focus_areas.append("architecture")
    if jd_signals.get("performance_heavy"):
        focus_areas.append("performance")
    if jd_signals.get("business_heavy"):
        focus_areas.append("business")
    if jd_signals.get("leadership_heavy") or level == "tl":
        focus_areas.append("leadership")
    if not focus_areas:
        focus_areas = ["android-core", "architecture", "performance", "leadership"]

    resume_lower = resume_text.lower()
    job_profile = {
        "target_level": level,
        "language_mode": language,
        "keywords": sorted(list(keywords(jd_text)))[:24],
        "focus_areas": focus_areas,
        "priority_signals": jd_signals,
        "english_required": jd_signals.get("english_required", False),
    }
    candidate_profile = {
        "keywords": sorted(list(keywords(resume_text)))[:24],
        "signals": {
            "contains_metrics": bool(re.search(r"\b\d+(\.\d+)?%|\b\d+ms\b|\b\d+x\b", resume_lower)),
            "contains_ownership": any(token in resume_lower for token in ["i led", "i owned", "responsible", "ownership"]),
            "contains_leadership": any(token in resume_lower for token in ["lead", "mentor", "stakeholder", "align", "priority", "conflict"]),
            "contains_architecture": any(token in resume_lower for token in ["architecture", "modular", "module", "system", "design"]),
            "contains_english_context": any(token in resume_lower for token in ["english", "global", "international"]),
        },
    }
    return job_profile, candidate_profile


def _screening_dimension(
    name: str,
    label: str,
    score: float,
    confidence: float,
    strengths: list[str],
    risks: list[str],
    missing: list[str],
    summary: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "label": label,
        "score": round(score, 2),
        "confidence": round(confidence, 2),
        "strength_evidence": sorted(set(strengths)),
        "risk_evidence": sorted(set(risks)),
        "missing_evidence": sorted(set(missing)),
        "summary": summary,
    }


def build_screening_summary(
    jd_text: str,
    resume_text: str,
    level: str,
    language: str,
    interview_plan: dict[str, Any] | None,
    job_profile: dict[str, Any] | None = None,
    candidate_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    job_profile = job_profile or build_profiles(jd_text, resume_text, level, language)[0]
    candidate_profile = candidate_profile or build_profiles(jd_text, resume_text, level, language)[1]
    jd_signals = dict(job_profile.get("priority_signals", detect_jd_priority_signals(jd_text)))
    resume_gaps = detect_resume_gap_signals(resume_text, candidate_profile, language)
    candidate_signals = dict(candidate_profile.get("signals", {}))
    job_keywords = set(job_profile.get("keywords", []))
    candidate_keywords = set(candidate_profile.get("keywords", []))
    overlap = sorted(job_keywords & candidate_keywords)
    resume_lower = resume_text.lower()

    role_alignment_score = 2.4
    if len(overlap) >= 6:
        role_alignment_score = 4.5
    elif len(overlap) >= 4:
        role_alignment_score = 4.0
    elif len(overlap) >= 2:
        role_alignment_score = 3.5
    elif overlap:
        role_alignment_score = 3.0
    role_alignment_strengths = [f"JD / 简历关键词重叠较多：{', '.join(overlap[:6])}。"] if overlap else []
    role_alignment_risks = [] if overlap else ["JD 与简历的显式关键词重叠较少，需要通过面试确认真实匹配度。"]
    role_alignment_missing = [] if len(overlap) >= 2 else ["需要通过项目案例进一步确认 JD 核心要求与实际经历是否贴合。"]

    ownership_score = 4.2 if candidate_signals.get("contains_ownership") else 2.5
    ownership_strengths = ["简历中已出现 ownership / responsible / led 等个人职责信号。"] if candidate_signals.get("contains_ownership") else []
    ownership_risks = [] if candidate_signals.get("contains_ownership") else ["简历层面对个人职责边界表达偏弱。"]
    ownership_missing = [] if candidate_signals.get("contains_ownership") else ["需要在 screening 和自我介绍环节确认候选人的个人 ownership。"]

    metrics_score = 4.1 if candidate_signals.get("contains_metrics") else 2.4
    metrics_strengths = ["简历中已出现量化结果、时延或倍数级指标信号。"] if candidate_signals.get("contains_metrics") else []
    metrics_risks = [] if candidate_signals.get("contains_metrics") else ["简历中缺少明显量化结果，后续需要重点追问指标与业务结果。"]
    metrics_missing = [] if candidate_signals.get("contains_metrics") else ["需要补齐基线、指标口径、结果变化和上线后监控表现。"]

    architecture_terms = sum(1 for token in ["architecture", "modular", "module", "system", "design", "trace", "baseline", "performance"] if token in resume_lower)
    architecture_score = 3.2
    if architecture_terms >= 4:
        architecture_score = 4.4
    elif architecture_terms >= 2:
        architecture_score = 3.8
    elif jd_signals.get("architecture_heavy") or jd_signals.get("performance_heavy"):
        architecture_score = 2.8
    architecture_strengths = ["简历中已有架构 / 模块化 / 性能相关术语，可继续深挖真实深度。"] if architecture_terms >= 2 else []
    architecture_risks = ["JD 对架构或性能要求较强，但简历中的对应深度信号有限。"] if architecture_terms < 2 and (jd_signals.get("architecture_heavy") or jd_signals.get("performance_heavy")) else []
    architecture_missing = ["需要通过 round1 / round2 确认真实实现细节、权衡与问题定位能力。"] if architecture_terms < 4 else []

    leadership_terms = sum(1 for token in ["lead", "mentor", "stakeholder", "align", "priority", "conflict", "influence"] if token in resume_lower)
    leadership_score = 3.1
    if leadership_terms >= 4:
        leadership_score = 4.3
    elif leadership_terms >= 2:
        leadership_score = 3.7
    elif level == "tl" or jd_signals.get("leadership_heavy"):
        leadership_score = 2.6
    leadership_strengths = ["简历中已出现带人、协作或影响力信号。"] if leadership_terms >= 2 else []
    leadership_risks = ["目标岗位需要更强的领导力 / 跨团队推进证据。"] if leadership_terms < 2 and (level == "tl" or jd_signals.get("leadership_heavy")) else []
    leadership_missing = ["需要在 round3 / HR 环节验证冲突处理、优先级和影响力案例。"] if leadership_terms < 4 else []

    english_terms = sum(1 for token in ["english", "global", "international"] if token in resume_lower)
    english_score = 3.8 if language == "zh" else 3.1
    if language != "zh":
        if english_terms >= 2:
            english_score = 4.2
        elif english_terms >= 1:
            english_score = 3.7
        elif candidate_signals.get("contains_english_context"):
            english_score = 3.5
        else:
            english_score = 2.9
    english_strengths = ["简历中已有英文、国际化或 global 协作背景信号。"] if english_terms or candidate_signals.get("contains_english_context") else []
    english_risks = ["目标流程默认全英文，简历中暂未出现明显英文协作信号。"] if language != "zh" and not (english_terms or candidate_signals.get("contains_english_context")) else []
    english_missing = ["需要在自我介绍和首轮面试中观察英文表达的结构化程度与稳定性。"] if language != "zh" else []

    seniority_terms = sum(1 for token in ["architecture", "ownership", "lead", "mentor", "tradeoff", "rollback", "performance", "module"] if token in resume_lower)
    seniority_score = 3.2
    if seniority_terms >= 5:
        seniority_score = 4.3
    elif seniority_terms >= 3:
        seniority_score = 3.8
    elif level in {"senior", "tl"}:
        seniority_score = 2.9
    if level == "tl" and leadership_terms < 2:
        seniority_score = min(seniority_score, 2.8)
    seniority_strengths = ["简历文本已出现较多资深 / TL 常见信号词，可进一步验证其真实性。"] if seniority_terms >= 3 else []
    seniority_risks = ["目标级别是 senior / TL，但当前文本证据对 scope 和 seniority 上限支撑还不够强。"] if seniority_terms < 3 and level in {"senior", "tl"} else []
    seniority_missing = ["需要通过架构深挖、业务复盘和影响力案例确认是否达到目标级别。"] if seniority_terms < 5 else []

    dimensions = [
        _screening_dimension(
            "role_alignment",
            "岗位匹配度",
            role_alignment_score,
            0.55 + min(0.3, len(overlap) * 0.04),
            role_alignment_strengths,
            role_alignment_risks,
            role_alignment_missing,
            "判断 JD 要求与简历显式信息是否有基本对齐。",
        ),
        _screening_dimension(
            "ownership_evidence",
            "Ownership 证据",
            ownership_score,
            0.64,
            ownership_strengths,
            ownership_risks,
            ownership_missing,
            "判断候选人是否在简历层就写出了清晰的个人职责边界。",
        ),
        _screening_dimension(
            "metrics_orientation",
            "结果与指标意识",
            metrics_score,
            0.66,
            metrics_strengths,
            metrics_risks,
            metrics_missing,
            "判断候选人是否具备结果导向和量化表达习惯。",
        ),
        _screening_dimension(
            "architecture_depth_signal",
            "架构 / 性能深度信号",
            architecture_score,
            0.58,
            architecture_strengths,
            architecture_risks,
            architecture_missing,
            "判断简历是否已经暴露出值得继续深挖的架构、性能或实现复杂度信号。",
        ),
        _screening_dimension(
            "leadership_signal",
            "领导力 / 影响力信号",
            leadership_score,
            0.56,
            leadership_strengths,
            leadership_risks,
            leadership_missing,
            "判断候选人是否具备跨团队推动、协作和影响力证据。",
        ),
        _screening_dimension(
            "english_readiness",
            "英文面试准备度",
            english_score,
            0.52 if language != "zh" else 0.4,
            english_strengths,
            english_risks,
            english_missing,
            "判断全英文或半英文沉浸式面试下的预期风险。",
        ),
        _screening_dimension(
            "seniority_scope",
            "级别与 Scope 信号",
            seniority_score,
            0.58,
            seniority_strengths,
            seniority_risks,
            seniority_missing,
            "判断当前文本证据是否足以支撑目标级别的 scope 预期。",
        ),
    ]

    overall_score = round(sum(item["score"] for item in dimensions) / len(dimensions), 2)
    overall_confidence = round(sum(item["confidence"] for item in dimensions) / len(dimensions), 2)
    critical_risks = sorted({risk for item in dimensions for risk in item["risk_evidence"]})[:6]
    top_strengths = sorted({strength for item in dimensions for strength in item["strength_evidence"]})[:6]

    if overall_score >= 3.9 and len(critical_risks) <= 1:
        overall_decision = "strong_match"
        decision_reason = "简历层信号较完整，已具备较强岗位匹配基础，后续面试重点应转向验证真实性和上限。"
    elif overall_score >= 3.3:
        overall_decision = "viable_with_risks"
        decision_reason = "整体可进入正式模拟面试，但仍有若干高优先级风险需要通过逐轮追问验证。"
    elif overall_score >= 2.7:
        overall_decision = "needs_validation"
        decision_reason = "文本层匹配度一般，建议把一面和二面重心放在 ownership、指标、架构深度和英文表达验证。"
    else:
        overall_decision = "high_risk"
        decision_reason = "当前简历层证据偏弱，若不补齐关键项，正式面试大概率会在前两轮暴露明显风险。"

    recommended_focuses: list[str] = []
    if interview_plan:
        for round_item in interview_plan.get("rounds", []):
            for focus in round_item.get("priority_focuses", []):
                focus_name = normalize_dimension_name(focus)
                if focus_name and focus_name not in recommended_focuses:
                    recommended_focuses.append(focus_name)

    return {
        "target_level": level,
        "language_mode": language,
        "overall_score": overall_score,
        "overall_confidence": overall_confidence,
        "overall_decision": overall_decision,
        "decision_reason": decision_reason,
        "keyword_overlap": overlap[:10],
        "jd_priority_signals": jd_signals,
        "resume_gap_signals": resume_gaps,
        "dimensions": dimensions,
        "recommended_focuses": recommended_focuses[:8],
        "question_bank_focus_tags": recommended_focuses[:8],
        "critical_risks": critical_risks,
        "top_strengths": top_strengths,
        "notes": [
            "这是基于 JD 与简历文本的预筛选结果，不等于最终面试结论。",
            "逐轮面试会继续验证 ownership、指标、技术深度、业务理解和英文表达等能力。",
        ],
    }


def render_screening_summary(path: Path, session_id: str, screening_summary: dict[str, Any]) -> None:
    lines = [
        f"# Screening Summary - {session_id}",
        "",
        f"- Overall decision: `{screening_summary.get('overall_decision', 'unknown')}`",
        f"- Overall score: `{screening_summary.get('overall_score', 'n/a')}` / 5",
        f"- Overall confidence: `{screening_summary.get('overall_confidence', 'n/a')}`",
        f"- Language mode: `{screening_summary.get('language_mode', 'n/a')}`",
        f"- Target level: `{screening_summary.get('target_level', 'n/a')}`",
        "",
        "## Decision Reason",
        "",
        screening_summary.get("decision_reason", ""),
        "",
        "## Critical Risks",
        "",
    ]
    risks = screening_summary.get("critical_risks", [])
    if risks:
        lines.extend([f"- {item}" for item in risks])
    else:
        lines.append("- none")
    lines.extend(["", "## Recommended Focuses", ""])
    focuses = screening_summary.get("recommended_focuses", [])
    if focuses:
        lines.extend([f"- {item}" for item in focuses])
    else:
        lines.append("- none")
    lines.extend(["", "## Dimension Scorecards", ""])
    for item in screening_summary.get("dimensions", []):
        lines.append(f"- **{item['label']}**: score={item['score']} confidence={item['confidence']}")
        lines.append(f"  - Summary: {item['summary']}")
        if item.get("strength_evidence"):
            lines.append(f"  - Strengths: {'; '.join(item['strength_evidence'])}")
        if item.get("risk_evidence"):
            lines.append(f"  - Risks: {'; '.join(item['risk_evidence'])}")
        if item.get("missing_evidence"):
            lines.append(f"  - Missing: {'; '.join(item['missing_evidence'])}")
    lines.extend(["", "## Notes", ""])
    for note in screening_summary.get("notes", []):
        lines.append(f"- {note}")
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def build_resume_prep(
    jd_text: str,
    resume_text: str,
    level: str,
    language: str,
    screening_summary: dict[str, Any],
    interview_plan: dict[str, Any] | None = None,
    job_profile: dict[str, Any] | None = None,
    candidate_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    job_profile = job_profile or build_profiles(jd_text, resume_text, level, language)[0]
    candidate_profile = candidate_profile or build_profiles(jd_text, resume_text, level, language)[1]
    interview_plan = interview_plan or {"rounds": []}
    dimensions = list(screening_summary.get("dimensions", []))
    strongest_dimensions = sorted(dimensions, key=lambda item: (-float(item.get("score", 0)), -float(item.get("confidence", 0))))[:3]
    weakest_dimensions = sorted(dimensions, key=lambda item: (float(item.get("score", 0)), float(item.get("confidence", 0))))[:3]
    candidate_signals = dict(candidate_profile.get("signals", {}))
    focus_tags = list(screening_summary.get("recommended_focuses", []))[:4]
    keyword_overlap = list(screening_summary.get("keyword_overlap", []))[:6]

    rewrite_action_map = {
        "role_alignment": "把简历项目标题、项目背景和 JD 关键词对齐，避免只写技术名词，不写业务场景。",
        "ownership_evidence": "每个重点项目至少补一条“我负责什么”的主语化表述，避免只写团队结果。",
        "metrics_orientation": "为每个重点项目补齐基线、指标口径、优化动作和最终变化结果。",
        "architecture_depth_signal": "为至少一个项目补齐架构演进、权衡取舍、问题定位和回滚复盘。",
        "leadership_signal": "补一段跨团队推进或冲突处理案例，体现影响力而不是只体现执行。",
        "english_readiness": "准备 60-90 秒英文自我介绍，并把一个核心项目用英文讲清职责、指标和 tradeoff。",
        "seniority_scope": "明确写出项目 scope、复杂度、影响范围和你在关键决策中的角色。",
    }
    round_hint_map = {
        "role_alignment": "screening",
        "ownership_evidence": "screening / intro",
        "metrics_orientation": "round1 / round2",
        "architecture_depth_signal": "round1 / round2",
        "leadership_signal": "round3 / hr",
        "english_readiness": "intro / round1",
        "seniority_scope": "round2 / round3",
    }

    rewrite_priorities: list[dict[str, Any]] = []
    for item in weakest_dimensions:
        dimension_name = str(item.get("name", ""))
        rewrite_priorities.append(
            {
                "dimension": dimension_name,
                "label": item.get("label", dimension_name),
                "score": item.get("score"),
                "risk_anchor": (item.get("risk_evidence") or item.get("missing_evidence") or ["当前维度证据偏弱。"])[0],
                "rewrite_action": rewrite_action_map.get(dimension_name, "补齐这一维度的事实、职责、结果和复盘证据。"),
                "likely_round": round_hint_map.get(dimension_name, "follow-up"),
            }
        )

    intro_story_order = [
        "当前最匹配岗位的一段 Android 主线经历",
        "一个能证明你资深度的代表项目",
        "你亲自负责的关键职责与结果指标",
        "为什么这段经历与目标 JD 贴合",
    ]
    intro_watchouts = [
        "不要只讲团队背景，要尽快落到你的职责边界。",
        "不要只说做了什么，要补上结果、指标和 tradeoff。",
    ]
    if language != "zh":
        intro_watchouts.append("先用英文说完整主干，再视需要补充中文术语。")

    self_intro_blueprint = {
        "opening_positioning": f"我是一个以 Android {level} 级别职责为目标的候选人，最近的核心优势集中在 {', '.join(focus_tags[:2]) or 'Android delivery'}。",
        "story_order": intro_story_order,
        "metric_prompt": "自我介绍里至少提前埋一个可量化结果，方便后续面试深挖。",
        "fit_statement": f"把 JD 里的关键词自然融入收尾，例如：{', '.join(keyword_overlap[:4]) or 'ownership, architecture, performance'}。",
        "watchouts": intro_watchouts,
    }

    likely_probe_map = {
        "ownership": "请明确说清这个项目里你亲自负责了什么，以及不是你负责的部分是什么。",
        "delivery_scope": "这个项目的业务目标、影响范围和你的决策边界分别是什么？",
        "android_core": "你如何证明自己不是只会背概念，而是真的处理过 Android 生命周期和状态问题？",
        "architecture": "讲一个你做过的架构取舍，为什么不是另一个更直接的方案？",
        "performance": "你的性能优化 baseline、关键指标、回归保护和上线观测分别是什么？",
        "tradeoff_reasoning": "如果今天重做一次，你还会选同一个方案吗？为什么？",
        "technical_influence": "没有职位权力时，你具体怎么推动团队改变做法？",
        "cross_team_execution": "跨团队出现冲突或目标变化时，你如何保证方案落地？",
        "business_understanding": "业务约束改变后，你最先调整方案的哪一部分？",
        "leadership": "请讲一个带节奏、做优先级或处理冲突的真实例子。",
        "motivation": "为什么你会选择这个机会，而不是一个更稳定或更熟悉的岗位？",
        "english_interview": "Please walk me through your strongest Android project in English, with ownership and metrics.",
    }
    likely_interviewer_probes = []
    for focus in focus_tags:
        prompt = likely_probe_map.get(focus)
        if prompt and prompt not in likely_interviewer_probes:
            likely_interviewer_probes.append({"focus": focus, "prompt": prompt})

    resume_rewrite_checklist = [
        "每个重点项目至少保留一条主语清晰的 ownership 句子。",
        "每个重点项目至少补一个结果指标或影响范围。",
        "至少准备一个 architecture / performance / tradeoff 深挖项目。",
        "至少准备一个跨团队推进或冲突处理案例。",
    ]
    if not candidate_signals.get("contains_metrics", False):
        resume_rewrite_checklist.append("优先补指标口径和结果变化，否则前两轮会持续被追问。")
    if language != "zh":
        resume_rewrite_checklist.append("准备英文版 60-90 秒自我介绍和一个英文项目复盘。")

    round_previews = [
        {
            "round": item.get("round", ""),
            "label": item.get("label", ""),
            "priority_focuses": list(item.get("priority_focuses", [])),
            "language_mode": item.get("language_mode", language),
        }
        for item in interview_plan.get("rounds", [])
    ]

    if screening_summary.get("overall_decision") == "strong_match":
        positioning_summary = "简历基础较好，面试前重点不是大改，而是把最强项目讲得更有证据、更有层次。"
    elif screening_summary.get("overall_decision") == "viable_with_risks":
        positioning_summary = "可以直接进入模拟面试，但建议先把薄弱维度的简历描述补强，再进入正式逐轮演练。"
    elif screening_summary.get("overall_decision") == "needs_validation":
        positioning_summary = "当前简历需要先做一次针对性补强，否则一面和二面会花很多时间在补基础证据。"
    else:
        positioning_summary = "建议先修简历和项目叙事，再做高强度模拟面试，否则早期轮次很容易因为证据不足被打断。"

    return {
        "target_level": level,
        "language_mode": language,
        "positioning_summary": positioning_summary,
        "overall_decision": screening_summary.get("overall_decision", ""),
        "strongest_dimensions": strongest_dimensions,
        "rewrite_priorities": rewrite_priorities,
        "self_intro_blueprint": self_intro_blueprint,
        "likely_interviewer_probes": likely_interviewer_probes[:6],
        "resume_rewrite_checklist": resume_rewrite_checklist[:6],
        "keyword_overlap": keyword_overlap,
        "round_previews": round_previews,
    }


def render_resume_prep(path: Path, session_id: str, resume_prep: dict[str, Any]) -> None:
    lines = [
        f"# Resume Prep Brief - {session_id}",
        "",
        f"- Overall decision: `{resume_prep.get('overall_decision', 'unknown')}`",
        f"- Target level: `{resume_prep.get('target_level', 'n/a')}`",
        f"- Language mode: `{resume_prep.get('language_mode', 'n/a')}`",
        "",
        "## Positioning Summary",
        "",
        resume_prep.get("positioning_summary", ""),
        "",
        "## Rewrite Priorities",
        "",
    ]
    for item in resume_prep.get("rewrite_priorities", []):
        lines.append(f"- **{item['label']}**: {item['rewrite_action']}")
        lines.append(f"  - Risk anchor: {item['risk_anchor']}")
        lines.append(f"  - Likely round: {item['likely_round']}")
    lines.extend(["", "## Self Introduction Blueprint", ""])
    intro = resume_prep.get("self_intro_blueprint", {})
    lines.append(f"- Opening positioning: {intro.get('opening_positioning', '')}")
    for item in intro.get("story_order", []):
        lines.append(f"- Story order: {item}")
    lines.append(f"- Metric prompt: {intro.get('metric_prompt', '')}")
    lines.append(f"- Fit statement: {intro.get('fit_statement', '')}")
    for item in intro.get("watchouts", []):
        lines.append(f"- Watchout: {item}")
    lines.extend(["", "## Likely Interviewer Probes", ""])
    for item in resume_prep.get("likely_interviewer_probes", []):
        lines.append(f"- **{item['focus']}**: {item['prompt']}")
    lines.extend(["", "## Resume Rewrite Checklist", ""])
    for item in resume_prep.get("resume_rewrite_checklist", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Round Previews", ""])
    for item in resume_prep.get("round_previews", []):
        lines.append(f"- **{item['label']}**: focus={', '.join(item.get('priority_focuses', [])) or 'n/a'} | language={item.get('language_mode', 'n/a')}")
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def build_interview_flow_summary(
    *,
    session_status: str,
    final_decision: str,
    screening_summary: dict[str, Any] | None,
    resume_prep: dict[str, Any] | None,
    question_bank_validation: dict[str, Any] | None,
    round_summaries: list[dict[str, Any]] | list[RoundSummary] | None,
    pause_reason: str = "",
) -> dict[str, Any]:
    screening_summary = screening_summary or {}
    resume_prep = resume_prep or {}
    question_bank_validation = question_bank_validation or {}
    round_list = []
    for item in round_summaries or []:
        round_list.append(item if isinstance(item, dict) else asdict(item))
    round_map = {str(item.get("round", "")): item for item in round_list}
    round_label_map = {
        "intro": "自我介绍",
        "screening": "简历筛选",
        "round1": "一面",
        "round2": "二面",
        "round3": "三面",
        "hr": "HR 面",
    }
    steps: list[dict[str, Any]] = []

    def push_step(key: str, label: str, status: str, detail: str, round_name: str = "") -> None:
        steps.append(
            {
                "key": key,
                "label": label,
                "status": status,
                "detail": detail,
                "round": round_name,
            }
        )

    push_step(
        "resume_prep",
        "面试前准备",
        "done" if resume_prep else "pending",
        str(resume_prep.get("positioning_summary", "已生成准备建议")) if resume_prep else "尚未生成简历准备建议",
    )
    push_step(
        "question_bank_validation",
        "题库校验",
        "done" if question_bank_validation.get("status") in {"valid", "valid_with_warnings"} else "blocked" if question_bank_validation.get("status") == "invalid" else "pending",
        f"状态：{question_bank_validation.get('status', 'unknown')}，题目数：{question_bank_validation.get('question_count', 0)}",
    )
    push_step(
        "screening",
        "简历筛选",
        "done" if screening_summary else "pending",
        str(screening_summary.get("decision_reason", "已完成简历预筛选")) if screening_summary else "尚未完成筛选",
    )

    blocked_round = ""
    blocked_reason = ""
    if session_status == "session_paused":
        blocked_round = "当前流程"
        blocked_reason = pause_reason or "会话已暂停"
    elif final_decision == "fail" or session_status == "session_terminated":
        for round_name in ["intro", "screening", "round1", "round2", "round3", "hr"]:
            item = round_map.get(round_name)
            if not item:
                continue
            if item.get("decision") == "reject":
                blocked_round = round_label_map.get(round_name, round_name)
                blocked_reason = str(item.get("decision_reason", "本轮未通过"))
                break
        if not blocked_round and round_map:
            last_round = next(reversed(round_map.values()))
            blocked_round = round_label_map.get(str(last_round.get("round", "")), str(last_round.get("round", "")))
            blocked_reason = str(last_round.get("decision_reason", "会话在此处停止"))

    for round_name in ["intro", "screening", "round1", "round2", "round3", "hr"]:
        item = round_map.get(round_name)
        label = round_label_map.get(round_name, round_name)
        if not item:
            status = "pending"
            detail = "尚未进入该轮"
        else:
            decision = str(item.get("decision", ""))
            if decision == "reject" or (blocked_round and label == blocked_round):
                status = "blocked"
            elif decision in {"advance", "advance_with_risk"}:
                status = "done"
            else:
                status = "current"
            detail = str(item.get("decision_reason", ""))
        push_step(f"round_{round_name}", label, status, detail, round_name)

    final_label_map = {
        "pass": "最终通过",
        "fail": "最终未通过",
        "borderline": "最终边缘",
        "paused": "流程暂停",
    }
    final_label = final_label_map.get(final_decision, "最终结论")
    final_status = "done" if final_decision == "pass" else "blocked" if final_decision == "fail" else "current" if final_decision == "paused" else "done"
    final_detail = "流程已完整结束" if final_decision == "pass" else blocked_reason or "等待进一步处理"
    push_step("final", final_label, final_status, final_detail)

    if final_decision == "pass":
        blocked_message = "当前未卡住，面试流程已全部完成。"
    elif blocked_round:
        blocked_message = f"卡在「{blocked_round}」：{blocked_reason}"
    elif session_status == "session_paused":
        blocked_message = f"当前暂停在：{pause_reason or '中途暂停'}"
    else:
        blocked_message = "暂无明确卡点。"

    return {
        "steps": steps,
        "blocked_message": blocked_message,
        "current_step": next((item for item in steps if item["status"] == "current"), steps[-1] if steps else {}),
        "blocked_round": blocked_round,
        "blocked_reason": blocked_reason,
    }


def build_consistency_summary(results: list[QuestionResult], screening_summary: dict[str, Any] | None = None) -> dict[str, Any]:
    screening_summary = screening_summary or {}
    categories = [
        {
            "name": "ownership",
            "label": "Ownership 一致性",
            "positive_tokens": ["ownership", "职责", "responsible", "led", "owned", "个人贡献"],
            "risk_tokens": ["职责边界", "团队表述较多", "ownership 证据偏弱", "个人职责边界"],
        },
        {
            "name": "metrics",
            "label": "指标一致性",
            "positive_tokens": ["指标", "量化", "latency", "startup", "anr", "oom", "%", "ms", "x"],
            "risk_tokens": ["缺少量化结果", "缺少可观测指标", "指标口径", "关键指标"],
        },
        {
            "name": "architecture",
            "label": "架构一致性",
            "positive_tokens": ["architecture", "modular", "module", "design", "tradeoff", "rollback", "performance", "trace"],
            "risk_tokens": ["深度能力未达到", "缺少明确的方案权衡说明", "缺少失败、问题或回滚相关说明"],
        },
        {
            "name": "leadership",
            "label": "领导力一致性",
            "positive_tokens": ["stakeholder", "align", "priority", "mentor", "lead", "cross-team", "影响力"],
            "risk_tokens": ["领导力", "跨团队推进", "影响力", "冲突处理"],
        },
        {
            "name": "english",
            "label": "英文表达一致性",
            "positive_tokens": ["english", "global", "international"],
            "risk_tokens": ["英文表达", "英文协作", "全英文"],
        },
    ]

    def has_token(items: list[str], tokens: list[str]) -> bool:
        lowered_items = [item.lower() for item in items]
        return any(any(token.lower() in item for token in tokens) for item in lowered_items)

    signal_profiles: list[dict[str, Any]] = []
    adjustments = 0.0
    hard_flags: list[str] = []
    for category in categories:
        strengths = [item for result in results for item in result.strength_evidence if has_token([item], category["positive_tokens"])]
        risks = [item for result in results for item in result.risk_evidence if has_token([item], category["risk_tokens"])]
        missing = [item for result in results for item in result.missing_evidence if has_token([item], category["risk_tokens"])]
        if strengths and risks:
            status = "mixed"
            adjustment = -0.08
        elif strengths:
            status = "consistent_strength"
            adjustment = 0.0
        elif risks or missing:
            status = "consistent_risk"
            adjustment = -0.12
        else:
            status = "insufficient_data"
            adjustment = -0.04
        adjustments += adjustment
        if status == "mixed" and len(strengths) >= 2 and len(risks) >= 2:
            hard_flags.append(f"{category['label']} 同时存在强信号和风险信号，需要人工复核。")
        signal_profiles.append(
            {
                "name": category["name"],
                "label": category["label"],
                "status": status,
                "score_adjustment": round(adjustment, 2),
                "strength_evidence": sorted(set(strengths))[:4],
                "risk_evidence": sorted(set(risks))[:4],
                "missing_evidence": sorted(set(missing))[:4],
            }
        )

    if adjustments <= -0.28:
        overall = "low"
    elif adjustments <= -0.12:
        overall = "medium"
    else:
        overall = "high"

    round_decisions = {result.round: result.decision_result for result in results}
    return {
        "overall_consistency": overall,
        "score_adjustment": round(adjustments, 2),
        "signals": signal_profiles,
        "round_decisions": round_decisions,
        "screening_alignment": screening_summary.get("overall_decision", ""),
        "hard_review_flags": hard_flags,
    }


def render_pass_summary(path: Path, session_id: str, session_data: dict[str, Any], score_data: dict[str, Any]) -> None:
    lines = [
        f"# Interview Pass Summary - {session_id}",
        "",
        f"- Final decision: `{score_data['final_decision']}`",
        f"- Session status: `{session_data['session_status']}`",
        f"- Screening decision: `{session_data.get('screening_summary', {}).get('overall_decision', 'n/a')}`",
        f"- Overall consistency: `{score_data.get('consistency_summary', {}).get('overall_consistency', 'n/a')}`",
        "",
        "## Best Strengths",
        "",
    ]
    for item in score_data.get("best_strengths", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Main Gaps to Keep Improving", ""])
    for item in score_data.get("main_gaps", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Cross-question Consistency", ""])
    for item in score_data.get("consistency_summary", {}).get("signals", []):
        lines.append(f"- **{item['label']}**: {item['status']} (adjustment {item['score_adjustment']})")
    lines.extend(["", "## Next Step", ""])
    lines.append("Proceed to the next interview stage or use the listed gaps as a preparation checklist.")
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def round_plan(results: list[QuestionResult]) -> list[dict[str, Any]]:
    return [
        {
            "round": result.round,
            "label": ROUND_LABELS.get(result.round, result.round),
            "question_id": result.id,
            "target_competency": result.title,
            "decision_result": result.decision_result,
            "persona": result.persona,
            "focus": result.round_focus,
        }
        for result in results
    ]


def build_round_summaries(
    results: list[QuestionResult],
    level: str = "senior",
    interview_plan: dict[str, Any] | None = None,
) -> list[RoundSummary]:
    grouped: dict[str, list[QuestionResult]] = defaultdict(list)
    for result in results:
        grouped[result.round].append(result)

    summaries: list[RoundSummary] = []
    round_order = ["intro", "screening", "round1", "round2", "round3", "hr"]
    for round_name in round_order:
        items = grouped.get(round_name)
        if not items:
            continue
        avg_score = round(sum(item.score for item in items) / len(items), 2)
        avg_conf = round(sum(item.confidence for item in items) / len(items), 2)
        strengths = sorted({e for item in items for e in item.strength_evidence})
        risks = sorted({e for item in items for e in item.risk_evidence})
        missing = sorted({e for item in items for e in item.missing_evidence})
        terminated = any(item.decision_result == "terminate_round_fail" for item in items)
        policy = threshold_policy(level, round_name)
        planned_focuses = planned_focuses_for_round(interview_plan, round_name)
        critical_focuses = critical_focuses_for_round(policy, planned_focuses)
        failed_focuses: list[str] = []
        for focus in critical_focuses:
            focus_scores = [item.score for item in items if focus in question_focuses(item)]
            if focus_scores and (sum(focus_scores) / len(focus_scores)) < policy["critical_min_score"]:
                failed_focuses.append(focus)
        if terminated or avg_score <= 2 or failed_focuses:
            decision = "reject"
            if failed_focuses:
                reason = f"本轮关键能力未达阈值：{', '.join(failed_focuses)}。"
            else:
                reason = "本轮关键证据不足，已达到提前淘汰或强风险阈值。"
        elif avg_score >= max(4.0, policy["min_round_score"]) and avg_conf >= max(0.72, policy["min_confidence"]) and not missing:
            decision = "advance"
            reason = "本轮已收集到较充分的正向证据，可进入下一轮。"
        elif avg_score >= policy["min_round_score"] and avg_conf >= policy["min_confidence"]:
            decision = "advance_with_risk"
            reason = "本轮达到基本通过阈值，但仍保留若干需要在后续轮次继续验证的风险。"
        else:
            decision = "borderline"
            reason = "本轮分数或置信度尚未达到目标阈值，建议继续补充验证。"
        summaries.append(
            RoundSummary(
                round=round_name,
                label=ROUND_LABELS.get(round_name, round_name),
                persona=items[0].persona,
                focus=items[0].round_focus,
                score=avg_score,
                confidence=avg_conf,
                decision=decision,
                decision_reason=reason,
                strengths=strengths,
                risks=risks,
                missing=missing,
                question_ids=[item.id for item in items],
                terminated=terminated,
                threshold_summary={
                    "min_round_score": policy["min_round_score"],
                    "min_confidence": policy["min_confidence"],
                    "critical_focuses": critical_focuses,
                    "critical_min_score": policy["critical_min_score"],
                    "failed_focuses": failed_focuses,
                },
            )
        )
    return summaries


def build_round_deliberations(
    results: list[QuestionResult],
    level: str = "senior",
    interview_plan: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    summaries = build_round_summaries(results, level, interview_plan)
    scorecards = scorecard_map(build_round_scorecards(results, summaries, interview_plan, level))
    deliberations: list[dict[str, Any]] = []
    for summary in summaries:
        scorecard = scorecards.get(summary.round, {})
        critical_focuses = list(scorecard.get("critical_focuses", []))
        competency_checks = list(scorecard.get("competency_checks", []))
        failed_focuses = [item["focus"] for item in competency_checks if item.get("verdict") == "fail"]
        missing_focuses = [item["focus"] for item in competency_checks if item.get("verdict") == "missing"]
        if summary.decision == "reject":
            next_action = "stop_session"
            review_mode = "reject_review"
            panel_reason = "The panel considers the round too weak to justify continuing without extra evidence."
        elif summary.decision == "advance_with_risk":
            next_action = "continue_with_targeted_probe"
            review_mode = "risk_review"
            panel_reason = "The panel agrees to continue, but wants targeted probing on the remaining risk areas."
        elif summary.decision == "advance":
            next_action = "advance_to_next_round"
            review_mode = "advance_review"
            panel_reason = "The panel sees enough evidence to move forward cleanly."
        else:
            next_action = "seek_more_evidence"
            review_mode = "borderline_review"
            panel_reason = "The panel is not confident enough yet and would keep pressure on the current theme."

        review_notes: list[str] = []
        if critical_focuses:
            review_notes.append(f"Critical focuses: {', '.join(critical_focuses)}")
        if failed_focuses:
            review_notes.append(f"Failed focuses: {', '.join(failed_focuses)}")
        if missing_focuses:
            review_notes.append(f"Missing focuses: {', '.join(missing_focuses)}")
        if summary.strengths:
            review_notes.append(f"Strength anchors: {', '.join(summary.strengths[:3])}")
        if summary.risks:
            review_notes.append(f"Risk anchors: {', '.join(summary.risks[:3])}")

        deliberations.append(
            {
                "round": summary.round,
                "label": summary.label,
                "persona": summary.persona,
                "score": summary.score,
                "confidence": summary.confidence,
                "decision": summary.decision,
                "decision_reason": summary.decision_reason,
                "review_mode": review_mode,
                "next_action": next_action,
                "panel_reason": panel_reason,
                "critical_focuses": critical_focuses,
                "failed_focuses": failed_focuses,
                "missing_focuses": missing_focuses,
                "review_notes": review_notes[:5],
            }
        )
    return deliberations


def _aggregate_named_dimensions(results: list[QuestionResult], extractor: callable) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for result in results:
        names = extractor(result)
        for name in names:
            bucket = buckets.setdefault(
                name,
                {
                    "name": name,
                    "scores": [],
                    "confidences": [],
                    "strength_evidence": set(),
                    "risk_evidence": set(),
                    "missing_evidence": set(),
                    "question_ids": [],
                },
            )
            bucket["scores"].append(result.score)
            bucket["confidences"].append(result.confidence)
            bucket["strength_evidence"].update(result.strength_evidence)
            bucket["risk_evidence"].update(result.risk_evidence)
            bucket["missing_evidence"].update(result.missing_evidence)
            bucket["question_ids"].append(result.id)

    payload: list[dict[str, Any]] = []
    for name in sorted(buckets):
        bucket = buckets[name]
        payload.append(
            {
                "name": name,
                "score": round(sum(bucket["scores"]) / len(bucket["scores"]), 2),
                "confidence": round(sum(bucket["confidences"]) / len(bucket["confidences"]), 2),
                "strength_evidence": sorted(bucket["strength_evidence"]),
                "risk_evidence": sorted(bucket["risk_evidence"]),
                "missing_evidence": sorted(bucket["missing_evidence"]),
                "question_ids": bucket["question_ids"],
            }
        )
    return payload


def build_sub_competencies(results: list[QuestionResult]) -> list[dict[str, Any]]:
    return _aggregate_named_dimensions(
        results,
        lambda result: result.competencies or ([result.direction] if result.direction else []),
    )


def build_competency_families(results: list[QuestionResult]) -> list[dict[str, Any]]:
    def family_names(result: QuestionResult) -> list[str]:
        raw = result.competencies or ([result.direction] if result.direction else [])
        families = [COMPETENCY_FAMILY_MAP.get(name, name) for name in raw]
        return sorted(set(families))

    return _aggregate_named_dimensions(results, family_names)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def render_transcript(
    path: Path,
    session_id: str,
    results: list[QuestionResult],
    round_summaries: list[RoundSummary] | None = None,
    round_deliberations: list[dict[str, Any]] | None = None,
    turn_events: list[TurnEvent] | list[dict[str, Any]] | None = None,
) -> None:
    lines = [f"# Interview Transcript - {session_id}", ""]
    timeline_records = build_timeline_records(turn_events, results)
    if round_summaries:
        lines.append("## Round Summaries")
        lines.append("")
        for summary in round_summaries:
            lines.append(f"- **{summary.label}**: {summary.decision} | score {summary.score} | confidence {summary.confidence}")
            lines.append(f"  - Persona: {summary.persona}")
            lines.append(f"  - Reason: {summary.decision_reason}")
            if summary.threshold_summary:
                lines.append(f"  - Threshold: min_score={summary.threshold_summary.get('min_round_score')} min_confidence={summary.threshold_summary.get('min_confidence')}")
                if summary.threshold_summary.get("failed_focuses"):
                    lines.append(f"  - Failed focuses: {', '.join(summary.threshold_summary['failed_focuses'])}")
        lines.append("")
    if round_deliberations:
        lines.append("## Round Deliberations")
        lines.append("")
        for item in round_deliberations:
            lines.append(f"- **{item['label']}**: {item['review_mode']} | next={item['next_action']}")
            lines.append(f"  - Reason: {item['panel_reason']}")
            if item.get("review_notes"):
                lines.append(f"  - Notes: {'; '.join(item['review_notes'])}")
        lines.append("")

    grouped: dict[str, list[QuestionResult]] = defaultdict(list)
    for result in sorted(results, key=lambda item: (round_sort_index(item.round), item.turn_index, item.id)):
        grouped[result.round].append(result)

    for round_name in ROUND_SEQUENCE:
        round_results = grouped.get(round_name, [])
        if not round_results:
            continue
        lines.append(f"## {ROUND_LABELS.get(round_name, round_name)}")
        lines.append("")
        for result in round_results:
            lines.append(f"### {result.title}")
            lines.append("")
            lines.append(f"- Persona: {result.persona}")
            lines.append(f"- Decision Result: {result.decision_result}")
            lines.append(f"- Decision Reason: {result.decision_reason}")
            lines.append(f"- Score: {result.score} / 5")
            lines.append(f"- Confidence: {result.confidence}")
            lines.append("")
            lines.append(f"**Question**: {result.question}")
            lines.append("")
            lines.append(f"**Answer**: {result.answer}")
            lines.append("")
            for idx, follow_up in enumerate(result.follow_up_chain, start=1):
                lines.append(f"**Follow-up {idx}**: {follow_up['question']}")
                lines.append("")
                lines.append(f"**Candidate**: {follow_up['answer'] or '[no follow-up answer]'}")
                lines.append("")
            if result.strength_evidence:
                lines.append("**Strength Evidence**:")
                for item in result.strength_evidence:
                    lines.append(f"- {item}")
                lines.append("")
            if result.risk_evidence:
                lines.append("**Risk Evidence**:")
                for item in result.risk_evidence:
                    lines.append(f"- {item}")
                lines.append("")
            if result.missing_evidence:
                lines.append("**Missing Evidence**:")
                for item in result.missing_evidence:
                    lines.append(f"- {item}")
                lines.append("")

    if timeline_records:
        lines.append("## Chronological Turn Log")
        lines.append("")
        for event in timeline_records:
            lines.append(
                f"- {event['display_turn_index']} | {ROUND_LABELS.get(event['round'], event['round'])} | {stage_label(event['stage'])} | {event['group_label']} | decision={event['decision_result'] or 'pending'}"
            )
            if event.get("parent_display"):
                lines.append(f"  - Parent: {event['parent_display']}")
            if event.get("prompt"):
                lines.append(f"  - Prompt: {event['prompt']}")
            if event.get("response"):
                lines.append(f"  - Response: {event['response']}")
            if event.get("notes"):
                lines.append(f"  - Notes: {', '.join(event['notes'])}")
        lines.append("")
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def render_report(path: Path, session_data: dict[str, Any], score_data: dict[str, Any]) -> None:
    def zh_decision(value: Any) -> str:
        mapping = {
            "pass": "通过",
            "fail": "未通过",
            "borderline": "边缘待定",
            "paused": "已暂停",
            "completed": "已完成",
            "advance": "进入下一轮",
            "advance_with_risk": "进入下一轮（带风险）",
            "reject": "终止淘汰",
            "needs_validation": "待进一步核验",
            "strong_yes": "强烈推荐",
            "yes": "推荐",
            "mixed": "意见分化",
            "no": "不推荐",
            "continue_with_targeted_probe": "定向追问后继续推进",
        }
        text = str(value or "").strip()
        return mapping.get(text, text or "未知")

    def zh_status(value: Any) -> str:
        mapping = {
            "completed": "已完成",
            "session_paused": "已暂停",
            "session_terminated": "已终止",
            "planning": "筹备中",
            "reporting": "报告生成中",
            "intake": "信息收集中",
            "valid": "通过",
            "valid_with_warnings": "通过（有警告）",
            "invalid": "未通过",
            "unknown": "未知",
            "high": "高",
            "medium": "中",
            "low": "低",
            "strong": "强",
            "moderate": "中等",
            "weak": "弱",
            "stable": "稳定",
            "mixed": "波动",
            "inconsistent": "不一致",
            "none": "无",
        }
        text = str(value or "").strip()
        return mapping.get(text, text or "未知")

    def zh_bool(value: Any) -> str:
        return "是" if bool(value) else "否"

    def zh_mode(value: Any) -> str:
        mapping = {
            "simulate": "模拟面试",
        }
        text = str(value or "").strip()
        return mapping.get(text, text or "未知")

    def zh_language(value: Any) -> str:
        mapping = {
            "en": "全英文沉浸式",
            "zh": "中文",
            "mixed": "中英混合",
        }
        text = str(value or "").strip()
        return mapping.get(text, text or "未知")

    def zh_review_mode(value: Any) -> str:
        mapping = {
            "reject_review": "淘汰评审",
            "risk_review": "风险评审",
            "advance_review": "晋级评审",
            "borderline_review": "边缘复核",
        }
        text = str(value or "").strip()
        return mapping.get(text, text or "未知")

    def zh_next_action(value: Any) -> str:
        mapping = {
            "stop_session": "终止流程",
            "continue_with_targeted_probe": "带着针对性追问继续",
            "advance_to_next_round": "进入下一轮",
            "seek_more_evidence": "继续补证据",
        }
        text = str(value or "").strip()
        return mapping.get(text, text or "未知")

    def zh_result_action(value: Any) -> str:
        mapping = {
            "advance": "继续推进",
            "advance_with_risk": "推进但保留风险",
            "terminate_round_fail": "本轮终止",
            "hold": "暂缓观察",
            "probe_more": "继续追问",
            "advance_same_round": "同轮继续推进",
            "follow_up_same_topic": "围绕同主题继续追问",
            "increase_difficulty": "提高后续难度",
            "complete_round_pass": "本轮通过并进入下一轮",
            "switch_topic": "切换考察主题",
        }
        text = str(value or "").strip()
        return mapping.get(text, text or "未知")

    def zh_round_verdict(value: Any) -> str:
        mapping = {
            "pass": "本轮达标",
            "risk": "本轮带风险通过",
            "fail": "本轮未达标",
        }
        text = str(value or "").strip()
        return mapping.get(text, text or "未知")

    def zh_competency_verdict(value: Any) -> str:
        mapping = {
            "pass": "达标",
            "fail": "未达标",
            "missing": "证据不足",
        }
        text = str(value or "").strip()
        return mapping.get(text, text or "未知")

    def zh_round_label(value: Any) -> str:
        mapping = {
            "intro": "自我介绍",
            "screening": "简历筛选",
            "round1": "一面",
            "round2": "二面",
            "round3": "三面",
            "hr": "HR 面",
        }
        text = str(value or "").strip()
        return mapping.get(text, text or "未知轮次")

    def zh_question_alignment(value: Any) -> str:
        mapping = {
            "strong_match": "高度匹配",
            "partial_match": "部分匹配",
            "risk_match": "存在偏差风险",
            "no_match": "未匹配",
        }
        text = str(value or "").strip()
        return mapping.get(text, text or "未知")

    def zh_focus_name(value: Any) -> str:
        mapping = {
            "communication": "表达沟通",
            "project_authenticity": "项目真实性",
            "english_interview": "英文面试表达",
            "ownership": "职责归属",
            "delivery_scope": "交付范围",
            "resume_authenticity": "简历真实性",
            "implementation_detail": "实现细节",
            "android_core": "Android 核心能力",
            "problem_solving": "问题分析与解决",
            "tradeoff_reasoning": "方案权衡",
            "architecture": "架构设计",
            "performance": "性能优化",
            "business_understanding": "业务理解",
            "technical_influence": "技术影响力",
            "cross_team_execution": "跨团队推进",
            "leadership": "领导力",
            "motivation": "求职动机",
            "conflict_handling": "冲突处理",
            "stability": "稳定性",
            "technical_depth": "技术深度",
            "engineering_execution": "工程执行",
            "architecture_and_system_thinking": "架构与系统思维",
        }
        text = str(value or "").strip()
        return mapping.get(text, text or "未知")

    def zh_focus_list(values: Any) -> str:
        if not values:
            return "无"
        if isinstance(values, str):
            return zh_focus_name(values)
        return "、".join(zh_focus_name(item) for item in values)

    def zh_internal_text(value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        for english, chinese in {
            "Self Introduction": "自我介绍",
            "Screening": "简历筛选",
            "Round 1": "一面",
            "Round 2": "二面",
            "Round 3": "三面",
            "HR Interview": "HR 面",
        }.items():
            text = text.replace(english, chinese)
        if text == "The panel agrees to continue, but wants targeted probing on the remaining risk areas.":
            return "评审意见为继续推进，但要求在后续轮次针对剩余风险点进行定向深挖。"
        if text.startswith("The previous round, ") and "still left risk around the remaining risk areas." in text:
            round_name = text[len("The previous round, ") :].split(",", 1)[0].strip()
            return f"上一轮「{round_name}」仍遗留若干风险点，因此本轮会带着这些风险继续追问，而不会视作重新开始。"
        if text.startswith("The previous round, ") and "still left risk around " in text:
            round_name = text[len("The previous round, ") :].split(",", 1)[0].strip()
            risk_area = text.split("still left risk around ", 1)[1].split(".", 1)[0].strip()
            return f"上一轮「{round_name}」在「{zh_focus_name(risk_area)}」上仍存在风险，因此本轮会延续这一压力继续深挖。"
        if text.startswith("The previous round, ") and "collected enough evidence cleanly." in text:
            round_name = text[len("The previous round, ") :].split(",", 1)[0].strip()
            return f"上一轮「{round_name}」已经收集到较完整且干净的证据，因此本轮会抬高要求，进入下一层验证。"
        if text == "Round evidence meets the configured threshold.":
            return "本轮证据已达到预设阈值。"
        replacements = {
            "Critical focuses: ": "关键考察点：",
            "Missing focuses: ": "缺失考察点：",
            "Strength anchors: ": "优势锚点：",
            "Risk anchors: ": "风险锚点：",
            "Failed focuses: ": "未达标考察点：",
            "score=": "分数=",
            "confidence=": "置信度=",
            "missing=": "缺失=",
            "risk=": "风险=",
        }
        for source, target in replacements.items():
            if text.startswith(source):
                suffix = text[len(source) :]
                if source.endswith("focuses: "):
                    return target + zh_focus_list([item.strip() for item in suffix.split(",") if item.strip()])
                return target + suffix
        for source, target in {
            "score=": "分数=",
            "confidence=": "置信度=",
            "missing=": "缺失=",
            "risk=": "风险=",
        }.items():
            text = text.replace(source, target)
        for raw_focus in [
            "communication",
            "project_authenticity",
            "english_interview",
            "ownership",
            "delivery_scope",
            "resume_authenticity",
            "implementation_detail",
            "android_core",
            "problem_solving",
            "tradeoff_reasoning",
            "architecture_and_system_thinking",
            "architecture",
            "performance",
            "business_understanding",
            "technical_influence",
            "cross_team_execution",
            "leadership",
            "motivation",
            "conflict_handling",
            "stability",
            "technical_depth",
            "engineering_execution",
        ]:
            text = text.replace(raw_focus, zh_focus_name(raw_focus))
        return text

    def evidence_summary(item: dict[str, Any]) -> str:
        parts: list[str] = []
        strengths = item.get("strength_evidence") or []
        risks = item.get("risk_evidence") or []
        missing = item.get("missing_evidence") or []
        if strengths:
            parts.append("优势证据：" + "；".join(str(x) for x in strengths))
        if risks:
            parts.append("风险证据：" + "；".join(str(x) for x in risks))
        if missing:
            parts.append("缺失证据：" + "；".join(str(x) for x in missing))
        return " ".join(parts) if parts else "无补充说明"

    def zh_final_summary_text() -> str:
        decision = str(score_data.get("final_decision", "")).strip()
        pause_reason = str(session_data.get("pause_reason", "")).strip()
        hard_fail_flags = score_data.get("hard_fail_flags") or []
        round_summaries = session_data.get("round_summaries") or []
        if decision == "paused":
            return pause_reason or "本次面试流程尚未结束，可基于当前检查点继续恢复。"
        if decision == "aborted":
            return "候选人在收集到足够证据之前主动结束了流程。"
        if decision == "pass":
            return "候选人在关键轮次中提供了足够的有效证据，当前目标级别下可判定为通过。"
        if hard_fail_flags:
            return f"本次流程触发了明确的高风险信号：{hard_fail_flags[0]}"
        if any(str(item.get("decision", "")).strip() == "advance_with_risk" for item in round_summaries):
            return "候选人存在一定匹配度，但仍有若干关键能力需要进一步补证和核验。"
        return "本次收集到的证据尚不足以支撑明确通过结论。"

    ordered_questions = sorted(
        list(score_data.get("questions", []) or []),
        key=lambda item: (
            round_sort_index(str(item.get("round", ""))),
            int(item.get("turn_index", 0) or 0),
            str(item.get("id", "")),
        ),
    )
    ordered_turn_events = sorted(
        list(session_data.get("turn_events", []) or []),
        key=lambda item: int(item.get("turn_index", 0) or 0),
    )
    timeline_records = build_timeline_records(ordered_turn_events, ordered_questions)
    round_summary_map = {str(item.get("round", "")): item for item in session_data.get("round_summaries", []) or []}
    round_deliberation_map = {str(item.get("round", "")): item for item in session_data.get("round_deliberations", []) or []}

    phase_records: list[dict[str, Any]] = []
    for round_name in ROUND_SEQUENCE:
        round_questions = [item for item in ordered_questions if str(item.get("round", "")) == round_name]
        round_events = [item for item in ordered_turn_events if str(item.get("round", "")) == round_name]
        round_summary = round_summary_map.get(round_name, {})
        round_deliberation = round_deliberation_map.get(round_name, {})
        if not round_questions and not round_events and not round_summary:
            continue
        key_events = [
            item
            for item in round_events
            if str(item.get("stage", "")) in {"intro", "round_transition", "handoff_route", "summary", "deliberation", "hold", "advance", "reject", "adaptive_route", "switch_topic"}
        ]
        phase_records.append(
            {
                "round": round_name,
                "label": ROUND_LABELS.get(round_name, round_name),
                "summary": round_summary,
                "deliberation": round_deliberation,
                "questions": round_questions,
                "events": key_events,
                "question_count": len(round_questions),
                "event_count": len(round_events),
                "status": (
                    "blocked"
                    if str(round_summary.get("decision", "")) == "reject"
                    else "done"
                    if str(round_summary.get("decision", "")) in {"advance", "advance_with_risk"}
                    else "current"
                    if round_summary
                    else "pending"
                ),
            }
        )

    main_question_events = [item for item in ordered_turn_events if str(item.get("stage", "")) == "questioning"]
    follow_up_events = [item for item in ordered_turn_events if str(item.get("stage", "")) in {"follow_up", "challenge"}]
    report_completeness = {
        "result_question_count": len(ordered_questions),
        "main_question_event_count": len(main_question_events),
        "follow_up_event_count": len(follow_up_events),
        "timeline_follow_up_count": len([item for item in timeline_records if str(item.get("stage", "")) in FOLLOW_UP_STAGES]),
        "coverage_status": "complete" if len(ordered_questions) == len(main_question_events) else "partial",
        "coverage_message": (
            "结果题目数与主问题事件数一致，数据层没有丢题，之前主要是报告展示方式没有把完整流程按阶段展开。"
            if len(ordered_questions) == len(main_question_events)
            else "结果题目数与主问题事件数不一致，说明在渲染前的数据归集阶段仍存在需要继续排查的缺口。"
        ),
    }

    template = Template(
        """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>Android 面试报告 - {{ session.session_id }}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", sans-serif; margin: 2rem auto; max-width: 1180px; line-height: 1.7; color: #17202a; background: linear-gradient(180deg, #f3f7fb 0%, #eef5f2 100%); }
    h1, h2, h3 { color: #0f2a43; }
    .badge { display: inline-block; padding: 0.24rem 0.62rem; border-radius: 999px; background: #e8f1fb; margin-right: 0.45rem; margin-bottom: 0.35rem; }
    .pass { color: #137333; }
    .fail { color: #b42318; }
    .neutral { color: #175cd3; }
    .layout { display: grid; gap: 1rem; }
    .card { border: 1px solid #d9e2ec; border-radius: 16px; padding: 1rem 1.1rem; background: rgba(255, 255, 255, 0.96); box-shadow: 0 10px 26px rgba(15, 42, 67, 0.05); }
    ul { padding-left: 1.2rem; }
    code { background: #f5f7fa; padding: 0.1rem 0.25rem; border-radius: 4px; }
    .two-col { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; }
    table { width: 100%; border-collapse: collapse; }
    th, td { text-align: left; padding: 0.55rem; border-bottom: 1px solid #e5edf5; vertical-align: top; }
    .hero { display: grid; gap: 0.8rem; }
    .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 0.8rem; }
    .summary-tile { border-radius: 14px; padding: 0.85rem 0.9rem; background: linear-gradient(135deg, #f8fbff 0%, #edf6ef 100%); border: 1px solid #d6e6dd; }
    .summary-tile strong { display: block; color: #0f2a43; margin-bottom: 0.25rem; }
    .flow-banner { padding: 0.9rem 1rem; border-radius: 14px; background: linear-gradient(135deg, #fff5e8 0%, #f3fbff 100%); border: 1px solid #f0d8ab; }
    .flow-rail { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 0.75rem; margin-top: 1rem; }
    .flow-step-card { border-radius: 14px; padding: 0.85rem 0.9rem; border: 1px solid #d9e2ec; background: #fdfefe; min-height: 88px; }
    .flow-step-card.done { background: linear-gradient(135deg, #edf9f0 0%, #f8fffb 100%); border-color: #b7dfc2; }
    .flow-step-card.current { background: linear-gradient(135deg, #edf4ff 0%, #f9fbff 100%); border-color: #b9d1ff; }
    .flow-step-card.blocked { background: linear-gradient(135deg, #fff1ef 0%, #fff9f8 100%); border-color: #f0b7b1; }
    .flow-step-card.pending { background: linear-gradient(135deg, #f5f7fa 0%, #fbfcfd 100%); border-color: #d7e1ea; }
    .flow-step-card strong { display: block; margin-bottom: 0.35rem; }
    .timeline { display: grid; gap: 0.9rem; position: relative; margin-top: 1rem; }
    .timeline-item { position: relative; padding: 0.2rem 0 0.2rem 1.8rem; }
    .timeline-item::before { content: ""; position: absolute; left: 0.42rem; top: 0.1rem; bottom: -0.9rem; width: 2px; background: #d7e4ef; }
    .timeline-item:last-child::before { bottom: 0.8rem; }
    .timeline-dot { position: absolute; left: 0; top: 0.2rem; width: 0.88rem; height: 0.88rem; border-radius: 999px; border: 3px solid #fff; box-shadow: 0 0 0 1px rgba(15, 42, 67, 0.08); }
    .timeline-item.done .timeline-dot { background: #137333; }
    .timeline-item.current .timeline-dot { background: #175cd3; }
    .timeline-item.blocked .timeline-dot { background: #b42318; }
    .timeline-item.pending .timeline-dot { background: #9aa5b1; }
    .timeline-step { display: flex; gap: 0.6rem; align-items: center; flex-wrap: wrap; }
    .chip { display: inline-block; border-radius: 999px; padding: 0.12rem 0.55rem; font-size: 0.84rem; }
    .chip.done { background: #e6f4ea; color: #137333; }
    .chip.current { background: #e8f1fb; color: #175cd3; }
    .chip.blocked { background: #fdecea; color: #b42318; }
    .chip.pending { background: #eef2f6; color: #52606d; }
    .muted { color: #52606d; }
    .phase-grid { display: grid; gap: 1rem; }
    .phase-stage { border-radius: 18px; padding: 1rem 1.05rem; background: linear-gradient(180deg, #ffffff 0%, #f9fbfc 100%); border: 1px solid #dce7f1; }
    .phase-stage header { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; flex-wrap: wrap; margin-bottom: 0.8rem; }
    .phase-stage h3 { margin: 0; }
    .phase-meta { display: flex; gap: 0.4rem; flex-wrap: wrap; }
    .kpi-pill { display: inline-block; border-radius: 999px; padding: 0.18rem 0.58rem; background: #f2f7fb; color: #0f2a43; font-size: 0.84rem; }
    .qa-card { border-radius: 14px; border: 1px solid #e3ebf3; background: #fff; padding: 0.95rem 1rem; margin-top: 0.85rem; }
    .qa-card h4 { margin: 0 0 0.55rem 0; color: #12344d; }
    .stage-events { margin-top: 0.7rem; }
    .stage-events ul { margin: 0.35rem 0 0 0; }
    .note-box { border-radius: 14px; border: 1px solid #d9e7f5; background: linear-gradient(135deg, #f8fbff 0%, #ffffff 100%); padding: 0.9rem 1rem; }
    .compact-table th, .compact-table td { padding: 0.45rem 0.5rem; font-size: 0.94rem; }
  </style>
</head>
<body>
  <h1>Android 面试报告</h1>
  <p>
    <span class="badge">会话 {{ session.session_id }}</span>
    <span class="badge">结论 {{ zh_decision(score.final_decision) }}</span>
    <span class="badge">模式 {{ zh_mode(session.mode) }}</span>
    <span class="badge">语言 {{ zh_language(session.input_config.language) }}</span>
  </p>

  <div class="layout">
    <section class="card">
      <div class="hero">
      <h2 class="{{ 'pass' if score.final_decision == 'pass' else 'neutral' if score.final_decision in ['paused', 'borderline'] else 'fail' }}">最终结论：{{ zh_decision(score.final_decision) }}</h2>
      <p>{{ zh_final_summary }}</p>
      <div class="summary-grid">
        <div class="summary-tile">
          <strong>最终决策</strong>
          <span>{{ zh_decision(score.final_decision) }}</span>
        </div>
        <div class="summary-tile">
          <strong>题目总数</strong>
          <span>{{ score.question_count }}</span>
        </div>
        <div class="summary-tile">
          <strong>会话状态</strong>
          <span>{{ zh_status(session.session_status) }}</span>
        </div>
        <div class="summary-tile">
          <strong>整体一致性</strong>
          <span>{{ zh_status(score.consistency_summary.overall_consistency) if score.consistency_summary else '无' }}</span>
        </div>
      </div>
      {% if session.screening_summary %}
      <p><strong>筛选结果：</strong>{{ zh_decision(session.screening_summary.overall_decision) }}（分数 {{ session.screening_summary.overall_score }} / 5，置信度 {{ session.screening_summary.overall_confidence }}）</p>
      {% endif %}
      {% if session.pause_reason %}
      <p><strong>暂停原因：</strong>{{ session.pause_reason }}</p>
      {% endif %}
      {% if session.resume_context and session.resume_context.resumed %}
      <p><strong>续跑信息：</strong>是（轮次={{ zh_round_label(session.resume_context.resume_round) }}，续跑前完成题数={{ session.resume_context.completed_question_count_before_resume }}）</p>
      {% endif %}
      {% if score.hard_fail_flags %}
      <h3>强风险标记</h3>
      <ul>{% for item in score.hard_fail_flags %}<li>{{ item }}</li>{% endfor %}</ul>
      {% endif %}
      </div>
    </section>

    {% if session.interview_flow %}
    <section class="card">
      <h2>面试流程总览</h2>
      <div class="flow-banner">
        <strong>当前卡点：</strong>{{ session.interview_flow.blocked_message }}
      </div>
      <div class="flow-rail">
        {% for item in session.interview_flow.steps %}
        <div class="flow-step-card {{ item.status }}">
          <strong>{{ loop.index }}. {{ item.label }}</strong>
          <div>
            <span class="chip {{ item.status }}">
              {% if item.status == 'done' %}已完成{% elif item.status == 'current' %}进行中{% elif item.status == 'blocked' %}卡在这里{% else %}未开始{% endif %}
            </span>
          </div>
          <div class="muted">{{ zh_internal_text(item.detail) }}</div>
        </div>
        {% endfor %}
      </div>
      <div class="timeline">
        {% for item in session.interview_flow.steps %}
        <div class="timeline-item {{ item.status }}">
          <span class="timeline-dot"></span>
          <div class="timeline-step">
            <strong>{{ loop.index }}. {{ item.label }}</strong>
            <span class="chip {{ item.status }}">
              {% if item.status == 'done' %}已完成{% elif item.status == 'current' %}进行中{% elif item.status == 'blocked' %}卡在这里{% else %}未开始{% endif %}
            </span>
          </div>
          <div class="muted">{{ zh_internal_text(item.detail) }}</div>
        </div>
        {% endfor %}
      </div>
    </section>
    {% endif %}

    <section class="card">
      <h2>阶段总览</h2>
      <div class="summary-grid">
        {% for phase in phase_records %}
        <div class="summary-tile">
          <strong>{{ zh_round_label(phase.round) }}</strong>
          <span>{{ zh_decision(phase.summary.decision) if phase.summary else '未进入' }}</span>
          <div class="muted">问题 {{ phase.question_count }} | 事件 {{ phase.event_count }}</div>
        </div>
        {% endfor %}
      </div>
      <div class="note-box" style="margin-top: 1rem;">
        <strong>记录完整性：</strong>
        {{ '完整' if report_completeness.coverage_status == 'complete' else '待排查' }}。
        主问题事件 {{ report_completeness.main_question_event_count }} 条，评分结果 {{ report_completeness.result_question_count }} 条，追问事件 {{ report_completeness.follow_up_event_count }} 条。
        <div class="muted" style="margin-top: 0.35rem;">时间线已展开追问 {{ report_completeness.timeline_follow_up_count }} 条，并标注其归属主问题。</div>
        <div class="muted" style="margin-top: 0.35rem;">{{ report_completeness.coverage_message }}</div>
      </div>
    </section>

    <section class="two-col">
      <div class="card">
        <h3>面试配置</h3>
        <ul>
          <li>目标级别：<code>{{ session.input_config.level }}</code></li>
          <li>语言模式：<code>{{ zh_language(session.input_config.language) }}</code></li>
          <li>是否逐轮交互：<code>{{ zh_bool(session.interactive_mode) }}</code></li>
          <li>会话状态：<code>{{ zh_status(session.session_status) }}</code></li>
          <li>轮次事件数：<code>{{ session.turn_count }}</code></li>
          <li>TTS 状态：<code>{{ zh_status(session.tts_status) }}</code></li>
          <li>实时播报：<code>{{ zh_bool(session.input_config.speak_prompts) }}</code></li>
          <li>TTS 语言：<code>{{ session.input_config.tts_language or 'auto' }}</code></li>
          <li>TTS 默认音色：<code>{{ session.input_config.tts_voice or 'auto' }}</code></li>
          <li>TTS 语速：<code>{{ session.input_config.tts_rate or '+0%' }}</code></li>
          <li>TTS 音高：<code>{{ session.input_config.tts_pitch or '+0Hz' }}</code></li>
          <li>TTS 音量：<code>{{ session.input_config.tts_volume or '+0%' }}</code></li>
          <li>TTS 播放后端：<code>{{ session.input_config.tts_playback_backend_resolved or 'disabled' }}</code></li>
        </ul>
        {% if session.input_config.persona_voice_overrides %}
        <div class="muted">Persona voices:
          {% for key, value in session.input_config.persona_voice_overrides.items() %}
          <code>{{ key }}={{ value }}</code>{% if not loop.last %}, {% endif %}
          {% endfor %}
        </div>
        {% endif %}
      </div>
      <div class="card">
        <h3>关键信号</h3>
        <p><strong>主要优势</strong></p>
        <ul>{% for item in score.best_strengths %}<li>{{ zh_internal_text(item) }}</li>{% endfor %}</ul>
        <p><strong>主要短板</strong></p>
        <ul>{% for item in score.main_gaps %}<li>{{ zh_internal_text(item) }}</li>{% endfor %}</ul>
        {% if score.consistency_summary %}
        <p><strong>跨题一致性</strong></p>
        <ul>
          <li>整体={{ zh_status(score.consistency_summary.overall_consistency) }}</li>
          <li>调整值={{ score.consistency_summary.score_adjustment }}</li>
        </ul>
        {% endif %}
        <p><strong>改进建议</strong></p>
        <ul>{% for item in session.improvement_suggestions %}<li>{{ item }}</li>{% endfor %}</ul>
      </div>
    </section>

    {% if session.screening_summary %}
    <section class="card">
      <h2>筛选快照</h2>
      <p><strong>结论：</strong>{{ zh_decision(session.screening_summary.overall_decision) }} | 分数 {{ session.screening_summary.overall_score }} / 5 | 置信度 {{ session.screening_summary.overall_confidence }}</p>
      <p><strong>原因：</strong>{{ zh_internal_text(session.screening_summary.decision_reason) }}</p>
      <div class="two-col">
        <div>
          <p><strong>推荐重点</strong></p>
          <ul>{% for item in session.screening_summary.recommended_focuses %}<li>{{ zh_focus_name(item) }}</li>{% endfor %}</ul>
        </div>
        <div>
          <p><strong>关键风险</strong></p>
          <ul>{% for item in session.screening_summary.critical_risks %}<li>{{ item }}</li>{% endfor %}</ul>
        </div>
      </div>
      <table>
        <thead>
          <tr>
            <th>维度</th>
            <th>分数</th>
            <th>置信度</th>
            <th>说明</th>
          </tr>
        </thead>
        <tbody>
          {% for item in session.screening_summary.dimensions %}
          <tr>
            <td>{{ zh_focus_name(item.label) }}</td>
            <td>{{ item.score }}</td>
            <td>{{ item.confidence }}</td>
            <td>{{ item.summary }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </section>
    {% endif %}

    {% if session.question_bank_validation %}
    <section class="card">
      <h2>题库校验</h2>
      <p><strong>状态：</strong>{{ zh_status(session.question_bank_validation.status) }} | 题目 {{ session.question_bank_validation.question_count }} | 文件 {{ session.question_bank_validation.file_count }} | 错误 {{ session.question_bank_validation.error_count }} | 警告 {{ session.question_bank_validation.warning_count }}</p>
      <div class="two-col">
        <div>
          <p><strong>轮次覆盖</strong></p>
          <ul>{% for key, value in session.question_bank_validation.round_coverage.items() %}<li>{{ zh_round_label(key) }}: {{ value }}</li>{% endfor %}</ul>
        </div>
        <div>
          <p><strong>建议</strong></p>
          <ul>{% for item in session.question_bank_validation.suggestions %}<li>{{ item }}</li>{% endfor %}</ul>
        </div>
      </div>
      {% if session.question_bank_validation.issues %}
      <table>
        <thead>
          <tr>
            <th>级别</th>
            <th>代码</th>
            <th>问题</th>
          </tr>
        </thead>
        <tbody>
          {% for item in session.question_bank_validation.issues[:10] %}
          <tr>
            <td>{{ item.severity }}</td>
            <td>{{ item.code }}</td>
            <td>{{ item.message }}{% if item.path %} ({{ item.path }}){% endif %}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
      {% endif %}
    </section>
    {% endif %}

    {% if session.resume_prep %}
    <section class="card">
      <h2>简历准备简报</h2>
      <p><strong>定位建议：</strong>{{ session.resume_prep.positioning_summary }}</p>
      <div class="two-col">
        <div>
          <p><strong>改写优先级</strong></p>
          <ul>{% for item in session.resume_prep.rewrite_priorities %}<li>{{ item.label }}: {{ item.rewrite_action }}</li>{% endfor %}</ul>
        </div>
        <div>
          <p><strong>自我介绍注意点</strong></p>
          <ul>{% for item in session.resume_prep.self_intro_blueprint.watchouts %}<li>{{ item }}</li>{% endfor %}</ul>
        </div>
      </div>
      {% if session.resume_prep.likely_interviewer_probes %}
      <p><strong>高概率追问点</strong></p>
      <ul>{% for item in session.resume_prep.likely_interviewer_probes %}<li>{{ zh_focus_name(item.focus) }}: {{ item.prompt }}</li>{% endfor %}</ul>
      {% endif %}
    </section>
    {% endif %}

    {% if score.consistency_summary %}
    <section class="card">
      <h2>一致性检查</h2>
      <p><strong>整体一致性：</strong>{{ zh_status(score.consistency_summary.overall_consistency) }} | 调整值 {{ score.consistency_summary.score_adjustment }}</p>
      {% if score.consistency_summary.hard_review_flags %}
      <p><strong>人工复核标记</strong></p>
      <ul>{% for item in score.consistency_summary.hard_review_flags %}<li>{{ item }}</li>{% endfor %}</ul>
      {% endif %}
      <table>
        <thead>
          <tr>
            <th>信号</th>
            <th>状态</th>
            <th>调整</th>
            <th>备注</th>
          </tr>
        </thead>
        <tbody>
          {% for item in score.consistency_summary.signals %}
          <tr>
            <td>{{ zh_focus_name(item.label) }}</td>
            <td>{{ zh_status(item.status) }}</td>
            <td>{{ item.score_adjustment }}</td>
            <td>{{ evidence_summary(item) }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </section>
    {% endif %}

    <section class="card">
      <h2>按阶段记录</h2>
      <div class="phase-grid">
        {% for phase in phase_records %}
        <section class="phase-stage">
          <header>
            <div>
              <h3>{{ zh_round_label(phase.round) }}</h3>
              {% if phase.summary %}
              <div class="muted">{{ phase.summary.decision_reason }}</div>
              {% endif %}
            </div>
            <div class="phase-meta">
              <span class="kpi-pill">状态：{{ zh_decision(phase.summary.decision) if phase.summary else '未进入' }}</span>
              <span class="kpi-pill">问题 {{ phase.question_count }}</span>
              <span class="kpi-pill">事件 {{ phase.event_count }}</span>
              {% if phase.summary %}
              <span class="kpi-pill">分数 {{ phase.summary.score }} / 5</span>
              <span class="kpi-pill">置信度 {{ phase.summary.confidence }}</span>
              {% endif %}
            </div>
          </header>

          {% if phase.summary.focus %}
          <p><strong>阶段题型 / 重点：</strong>{{ zh_focus_list(phase.summary.focus) }}</p>
          {% elif phase.deliberation.critical_focuses %}
          <p><strong>阶段题型 / 重点：</strong>{{ zh_focus_list(phase.deliberation.critical_focuses) }}</p>
          {% endif %}

          {% if phase.events %}
          <div class="stage-events">
            <p><strong>阶段关键事件</strong></p>
            <ul>
              {% for event in phase.events %}
              <li>
                <strong>#{{ event.turn_index }} {{ stage_label(event.stage) }}</strong>
                {% if event.response %}：{{ zh_internal_text(event.response) }}{% endif %}
              </li>
              {% endfor %}
            </ul>
          </div>
          {% endif %}

          {% for result in phase.questions %}
          <article class="qa-card">
            <h4>{{ loop.index }}. {{ result.title }}</h4>
            <p><strong>题目：</strong>{{ result.question }}</p>
            {% if result.spoken_question and result.spoken_question != result.question %}
            <p><strong>实际播报：</strong>{{ zh_internal_text(result.spoken_question) }}</p>
            {% endif %}
            <p><strong>回答：</strong>{{ result.answer }}</p>
            {% if result.follow_up_chain %}
            <p><strong>追问链路</strong></p>
            <table class="compact-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>追问</th>
                  <th>回答</th>
                </tr>
              </thead>
              <tbody>
                {% for item in result.follow_up_chain %}
                <tr>
                  <td>{{ loop.index }}</td>
                  <td>{{ item.question }}</td>
                  <td>{{ item.answer or '无追问回答' }}</td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
            {% endif %}
            <div class="two-col">
              <div>
                <p><strong>阶段判断：</strong>{{ zh_result_action(result.decision_result) }}</p>
                <p><strong>理由：</strong>{{ zh_internal_text(result.decision_reason) }}</p>
              </div>
              <div>
                <p><strong>分数：</strong>{{ result.score }} / 5</p>
                <p><strong>置信度：</strong>{{ result.confidence }}</p>
                <p><strong>题库对齐度：</strong>{{ zh_question_alignment(result.question_bank_alignment) }}</p>
              </div>
            </div>
            <div class="two-col">
              <div>
                <p><strong>优势证据</strong></p>
                <ul>{% for item in result.strength_evidence %}<li>{{ item }}</li>{% endfor %}</ul>
              </div>
              <div>
                <p><strong>风险 / 缺失证据</strong></p>
                <ul>
                  {% for item in result.risk_evidence %}<li>{{ item }}</li>{% endfor %}
                  {% for item in result.missing_evidence %}<li>{{ item }}</li>{% endfor %}
                </ul>
              </div>
            </div>
          </article>
          {% endfor %}
        </section>
        {% endfor %}
      </div>
    </section>

    <section class="card">
      <h2>轮次总结</h2>
      <table>
        <thead>
          <tr>
            <th>轮次</th>
            <th>面试官风格</th>
            <th>分数</th>
            <th>结论</th>
            <th>原因</th>
          </tr>
        </thead>
        <tbody>
          {% for summary in session.round_summaries %}
          <tr>
            <td>{{ zh_round_label(summary.round) }}</td>
            <td>{{ summary.persona }}</td>
            <td>{{ summary.score }} / 5</td>
            <td>{{ zh_decision(summary.decision) }}</td>
            <td>{{ summary.decision_reason }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </section>

    {% if session.round_deliberations %}
    <section class="card">
      <h2>轮次评审</h2>
      <table>
        <thead>
          <tr>
            <th>轮次</th>
            <th>评审模式</th>
            <th>下一步动作</th>
            <th>评审理由</th>
          </tr>
        </thead>
        <tbody>
          {% for item in session.round_deliberations %}
          <tr>
            <td>{{ zh_round_label(item.round) }}</td>
            <td>{{ zh_review_mode(item.review_mode) }}</td>
            <td>{{ zh_next_action(item.next_action) }}</td>
            <td>{{ zh_internal_text(item.panel_reason) }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
      {% for item in session.round_deliberations %}
      {% if item.review_notes %}
      <p><strong>{{ zh_round_label(item.round) }} 备注：</strong> {% for note in item.review_notes %}{{ zh_internal_text(note) }}{% if not loop.last %} | {% endif %}{% endfor %}</p>
      {% endif %}
      {% endfor %}
    </section>
    {% endif %}

    {% if session.panel_memos %}
    <section class="card">
      <h2>面试官备忘</h2>
      {% for item in session.panel_memos %}
      <div class="card">
        <p><strong>轮次：</strong> {{ zh_round_label(item.round) }}</p>
        {% if item.next_round %}<p><strong>下一轮：</strong> {{ zh_round_label(item.next_round) }}</p>{% endif %}
        <p><strong>决策：</strong> {{ zh_decision(item.decision) }}</p>
        <p><strong>原因：</strong> {{ zh_internal_text(item.panel_reason if item.panel_reason else item.reason) }}</p>
        {% if item.focuses %}<p><strong>重点：</strong> {{ zh_focus_list(item.focuses) }}</p>{% endif %}
        {% if item.before_order and item.after_order %}<p><strong>题目路由：</strong> {{ item.before_order|join(' -> ') }} → {{ item.after_order|join(' -> ') }}</p>{% endif %}
      </div>
      {% endfor %}
    </section>
    {% endif %}

    {% set hold_events = session.turn_events | selectattr('stage', 'equalto', 'hold') | list %}
    {% if hold_events %}
    <section class="card">
      <h2>轮次暂停点</h2>
      <table>
        <thead>
          <tr>
            <th>事件</th>
            <th>轮次</th>
            <th>决策</th>
            <th>说明</th>
          </tr>
        </thead>
        <tbody>
          {% for item in hold_events %}
          <tr>
            <td>{{ item.turn_index }}</td>
            <td>{{ zh_round_label(item.round) }}</td>
            <td>{{ zh_result_action(item.decision_result) }}</td>
            <td>{{ zh_internal_text(item.response) }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </section>
    {% endif %}

    {% set transition_events = session.turn_events | selectattr('stage', 'equalto', 'round_transition') | list %}
    {% if transition_events %}
    <section class="card">
      <h2>轮次过渡</h2>
      <table>
        <thead>
          <tr>
            <th>事件</th>
            <th>轮次</th>
            <th>模式</th>
            <th>说明</th>
          </tr>
        </thead>
        <tbody>
          {% for item in transition_events %}
          <tr>
            <td>{{ item.turn_index }}</td>
            <td>{{ zh_round_label(item.round) }}</td>
            <td>{{ zh_internal_text(item.notes|join(', ')) }}</td>
            <td>{{ zh_internal_text(item.response) }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </section>
    {% endif %}

    {% set handoff_events = session.turn_events | selectattr('stage', 'equalto', 'handoff_route') | list %}
    {% if handoff_events %}
    <section class="card">
      <h2>题目交接路由</h2>
      <table>
        <thead>
          <tr>
            <th>事件</th>
            <th>轮次</th>
            <th>路由说明</th>
          </tr>
        </thead>
        <tbody>
          {% for item in handoff_events %}
          <tr>
            <td>{{ item.turn_index }}</td>
            <td>{{ zh_round_label(item.round) }}</td>
            <td>{{ zh_internal_text(item.response) }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </section>
    {% endif %}

    <section class="card">
      <h2>轮次评分卡</h2>
      {% for scorecard in score.round_scorecards %}
      <div class="card">
        <h3>{{ zh_round_label(scorecard.round) }} - {{ zh_round_verdict(scorecard.round_verdict) }}</h3>
        <p><strong>阈值：</strong>最低分 {{ scorecard.threshold.min_round_score }}，最低置信度 {{ scorecard.threshold.min_confidence }}，关键能力最低分 {{ scorecard.threshold.critical_min_score }}</p>
        <p><strong>判定原因：</strong>{{ zh_internal_text(scorecard.verdict_reason) }}</p>
        <table>
          <thead>
            <tr>
              <th>考察点</th>
              <th>目标值</th>
              <th>实际值</th>
              <th>置信度</th>
              <th>判定</th>
            </tr>
          </thead>
          <tbody>
            {% for item in scorecard.competency_checks %}
            <tr>
              <td>{{ zh_focus_name(item.focus) }}</td>
              <td>{{ item.expected_min_score }}</td>
              <td>{{ item.actual_score if item.actual_score is not none else '无' }}</td>
              <td>{{ item.actual_confidence if item.actual_confidence is not none else '无' }}</td>
              <td>{{ zh_competency_verdict(item.verdict) }}</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
      {% endfor %}
    </section>

    <section class="two-col">
      <div class="card">
        <h2>能力族总览</h2>
        <table>
          <thead>
            <tr>
              <th>能力族</th>
              <th>分数</th>
              <th>置信度</th>
            </tr>
          </thead>
          <tbody>
            {% for item in score.competency_families %}
            <tr>
              <td>{{ zh_focus_name(item.name) }}</td>
              <td>{{ item.score }}</td>
              <td>{{ item.confidence }}</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
      <div class="card">
        <h2>面试计划</h2>
        <ul>
          {% for item in session.interview_plan.rounds %}
          <li><strong>{{ zh_round_label(item.round) }}</strong>：重点={{ zh_focus_list(item.priority_focuses) }}, 语言={{ zh_language(item.language_mode) }}, 目标题数={{ item.question_target }}, 已选题数={{ item.selected_questions|length }}</li>
          {% endfor %}
        </ul>
      </div>
      <div class="card">
        <h2>题库来源</h2>
        <ul>{% for item in session.question_bank_sources %}<li><code>{{ item }}</code></li>{% endfor %}</ul>
        {% if session.tts_files %}
        <h3>TTS 产物</h3>
        <ul>{% for item in session.tts_files %}<li><code>{{ item }}</code></li>{% endfor %}</ul>
        {% endif %}
      </div>
    </section>

    {% set adaptive_events = session.turn_events | selectattr('stage', 'equalto', 'adaptive_route') | list %}
    {% if adaptive_events %}
    <section class="card">
      <h2>自适应路由</h2>
      <table>
        <thead>
          <tr>
            <th>事件</th>
            <th>轮次</th>
            <th>动作</th>
            <th>原因</th>
          </tr>
        </thead>
        <tbody>
          {% for item in adaptive_events %}
          <tr>
            <td>{{ item.turn_index }}</td>
            <td>{{ zh_round_label(item.round) }}</td>
            <td>{{ zh_internal_text(item.notes|join(', ')) }}</td>
            <td>{{ zh_internal_text(item.response) }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </section>
    {% endif %}

    {% set consistency_events = session.turn_events | selectattr('stage', 'equalto', 'consistency_challenge') | list %}
    {% if consistency_events %}
    <section class="card">
      <h2>一致性挑战</h2>
      <table>
        <thead>
          <tr>
            <th>事件</th>
            <th>轮次</th>
            <th>信号</th>
            <th>追问</th>
          </tr>
        </thead>
        <tbody>
          {% for item in consistency_events %}
          <tr>
            <td>{{ item.turn_index }}</td>
            <td>{{ zh_round_label(item.round) }}</td>
            <td>{{ zh_internal_text(item.notes|join(', ')) }}</td>
            <td>{{ item.prompt }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </section>
    {% endif %}

    <section class="card">
      <h2>完整面试时间线</h2>
      <table class="compact-table">
        <thead>
          <tr>
            <th>序号</th>
            <th>阶段</th>
            <th>事件类型</th>
            <th>归属链路</th>
            <th>Prompt / 题目</th>
            <th>记录 / 回答</th>
          </tr>
        </thead>
        <tbody>
          {% for event in timeline_records %}
          <tr>
            <td>{{ event.display_turn_index }}</td>
            <td>{{ zh_round_label(event.round) }}</td>
            <td>
              <div>{{ stage_label(event.stage) }}</div>
              <div class="muted">{{ event.group_label }}</div>
            </td>
            <td>
              {% if event.parent_display %}
              {{ event.parent_display }}
              {% elif event.question_title %}
              主问题 {{ event.question_title }}
              {% else %}
              <span class="muted">非问答事件</span>
              {% endif %}
              {% if event.is_synthetic %}
              <div class="muted">由评分追问链补全</div>
              {% endif %}
            </td>
            <td>{{ event.prompt or '无' }}</td>
            <td>
              {% if event.response %}
              {{ zh_internal_text(event.response) }}
              {% else %}
              <span class="muted">无响应内容</span>
              {% endif %}
              {% if event.tts_file %}
              <div class="muted">TTS: <code>{{ event.tts_file }}</code></div>
              {% endif %}
              {% if event.spoken_text and event.spoken_text != event.prompt %}
              <div class="muted">Spoken: {{ zh_internal_text(event.spoken_text) }}</div>
              {% endif %}
              {% if event.decision_result and event.decision_result != 'pending' %}
              <div class="muted">决策：{{ zh_result_action(event.decision_result) }}</div>
              {% endif %}
              {% if event.score is not none %}
              <div class="muted">分数：{{ event.score }} | 置信度：{{ event.confidence }}</div>
              {% endif %}
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </section>
  </div>
</body>
</html>
""".strip()
    )
    html = template.render(
        session=session_data,
        score=score_data,
        zh_decision=zh_decision,
        zh_status=zh_status,
        zh_bool=zh_bool,
        zh_mode=zh_mode,
        zh_language=zh_language,
        zh_review_mode=zh_review_mode,
        zh_next_action=zh_next_action,
        zh_result_action=zh_result_action,
        zh_round_verdict=zh_round_verdict,
        zh_competency_verdict=zh_competency_verdict,
        zh_round_label=zh_round_label,
        zh_question_alignment=zh_question_alignment,
        zh_focus_name=zh_focus_name,
        zh_focus_list=zh_focus_list,
        zh_internal_text=zh_internal_text,
        stage_label=stage_label,
        evidence_summary=evidence_summary,
        zh_final_summary=zh_final_summary_text(),
        phase_records=phase_records,
        ordered_turn_events=ordered_turn_events,
        timeline_records=timeline_records,
        ordered_questions=ordered_questions,
        report_completeness=report_completeness,
    )
    path.write_text(html, encoding="utf-8")


def render_reject_mail(path: Path, session_id: str, hard_fail_flags: list[str], round_summaries: list[RoundSummary] | None = None) -> None:
    lines = [
        "<!DOCTYPE html>",
        "<html lang=\"en\"><body>",
        "<p>Dear candidate,</p>",
        f"<p>Thank you for taking part in the Android interview session ({session_id}). After reviewing the interview evidence, we will not move forward this time.</p>",
        "<p>Key concerns:</p>",
        "<ul>",
    ]
    for flag in hard_fail_flags:
        lines.append(f"<li>{flag}</li>")
    lines.append("</ul>")
    if round_summaries:
        lines.append("<p>Round-level notes:</p><ul>")
        for summary in round_summaries:
            if summary.decision in {"reject", "borderline", "advance_with_risk"}:
                lines.append(f"<li>{summary.label}: {summary.decision_reason}</li>")
        lines.append("</ul>")
    lines.extend(
        [
            "<p>We appreciate your time and encourage you to continue strengthening the areas above.</p>",
            "</body></html>",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def render_failure_summary(path: Path, session_data: dict[str, Any], score_data: dict[str, Any]) -> None:
    lines = [
        f"# Interview Failure Summary - {session_data['session_id']}",
        "",
        f"- Final decision: `{score_data['final_decision']}`",
        f"- Session status: `{session_data['session_status']}`",
        f"- Terminated early: `{str(session_data['terminated_early']).lower()}`",
        f"- Termination reason: {session_data['termination_reason'] or 'n/a'}",
        "",
        "## Hard Fail Flags",
        "",
    ]
    hard_fail_flags = score_data.get("hard_fail_flags", [])
    if hard_fail_flags:
        for item in hard_fail_flags:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.extend(["", "## Round Notes", ""])
    for summary in session_data.get("round_summaries", []):
        lines.append(f"- **{summary['label']}**: {summary['decision']} | {summary['decision_reason']}")
    lines.extend(["", "## Improvement Suggestions", ""])
    for item in session_data.get("improvement_suggestions", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Highest Risk Patterns", ""])
    for item in score_data.get("risk_summary", []):
        lines.append(f"- {item}")
    consistency = score_data.get("consistency_summary", {})
    if consistency:
        lines.extend(["", "## Consistency Review", ""])
        lines.append(f"- Overall consistency: `{consistency.get('overall_consistency', 'n/a')}`")
        lines.append(f"- Score adjustment: `{consistency.get('score_adjustment', 'n/a')}`")
        for item in consistency.get("hard_review_flags", []):
            lines.append(f"- Manual review flag: {item}")
    screening = session_data.get("screening_summary", {})
    if screening:
        lines.extend(["", "## Screening Snapshot", ""])
        lines.append(f"- Overall decision: `{screening.get('overall_decision', 'unknown')}`")
        lines.append(f"- Overall score: `{screening.get('overall_score', 'n/a')}`")
        for item in screening.get("critical_risks", []):
            lines.append(f"- Screening risk: {item}")
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def synthesize_summary_artifacts(
    output_dir: Path,
    results: list[QuestionResult],
    decision: str,
    voice: str,
    *,
    rate: str = "+0%",
    pitch: str = "+0Hz",
    volume: str = "+0%",
) -> list[str]:
    tts_dir = output_dir / "tts"
    opening = "Welcome to the Android senior interview practice session. We will assess Android fundamentals, architecture, performance, leadership, and evidence quality."
    questions = " ".join(
        [
            f"In {ROUND_LABELS.get(result.round, result.round)}, question: {result.spoken_question or result.question}"
            for result in results
        ]
    )
    summary = f"The final decision is {decision}. Please review the written report for detailed strengths, risks, missing evidence, and round level decisions."
    files = [
        ("opening.mp3", opening),
        ("questions.mp3", questions),
        ("summary.mp3", summary),
    ]
    generated: list[str] = []
    for filename, text in files:
        synthesize_text(
            text=text,
            output_path=tts_dir / filename,
            voice=voice,
            rate=rate,
            pitch=pitch,
            volume=volume,
        )
        generated.append(str((tts_dir / filename).relative_to(output_dir)))
    return generated


def synthesize_turn_prompt(
    output_dir: Path,
    turn_index: int,
    prompt: str,
    voice: str,
    *,
    rate: str = "+0%",
    pitch: str = "+0Hz",
    volume: str = "+0%",
) -> str:
    tts_dir = output_dir / "tts"
    filename = f"turn-{turn_index:03d}.mp3"
    synthesize_text(
        text=prompt,
        output_path=tts_dir / filename,
        voice=voice,
        rate=rate,
        pitch=pitch,
        volume=volume,
    )
    return str((tts_dir / filename).relative_to(output_dir))


def build_final_summary(decision: str, round_summaries: list[RoundSummary], hard_fail_flags: list[str], pause_reason: str = "") -> str:
    if decision == "paused":
        return pause_reason or "The session was paused before the interview finished. Resume from the saved checkpoint to continue."
    if decision == "aborted":
        return "The session was ended early by the candidate before enough evidence could be collected."
    if decision == "pass":
        return "The candidate demonstrated enough evidence across key rounds to be considered a pass for the current target level."
    if hard_fail_flags:
        return f"The session ended with hard-fail signals: {hard_fail_flags[0]}"
    if any(summary.decision == "advance_with_risk" for summary in round_summaries):
        return "The candidate showed partial fit, but several dimensions still require follow-up verification."
    return "The evidence collected in this session is not strong enough for a confident pass recommendation."


def session_payload(
    session_id: str,
    level: str,
    language: str,
    enable_tts: bool,
    voice: str,
    job_profile: dict[str, Any],
    candidate_profile: dict[str, Any],
    results: list[QuestionResult],
    turn_events: list[TurnEvent],
    tts_status: str,
    tts_files: list[str],
    question_sources: list[str],
    hard_fail_flags: list[str],
    *,
    mode: str = "simulate",
    interactive_mode: bool = False,
    round_summaries: list[RoundSummary] | None = None,
    round_deliberations: list[dict[str, Any]] | None = None,
    persona_configs: list[PersonaConfig] | None = None,
    session_state_history: list[str] | None = None,
    session_status: str = "completed",
    final_decision_value: str = "",
    interview_plan: dict[str, Any] | None = None,
    terminated_early: bool | None = None,
    round_scorecards: list[dict[str, Any]] | None = None,
    pause_reason: str = "",
    resume_context: dict[str, Any] | None = None,
    extra_input_config: dict[str, Any] | None = None,
    screening_summary: dict[str, Any] | None = None,
    consistency_summary: dict[str, Any] | None = None,
    panel_memos: list[dict[str, Any]] | None = None,
    question_bank_validation: dict[str, Any] | None = None,
    resume_prep: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summaries = round_summaries or build_round_summaries(results)
    decision = final_decision_value or "completed"
    terminated = bool(hard_fail_flags) if terminated_early is None else terminated_early
    return {
        "session_id": session_id,
        "created_at": datetime.now().isoformat(),
        "session_status": session_status,
        "mode": mode,
        "interactive_mode": interactive_mode,
        "input_config": {
            "level": level,
            "language": language,
            "enable_tts": enable_tts,
            "voice": voice,
            **(extra_input_config or {}),
        },
        "job_profile": job_profile,
        "candidate_profile": candidate_profile,
        "round_plan": round_plan(results),
        "persona_plan": [asdict(item) for item in (persona_configs or build_persona_configs(language, [result.round for result in results]))],
        "round_summaries": [asdict(item) for item in summaries],
        "round_deliberations": round_deliberations or build_round_deliberations(results),
        "question_bank_sources": question_sources,
        "screening_summary": screening_summary or {},
        "consistency_summary": consistency_summary or {},
        "question_bank_validation": question_bank_validation or {},
        "resume_prep": resume_prep or {},
        "question_records": [serialize_question_record(item) for item in results],
        "terminated_early": terminated,
        "termination_reason": hard_fail_flags[0] if hard_fail_flags else "",
        "tts_status": tts_status,
        "tts_files": tts_files,
        "turn_count": len(turn_events),
        "turn_events": [asdict(item) for item in turn_events],
        "session_state_history": session_state_history or ["intake", "planning", "reporting", "completed"],
        "final_decision": decision,
        "final_summary": build_final_summary(decision, summaries, hard_fail_flags, pause_reason=pause_reason),
        "interview_flow": build_interview_flow_summary(
            session_status=session_status,
            final_decision=decision,
            screening_summary=screening_summary or {},
            resume_prep=resume_prep or {},
            question_bank_validation=question_bank_validation or {},
            round_summaries=summaries,
            pause_reason=pause_reason,
        ),
        "interview_plan": interview_plan or {"rounds": []},
        "improvement_suggestions": build_improvement_suggestions(results),
        "round_scorecards": round_scorecards or [],
        "pause_reason": pause_reason,
        "resume_context": resume_context or {"resumed": False},
        "panel_memos": panel_memos or [],
    }


def score_payload(
    results: list[QuestionResult],
    hard_fail_flags: list[str],
    decision: str,
    round_summaries: list[RoundSummary] | None = None,
    round_scorecards: list[dict[str, Any]] | None = None,
    consistency_summary: dict[str, Any] | None = None,
    round_deliberations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    summaries = round_summaries or build_round_summaries(results)
    scorecards = round_scorecards or []
    question_payload = [
        serialize_question_record(result)
        for result in results
    ]
    return {
        "score_scale": "1-5",
        "question_count": len(results),
        "questions": question_payload,
        "sub_competencies": build_sub_competencies(results),
        "competency_families": build_competency_families(results),
        "round_scorecards": scorecards,
        "round_scores": [
            {
                "round": summary.round,
                "label": summary.label,
                "score": summary.score,
                "confidence": summary.confidence,
                "decision": summary.decision,
                "decision_reason": summary.decision_reason,
            }
            for summary in summaries
        ],
        "hard_fail_flags": hard_fail_flags,
        "final_decision": decision,
        "confidence_summary": round(sum(result.confidence for result in results) / max(1, len(results)), 2),
        "consistency_summary": consistency_summary or {},
        "round_deliberations": round_deliberations or build_round_deliberations(results),
        "risk_summary": sorted({risk for result in results for risk in result.risk_evidence}),
        "best_strengths": sorted({item for result in results for item in result.strength_evidence}),
        "main_gaps": sorted({item for result in results for item in result.missing_evidence}),
    }
