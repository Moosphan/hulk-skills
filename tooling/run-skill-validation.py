#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class CheckResult:
    status: str
    message: str


@dataclass
class ScenarioResult:
    skill: str
    platform: str
    name: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def failed(self) -> bool:
        return any(check.status == "FAIL" for check in self.checks)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_matrix(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError("validation matrix must be a mapping")
    return data


def scenario_file_path(root: Path, scenario: dict[str, Any]) -> Path | None:
    rel = scenario.get("scenario_file")
    if not rel:
        return None
    return root / "tests" / "scenarios" / Path(rel)


def validate_script_output(root: Path, validator: dict[str, Any]) -> list[CheckResult]:
    command = validator["command"]
    expected = validator.get("expected", {})
    proc = subprocess.run(
        command,
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    checks = []
    if proc.returncode != 0:
        checks.append(CheckResult("FAIL", f"command exited with {proc.returncode}"))
        if proc.stderr.strip():
            checks.append(CheckResult("FAIL", proc.stderr.strip()))
        return checks

    output = proc.stdout
    for needle in expected.get("contains", []):
        if needle in output:
            checks.append(CheckResult("PASS", f"contains {needle!r}"))
        else:
            checks.append(CheckResult("FAIL", f"missing {needle!r}"))

    return checks


def validate_skill_contract(root: Path, skill_name: str, validator: dict[str, Any]) -> list[CheckResult]:
    skill_md = root / "skills" / skill_name / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    checks = []
    for snippet in validator.get("required_snippets", []):
        if snippet in text:
            checks.append(CheckResult("PASS", f"contains {snippet!r}"))
        else:
            checks.append(CheckResult("FAIL", f"missing {snippet!r}"))
    return checks


def validate_scenario(root: Path, skill_name: str, scenario: dict[str, Any]) -> ScenarioResult:
    platform = scenario["platform"]
    name = scenario["name"]
    result = ScenarioResult(skill=skill_name, platform=platform, name=name)

    skill_dir = root / "skills" / skill_name
    skill_md = skill_dir / "SKILL.md"
    if skill_dir.is_dir():
        result.checks.append(CheckResult("PASS", f"skill dir exists: {skill_dir.relative_to(root)}"))
    else:
        result.checks.append(CheckResult("FAIL", f"missing skill dir: {skill_dir.relative_to(root)}"))

    if skill_md.exists():
        result.checks.append(CheckResult("PASS", f"skill file exists: {skill_md.relative_to(root)}"))
    else:
        result.checks.append(CheckResult("FAIL", f"missing skill file: {skill_md.relative_to(root)}"))

    platform_metadata = skill_dir / "agents" / "openai.yaml"
    if platform == "codex" and not platform_metadata.exists():
        result.checks.append(CheckResult("WARN", f"optional Codex metadata missing: {platform_metadata.relative_to(root)}"))

    scen_path = scenario_file_path(root, scenario)
    if scen_path is not None:
        if scen_path.exists():
            result.checks.append(CheckResult("PASS", f"scenario file exists: {scen_path.relative_to(root)}"))
        else:
            result.checks.append(CheckResult("FAIL", f"missing scenario file: {scen_path.relative_to(root)}"))

    validator = scenario.get("validator", {})
    vtype = validator.get("type")
    if vtype == "script-output":
        result.checks.extend(validate_script_output(root, validator))
    elif vtype == "skill-contract":
        result.checks.extend(validate_skill_contract(root, skill_name, validator))
    else:
        result.checks.append(CheckResult("WARN", f"no validator configured for {skill_name}/{name}"))

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run hulk-skills scenario validation.")
    parser.add_argument(
        "--matrix",
        default=str(repo_root() / "tests" / "scenarios" / "validation-matrix.yaml"),
        help="Path to the validation matrix.",
    )
    parser.add_argument("--skill", action="append", help="Limit to a specific skill.")
    parser.add_argument("--platform", action="append", help="Limit to a specific platform.")
    parser.add_argument("--json", action="store_true", help="Reserved for future machine output.")
    args = parser.parse_args()

    root = repo_root()
    matrix_path = Path(args.matrix)
    if not matrix_path.is_absolute():
        matrix_path = root / matrix_path

    data = load_matrix(matrix_path)
    allowed_skills = set(args.skill or [])
    allowed_platforms = set(args.platform or [])

    results: list[ScenarioResult] = []
    matrix_platforms = set(data.get("platforms", []))
    if allowed_platforms:
        matrix_platforms &= allowed_platforms

    for skill_name, scenarios in data.get("skills", {}).items():
        if allowed_skills and skill_name not in allowed_skills:
            continue
        for scenario in scenarios:
            if scenario.get("platform") not in matrix_platforms:
                continue
            results.append(validate_scenario(root, skill_name, scenario))

    failure_count = 0
    warn_count = 0
    for result in results:
        print(f"[{result.platform}] {result.skill} / {result.name}")
        for check in result.checks:
            print(f"  [{check.status}] {check.message}")
            if check.status == "FAIL":
                failure_count += 1
            elif check.status == "WARN":
                warn_count += 1

    print(
        f"\nSummary: {len(results)} scenarios, {failure_count} failures, {warn_count} warnings"
    )
    return 1 if failure_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
