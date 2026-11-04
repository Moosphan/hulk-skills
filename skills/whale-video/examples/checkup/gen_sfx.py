#!/usr/bin/env python3
"""柔和音效：印章、叮（低通 + 低增益，不抢人声）"""
import numpy as np, wave, os

SR = 48000
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public", "audio")
os.makedirs(OUT, exist_ok=True)

def w(name, x):
    x = np.clip(x, -1, 1)
    d = (x * 32767).astype(np.int16)
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes(d.tobytes())

def t_(d): return np.arange(int(SR * d)) / SR

def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.zeros_like(x); acc = 0.0
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y

def env(n, a=0.004, r=0.25):
    e = np.ones(n)
    na, nr = int(SR * a), int(SR * r)
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] = np.linspace(1, 0, nr) ** 2
    return e

rng = np.random.default_rng(11)

# 印章：低频闷响（低通 500Hz）
d = 0.30; x = t_(d)
thump = np.sin(2 * np.pi * (58 + 26 * np.exp(-x * 26)) * x) * np.exp(-x * 13)
click = rng.standard_normal(len(x)) * np.exp(-x * 70)
s0 = lowpass(thump * 0.8 + click * 0.18, 520)
w("sfx_stamp", s0 * env(len(x), 0.004, 0.22) * 0.55)

# 叮：柔和的单音 + 泛音（低通 2.6k）
d = 0.55; x = t_(d)
ding = np.sin(2 * np.pi * 880 * x) + 0.25 * np.sin(2 * np.pi * 1760 * x)
w("sfx_ding", lowpass(ding, 2600) * np.exp(-x * 7) * env(len(x), 0.006, 0.2) * 0.26)

# 纸张：极轻的沙沙（低通 1.8k）
d = 0.22; x = t_(d)
n = rng.standard_normal(len(x))
w("sfx_page", lowpass(n, 1800) * np.exp(-x * 16) * env(len(x), 0.008, 0.12) * 0.5)

print("sfx ok")
