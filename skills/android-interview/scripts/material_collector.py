from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
import urllib.request


MaterialSourceType = Literal["file_path", "url", "inline_text"]


@dataclass
class MaterialSource:
    source_type: MaterialSourceType
    value: str
    resolved: bool
    content: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.source_type,
            "value": self.value,
            "resolved": self.resolved,
            "content_length": len(self.content),
            "content_preview": self.content[:160],
        }


def detect_material_source(value: str | Path) -> MaterialSourceType:
    text = str(value).strip()
    if not text:
        return "inline_text"
    if text.startswith(("http://", "https://")):
        return "url"
    try:
        if Path(text).exists():
            return "file_path"
    except OSError:
        pass
    return "inline_text"


def resolve_material_source(value: str | Path, *, timeout_seconds: int = 20) -> MaterialSource:
    text = str(value).strip()
    if not text:
        return MaterialSource(source_type="inline_text", value="", resolved=False, content="")
    source_type = detect_material_source(text)
    if source_type == "file_path":
        content = Path(text).read_text(encoding="utf-8").strip()
        return MaterialSource(source_type=source_type, value=text, resolved=True, content=content)
    if source_type == "url":
        with urllib.request.urlopen(text, timeout=timeout_seconds) as response:
            payload = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
        content = payload.decode(charset, errors="replace").strip()
        return MaterialSource(source_type=source_type, value=text, resolved=True, content=content)
    return MaterialSource(source_type=source_type, value=text, resolved=bool(text), content=text)


def resolve_material_text(value: str | Path, *, timeout_seconds: int = 20) -> str:
    return resolve_material_source(value, timeout_seconds=timeout_seconds).content


def collect_session_materials(
    *,
    jd_input: str | Path = "",
    resume_input: str | Path = "",
    collection_mode: str = "cli",
) -> dict[str, Any]:
    jd_source = resolve_material_source(jd_input) if str(jd_input).strip() else MaterialSource("inline_text", "", False, "")
    resume_source = resolve_material_source(resume_input) if str(resume_input).strip() else MaterialSource("inline_text", "", False, "")
    materials = {
        "jd": jd_source.to_dict(),
        "resume": resume_source.to_dict(),
    }
    missing_materials = [name for name, item in materials.items() if not bool(item.get("resolved"))]
    return {
        "materials": materials,
        "missing_materials": missing_materials,
        "collection_mode": collection_mode,
        "ready_for_interview": not missing_materials,
    }
