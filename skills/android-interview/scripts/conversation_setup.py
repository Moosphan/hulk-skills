from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from profile_schema import DEFAULT_ALLOWED_LEVELS, InterviewTemplate
from template_resolver import TemplateMatch, resolve_template
from template_store import PRESET_TEMPLATE_DIR, USER_TEMPLATE_DIR, load_template_catalog


def slugify(text: str) -> str:
    value = "".join(ch.lower() if ch.isalnum() else "_" for ch in text.strip())
    collapsed = "_".join(part for part in value.split("_") if part)
    return collapsed or "custom_template"


def parse_csv_text(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def bool_from_text(value: str) -> bool:
    lowered = str(value or "").strip().lower()
    return lowered in {"y", "yes", "true", "1", "是", "需要", "要", "创建", "create"}


@dataclass
class TemplateWizardAnswers:
    display_name: str = ""
    target_role: str = ""
    role_family: str = "general"
    candidate_level: str = "senior"
    default_language: str = "zh"
    inherits_from: str = ""
    aliases: list[str] = field(default_factory=list)


@dataclass
class IntakeResolution:
    template_match: TemplateMatch
    jd_input: str
    resume_input: str
    level: str
    language: str
    created_template_path: str = ""
    created_template_id: str = ""
    notes: list[str] = field(default_factory=list)


class SetupPrompter:
    def ask_text(self, key: str, label: str, default: str = "", allow_empty: bool = True) -> str:
        raise NotImplementedError

    def ask_choice(self, key: str, label: str, choices: list[str], default: str) -> str:
        while True:
            value = self.ask_text(key, f"{label} ({'/'.join(choices)})", default, allow_empty=False)
            if value in choices:
                return value
            self.show_message(f"Please choose one of: {', '.join(choices)}")

    def ask_yes_no(self, key: str, label: str, default: bool = False) -> bool:
        default_text = "yes" if default else "no"
        value = self.ask_text(key, f"{label} (yes/no)", default_text, allow_empty=False)
        return bool_from_text(value)

    def show_message(self, text: str) -> None:
        raise NotImplementedError


def infer_role_family_from_text(text: str) -> str:
    lowered = str(text or "").strip().lower()
    mapping = [
        ("android", ["android", "安卓"]),
        ("backend", ["backend", "后端", "java", "go", "server", "service"]),
        ("frontend", ["frontend", "前端", "web", "react", "vue", "h5"]),
        ("product", ["product", "pm", "产品", "产品经理"]),
        ("design", ["design", "designer", "设计", "ux", "ui"]),
        ("data", ["data", "analytics", "算法", "数据"]),
        ("qa", ["qa", "test", "测试"]),
    ]
    for family, aliases in mapping:
        if any(alias in lowered for alias in aliases):
            return family
    return "general"


def default_rounds_for_role_family(role_family: str) -> list[dict[str, Any]]:
    family = str(role_family or "general").strip().lower() or "general"
    if family == "product":
        return [
            {
                "round_id": "intro",
                "label": {"en": "Self Introduction", "zh": "自我介绍"},
                "enabled": True,
                "order": 10,
                "target_question_count": 1,
                "focuses": ["communication", "project_authenticity", "business_understanding"],
            },
            {
                "round_id": "screening",
                "label": {"en": "Screening", "zh": "初筛"},
                "enabled": True,
                "order": 20,
                "target_question_count": 1,
                "focuses": ["ownership", "delivery_scope", "resume_authenticity"],
            },
            {
                "round_id": "round1",
                "label": {"en": "Round 1", "zh": "第一轮"},
                "enabled": True,
                "order": 30,
                "target_question_count": 2,
                "focuses": ["business_understanding", "problem_solving", "communication"],
            },
            {
                "round_id": "round2",
                "label": {"en": "Round 2", "zh": "第二轮"},
                "enabled": True,
                "order": 40,
                "target_question_count": 2,
                "focuses": ["tradeoff_reasoning", "cross_team_execution", "technical_influence"],
            },
            {
                "round_id": "hr",
                "label": {"en": "HR Interview", "zh": "HR 面"},
                "enabled": True,
                "order": 50,
                "target_question_count": 2,
                "focuses": ["motivation", "leadership", "stability"],
            },
        ]
    base_rounds = [
        {
            "round_id": "intro",
            "label": {"en": "Self Introduction", "zh": "自我介绍"},
            "enabled": True,
            "order": 10,
            "target_question_count": 1,
            "focuses": ["communication", "project_authenticity"],
        },
        {
            "round_id": "screening",
            "label": {"en": "Screening", "zh": "初筛"},
            "enabled": True,
            "order": 20,
            "target_question_count": 1,
            "focuses": ["ownership", "delivery_scope", "resume_authenticity"],
        },
        {
            "round_id": "round1",
            "label": {"en": "Round 1", "zh": "第一轮"},
            "enabled": True,
            "order": 30,
            "target_question_count": 2,
            "focuses": ["implementation_detail", "problem_solving", "ownership"],
        },
        {
            "round_id": "round2",
            "label": {"en": "Round 2", "zh": "第二轮"},
            "enabled": True,
            "order": 40,
            "target_question_count": 2,
            "focuses": ["architecture", "performance", "tradeoff_reasoning"],
        },
        {
            "round_id": "round3",
            "label": {"en": "Round 3", "zh": "第三轮"},
            "enabled": True,
            "order": 50,
            "target_question_count": 2,
            "focuses": ["business_understanding", "technical_influence", "cross_team_execution"],
        },
        {
            "round_id": "hr",
            "label": {"en": "HR Interview", "zh": "HR 面"},
            "enabled": True,
            "order": 60,
            "target_question_count": 2,
            "focuses": ["motivation", "communication", "leadership", "stability"],
        },
    ]
    if family == "backend":
        base_rounds[2]["focuses"] = ["implementation_detail", "problem_solving", "ownership"]
    elif family == "frontend":
        base_rounds[2]["focuses"] = ["implementation_detail", "communication", "problem_solving"]
    elif family == "design":
        base_rounds[2]["focuses"] = ["business_understanding", "communication", "tradeoff_reasoning"]
        base_rounds[3]["focuses"] = ["cross_team_execution", "leadership", "tradeoff_reasoning"]
    return base_rounds


def build_template_payload_from_answers(answers: TemplateWizardAnswers) -> dict[str, Any]:
    catalog = load_template_catalog()
    preset_choices = {item.template_id for item in catalog.preset_templates}
    inherits_from = answers.inherits_from if answers.inherits_from in preset_choices else ""
    template_id = slugify(answers.display_name or answers.target_role)
    rounds = default_rounds_for_role_family(answers.role_family)
    return {
        "template_id": template_id,
        "display_name": answers.display_name or answers.target_role,
        "template_type": "user",
        "version": 1,
        "enabled": True,
        "aliases": list(dict.fromkeys([answers.target_role, *answers.aliases])),
        "inherits_from": inherits_from,
        "target_role": answers.target_role,
        "role_family": answers.role_family,
        "candidate_level": answers.candidate_level,
        "supported_levels": sorted(set([answers.candidate_level, *sorted(DEFAULT_ALLOWED_LEVELS)])),
        "default_language": answers.default_language,
        "default_speech_language": answers.default_language if answers.default_language != "bilingual" else "auto",
        "rounds": rounds,
        "persona_defaults": {
            "default_persona": "引导教练型",
        },
        "question_bank_rules": {
            "allowed_rounds": [item["round_id"] for item in rounds],
            "allowed_levels": sorted(DEFAULT_ALLOWED_LEVELS),
            "allowed_languages": ["zh", "en", "bilingual"],
            "allowed_difficulties": ["L1", "L2", "L3", "L4", "L5"],
        },
    }


def save_user_template_payload(payload: dict[str, Any], output_dir: str | Path | None = None) -> Path:
    directory = Path(output_dir) if output_dir else USER_TEMPLATE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    output_path = directory / f"{payload['template_id']}.yaml"
    output_path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return output_path


def needs_template_creation(user_request: str, template_match: TemplateMatch | None) -> bool:
    lowered = str(user_request or "").strip().lower()
    trigger_texts = ["新建模板", "创建模板", "create template", "new template", "自定义模板", "岗位模板"]
    if any(item in lowered for item in trigger_texts):
        return True
    if template_match is None:
        return False
    return template_match.reason == "default_fallback" and template_match.confidence <= 0.4


def run_template_creation_dialog(
    prompter: SetupPrompter,
    *,
    requested_role: str = "",
    requested_role_family: str = "",
    requested_language: str = "",
    requested_level: str = "",
) -> tuple[InterviewTemplate, Path]:
    catalog = load_template_catalog()
    preset_ids = [item.template_id for item in catalog.preset_templates]
    target_role = requested_role or prompter.ask_text("template_target_role", "你要创建什么岗位模板？", "", allow_empty=False)
    display_name = prompter.ask_text("template_display_name", "这个模板的展示名称是什么？", f"{target_role} Interview")
    inferred_role_family = requested_role_family or infer_role_family_from_text(target_role)
    role_family = prompter.ask_choice(
        "template_role_family",
        "岗位所属 role family 是什么？",
        ["android", "backend", "frontend", "product", "design", "general"],
        inferred_role_family if inferred_role_family in {"android", "backend", "frontend", "product", "design", "general"} else "general",
    )
    candidate_level = prompter.ask_choice(
        "template_candidate_level",
        "这个模板默认面向哪个级别？",
        sorted(DEFAULT_ALLOWED_LEVELS),
        requested_level or "senior",
    )
    default_language = prompter.ask_choice(
        "template_default_language",
        "这个模板默认使用什么语言？",
        ["zh", "en", "bilingual"],
        requested_language or "zh",
    )
    inherits_from = ""
    if preset_ids:
        suggested_parent = next((item for item in preset_ids if role_family in item), preset_ids[0])
        if prompter.ask_yes_no("template_inherit_enabled", "是否基于现有预设模板继承？", True):
            inherits_from = prompter.ask_choice(
                "template_inherit_from",
                "请选择继承的预设模板",
                preset_ids,
                suggested_parent,
            )
    aliases_text = prompter.ask_text(
        "template_aliases",
        "还需要补充哪些自然语言别名？用逗号分隔，可留空",
        target_role,
    )
    payload = build_template_payload_from_answers(
        TemplateWizardAnswers(
            display_name=display_name,
            target_role=target_role,
            role_family=role_family,
            candidate_level=candidate_level,
            default_language=default_language,
            inherits_from=inherits_from,
            aliases=parse_csv_text(aliases_text),
        )
    )
    output_path = save_user_template_payload(payload)
    prompter.show_message(f"已创建用户模板：{output_path}")
    refreshed = load_template_catalog()
    return refreshed.by_id[payload["template_id"]], output_path


def run_conversational_intake(
    prompter: SetupPrompter,
    *,
    template_id: str = "",
    target_role: str = "",
    role_family: str = "",
    jd_input: str = "",
    resume_input: str = "",
    level: str = "",
    language: str = "",
    allow_missing_materials: bool = False,
    allow_template_creation: bool = True,
    force_create_template: bool = False,
) -> IntakeResolution:
    notes: list[str] = []
    role_query = target_role
    resolved_level = level or "senior"
    resolved_language = language or "zh"

    if not role_query:
        role_query = prompter.ask_text("intake_target_role", "这次你要模拟的目标岗位是什么？", "", allow_empty=False)
    if not role_family:
        role_family = infer_role_family_from_text(role_query)

    template_match = resolve_template(
        template_id=template_id,
        query=role_query,
        target_role=role_query,
        role_family=role_family,
    )
    created_template_path = ""
    created_template_id = ""

    should_create_template = force_create_template or needs_template_creation(role_query, template_match)
    if allow_template_creation and should_create_template:
        if prompter.ask_yes_no("intake_create_template", "当前没有高置信命中的模板，是否现在新建一个可复用模板？", True):
            created_template, created_path = run_template_creation_dialog(
                prompter,
                requested_role=role_query,
                requested_role_family=role_family,
                requested_language=resolved_language,
                requested_level=resolved_level,
            )
            template_match = TemplateMatch(
                template=created_template,
                source=created_template.template_type,
                confidence=1.0,
                reason="user_created_template",
            )
            created_template_path = str(created_path)
            created_template_id = created_template.template_id
            notes.append(f"created_template={created_template.template_id}")

    if not jd_input:
        jd_input = prompter.ask_text(
            "intake_jd",
            "请提供岗位 JD 路径、URL，或直接粘贴 JD 内容",
            "",
            allow_empty=allow_missing_materials,
        )
    if not resume_input:
        resume_input = prompter.ask_text(
            "intake_resume",
            "请提供个人简历路径、URL，或直接粘贴简历内容",
            "",
            allow_empty=allow_missing_materials,
        )
    if not resolved_level:
        resolved_level = prompter.ask_choice("intake_level", "候选人目标级别是什么？", sorted(DEFAULT_ALLOWED_LEVELS), "senior")
    if not resolved_language:
        resolved_language = prompter.ask_choice("intake_language", "面试默认使用什么语言？", ["zh", "en", "bilingual"], "zh")

    if not jd_input or not resume_input:
        if allow_missing_materials:
            notes.append("missing_materials_allowed")
        else:
            proceed = prompter.ask_yes_no("intake_continue_missing", "JD 或简历仍缺失，是否按泛化 mock interview 继续？", False)
            if not proceed:
                raise RuntimeError("Interview setup stopped because required materials were not provided.")
            notes.append("continue_without_full_materials")

    return IntakeResolution(
        template_match=template_match,
        jd_input=jd_input,
        resume_input=resume_input,
        level=resolved_level,
        language=resolved_language,
        created_template_path=created_template_path,
        created_template_id=created_template_id,
        notes=notes,
    )
