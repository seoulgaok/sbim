"""Scheme JSON load/save 헬퍼."""

from __future__ import annotations

import json
from pathlib import Path

from .types import Scheme, SurroundingBuilding, Unit


def load_scheme(path: str | Path) -> Scheme:
    """scheme.json 파일을 Scheme 객체로 로드."""
    with open(path, encoding="utf-8") as f:
        return Scheme.model_validate(json.load(f))


def save_scheme(scheme: Scheme, path: str | Path) -> None:
    """Scheme을 scheme.json으로 저장 (atomic write)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(scheme.model_dump_json(indent=2), encoding="utf-8")
    tmp.replace(p)


def load_units(path: str | Path) -> list[Unit]:
    """units.json 파일을 Unit 배열로 로드."""
    with open(path, encoding="utf-8") as f:
        return [Unit.model_validate(item) for item in json.load(f)]


def save_units(units: list[Unit], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = [u.model_dump() for u in units]
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)


def load_surroundings(path: str | Path) -> list[SurroundingBuilding]:
    """surroundings.json 파일을 SurroundingBuilding 배열로 로드."""
    with open(path, encoding="utf-8") as f:
        return [SurroundingBuilding.model_validate(item) for item in json.load(f)]


def save_surroundings(surroundings: list[SurroundingBuilding], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = [s.model_dump() for s in surroundings]
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)
