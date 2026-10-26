import array
import hashlib
import json
import math
import re
import shutil
import subprocess
from pathlib import Path


def run(arguments, capture=True):
    result = subprocess.run([str(argument) for argument in arguments], capture_output=capture, text=capture)
    if result.returncode:
        detail = (result.stderr or "")[-4000:] if capture else "See worker output above"
        raise RuntimeError(f"{Path(str(arguments[0])).name} failed ({result.returncode}): {detail}")
    return result.stdout if capture else None


def require_ffmpeg():
    for name in ["ffmpeg", "ffprobe"]:
        if not shutil.which(name):
            raise ValueError(f"Missing {name}; install FFmpeg and add it to PATH")


def probe(path):
    data = json.loads(run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", path]))
    audio = next((stream for stream in data["streams"] if stream.get("codec_type") == "audio"), None)
    if not audio:
        raise ValueError("The source has no audio stream")
    duration = float(audio.get("duration") or data["format"]["duration"])
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("The source has no finite audio duration")
    return {"duration": duration, "sample_rate": int(audio["sample_rate"]), "channels": audio["channels"]}


def extract(source, destination, sample_rate=None, mono=False, channels=None):
    arguments = ["ffmpeg", "-nostdin", "-v", "error", "-n", "-i", source, "-map", "0:a:0", "-vn", "-map_metadata", "-1"]
    if sample_rate:
        arguments.extend(["-ar", sample_rate])
    if mono:
        arguments.extend(["-ac", "1"])
    elif channels:
        arguments.extend(["-ac", channels])
    arguments.extend(["-c:a", "pcm_f32le", destination])
    run(arguments)


def cut(source, destination, ranges):
    chains = []
    for index, (start, end) in enumerate(ranges):
        chains.append(f"[0:a:0]atrim=start={start:.9f}:end={end:.9f},asetpts=PTS-STARTPTS[part{index}]")
    chains.append("".join(f"[part{index}]" for index in range(len(ranges))) + f"concat=n={len(ranges)}:v=0:a=1[out]")
    run(["ffmpeg", "-nostdin", "-v", "error", "-n", "-i", source, "-filter_complex", ";".join(chains), "-map", "[out]", "-c:a", "pcm_f32le", destination])


def detect_silences(source, duration, threshold=-40, minimum=0.6):
    if not math.isfinite(threshold) or not -100 <= threshold <= -1 or not math.isfinite(minimum) or minimum <= 0:
        raise ValueError("Silence threshold must be -100..-1 dB; minimum duration must be positive")
    result = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-i", str(source), "-af", f"silencedetect=noise={threshold}dB:d={minimum}", "-f", "null", "-"], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-2000:])
    silences = []
    start = None
    for event, value in re.findall(r"silence_(start|end):\s*([\d.]+)", result.stderr):
        if event == "start":
            start = float(value)
        elif start is not None:
            silences.append((start, min(duration, float(value))))
            start = None
    if start is not None:
        silences.append((start, duration))
    return silences


def fingerprint(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def export(source, directory, normalize=True):
    wav = directory / "voice.wav"
    m4a = directory / "voice.m4a"
    arguments = ["ffmpeg", "-nostdin", "-v", "error", "-n", "-i", source]
    if normalize:
        measured = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-i", str(source), "-af", "loudnorm=I=-18:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True, check=True)
        match = re.search(r'\{\s*"input_i".*?\}', measured.stderr, re.S)
        if not match:
            raise ValueError("Could not measure output loudness")
        values = json.loads(match.group())
        if not all(math.isfinite(float(values[key])) for key in ["input_i", "input_tp", "input_lra", "input_thresh", "target_offset"]):
            raise ValueError("No measurable speech/audio remains; refusing a silent success")
        settings = "loudnorm=I=-18:TP=-1.5:LRA=11:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:measured_thresh={input_thresh}:offset={target_offset}:linear=true".format(**values)
        arguments.extend(["-af", settings])
    arguments.extend(["-ar", probe(source)["sample_rate"], "-c:a", "pcm_s24le", wav])
    run(arguments)
    run(["ffmpeg", "-nostdin", "-v", "error", "-n", "-i", wav, "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", m4a])
    return wav, m4a


def validate_audio(path, expected_duration):
    metadata = probe(path)
    process = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    peak = 0
    total = 0
    clipped = 0
    finite = True
    while True:
        block = process.stdout.read(65536)
        if not block:
            break
        samples = array.array("f", block)
        finite = finite and all(math.isfinite(value) for value in samples)
        peak = max(peak, max((abs(value) for value in samples), default=0))
        clipped += sum(abs(value) >= 1 for value in samples)
        total += len(samples)
    errors = process.stderr.read().decode(errors="replace")
    if process.wait() or not finite:
        raise ValueError(f"Audio decode validation failed: {errors[-2000:]}")
    decoded_duration = total / 16000
    if peak < 1e-6 or abs(decoded_duration - expected_duration) > 0.08:
        raise ValueError(f"Output is silent or duration changed: expected {expected_duration:.3f}, got {decoded_duration:.3f}")
    if clipped:
        raise ValueError(f"Output contains {clipped} full-scale samples; lower the level before delivery")
    return {**metadata, "decoded_duration": decoded_duration, "peak_dbfs": round(20 * math.log10(peak), 2), "clipped_samples": clipped}
