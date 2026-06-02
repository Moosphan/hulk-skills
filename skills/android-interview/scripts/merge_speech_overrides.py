#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge missing-speech-overrides.json back into a reusable formal speech-overrides.json."
    )
    parser.add_argument("--base", required=True, help="Existing formal speech-overrides.json. If the file does not exist, a new one will be created.")
    parser.add_argument("--missing", required=True, help="Path to missing-speech-overrides.json captured from an interactive session.")
    parser.add_argument("--output", required=True, help="Path to write the merged speech-overrides.json.")
    parser.add_argument(
        "--merge-mode",
        default="fill-missing",
        choices=["fill-missing", "overwrite-empty", "overwrite-all"],
        help="fill-missing keeps existing formal entries; overwrite-empty also replaces blank strings; overwrite-all always replaces with missing payload values.",
    )
    return parser.parse_args()


def load_json_or_empty(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_payload_shape(payload: dict[str, Any] | None) -> dict[str, Any]:
    data = dict(payload or {})
    data.setdefault("meta", {})
    data.setdefault("questions", {})
    data.setdefault("follow_up_categories", {})
    return data


def should_replace(existing_value: str, incoming_value: str, merge_mode: str) -> bool:
    if not str(incoming_value or "").strip():
        return False
    current = str(existing_value or "").strip()
    if merge_mode == "overwrite-all":
        return True
    if merge_mode == "overwrite-empty":
        return not current
    return not current


def merge_question_entry(base_entry: dict[str, Any], missing_entry: dict[str, Any], merge_mode: str) -> int:
    updates = 0
    base_entry.setdefault("spoken_question", {})
    base_entry.setdefault("spoken_follow_ups", {})

    for language, incoming_value in dict(missing_entry.get("spoken_question", {})).items():
        current_value = str(base_entry["spoken_question"].get(language, ""))
        if should_replace(current_value, str(incoming_value), merge_mode):
            base_entry["spoken_question"][language] = str(incoming_value).strip()
            updates += 1

    missing_follow_ups = dict(missing_entry.get("spoken_follow_ups", {}))
    for language, incoming_values in missing_follow_ups.items():
        incoming_list = [str(item).strip() for item in list(incoming_values or [])]
        current_list = list(base_entry["spoken_follow_ups"].get(language, []) or [])
        if len(current_list) < len(incoming_list):
            current_list.extend([""] * (len(incoming_list) - len(current_list)))
        changed = False
        for index, incoming_value in enumerate(incoming_list):
            existing_value = current_list[index] if index < len(current_list) else ""
            if should_replace(existing_value, incoming_value, merge_mode):
                current_list[index] = incoming_value
                updates += 1
                changed = True
        if changed:
            base_entry["spoken_follow_ups"][language] = current_list
        elif language not in base_entry["spoken_follow_ups"] and current_list:
            base_entry["spoken_follow_ups"][language] = current_list

    return updates


def merge_question_payload(base_questions: dict[str, Any], missing_questions: dict[str, Any], merge_mode: str) -> tuple[int, int]:
    updated_questions = 0
    updated_fields = 0
    for question_id, missing_entry_raw in missing_questions.items():
        missing_entry = dict(missing_entry_raw or {})
        base_entry = dict(base_questions.get(question_id, {}) or {})
        if question_id not in base_questions:
            base_questions[question_id] = base_entry
        for key in ("title", "round", "source_path"):
            if str(missing_entry.get(key, "")).strip() and not str(base_entry.get(key, "")).strip():
                base_entry[key] = missing_entry[key]
        field_updates = merge_question_entry(base_entry, missing_entry, merge_mode)
        if field_updates:
            updated_questions += 1
            updated_fields += field_updates
        base_questions[question_id] = base_entry
    return updated_questions, updated_fields


def merge_follow_up_categories(base_categories: dict[str, Any], missing_categories: dict[str, Any], merge_mode: str) -> tuple[int, int]:
    updated_categories = 0
    updated_fields = 0
    for category, missing_entry_raw in missing_categories.items():
        missing_entry = dict(missing_entry_raw or {})
        base_entry = dict(base_categories.get(category, {}) or {})
        if category not in base_categories:
            base_categories[category] = base_entry
        category_updates = 0
        for language, incoming_value in missing_entry.items():
            current_value = str(base_entry.get(language, ""))
            if should_replace(current_value, str(incoming_value), merge_mode):
                base_entry[language] = str(incoming_value).strip()
                category_updates += 1
                updated_fields += 1
        if category_updates:
            updated_categories += 1
        base_categories[category] = base_entry
    return updated_categories, updated_fields


def merge_payloads(base_payload: dict[str, Any], missing_payload: dict[str, Any], merge_mode: str) -> tuple[dict[str, Any], dict[str, Any]]:
    merged = ensure_payload_shape(base_payload)
    missing = ensure_payload_shape(missing_payload)

    updated_questions, updated_question_fields = merge_question_payload(
        merged["questions"],
        dict(missing.get("questions", {})),
        merge_mode,
    )
    updated_categories, updated_category_fields = merge_follow_up_categories(
        merged["follow_up_categories"],
        dict(missing.get("follow_up_categories", {})),
        merge_mode,
    )

    merged_meta = merged.setdefault("meta", {})
    merged_meta["merged_at"] = datetime.now().isoformat()
    merged_meta["merge_mode"] = merge_mode
    merged_meta["merged_from_missing"] = str(missing.get("meta", {}).get("session_id", ""))
    merged_meta["merged_missing_source_path"] = str(missing.get("meta", {}).get("speech_overrides_source_path", ""))
    merged_meta["merged_question_count"] = len(merged.get("questions", {}))
    merged_meta["merged_follow_up_category_count"] = len(merged.get("follow_up_categories", {}))
    merged_meta["note"] = "Merged from formal overrides plus missing-speech-overrides runtime captures."

    stats = {
        "updated_questions": updated_questions,
        "updated_question_fields": updated_question_fields,
        "updated_follow_up_categories": updated_categories,
        "updated_follow_up_category_fields": updated_category_fields,
        "total_questions": len(merged.get("questions", {})),
        "total_follow_up_categories": len(merged.get("follow_up_categories", {})),
    }
    return merged, stats


def main() -> int:
    args = parse_args()
    base_path = Path(args.base)
    missing_path = Path(args.missing)
    output_path = Path(args.output)

    base_payload = load_json_or_empty(base_path)
    missing_payload = load_json_or_empty(missing_path)
    merged_payload, stats = merge_payloads(base_payload, missing_payload, args.merge_mode)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(merged_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"output={output_path}")
    print(f"merge_mode={args.merge_mode}")
    print(f"stats={json.dumps(stats, ensure_ascii=False, sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
