from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from profile_schema import InterviewTemplate
from profile_schema import DEFAULT_ALLOWED_DIFFICULTIES, DEFAULT_ALLOWED_LANGUAGES, DEFAULT_ALLOWED_LEVELS
from template_resolver import default_runtime_template


@dataclass
class Question:
    id: str
    title: str
    direction: str = ""
    round: str = ""
    level: str = ""
    difficulty: str = ""
    language: str = ""
    tags: list[str] = field(default_factory=list)
    weight: float = 1.0
    source: str = ""
    competencies: list[str] = field(default_factory=list)
    persona_fit: list[str] = field(default_factory=list)
    must_ask: bool = False
    follow_up_limit: int = 3
    expected_signal: str = ""
    question: str = ""
    intent: str = ""
    follow_ups: list[str] = field(default_factory=list)
    scoring_notes: list[str] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)
    good_signals: list[str] = field(default_factory=list)
    spoken_question: dict[str, str] = field(default_factory=dict)
    spoken_follow_ups: dict[str, list[str]] = field(default_factory=dict)
    source_path: str = ""


LEGACY_ALLOWED_ROUNDS = {"intro", "screening", "round1", "round2", "round3", "hr"}
LEGACY_ALLOWED_LEVELS = set(DEFAULT_ALLOWED_LEVELS)
LEGACY_ALLOWED_LANGUAGES = set(DEFAULT_ALLOWED_LANGUAGES)
LEGACY_ALLOWED_DIFFICULTIES = set(DEFAULT_ALLOWED_DIFFICULTIES)
ACTIVE_VALIDATION_TEMPLATE: InterviewTemplate | None = None


def configure_question_bank_template(template: InterviewTemplate | None = None) -> None:
    global ACTIVE_VALIDATION_TEMPLATE
    ACTIVE_VALIDATION_TEMPLATE = template


def build_question_bank_validation_rules(template: InterviewTemplate | None = None) -> dict[str, set[str]]:
    resolved_template = template or ACTIVE_VALIDATION_TEMPLATE
    if resolved_template is None:
        try:
            resolved_template = default_runtime_template()
        except Exception:
            resolved_template = None
    if resolved_template is None:
        return {
            "allowed_rounds": set(LEGACY_ALLOWED_ROUNDS),
            "allowed_levels": set(LEGACY_ALLOWED_LEVELS),
            "allowed_languages": set(LEGACY_ALLOWED_LANGUAGES),
            "allowed_difficulties": set(LEGACY_ALLOWED_DIFFICULTIES),
        }
    rules = resolved_template.question_bank_rules
    return {
        "allowed_rounds": set(rules.allowed_rounds or resolved_template.round_ids or LEGACY_ALLOWED_ROUNDS),
        "allowed_levels": set(rules.allowed_levels or LEGACY_ALLOWED_LEVELS),
        "allowed_languages": set(rules.allowed_languages or LEGACY_ALLOWED_LANGUAGES),
        "allowed_difficulties": {str(item).upper() for item in (rules.allowed_difficulties or LEGACY_ALLOWED_DIFFICULTIES)},
    }


def _read_frontmatter_markdown(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return {}, text
    header = parts[0].lstrip("-\n")
    body = parts[1]
    data = yaml.safe_load(header) or {}
    return data if isinstance(data, dict) else {}, body


def _extract_section(body: str, title: str) -> str:
    lines = body.splitlines()
    target = f"## {title}"
    start = None
    for idx, line in enumerate(lines):
        if line.strip() == target:
            start = idx + 1
            break
    if start is None:
        return ""
    end = len(lines)
    for idx in range(start, len(lines)):
        if lines[idx].startswith("## "):
            end = idx
            break
    return "\n".join(lines[start:end]).strip()


def _split_bullets(block: str) -> list[str]:
    out: list[str] = []
    for line in block.splitlines():
        line = line.strip()
        if line.startswith("- "):
            out.append(line[2:].strip())
    return out


def _parse_bool(value: Any) -> bool:
    return bool(value) and str(value).lower() not in {"false", "0", "no", "none"}


def parse_question_file(path: Path) -> Question:
    meta, body = _read_frontmatter_markdown(path)
    spoken_question = meta.get("spoken_question", {}) or {}
    spoken_follow_ups = meta.get("spoken_follow_ups", {}) or {}
    q = Question(
        id=str(meta.get("id", path.stem)),
        title=str(meta.get("title", path.stem)),
        direction=str(meta.get("direction", "")),
        round=str(meta.get("round", "")),
        level=str(meta.get("level", "")),
        difficulty=str(meta.get("difficulty", "")),
        language=str(meta.get("language", "")),
        tags=list(meta.get("tags", []) or []),
        weight=float(meta.get("weight", 1.0) or 1.0),
        source=str(meta.get("source", "")),
        competencies=list(meta.get("competencies", []) or []),
        persona_fit=list(meta.get("persona_fit", []) or []),
        must_ask=_parse_bool(meta.get("must_ask", False)),
        follow_up_limit=int(meta.get("follow_up_limit", 3) or 3),
        expected_signal=str(meta.get("expected_signal", "")),
        question=_extract_section(body, "Question"),
        intent=_extract_section(body, "Intent"),
        follow_ups=_split_bullets(_extract_section(body, "Follow-ups")),
        scoring_notes=_split_bullets(_extract_section(body, "Scoring Notes")),
        red_flags=_split_bullets(_extract_section(body, "Red Flags")),
        good_signals=_split_bullets(_extract_section(body, "Good Signals")),
        spoken_question={str(key): str(value) for key, value in dict(spoken_question).items() if str(value).strip()}
        if isinstance(spoken_question, dict)
        else {},
        spoken_follow_ups={
            str(key): [str(item) for item in value if str(item).strip()]
            for key, value in dict(spoken_follow_ups).items()
            if isinstance(value, list)
        }
        if isinstance(spoken_follow_ups, dict)
        else {},
        source_path=str(path),
    )
    if not q.question:
        q.question = body.strip().splitlines()[0].strip() if body.strip() else q.title
    return q


def load_question_bank(path: str | Path) -> list[Question]:
    root = Path(path)
    if root.is_file():
        return [parse_question_file(root)]
    questions: list[Question] = []
    for file_path in sorted(root.rglob("*.md")):
        if file_path.name.lower().startswith("readme"):
            continue
        questions.append(parse_question_file(file_path))
    return questions


def question_matches_template(question: Question, template: InterviewTemplate | None) -> bool:
    if template is None:
        return True
    rules = template.question_bank_rules
    blocked_tags = {str(item).strip().lower() for item in rules.blocked_tags if str(item).strip()}
    blocked_keywords = [str(item).strip().lower() for item in rules.blocked_keywords if str(item).strip()]
    if blocked_tags:
        question_tags = {str(item).strip().lower() for item in question.tags if str(item).strip()}
        if question_tags & blocked_tags:
            return False
    if blocked_keywords:
        haystacks = [
            str(question.title or "").lower(),
            str(question.question or "").lower(),
            str(question.intent or "").lower(),
            " ".join(str(item).lower() for item in question.tags if str(item).strip()),
            " ".join(str(item).lower() for item in question.competencies if str(item).strip()),
        ]
        for keyword in blocked_keywords:
            if any(keyword in text for text in haystacks):
                return False
    return True


def filter_questions_for_template(questions: list[Question], template: InterviewTemplate | None) -> list[Question]:
    filtered = [question for question in questions if question_matches_template(question, template)]
    return filtered


def load_speech_overrides(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def apply_speech_overrides(questions: list[Question], payload: dict[str, Any] | None) -> None:
    data = dict(payload or {})
    question_overrides = data.get("questions", {}) if isinstance(data.get("questions", {}), dict) else {}
    for question in questions:
        override = question_overrides.get(question.id, {})
        if not isinstance(override, dict):
            continue
        spoken_question = override.get("spoken_question", {})
        if isinstance(spoken_question, dict):
            question.spoken_question.update(
                {str(key): str(value) for key, value in spoken_question.items() if str(value).strip()}
            )
        spoken_follow_ups = override.get("spoken_follow_ups", {})
        if isinstance(spoken_follow_ups, dict):
            for key, value in spoken_follow_ups.items():
                if isinstance(value, list):
                    question.spoken_follow_ups[str(key)] = [str(item) for item in value if str(item).strip()]


def _validation_issue(severity: str, code: str, message: str, *, path: str = "", question_id: str = "") -> dict[str, Any]:
    return {
        "severity": severity,
        "code": code,
        "message": message,
        "path": path,
        "question_id": question_id,
    }


def _normalized_question_path(question: Question, root: Path) -> str:
    source_path = Path(question.source_path)
    if source_path.is_absolute():
        try:
            return str(source_path.relative_to(root))
        except ValueError:
            return str(source_path)
    try:
        return str(source_path.relative_to(root))
    except ValueError:
        return str(source_path)


def validate_question_bank(path: str | Path, questions: list[Question] | None = None) -> dict[str, Any]:
    root = Path(path)
    loaded_questions = list(questions or load_question_bank(root))
    issues: list[dict[str, Any]] = []
    file_paths = sorted({_normalized_question_path(question, root) for question in loaded_questions})
    validation_rules = build_question_bank_validation_rules()
    allowed_rounds = validation_rules["allowed_rounds"]
    allowed_levels = validation_rules["allowed_levels"]
    allowed_languages = validation_rules["allowed_languages"]
    allowed_difficulties = validation_rules["allowed_difficulties"]
    round_coverage: dict[str, int] = {name: 0 for name in sorted(allowed_rounds)}
    level_coverage: dict[str, int] = {name: 0 for name in sorted(allowed_levels)}
    language_coverage: dict[str, int] = {name: 0 for name in sorted(allowed_languages)}
    id_to_paths: dict[str, list[str]] = {}
    title_round_to_paths: dict[tuple[str, str], list[str]] = {}

    if not loaded_questions:
        issues.append(
            _validation_issue(
                "error",
                "empty_bank",
                "No Markdown question files were found in the question bank path.",
                path=str(root),
            )
        )

    for question in loaded_questions:
        rel_path = _normalized_question_path(question, root)
        question_id = str(question.id or "").strip()
        title = str(question.title or "").strip()
        round_name = str(question.round or "").strip()
        level_name = str(question.level or "").strip()
        language = str(question.language or "").strip()
        difficulty = str(question.difficulty or "").strip().upper()

        if question_id:
            id_to_paths.setdefault(question_id, []).append(rel_path)
        if title and round_name:
            title_round_to_paths.setdefault((title.lower(), round_name.lower()), []).append(rel_path)

        if round_name in round_coverage:
            round_coverage[round_name] += 1
        if level_name in level_coverage:
            level_coverage[level_name] += 1
        if language in language_coverage:
            language_coverage[language] += 1

        required_text_fields = [
            ("id", question_id),
            ("title", title),
            ("round", round_name),
            ("level", level_name),
            ("difficulty", difficulty),
            ("language", language),
            ("question", str(question.question or "").strip()),
        ]
        for field_name, value in required_text_fields:
            if not value:
                issues.append(
                    _validation_issue(
                        "error",
                        "missing_required_field",
                        f"Missing required field: {field_name}.",
                        path=rel_path,
                        question_id=question_id,
                    )
                )

        if round_name and round_name not in allowed_rounds:
            issues.append(
                _validation_issue(
                    "error",
                    "invalid_round",
                    f"Unknown round '{round_name}'. Allowed values: {', '.join(sorted(allowed_rounds))}.",
                    path=rel_path,
                    question_id=question_id,
                )
            )
        if level_name and level_name not in allowed_levels:
            issues.append(
                _validation_issue(
                    "error",
                    "invalid_level",
                    f"Unknown level '{level_name}'. Allowed values: {', '.join(sorted(allowed_levels))}.",
                    path=rel_path,
                    question_id=question_id,
                )
            )
        if language and language not in allowed_languages:
            issues.append(
                _validation_issue(
                    "error",
                    "invalid_language",
                    f"Unknown language '{language}'. Allowed values: {', '.join(sorted(allowed_languages))}.",
                    path=rel_path,
                    question_id=question_id,
                )
            )
        if difficulty and difficulty not in allowed_difficulties:
            issues.append(
                _validation_issue(
                    "error",
                    "invalid_difficulty",
                    f"Unknown difficulty '{difficulty}'. Allowed values: {', '.join(sorted(allowed_difficulties))}.",
                    path=rel_path,
                    question_id=question_id,
                )
            )
        if question.weight <= 0:
            issues.append(
                _validation_issue(
                    "error",
                    "invalid_weight",
                    "Question weight must be greater than 0.",
                    path=rel_path,
                    question_id=question_id,
                )
            )
        if question.follow_up_limit < 0:
            issues.append(
                _validation_issue(
                    "error",
                    "invalid_follow_up_limit",
                    "follow_up_limit must be greater than or equal to 0.",
                    path=rel_path,
                    question_id=question_id,
                )
            )
        if question.follow_ups and question.follow_up_limit == 0:
            issues.append(
                _validation_issue(
                    "warning",
                    "unused_follow_ups",
                    "This question defines follow-ups but follow_up_limit is 0.",
                    path=rel_path,
                    question_id=question_id,
                )
            )
        if question.follow_up_limit > 0 and not question.follow_ups:
            issues.append(
                _validation_issue(
                    "warning",
                    "missing_follow_ups",
                    "No follow-up prompts were defined for a question that allows follow-up turns.",
                    path=rel_path,
                    question_id=question_id,
                )
            )
        if not str(question.intent or "").strip():
            issues.append(
                _validation_issue(
                    "warning",
                    "missing_intent",
                    "Intent section is missing; interviewer guidance will be weaker.",
                    path=rel_path,
                    question_id=question_id,
                )
            )
        if not question.competencies:
            issues.append(
                _validation_issue(
                    "warning",
                    "missing_competencies",
                    "Competencies are missing; scoring and routing coverage will be weaker.",
                    path=rel_path,
                    question_id=question_id,
                )
            )
        if not question.tags:
            issues.append(
                _validation_issue(
                    "warning",
                    "missing_tags",
                    "Tags are missing; downstream topic routing and searchability will be weaker.",
                    path=rel_path,
                    question_id=question_id,
                )
            )
        if not question.scoring_notes:
            issues.append(
                _validation_issue(
                    "warning",
                    "missing_scoring_notes",
                    "Scoring Notes are missing; calibration guidance is incomplete.",
                    path=rel_path,
                    question_id=question_id,
                )
            )
        if not question.good_signals:
            issues.append(
                _validation_issue(
                    "warning",
                    "missing_good_signals",
                    "Good Signals are missing; evidence alignment will be weaker.",
                    path=rel_path,
                    question_id=question_id,
                )
            )
        if not question.red_flags:
            issues.append(
                _validation_issue(
                    "warning",
                    "missing_red_flags",
                    "Red Flags are missing; risk alignment will be weaker.",
                    path=rel_path,
                    question_id=question_id,
                )
            )
        if not str(question.expected_signal or "").strip():
            issues.append(
                _validation_issue(
                    "warning",
                    "missing_expected_signal",
                    "expected_signal is missing; target evidence is underspecified.",
                    path=rel_path,
                    question_id=question_id,
                )
            )
        if not question.persona_fit:
            issues.append(
                _validation_issue(
                    "warning",
                    "missing_persona_fit",
                    "persona_fit is missing; round persona matching may be less precise.",
                    path=rel_path,
                    question_id=question_id,
                )
            )

    for question_id, paths in sorted(id_to_paths.items()):
        if question_id and len(paths) > 1:
            issues.append(
                _validation_issue(
                    "error",
                    "duplicate_question_id",
                    f"Duplicate question id '{question_id}' found in: {', '.join(paths)}.",
                    path=paths[0],
                    question_id=question_id,
                )
            )

    for (title, round_name), paths in sorted(title_round_to_paths.items()):
        if len(paths) > 1:
            issues.append(
                _validation_issue(
                    "warning",
                    "duplicate_title_same_round",
                    f"Duplicate question title in round '{round_name}': '{title}'.",
                    path=paths[0],
                )
            )

    error_count = sum(1 for item in issues if item["severity"] == "error")
    warning_count = sum(1 for item in issues if item["severity"] == "warning")
    if error_count:
        status = "invalid"
    elif warning_count:
        status = "valid_with_warnings"
    else:
        status = "valid"

    suggestions: list[str] = []
    if any(item["code"] == "duplicate_question_id" for item in issues):
        suggestions.append("Make every question id globally unique across the imported Markdown bank.")
    if any(item["code"] == "missing_competencies" for item in issues):
        suggestions.append("Add competencies to every question so routing, scoring, and coverage analysis remain reliable.")
    if any(item["code"] == "missing_scoring_notes" for item in issues):
        suggestions.append("Add scoring notes so different interviewer personas still share a stable calibration baseline.")
    if any(item["code"] == "missing_good_signals" for item in issues) or any(item["code"] == "missing_red_flags" for item in issues):
        suggestions.append("Add Good Signals and Red Flags so the runtime evaluator can align evidence to question intent.")
    if any(item["code"] == "missing_follow_ups" for item in issues):
        suggestions.append("Add follow-up prompts for deeper probing in later turns of the same round.")

    return {
        "status": status,
        "source_path": str(root),
        "question_count": len(loaded_questions),
        "file_count": len(file_paths),
        "error_count": error_count,
        "warning_count": warning_count,
        "issues": issues,
        "round_coverage": round_coverage,
        "level_coverage": level_coverage,
        "language_coverage": language_coverage,
        "question_ids": sorted(id_to_paths),
        "files": file_paths,
        "suggestions": suggestions[:5],
    }


def render_question_bank_validation_markdown(path: str | Path, report: dict[str, Any]) -> Path:
    target = Path(path)
    lines = [
        "# Question Bank Validation",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Source path: `{report.get('source_path', '')}`",
        f"- Question count: `{report.get('question_count', 0)}`",
        f"- File count: `{report.get('file_count', 0)}`",
        f"- Errors: `{report.get('error_count', 0)}`",
        f"- Warnings: `{report.get('warning_count', 0)}`",
        "",
        "## Round Coverage",
        "",
    ]
    for round_name, count in sorted((report.get("round_coverage") or {}).items()):
        lines.append(f"- {round_name}: {count}")
    lines.extend(["", "## Level Coverage", ""])
    for level_name, count in sorted((report.get("level_coverage") or {}).items()):
        lines.append(f"- {level_name}: {count}")
    lines.extend(["", "## Language Coverage", ""])
    for language_name, count in sorted((report.get("language_coverage") or {}).items()):
        lines.append(f"- {language_name}: {count}")
    lines.extend(["", "## Issues", ""])
    issues = report.get("issues", [])
    if issues:
        for item in issues:
            scope = []
            if item.get("path"):
                scope.append(str(item["path"]))
            if item.get("question_id"):
                scope.append(f"id={item['question_id']}")
            scope_text = f" ({', '.join(scope)})" if scope else ""
            lines.append(f"- [{item['severity']}] {item['code']}{scope_text}: {item['message']}")
    else:
        lines.append("- none")
    lines.extend(["", "## Suggestions", ""])
    suggestions = report.get("suggestions", [])
    if suggestions:
        for item in suggestions:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    target.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return target


def write_question_bank_validation_artifacts(output_dir: str | Path, report: dict[str, Any]) -> tuple[Path, Path]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / "question-bank-validation.json"
    md_path = root / "question-bank-validation.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    render_question_bank_validation_markdown(md_path, report)
    return json_path, md_path
