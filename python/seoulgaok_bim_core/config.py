"""config.py — 사업 설정값 오버레이.

이 저장소는 **구조**(어떤 항목이 있고 어떤 의미인지)만 담고,
사업에 종속된 **값**(금융 조건 등)은 담지 않는다.
값은 저장소 밖 JSON 파일에서 주입한다.

탐색 순서:
  1. 환경변수 SBIM_CONFIG 가 가리키는 JSON 파일
  2. 현재 디렉토리부터 상위로 올라가며 찾은 sbim_config.json
  3. 없으면 {} — 오버레이 없음 (조용히 통과)

site_filter와 달리 여기서는 미설정을 예외로 만들지 않는다.
설정이 없어도 라이브러리는 동작해야 하고, 값이 꼭 필요한 항목은
자기 자리에서 None으로 남아 계산 시점에 터진다 (Financing 참조).

형식은 BuildOptions 트리와 동일한 중첩 구조:

    {
      "financing": { "land_loan_ltv": 0.7, "land_loan_rate": 0.05 },
      "concrete":  { "slab_thickness": 0.15 }
    }

예시는 examples/sbim_config.example.json.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

CONFIG_ENV = "SBIM_CONFIG"
CONFIG_NAME = "sbim_config.json"


def find_config() -> Path | None:
    """설정 파일 경로 — 환경변수 우선, 없으면 상위 디렉토리 탐색."""
    if env := os.getenv(CONFIG_ENV):
        return Path(env)
    here = Path.cwd().resolve()
    for ancestor in [here, *here.parents]:
        if (candidate := ancestor / CONFIG_NAME).exists():
            return candidate
    return None


def load_overrides(path: str | Path | None = None) -> dict:
    """설정 JSON 로드. 없으면 {}. 잘못된 형식은 조용히 넘기지 않는다."""
    p = Path(path) if path else find_config()
    if p is None:
        return {}
    if not p.exists():
        raise FileNotFoundError(f"설정 파일 없음: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"설정 최상위는 객체여야 합니다: {p}")
    return data


def deep_merge(base: dict, over: dict) -> dict:
    """중첩 dict 병합 — over가 이긴다. dict가 아닌 값은 통째로 교체."""
    out = dict(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def build_options(config_path: str | Path | None = None, **kwargs: Any):
    """설정 오버레이 + 호출자 인자를 병합해 BuildOptions 생성.

    우선순위: kwargs > 설정 파일 > 모델 기본값.
    BuildOptions(...)를 직접 써도 되지만, 그러면 설정 파일이 무시된다.
    """
    from .options import BuildOptions  # 순환 import 회피

    merged = deep_merge(load_overrides(config_path), kwargs)
    return BuildOptions.model_validate(merged)


if __name__ == "__main__":
    # self-check — 병합 규칙 (설정 파일 없이도 도는 경로만)
    assert deep_merge({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}
    assert deep_merge({"a": 1}, {"a": 2}) == {"a": 2}, "over가 이긴다"
    assert deep_merge({"f": {"x": 1, "y": 2}}, {"f": {"y": 9}}) == {
        "f": {"x": 1, "y": 9}}, "중첩은 병합"
    assert deep_merge({"f": {"x": 1}}, {"f": 5}) == {"f": 5}, "타입 다르면 교체"
    assert deep_merge({}, {}) == {}

    # 원본 불변
    base = {"f": {"x": 1}}
    deep_merge(base, {"f": {"x": 2}})
    assert base == {"f": {"x": 1}}, "입력을 변조하면 안 됨"

    # kwargs가 설정을 이긴다
    opts = build_options(exterior={"style": "brick"})
    assert opts.exterior.style == "brick", opts.exterior

    # 금융 값은 기본 미설정 — 조용한 가정 금지
    assert opts.financing.land_loan_rate is None, "금융 기본값은 None이어야"

    print("config self-check OK")
