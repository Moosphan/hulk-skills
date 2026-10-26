import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = Path(__file__).resolve().parent
MODULES = {"separation": ["torch", "demucs", "safetensors", "soundfile"], "denoise": ["torch", "modelscope", "soundfile"], "transcribe": ["whisper"], "download": ["yt_dlp"]}


class Runtime:
    def __init__(self, options):
        self.options = options
        self.cache = Path(options.cache_dir).expanduser().resolve()

    def python(self, component, required=True):
        explicit = getattr(self.options, component + "_python", None) or os.environ.get(f"CLEAN_VOICE_{component.upper()}_PYTHON")
        candidates = [Path(explicit).expanduser()] if explicit else [self.cache / "envs" / component / ("Scripts/python.exe" if os.name == "nt" else "bin/python"), Path(sys.executable)]
        for candidate in candidates:
            if not candidate.is_file():
                continue
            script = "import importlib.util,sys; sys.exit(0 if all(importlib.util.find_spec(name) for name in " + repr(MODULES[component]) + ") else 1)"
            result = subprocess.run([str(candidate), "-c", script], capture_output=True)
            if result.returncode == 0:
                return candidate
        if required:
            raise ValueError(f"Missing {component} runtime; run: python scripts/voice.py setup --component {component}; or set CLEAN_VOICE_{component.upper()}_PYTHON")
        return None

    def model(self, component, required=True):
        explicit = getattr(self.options, component + "_model", None) or os.environ.get(f"CLEAN_VOICE_{component.upper()}_MODEL")
        if component == "separation":
            candidates = [Path(explicit).expanduser()] if explicit else [self.cache / "models/separation/04573f0d.safetensors"]
            hub = Path(os.environ.get("HF_HUB_CACHE", str(Path.home() / ".cache/huggingface/hub")))
            candidates.extend(sorted(hub.glob("models--adefossez--HTDemucs-ft/snapshots/*/04573f0d.safetensors")) if not explicit else [])
            result = next((path for path in candidates if path.is_file()), None)
        else:
            path = Path(explicit).expanduser() if explicit else self.cache / "models/denoise"
            result = path if all((path / filename).is_file() for filename in ["configuration.json", "pytorch_model.bin"]) else None
        if required and result is None:
            raise ValueError(f"Missing {component} model; run setup --component {component} or configure --{component}-model")
        return result

    def worker(self, stage, source, destination, component, **extra):
        python = self.python(component)
        arguments = [python, "-u", PACKAGE / "worker.py", stage, "--input", source, "--output", destination, "--threads", self.options.threads]
        if component in ["separation", "denoise"]:
            arguments.extend(["--model", self.model(component)])
        for key, value in extra.items():
            if value is not None:
                arguments.extend(["--" + key.replace("_", "-"), value])
        environment = dict(os.environ, PYTHONUNBUFFERED="1")
        result = subprocess.run([str(argument) for argument in arguments], stdout=sys.stderr, stderr=sys.stderr, env=environment)
        if result.returncode:
            raise RuntimeError(f"{stage} worker failed ({result.returncode}); the original and intermediate files remain available")

    def doctor(self):
        return {
            "ffmpeg": shutil.which("ffmpeg"), "ffprobe": shutil.which("ffprobe"), "cache": str(self.cache),
            "runtimes": {name: str(self.python(name, False) or "not installed") for name in MODULES},
            "models": {name: str(self.model(name, False) or "not installed") for name in ["separation", "denoise"]},
        }

    def setup(self, component):
        components = list(MODULES) if component == "all" else [component]
        for name in components:
            environment = self.cache / "envs" / name
            python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            environment.parent.mkdir(parents=True, exist_ok=True)
            if not python.is_file():
                subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True)
            subprocess.run([str(python), "-m", "pip", "install", "-r", str(PACKAGE / "requirements" / f"{name}.txt")], check=True, stdout=sys.stderr)
            if name in ["separation", "denoise"]:
                subprocess.run([str(python), "-u", str(PACKAGE / "worker.py"), "prepare", "--component", name, "--output", str(self.cache / "models" / name)], check=True, stdout=sys.stderr)
        return self.doctor()
