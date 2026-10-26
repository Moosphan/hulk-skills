import argparse
import json
import math
import os
import sys
from pathlib import Path

from . import __version__
from .core import intersect_ranges, phrase_range, select_ranges, speech_ranges
from .media import cut, detect_silences, export, extract, fingerprint, probe, require_ffmpeg, run, validate_audio
from .runtime import Runtime
from .sources import acquire


def common_options(parser):
    parser.add_argument("--cache-dir", default=os.environ.get("CLEAN_VOICE_CACHE", str(Path.home() / ".cache/clean-voice")))
    parser.add_argument("--threads", type=int, default=4)
    for component in ["separation", "denoise", "transcribe", "download"]:
        parser.add_argument(f"--{component}-python")
    for component in ["separation", "denoise"]:
        parser.add_argument(f"--{component}-model")


def parser():
    root = argparse.ArgumentParser(description="Clean Voice: extract, separate, denoise and edit speech. Natural language is interpreted by the host agent.")
    root.add_argument("--version", action="version", version=__version__)
    commands = root.add_subparsers(dest="command", required=True)
    doctor = commands.add_parser("doctor", help="Report tool, runtime and model availability as JSON")
    common_options(doctor)
    setup = commands.add_parser("setup", help="Install isolated optional runtimes and download models")
    common_options(setup)
    setup.add_argument("--component", choices=["all", "separation", "denoise", "transcribe", "download"], default="all")
    for name in ["process", "transcribe"]:
        operation = commands.add_parser(name)
        common_options(operation)
        operation.add_argument("--input", required=True, help="Local audio/video file or HTTP(S) URL")
        operation.add_argument("--output", required=True, type=Path, help="A new output directory")
        operation.add_argument("--cookies", type=Path, help="Explicitly provided Netscape cookie file for yt-dlp")
        operation.add_argument("--asr-model", default="small")
        operation.add_argument("--language", default=None)
        if name == "process":
            operation.add_argument("--mode", choices=["clean", "separate", "denoise", "extract"], default="clean")
            operation.add_argument("--denoiser", choices=["neural", "spectral"], default="neural")
            operation.add_argument("--keep", action="append", default=[])
            operation.add_argument("--remove", action="append", default=[])
            operation.add_argument("--keep-text", action="append", default=[])
            operation.add_argument("--remove-text", action="append", default=[])
            operation.add_argument("--transcript", type=Path)
            operation.add_argument("--occurrence", type=int)
            operation.add_argument("--text-padding", type=float, default=0.06)
            operation.add_argument("--remove-silence", action="store_true")
            operation.add_argument("--silence-threshold", type=float, default=-40)
            operation.add_argument("--silence-minimum", type=float, default=0.6)
            operation.add_argument("--silence-padding", type=float, default=0.15)
            operation.add_argument("--no-normalize", action="store_true")
            operation.add_argument("--plan-only", action="store_true", help="Decode and report edits without separation/export")
    return root


def notify(stage):
    print(json.dumps({"stage": stage}, ensure_ascii=False), file=sys.stderr, flush=True)


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def transcribe(runtime, original, destination, options):
    runtime.worker("transcribe", original, destination, component="transcribe", model=options.asr_model, language=options.language, model_cache=runtime.cache / "models/whisper")
    data = json.loads(destination.read_text(encoding="utf-8"))
    data["audio_sha256"] = fingerprint(original)
    write_json(destination, data)
    return data


def edits(options, runtime, original, duration, work):
    keep = list(options.keep)
    remove = list(options.remove)
    if options.keep_text or options.remove_text:
        data = json.loads(options.transcript.read_text(encoding="utf-8")) if options.transcript else transcribe(runtime, original, work / "transcript.json", options)
        expected = data.get("audio_sha256")
        if expected and expected != fingerprint(original):
            raise ValueError("Transcript source fingerprint does not match this audio; transcribe this source again")
        words = data.get("words") or [word for segment in data.get("segments", []) for word in segment.get("words", [])]
        if not words:
            raise ValueError("Text editing needs word timestamps; run transcribe first")
        for phrases, target in [(options.keep_text, keep), (options.remove_text, remove)]:
            for phrase in phrases:
                start, end = phrase_range(words, phrase, options.occurrence, options.text_padding)
                if start >= duration or end > duration + options.text_padding + 0.1:
                    raise ValueError("Transcript phrase falls outside this audio")
                target.append(f"{start:.9f}-{min(end, duration):.9f}")
    ranges = select_ranges(duration, keep, remove)
    if options.remove_silence:
        silences = detect_silences(original, duration, options.silence_threshold, options.silence_minimum)
        ranges = intersect_ranges(ranges, speech_ranges(duration, silences, options.silence_padding))
    return ranges


def operate(options, runtime):
    require_ffmpeg()
    output = options.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    work = output / "work"
    work.mkdir()
    notify("acquire")
    source = acquire(options.input, work, runtime, options.cookies)
    original = output / "original.wav"
    extract(source, original)
    metadata = probe(original)
    if options.command == "transcribe":
        notify("transcribe")
        transcript_path = output / "transcript.json"
        transcribe(runtime, original, transcript_path, options)
        return {"status": "complete", "transcript": str(transcript_path), "audio": str(original)}
    ranges = edits(options, runtime, original, metadata["duration"], work)
    report = {"version": __version__, "source": options.input, "source_sha256": fingerprint(original), "source_duration": metadata["duration"], "source_ranges": ranges, "mode": options.mode, "denoiser": options.denoiser, "status": "planned"}
    report_path = output / "report.json"
    write_json(report_path, report)
    if options.plan_only:
        return {**report, "report": str(report_path)}
    selected = work / "selected.wav"
    notify("cut")
    cut(original, selected, ranges)
    current = selected
    if options.mode in ["clean", "separate"]:
        notify("separate")
        separation_input = work / "separation-44k.wav"
        extract(selected, separation_input, sample_rate=44100, channels=2)
        current = work / "vocals.wav"
        runtime.worker("separate", separation_input, current, component="separation")
    if options.mode in ["clean", "denoise"]:
        notify("denoise")
        denoise_input = current
        enhanced = work / "enhanced.wav"
        if options.denoiser == "neural":
            prepared = work / "speech-16k.wav"
            extract(denoise_input, prepared, sample_rate=16000, mono=True)
            runtime.worker("enhance", prepared, enhanced, component="denoise")
        else:
            run(["ffmpeg", "-nostdin", "-v", "error", "-n", "-i", denoise_input, "-af", "highpass=f=70,afftdn=nr=12:nf=-45:tn=1:gs=6", "-c:a", "pcm_f32le", enhanced])
        current = enhanced
    notify("export_and_validate")
    wav, m4a = export(current, output, not options.no_normalize)
    expected_duration = sum(end - start for start, end in ranges)
    validations = {path.name: validate_audio(path, expected_duration) for path in [wav, m4a]}
    report.update({"status": "complete", "output_duration": validations[wav.name]["duration"], "files": {"wav": str(wav), "m4a": str(m4a), "original": str(original)}, "validation": validations, "limits": "Speech/music separation may retain overlapping voices, singing, reverb or sound effects. ASR edits need review. No subjective listening verification is implied."})
    write_json(report_path, report)
    return {"status": "complete", "files": report["files"], "report": str(report_path)}


def main():
    options = parser().parse_args()
    try:
        if not 1 <= options.threads <= 64:
            raise ValueError("--threads must be between 1 and 64")
        runtime = Runtime(options)
        if options.command == "doctor":
            result = runtime.doctor()
        elif options.command == "setup":
            result = runtime.setup(options.component)
        else:
            result = operate(options, runtime)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as error:
        print(json.dumps({"status": "error", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
