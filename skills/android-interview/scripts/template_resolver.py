from __future__ import annotations

import re
from dataclasses import dataclass

from profile_schema import InterviewTemplate
from template_store import TemplateCatalog, load_default_template, load_template_catalog


@dataclass
class TemplateMatch:
    template: InterviewTemplate
    source: str
    confidence: float
    reason: str


def _normalize_text(value: str) -> str:
    lowered = str(value or "").strip().lower()
    return re.sub(r"[\s_\-]+", "", lowered)


def _candidate_texts(template: InterviewTemplate) -> list[str]:
    texts = [template.template_id, template.display_name, template.target_role, template.role_family, *template.aliases]
    return [_normalize_text(item) for item in texts if _normalize_text(item)]


def resolve_template(
    *,
    template_id: str = "",
    query: str = "",
    target_role: str = "",
    role_family: str = "",
    catalog: TemplateCatalog | None = None,
) -> TemplateMatch:
    catalog = catalog or load_template_catalog()
    if template_id:
        resolved = catalog.by_id.get(template_id)
        if resolved is not None:
            return TemplateMatch(template=resolved, source=resolved.template_type, confidence=1.0, reason="template_id")

    search_values = [item for item in [query, target_role, role_family] if str(item).strip()]
    normalized_search_values = [_normalize_text(item) for item in search_values if _normalize_text(item)]
    candidates = [*catalog.user_templates, *catalog.preset_templates]

    for search_value in normalized_search_values:
        for template in candidates:
            if search_value in _candidate_texts(template):
                return TemplateMatch(template=template, source=template.template_type, confidence=0.96, reason="exact_alias")

    for search_value in normalized_search_values:
        for template in candidates:
            candidate_texts = _candidate_texts(template)
            if any(search_value in item or item in search_value for item in candidate_texts):
                return TemplateMatch(template=template, source=template.template_type, confidence=0.8, reason="fuzzy_alias")

    default_template = load_default_template(catalog)
    return TemplateMatch(template=default_template, source=default_template.template_type, confidence=0.4, reason="default_fallback")


def default_runtime_template(catalog: TemplateCatalog | None = None) -> InterviewTemplate:
    return load_default_template(catalog)

