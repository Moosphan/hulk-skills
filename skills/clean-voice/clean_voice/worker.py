import argparse
import json
import os
import shutil
import sys
from pathlib import Path


def event(stage, **values):
    print(json.dumps({"stage": stage, **values}, ensure_ascii=False), flush=True)


def prepare(options):
    options.output.mkdir(parents=True, exist_ok=True)
    if options.component == "separation":
        from huggingface_hub import hf_hub_download

        source = hf_hub_download("adefossez/HTDemucs-ft", "04573f0d.safetensors")
        shutil.copy2(source, options.output / "04573f0d.safetensors")
    else:
        from modelscope import snapshot_download

        source = Path(snapshot_download("iic/speech_zipenhancer_ans_multiloss_16k_base"))
        for name in ["configuration.json", "pytorch_model.bin"]:
            shutil.copy2(source / name, options.output / name)
    event("prepared", component=options.component, path=str(options.output))


def separate(options):
    import numpy as np
    import soundfile as sf
    import torch
    from demucs.apply import apply_model
    from demucs.htdemucs import HTDemucs
    from fractions import Fraction
    from safetensors import safe_open
    from safetensors.torch import load_file

    with safe_open(options.model, framework="pt") as handle:
        metadata = handle.metadata()
        if metadata.get("klass") != "demucs.htdemucs.HTDemucs":
            raise ValueError("Expected an HTDemucs safetensors checkpoint")
        configuration = json.loads(metadata["kwargs"])
    segment = configuration.get("segment")
    if isinstance(segment, dict):
        configuration["segment"] = Fraction(segment["numerator"], segment["denominator"])
    torch.set_num_threads(options.threads)
    torch.manual_seed(0)
    model = HTDemucs(**configuration)
    model.load_state_dict(load_file(options.model), strict=True)
    model.eval()
    samples, sample_rate = sf.read(options.input, dtype="float32", always_2d=True)
    if sample_rate != 44100 or samples.shape[1] != 2:
        raise ValueError("Separation worker requires 44.1 kHz stereo WAV")
    waveform = torch.from_numpy(samples.T.copy())
    reference = waveform.mean(0)
    mean = reference.mean()
    deviation = reference.std().clamp_min(1e-8)
    if waveform.abs().max() < 1e-7:
        raise ValueError("Input is silent")
    with torch.inference_mode():
        stems = apply_model(model, ((waveform - mean) / deviation)[None], device="cpu", shifts=1, split=True, overlap=0.25, progress=True, num_workers=0)[0]
    vocals = (stems[model.sources.index("vocals")] * deviation + mean).cpu().numpy().T
    if not np.isfinite(vocals).all():
        raise ValueError("Separation produced nonfinite samples")
    peak = float(np.abs(vocals).max())
    if peak > 0.89:
        vocals *= 0.89 / peak
    sf.write(options.output, vocals, sample_rate, subtype="FLOAT")
    event("separation_complete", duration=len(vocals) / sample_rate)


def enhance(options):
    os.environ["MODELSCOPE_OFFLINE"] = "1"
    import numpy as np
    import soundfile as sf
    import torch
    from modelscope.pipelines import pipeline
    from modelscope.utils.constant import Tasks

    torch.set_num_threads(options.threads)
    enhancer = pipeline(Tasks.acoustic_noise_suppression, model=str(options.model), device="cpu")
    prepared = enhancer.preprocess(str(options.input))
    waveform = prepared["ndarray"].reshape(-1)
    length = prepared["nsamples"]
    window = 32000
    hop = 24000
    result = np.zeros(length, dtype=np.float64)
    normalization = np.zeros(length, dtype=np.float64)
    blend = np.maximum(np.hanning(window), 1e-3)
    with torch.inference_mode():
        for start in range(0, length, hop):
            end = min(start + window, length)
            chunk = np.zeros(window, dtype=np.float32)
            chunk[:end - start] = waveform[start:end]
            predicted = enhancer.model({"noisy": torch.from_numpy(chunk[None])})["wav_l2"][0].cpu().numpy().reshape(-1)
            if len(predicted) < end - start:
                raise ValueError("Enhancer returned a short chunk")
            result[start:end] += predicted[:end - start] * blend[:end - start]
            normalization[start:end] += blend[:end - start]
            event("enhancement", percent=round(end * 100 / length, 1))
    result /= normalization
    if not np.isfinite(result).all() or float(np.abs(result).max()) < 1e-7:
        raise ValueError("Enhancement produced silence or invalid samples")
    peak = float(np.abs(result).max())
    if peak > 0.89:
        result *= 0.89 / peak
    sf.write(options.output, result, 16000, subtype="FLOAT")
    event("enhancement_complete", duration=length / 16000)


def transcribe(options):
    import torch
    import whisper

    torch.set_num_threads(options.threads)
    model = whisper.load_model(str(options.model), device="cpu", download_root=str(options.model_cache))
    result = model.transcribe(str(options.input), language=options.language, word_timestamps=True, fp16=False, verbose=False)
    result["words"] = [word for segment in result.get("segments", []) for word in segment.get("words", [])]
    options.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    event("transcription_complete", words=len(result["words"]), path=str(options.output))


def download(options):
    import yt_dlp

    settings = {"format": "bestaudio/best", "outtmpl": str(options.output.parent / "download.%(ext)s"), "noplaylist": True, "overwrites": False, "quiet": True, "no_warnings": False, "progress_hooks": [lambda progress: event("download", status=progress.get("status")) if progress.get("status") == "finished" else None]}
    if options.cookies:
        if not options.cookies.is_file():
            raise ValueError("Provided cookie file does not exist")
        settings["cookiefile"] = str(options.cookies)
    with yt_dlp.YoutubeDL(settings) as downloader:
        information = downloader.extract_info(str(options.input), download=False)
        if information.get("_type") in ["playlist", "multi_video"]:
            raise ValueError("Specify one video rather than a playlist")
        if information.get("has_drm"):
            raise ValueError("DRM source cannot be processed")
        information = downloader.process_ie_result(information, download=True)
        filename = downloader.prepare_filename(information)
    options.output.write_text(json.dumps({"file": str(Path(filename).resolve()), "title": information.get("title")}, ensure_ascii=False), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["prepare", "separate", "enhance", "transcribe", "download"])
    parser.add_argument("--input")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model")
    parser.add_argument("--model-cache", type=Path)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--language")
    parser.add_argument("--cookies", type=Path)
    parser.add_argument("--component", choices=["separation", "denoise"])
    options = parser.parse_args()
    try:
        if options.stage != "prepare" and options.output.exists():
            raise FileExistsError(options.output)
        operations = {"prepare": prepare, "separate": separate, "enhance": enhance, "transcribe": transcribe, "download": download}
        operations[options.stage](options)
    except Exception as error:
        event("error", error=str(error))
        sys.exit(1)


if __name__ == "__main__":
    main()
