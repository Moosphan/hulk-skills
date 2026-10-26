import argparse
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENTS = ["SKILL.md", "README.md", "LICENSE", "THIRD-PARTY.md", "VALIDATION.md", "agents", "clean_voice", "scripts", "references", "tests", "pyproject.toml"]


def destination(target, home=None):
    home = home or Path.home()
    if target == "codex":
        return Path(os.environ["CODEX_HOME"]).expanduser() / "skills" if os.environ.get("CODEX_HOME") else home / ".agents/skills"
    return home / (".claude/skills" if target == "claude" else ".dsh/skills")


def copy_project(target):
    for name in CONTENTS:
        source = ROOT / name
        if source.is_dir():
            shutil.copytree(source, target / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
        else:
            shutil.copy2(source, target / name)


def main():
    parser = argparse.ArgumentParser(description="Install self-contained Clean Voice skills without editing host configuration")
    parser.add_argument("--target", choices=["claude", "codex", "dsh", "all"], required=True)
    parser.add_argument("--destination", type=Path, help="Override one host's skills parent directory")
    parser.add_argument("--replace", action="store_true", help="Back up an existing skill before replacement")
    parser.add_argument("--dry-run", action="store_true")
    options = parser.parse_args()
    try:
        if options.destination and options.target == "all":
            raise ValueError("Use --destination with one target at a time")
        targets = ["claude", "codex", "dsh"] if options.target == "all" else [options.target]
        results = []
        for host in targets:
            parent = (options.destination or destination(host)).expanduser().resolve()
            target = parent / "clean-voice"
            if target == ROOT or ROOT.is_relative_to(target) or target.is_relative_to(ROOT):
                raise ValueError("Install destination overlaps the source project")
            if target.exists() and not options.replace:
                raise FileExistsError(f"Skill exists: {target}; use --replace to back it up first")
            results.append({"host": host, "path": str(target), "dry_run": options.dry_run})
        if not options.dry_run:
            for result in results:
                target = Path(result["path"])
                target.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.TemporaryDirectory(prefix=".clean-voice-", dir=target.parent) as temporary:
                    staging = Path(temporary) / "clean-voice"
                    staging.mkdir()
                    copy_project(staging)
                    if target.exists():
                        backup_root = target.parent / ".clean-voice-backups"
                        backup_root.mkdir(exist_ok=True)
                        backup = backup_root / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
                        target.rename(backup)
                        result["backup"] = str(backup)
                    staging.rename(target)
        print(json.dumps(results, ensure_ascii=False, indent=2))
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
