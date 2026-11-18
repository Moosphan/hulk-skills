import sys, wave, numpy as np, mlx_audio
from mlx_audio.tts.utils import load_model

import os
REF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets/xiaozi-voices/qwen-d1-soft.wav")
REF_TEXT = "你好呀，我是小紫。今天也想和你分享一点新鲜事。别看我个子小，想法可不少。要是讲得还不错，就给我个赞吧。你的喜欢，我可是会认真记住的。"

text, out = sys.argv[1], sys.argv[2]
model = load_model("mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16")
res = list(model.generate(text=text, ref_audio=REF, ref_text=REF_TEXT, lang_code="Chinese", temperature=0.7, top_p=0.9, repetition_penalty=1.05))
audio = np.array(res[0].audio, dtype=np.float32).flatten()
sr = int(getattr(res[0], "sample_rate", 24000) or 24000)
with wave.open(out, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())
print("ok", out, len(audio)/sr, sr)
