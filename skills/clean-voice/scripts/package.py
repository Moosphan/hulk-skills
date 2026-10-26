import argparse
import json
import zipfile
from pathlib import Path

from install import CONTENTS, ROOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    target = options.output.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in CONTENTS:
            source = ROOT / name
            paths = sorted(source.rglob("*")) if source.is_dir() else [source]
            for path in paths:
                if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc" and path.name != ".DS_Store":
                    archive.write(path, str(Path("clean-voice") / path.relative_to(ROOT)))
    print(json.dumps({"archive": str(target), "bytes": target.stat().st_size}, ensure_ascii=False))


if __name__ == "__main__":
    main()
