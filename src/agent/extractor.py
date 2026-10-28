from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

from src.schemas import CaseAnalysis


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_cache_path() -> Path:
    return _repo_root() / "data" / "cached_extractions.json"


def load_cached_extractions(cache_path: str | Path | None = None) -> dict[str, CaseAnalysis]:
    path = Path(cache_path) if cache_path else _default_cache_path()
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {case_id: CaseAnalysis.model_validate(payload) for case_id, payload in data.items()}


def _load_cached_case(player_id: str, cache_path: str | Path | None = None) -> CaseAnalysis:
    cache = load_cached_extractions(cache_path)
    if player_id not in cache:
        raise KeyError(f"No cached extraction for {player_id}")
    return cache[player_id]


def _build_case_contents(case_folder: Path) -> list[Any]:
    parts: list[Any] = []
    instructions = (
        "You are a multimodal football academy retention and intervention analyst. "
        "Extract structured risk signals and interventions following the CaseAnalysis schema. "
        "Ground every extracted signal in explicit evidence from the provided files."
    )
    parts.append(instructions)

    for file_path in sorted(case_folder.iterdir()):
        if file_path.is_dir():
            continue
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            parts.append(types.Part.from_bytes(data=file_path.read_bytes(), mime_type="application/pdf"))
        elif suffix == ".png":
            parts.append(types.Part.from_bytes(data=file_path.read_bytes(), mime_type="image/png"))
        elif suffix == ".wav":
            parts.append(types.Part.from_bytes(data=file_path.read_bytes(), mime_type="audio/wav"))
        elif suffix == ".json":
            parts.append(f"JSON file ({file_path.name}):\n{file_path.read_text(encoding='utf-8')}")
        else:
            parts.append(f"Text file ({file_path.name}):\n{file_path.read_text(encoding='utf-8')}")

    parts.append("Return valid JSON only.")
    return parts


def analyze_case_live(case_folder: str | Path, player_id: str, api_key: str | None = None) -> tuple[CaseAnalysis, bool, str]:
    folder = Path(case_folder)
    if not api_key:
        cached = _load_cached_case(player_id)
        return cached, True, "No API key provided. Showing cached extraction."

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=_build_case_contents(folder),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CaseAnalysis,
                temperature=0.2,
            ),
        )

        if getattr(response, "parsed", None) is not None:
            parsed = response.parsed
            case_analysis = parsed if isinstance(parsed, CaseAnalysis) else CaseAnalysis.model_validate(parsed)
        else:
            case_analysis = CaseAnalysis.model_validate_json(response.text)
        return case_analysis, False, "Live Gemini analysis completed."
    except Exception as exc:  # noqa: BLE001
        cached = _load_cached_case(player_id)
        return cached, True, f"Live API failed ({exc}). Falling back to cached extraction."
