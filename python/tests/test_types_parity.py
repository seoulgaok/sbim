"""types.py(정본) ↔ types.ts(손판) — 인터페이스·필드 집합이 같은가.

둘은 손 두 벌이다. 한쪽에만 키를 더하면 소비처(nextbase)가 보는 계약과 생성기가
검증하는 계약이 갈린다 — 그 갈림을 여기서 잡는다. TS 는 정규식으로 읽는다:
`export interface X( extends Y)? {…}` 와 줄머리 2칸 들여쓰기 필드 `  name?:`.
파이썬은 공개 pydantic 모델(이름이 `_` 로 안 시작하는 것)의 `model_fields`(alias 우선).
"""

import re
from pathlib import Path

from pydantic import BaseModel

import seoulgaok_bim_core.types as T

TS_PATH = Path(__file__).resolve().parents[2] / "typescript" / "src" / "types.ts"

# TS 의 `type` 별칭(인터페이스가 아니다)과 파이썬 내부 모델 — 비교에서 뺀다
TS_TYPE_ALIASES = {"Point2", "Ring", "PartUserData", "ResolvedSource"}


def _ts_interfaces() -> dict[str, list[str]]:
    """{인터페이스: 필드 목록} — extends 는 부모 필드를 앞에 펴서 합친다."""
    ts = TS_PATH.read_text(encoding="utf-8")
    raw: dict[str, tuple[str | None, list[str]]] = {}
    for m in re.finditer(r"export interface (\w+)(?: extends (\w+))? \{([\s\S]*?)\n\}", ts):
        name, ext, body = m.groups()
        raw[name] = (ext, re.findall(r"^ {2}(\w+)\??:", body, re.M))
    out: dict[str, list[str]] = {}

    def fields(name: str) -> list[str]:
        ext, own = raw[name]
        return (fields(ext) if ext else []) + own

    for name in raw:
        out[name] = fields(name)
    return out


def _py_models() -> dict[str, list[str]]:
    """{모델: 필드 목록(alias 우선)} — types.py 에서 정의한 공개 모델만."""
    return {
        name: [f.alias or n for n, f in cls.model_fields.items()]
        for name, cls in vars(T).items()
        if isinstance(cls, type) and issubclass(cls, BaseModel) and cls is not BaseModel
        and cls.__module__ == T.__name__ and not name.startswith("_")
    }


def test_interface_sets_match():
    ts, py = _ts_interfaces(), _py_models()
    assert set(ts) - TS_TYPE_ALIASES == set(py), {
        "TS에만": sorted(set(ts) - TS_TYPE_ALIASES - set(py)),
        "python에만": sorted(set(py) - set(ts)),
    }


def test_field_sets_match():
    ts, py = _ts_interfaces(), _py_models()
    diff = {
        name: {"TS에만": sorted(set(ts[name]) - set(py[name])),
               "python에만": sorted(set(py[name]) - set(ts[name]))}
        for name in set(ts) & set(py)
        if set(ts[name]) != set(py[name])
    }
    assert diff == {}, diff


def test_scheme_underscore_keys_are_aliases():
    """밑줄 키는 파이썬 속성이 아니라 alias 다 — JSON 키 집합이 TS 와 같아야 한다."""
    aliases = {f.alias for f in T.SchemeSpatial.model_fields.values()}
    assert aliases == set(_ts_interfaces()["SchemeSpatial"])
    assert all(a.startswith("_") for a in aliases)
    assert not any(n.startswith("_") for n in T.SchemeSpatial.model_fields)
