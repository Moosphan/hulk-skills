from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


AIMode = Literal["off", "assist", "required"]
AIProvider = Literal["auto", "openai-compatible", "fixture", "none"]


@dataclass
class AIConfig:
    mode: AIMode = "off"
    provider: AIProvider = "auto"
    model: str = ""
    timeout_seconds: int = 45
    cache_dir: str = ""
    fixture_dir: str = ""

    @property
    def enabled(self) -> bool:
        return self.mode in {"assist", "required"}

    @property
    def required(self) -> bool:
        return self.mode == "required"

    def metadata(self) -> dict[str, Any]:
        return {
            "ai_mode": self.mode,
            "ai_provider": self.provider,
            "ai_model": self.model,
            "ai_timeout_seconds": self.timeout_seconds,
            "ai_cache_dir": self.cache_dir,
            "ai_fixture_dir": self.fixture_dir,
            "ai_enabled": self.enabled,
            "ai_required": self.required,
        }


@dataclass
class AITraceEvent:
    role: str
    action: str
    status: str
    provider: str
    model: str = ""
    fallback_used: bool = False
    error: str = ""
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AIEvaluation:
    score: int
    confidence: float
    strength_evidence: list[str]
    risk_evidence: list[str]
    missing_evidence: list[str]
    recommended_next_action: str = ""
    hard_fail_flags: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class AIFollowUp:
    action: str
    probe_type: str
    prompt: str
    rationale: str = ""
    stop_condition: str = ""
    stage: str = "follow_up"
    notes: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)
