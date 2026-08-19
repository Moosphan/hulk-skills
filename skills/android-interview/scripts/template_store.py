from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from profile_schema import DEFAULT_TEMPLATE_ID, InterviewTemplate


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
PRESET_TEMPLATE_DIR = SKILL_DIR / "data" / "presets"
USER_TEMPLATE_DIR = SKILL_DIR / "data" / "user-templates"


@dataclass
class TemplateRecord:
    template_id: str
    payload: dict[str, Any]
    source: str
    path: Path


@dataclass
class TemplateCatalog:
    preset_templates: list[InterviewTemplate]
    user_templates: list[InterviewTemplate]
    all_templates: list[InterviewTemplate]
    by_id: dict[str, InterviewTemplate]


def _read_template_payload(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        payload = json.loads(text)
    else:
        payload = yaml.safe_load(text) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Template file must contain a mapping: {path}")
    return payload


def _discover_template_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    files = [path for path in sorted(directory.iterdir()) if path.is_file() and path.suffix.lower() in {".yaml", ".yml", ".json"}]
    return files


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(dict(merged[key]), value)
            continue
        merged[key] = value
    return merged


def _collect_template_records(directory: Path, source: str) -> list[TemplateRecord]:
    records: list[TemplateRecord] = []
    for path in _discover_template_files(directory):
        payload = _read_template_payload(path)
        template_id = str(payload.get("template_id", path.stem)).strip() or path.stem
        payload = dict(payload)
        payload.setdefault("template_id", template_id)
        payload.setdefault("template_type", source)
        records.append(TemplateRecord(template_id=template_id, payload=payload, source=source, path=path))
    return records


def _resolve_template_payload(
    template_id: str,
    raw_records: dict[str, TemplateRecord],
    resolved: dict[str, dict[str, Any]],
    stack: set[str],
) -> dict[str, Any]:
    if template_id in resolved:
        return resolved[template_id]
    if template_id in stack:
        raise ValueError(f"Cyclic template inheritance detected for '{template_id}'.")
    record = raw_records[template_id]
    stack.add(template_id)
    payload = dict(record.payload)
    parent_id = str(payload.get("inherits_from", "")).strip()
    merged = payload
    if parent_id:
        if parent_id not in raw_records:
            raise ValueError(f"Template '{template_id}' inherits from missing template '{parent_id}'.")
        parent_payload = _resolve_template_payload(parent_id, raw_records, resolved, stack)
        merged = _deep_merge(parent_payload, payload)
    merged["template_id"] = template_id
    merged["template_type"] = str(payload.get("template_type", record.source)).strip() or record.source
    merged["_source_path"] = str(record.path)
    resolved[template_id] = merged
    stack.remove(template_id)
    return merged


def load_template_catalog(
    *,
    preset_dir: str | Path | None = None,
    user_dir: str | Path | None = None,
) -> TemplateCatalog:
    preset_path = Path(preset_dir) if preset_dir else PRESET_TEMPLATE_DIR
    user_path = Path(user_dir) if user_dir else USER_TEMPLATE_DIR

    preset_records = _collect_template_records(preset_path, "preset")
    user_records = _collect_template_records(user_path, "user")
    raw_records: dict[str, TemplateRecord] = {item.template_id: item for item in preset_records}
    for item in user_records:
        raw_records[item.template_id] = item

    resolved_payloads: dict[str, dict[str, Any]] = {}
    for template_id in list(raw_records.keys()):
        _resolve_template_payload(template_id, raw_records, resolved_payloads, set())

    preset_templates: list[InterviewTemplate] = []
    user_templates: list[InterviewTemplate] = []
    by_id: dict[str, InterviewTemplate] = {}
    for template_id, payload in resolved_payloads.items():
        template = InterviewTemplate.from_dict(payload, source_path=str(payload.get("_source_path", "")))
        if not template.enabled:
            continue
        by_id[template_id] = template
        if template.template_type == "user":
            user_templates.append(template)
        else:
            preset_templates.append(template)
    preset_templates.sort(key=lambda item: item.template_id)
    user_templates.sort(key=lambda item: item.template_id)
    all_templates = [*user_templates, *preset_templates]
    return TemplateCatalog(
        preset_templates=preset_templates,
        user_templates=user_templates,
        all_templates=all_templates,
        by_id=by_id,
    )


def load_default_template(catalog: TemplateCatalog | None = None) -> InterviewTemplate:
    catalog = catalog or load_template_catalog()
    if DEFAULT_TEMPLATE_ID in catalog.by_id:
        return catalog.by_id[DEFAULT_TEMPLATE_ID]
    if catalog.preset_templates:
        return catalog.preset_templates[0]
    if catalog.user_templates:
        return catalog.user_templates[0]
    raise ValueError("No interview templates are available.")

