#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist"
DEFAULT_PLATFORMS = ("claude-code", "codex")


def sha256_for_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_skill_dirs(root: Path) -> list[Path]:
    skills_root = root / "skills"
    if not skills_root.exists():
        return []
    return sorted(
        path for path in skills_root.iterdir() if path.is_dir() and (path / "SKILL.md").exists()
    )


def copy_tree(src: Path, dest: Path) -> None:
    if not src.exists():
        return
    if src.is_file():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return
    for path in sorted(src.rglob("*")):
        if "__pycache__" in path.parts or path.name.endswith(".pyc"):
            continue
        if path.is_dir():
            continue
        rel = path.relative_to(src)
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def build_package(skill_dir: Path, platform: str, version: str) -> dict[str, str]:
    skill_name = skill_dir.name
    platform_dir = DIST_DIR / "packages" / platform
    platform_dir.mkdir(parents=True, exist_ok=True)

    archive_name = f"{skill_name}-{platform}-{version}.zip"
    archive_path = platform_dir / archive_name
    staging_root = Path(tempfile.mkdtemp(prefix=f"{skill_name}-{platform}-"))
    staging_dir = staging_root / skill_name

    try:
        copy_tree(skill_dir / "SKILL.md", staging_dir / "SKILL.md")
        copy_tree(skill_dir / "references", staging_dir / "references")
        copy_tree(skill_dir / "scripts", staging_dir / "scripts")
        copy_tree(skill_dir / "assets", staging_dir / "assets")

        if platform == "codex":
            copy_tree(skill_dir / "agents", staging_dir / "agents")
        overlay_dir = skill_dir / "platforms" / platform
        copy_tree(overlay_dir, staging_dir)

        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(staging_dir.rglob("*")):
                if path.is_file():
                    zf.write(path, path.relative_to(staging_root))
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)

    return {
        "skill": skill_name,
        "platform": platform,
        "archive": str(archive_path.relative_to(ROOT)),
        "sha256": sha256_for_file(archive_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Claude Code and Codex skill packages.")
    parser.add_argument("--version", default="local", help="Version label used in archive names.")
    parser.add_argument(
        "--platform",
        action="append",
        choices=DEFAULT_PLATFORMS,
        help="Limit packaging to specific platforms.",
    )
    parser.add_argument("--skill", action="append", help="Limit packaging to specific skills.")
    parser.add_argument("--clean", action="store_true", help="Remove dist before building.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.clean and DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    selected_platforms = list(args.platform or DEFAULT_PLATFORMS)
    selected_skills = set(args.skill or [])

    packages: list[dict[str, str]] = []
    for skill_dir in iter_skill_dirs(ROOT):
        if selected_skills and skill_dir.name not in selected_skills:
            continue
        for platform in selected_platforms:
            packages.append(build_package(skill_dir, platform, args.version))

    manifest = {"version": args.version, "packages": packages}
    manifest_path = DIST_DIR / f"package-manifest-{args.version}.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {manifest_path.relative_to(ROOT)}")
    for pkg in packages:
        print(f"built {pkg['archive']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
