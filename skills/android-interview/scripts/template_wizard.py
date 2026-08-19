#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from profile_schema import DEFAULT_ALLOWED_LEVELS
from conversation_setup import TemplateWizardAnswers, build_template_payload_from_answers, save_user_template_payload
from template_store import PRESET_TEMPLATE_DIR, USER_TEMPLATE_DIR, load_template_catalog


def slugify(text: str) -> str:
    value = "".join(ch.lower() if ch.isalnum() else "_" for ch in text.strip())
    collapsed = "_".join(part for part in value.split("_") if part)
    return collapsed or "custom_template"


def prompt_text(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default


def prompt_choice(label: str, choices: list[str], default: str) -> str:
    choice_text = "/".join(choices)
    while True:
        value = prompt_text(f"{label} ({choice_text})", default)
        if value in choices:
            return value
        print(f"Please choose one of: {choice_text}")


def build_template_payload(args: argparse.Namespace) -> dict:
    catalog = load_template_catalog()
    preset_choices = [item.template_id for item in catalog.preset_templates]
    display_name = args.display_name or prompt_text("Template display name", "My Interview Template")
    target_role = args.target_role or prompt_text("Target role", display_name)
    role_family = args.role_family or prompt_text("Role family", "general")
    candidate_level = args.candidate_level or prompt_choice("Candidate level", sorted(DEFAULT_ALLOWED_LEVELS), "senior")
    default_language = args.language or prompt_choice("Default language", ["zh", "en", "bilingual"], "zh")
    inherits_from = args.inherits_from
    if not inherits_from and preset_choices:
        suggested = preset_choices[0]
        inherits_from = prompt_text("Inherit from preset template ID (leave empty for none)", suggested)
        if inherits_from not in preset_choices:
            inherits_from = ""
    payload = build_template_payload_from_answers(
        TemplateWizardAnswers(
            display_name=display_name,
            target_role=target_role,
            role_family=role_family,
            candidate_level=candidate_level,
            default_language=default_language,
            inherits_from=inherits_from,
            aliases=[item.strip() for item in (args.aliases.split(",") if args.aliases else []) if item.strip()],
        )
    )
    payload["template_id"] = args.template_id or slugify(display_name)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a reusable user interview template.")
    parser.add_argument("--template-id", default="", help="Explicit template ID. Defaults to a slugified display name.")
    parser.add_argument("--display-name", default="", help="Display name for the template.")
    parser.add_argument("--target-role", default="", help="Target role name.")
    parser.add_argument("--role-family", default="", help="Role family, for example backend, android, pm.")
    parser.add_argument("--candidate-level", default="", help="Default candidate level.")
    parser.add_argument("--language", default="", help="Default interview language.")
    parser.add_argument("--inherits-from", default="", help="Preset template ID to inherit from.")
    parser.add_argument("--aliases", default="", help="Comma-separated aliases for natural-language matching.")
    parser.add_argument("--output-dir", default=str(USER_TEMPLATE_DIR), help="Directory used to save the generated user template.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_template_payload(args)
    output_path = save_user_template_payload(payload, args.output_dir)
    print(f"template_id={payload['template_id']}")
    print(f"output_path={output_path}")
    print(f"inherits_from={payload.get('inherits_from', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
