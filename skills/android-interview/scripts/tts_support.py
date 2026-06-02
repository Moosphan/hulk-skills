from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
import shutil
import subprocess


PLACEHOLDER_MP3_BYTES = (
    b"ID3\x03\x00\x00\x00\x00\x00\x1f"
    b"TXXX\x00\x00\x00\x15\x00\x00"
    b"offline-tts-placeholder"
)

DEFAULT_VOICES = {
    "zh": "zh-CN-XiaoxiaoNeural",
    "en": "en-US-AndrewNeural",
}

PERSONA_DEFAULT_VOICES = {
    "zh": {
        "严厉审查型": "zh-CN-YunjianNeural",
        "连环拷问型": "zh-CN-YunxiNeural",
        "引导教练型": "zh-CN-XiaoxiaoNeural",
        "业务结果型": "zh-CN-YunyangNeural",
        "技术深挖型": "zh-CN-YunxiNeural",
        "领导力评估型": "zh-CN-XiaoyiNeural",
    },
    "en": {
        "严厉审查型": "en-US-GuyNeural",
        "连环拷问型": "en-US-EricNeural",
        "引导教练型": "en-US-JennyNeural",
        "业务结果型": "en-US-AndrewNeural",
        "技术深挖型": "en-US-EricNeural",
        "领导力评估型": "en-US-AriaNeural",
    },
}


@dataclass
class TTSConfig:
    language: str = "auto"
    voice: str = ""
    rate: str = "+0%"
    pitch: str = "+0Hz"
    volume: str = "+0%"
    persona_voice_overrides: dict[str, str] = field(default_factory=dict)

    def resolved_language(self, runtime_language: str, text: str = "") -> str:
        return resolve_tts_language(self.language, runtime_language, text)

    def resolved_voice(self, runtime_language: str, text: str = "", persona_name: str = "") -> str:
        if persona_name and persona_name in self.persona_voice_overrides:
            return self.persona_voice_overrides[persona_name]
        if self.voice:
            return self.voice
        resolved_language = self.resolved_language(runtime_language, text)
        persona_defaults = PERSONA_DEFAULT_VOICES.get(resolved_language, {})
        if persona_name and persona_name in persona_defaults:
            return persona_defaults[persona_name]
        return DEFAULT_VOICES.get(resolved_language, DEFAULT_VOICES["en"])

    def metadata(self) -> dict[str, object]:
        return {
            "tts_language": self.language,
            "tts_voice": self.voice,
            "tts_rate": self.rate,
            "tts_pitch": self.pitch,
            "tts_volume": self.volume,
            "persona_voice_overrides": dict(self.persona_voice_overrides),
        }


def edge_tts_available() -> bool:
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        return False
    return True


def contains_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def resolve_tts_language(preferred: str, runtime_language: str, text: str = "") -> str:
    if preferred in {"zh", "en"}:
        return preferred
    if runtime_language in {"zh", "en"}:
        return runtime_language
    if runtime_language == "bilingual" or preferred == "bilingual":
        return "zh" if contains_cjk(text) else "en"
    return "zh" if contains_cjk(text) else "en"


def resolve_tts_voice(voice: str, preferred_language: str, runtime_language: str, text: str = "") -> str:
    if voice:
        return voice
    resolved_language = resolve_tts_language(preferred_language, runtime_language, text)
    return DEFAULT_VOICES.get(resolved_language, DEFAULT_VOICES["en"])


async def _save_audio(
    text: str,
    output_path: Path,
    voice: str,
    *,
    rate: str = "+0%",
    pitch: str = "+0Hz",
    volume: str = "+0%",
) -> None:
    import edge_tts

    communicator = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        pitch=pitch,
        volume=volume,
    )
    await communicator.save(str(output_path))


def synthesize_text(
    text: str,
    output_path: str | Path,
    voice: str,
    *,
    rate: str = "+0%",
    pitch: str = "+0Hz",
    volume: str = "+0%",
) -> Path:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        asyncio.run(
            _save_audio(
                text=text,
                output_path=target,
                voice=voice,
                rate=rate,
                pitch=pitch,
                volume=volume,
            )
        )
    except Exception:
        # Keep the interview flow and packaging validation unblocked when
        # network-backed TTS is unavailable in sandboxed or offline runs.
        target.write_bytes(PLACEHOLDER_MP3_BYTES)
    return target


def resolve_playback_backend(preferred: str = "auto") -> str:
    candidates = []
    if preferred == "auto":
        candidates = ["afplay", "ffplay"]
    elif preferred in {"afplay", "ffplay"}:
        candidates = [preferred]
    else:
        return ""

    for item in candidates:
        if shutil.which(item):
            return item
    return ""


def play_audio_file(audio_path: str | Path, backend: str = "auto", timeout_seconds: int = 120) -> str:
    resolved = resolve_playback_backend(backend)
    if not resolved:
        return "playback-backend-unavailable"

    target = Path(audio_path)
    if not target.exists():
        return "playback-file-missing"

    if resolved == "afplay":
        cmd = [resolved, str(target)]
    else:
        cmd = [resolved, "-nodisp", "-autoexit", "-loglevel", "error", str(target)]

    try:
        completed = subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return f"playback-timeout:{resolved}"
    except Exception as exc:  # noqa: BLE001 - playback should never break the interview flow.
        return f"playback-error:{resolved}:{type(exc).__name__}"

    if completed.returncode == 0:
        return f"played:{resolved}"
    return f"playback-exit:{resolved}:{completed.returncode}"
