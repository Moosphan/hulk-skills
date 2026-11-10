#!/usr/bin/env python3
"""紫鸦zya 配音生成器（Qwen3-TTS Base 参考音克隆）。

用法：
  ~/dsh-space/whale-video/.venv-tts/bin/python zya_tts.py lines.json <out_dir>

lines.json 结构：
  {"scenes": [{"id": "open", "lines": ["...", "..."]}, ...]}

输出：<out_dir>/<id>_01.wav ...（48k / 立体声 / -16 LUFS，已去首尾静音并加淡入淡出）
"""
import json
import os
import subprocess
import sys

import mlx.core as mx
from mlx_audio.tts.generate import generate_audio

SKILL = os.path.expanduser("~/.dsh/skills/ai-daily-paper")
CFG = json.load(open(os.path.join(SKILL, "voices/zya-voice.json")))
REF_AUDIO = os.path.join(SKILL, "voices/zya-ref-P.wav")
REF_TEXT = open(os.path.join(SKILL, "voices/zya-ref-P.txt")).read().strip()

POST = "aresample=48000,loudnorm=I=-16:TP=-1.5"


def dur(path: str) -> float:
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]
    ).decode())


def synth(text: str, out_wav: str, seed: int) -> None:
    raw_dir = os.path.dirname(out_wav) or "."
    prefix = "_raw_" + os.path.basename(out_wav).replace(".wav", "")
    mx.random.seed(seed)
    generate_audio(
        text=text,
        model=CFG["model"],
        lang_code="zh",
        ref_audio=REF_AUDIO,
        ref_text=REF_TEXT,
        temperature=CFG["sampling"]["temperature"],
        top_p=CFG["sampling"]["top_p"],
        repetition_penalty=CFG["sampling"]["repetition_penalty"],
        output_path=raw_dir,
        file_prefix=prefix,
        save=True,
        verbose=False,
    )
    raw = os.path.join(raw_dir, prefix + "_000.wav")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", POST,
         "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", out_wav],
        check=True,
    )
    os.remove(raw)


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    script = json.load(open(sys.argv[1]))
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    seed = CFG["seed"]["am"]
    for scene in script["scenes"]:
        for i, line in enumerate(scene["lines"], 1):
            wav = os.path.join(out_dir, f"{scene['id']}_{i:02d}.wav")
            synth(line, wav, seed)
            d = dur(wav)
            flag = "  <-- 检查" if d > 30 or d < 0.6 else ""
            print(f"ok {os.path.basename(wav)} {d:.2f}s{flag}")


if __name__ == "__main__":
    main()
