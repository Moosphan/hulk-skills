#!/usr/bin/env python3
"""TTS 逐句合成 -> 对齐 -> 混 BGM/SFX（numpy 混音）-> 成片音轨 + 时间轴"""
import json, os, subprocess, wave
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
TTS = os.path.join(os.path.dirname(ROOT), ".venv-tts", "bin", "edge-tts")
VOICE = "zh-CN-XiaoyiNeural"
WORK = os.path.join(ROOT, "build", "vo")
os.makedirs(WORK, exist_ok=True)
SR = 48000
LEAD, GAP, TAIL = 0.55, 0.26, 0.5

def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def load(p):
    with wave.open(p) as f:
        assert f.getframerate() == SR and f.getnchannels() == 1
        a = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return a

script = json.load(open(os.path.join(ROOT, "script.json")))
lines = script["lines"]
cues, t = [], LEAD
for ln in lines:
    mp3 = os.path.join(WORK, ln["id"] + ".mp3")
    wav = os.path.join(WORK, ln["id"] + ".wav")
    if not os.path.exists(mp3):
        run([TTS, "--voice", VOICE, "--text", ln["text"], "--rate=-2%", "--pitch=+8Hz", "--write-media", mp3])
    run(["ffmpeg", "-y", "-i", mp3, "-ar", str(SR), "-ac", "1", wav])
    a = load(wav); d = len(a) / SR
    cues.append({"id": ln["id"], "text": ln["text"], "scene": ln["scene"], "start": round(t, 3), "dur": round(d, 3)})
    t += d + GAP
total = round(t - GAP + TAIL, 3)

scenes, order = [], []
for c in cues:
    if c["scene"] not in order:
        order.append(c["scene"]); scenes.append({"id": c["scene"], "start": c["start"], "cues": []})
    scenes[-1]["cues"].append(c["id"])
for i, s in enumerate(scenes):
    s["end"] = scenes[i + 1]["start"] if i + 1 < len(scenes) else total
    s["dur"] = round(s["end"] - s["start"], 3)

N = int(total * SR) + SR
mix = np.zeros(N, dtype=np.float32)

# 人声
for c in cues:
    a = load(os.path.join(WORK, c["id"] + ".wav"))
    i = int(c["start"] * SR)
    mix[i:i + len(a)] += a * 1.0

# BGM
bgm = os.path.join(ROOT, "public", "audio", "Carefree.mp3")
raw = os.path.join(WORK, "bgm.wav")
run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", bgm, "-t", f"{total + 0.5}", "-ar", str(SR), "-ac", "1", raw])
b = load(raw)[:N]
n = len(b)
b = b * 0.15
b[:int(1.2 * SR)] *= np.linspace(0, 1, int(1.2 * SR))
tail = int(2.4 * SR)
b[-tail:] *= np.linspace(1, 0, tail)
mix[:len(b)] += b

# SFX
def sfx(name, at, gain=1.0):
    p = os.path.join(ROOT, "public", "audio", f"sfx_{name}.wav")
    if not os.path.exists(p): return
    s = load(p) * gain
    i = int(at * SR)
    mix[i:i + len(s)] += s

by_id = {c["id"]: c for c in cues}
for lid, name, g in [("l02", "page", 0.35), ("l05", "stamp", 0.55),
                     ("l11", "ding", 0.4), ("l15", "stamp", 0.45), ("l16", "ding", 0.45)]:
    c = by_id[lid]
    sfx(name, c["start"] + c["dur"] * 0.72, g)

# 归一
mix = np.tanh(mix * 1.02)
mix /= max(1e-6, np.abs(mix).max()) / 0.92
out = os.path.join(ROOT, "build", "mix_raw.wav")
with wave.open(out, "wb") as f:
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
    f.writeframes((mix * 32767).astype(np.int16).tobytes())

final = os.path.join(ROOT, "public", "audio", "checkup.wav")
run(["ffmpeg", "-y", "-i", out, "-af",
     "highshelf=f=6000:g=1.2,acompressor=threshold=-18dB:ratio=2:attack=8:release=180,"
     "loudnorm=I=-16:TP=-1.5:LRA=9,aresample=48000", "-ac", "1", "-ar", "48000", final])

tl = {"total": total, "cues": cues, "scenes": scenes, "audio": "audio/checkup.wav"}
os.makedirs(os.path.join(ROOT, "public", "data"), exist_ok=True)
json.dump(tl, open(os.path.join(ROOT, "public", "data", "checkup_timeline.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps({"total": total, "scenes": len(scenes), "cues": len(cues)}, ensure_ascii=False))
for c in cues:
    print(f"{c['start']:6.2f} +{c['dur']:5.2f}  {c['id']}  {c['text']}")
