"""site_filter.py — 대상 필지 선별 기준의 **구조**만 정의하는 래퍼.

무엇을 필터링하는지(컬럼·연산자·SQL 조립)는 여기 있고,
어떤 값으로 필터링하는지(임계값)는 **이 저장소에 두지 않는다** — 사업 정보다.

값은 다음 순서로 주입한다:
  1. build_where(criteria=...) 인자
  2. 환경변수 SBIM_SITE_FILTER 가 가리키는 JSON 파일
  3. 현재 디렉토리부터 상위로 올라가며 찾은 site_filter.json

셋 다 없으면 SiteFilterNotConfigured. 조용한 기본값은 두지 않는다 —
빠진 설정이 "전국 필지 전체 조회"로 흘러가는 편이 더 위험하다.

설정 형식은 examples/site_filter.example.json 참조.
TS 쌍은 typescript/src/siteFilter.ts (구조만, 값 없음).

컬럼은 필지 테이블 기준:
  garea 대지면적(㎡) · age 노후도(년) · zone_nm 용도지역명 ·
  terrain_height_nm 지형 · use_etc 용도(자유텍스트, 부분일치)
"""

from __future__ import annotations

import json
import os
from pathlib import Path

CONFIG_ENV = "SBIM_SITE_FILTER"
CONFIG_NAME = "site_filter.json"

# 인식하는 키 — 설정 파일 오타를 조용히 무시하지 않기 위한 목록
CRITERIA_KEYS = frozenset(
    {"min_garea", "max_garea", "min_age", "zones", "terrain", "use_keywords"}
)


class SiteFilterNotConfigured(RuntimeError):
    """선별 기준 설정을 찾지 못함."""


def find_config() -> Path | None:
    """설정 파일 경로 — 환경변수 우선, 없으면 상위 디렉토리 탐색."""
    if env := os.getenv(CONFIG_ENV):
        return Path(env)
    here = Path.cwd().resolve()
    for ancestor in [here, *here.parents]:
        if (candidate := ancestor / CONFIG_NAME).exists():
            return candidate
    return None


def load_criteria(path: str | Path | None = None) -> dict:
    """선별 기준 JSON 로드 + 키 검증."""
    p = Path(path) if path else find_config()
    if p is None:
        raise SiteFilterNotConfigured(
            f"선별 기준 설정을 찾을 수 없습니다. {CONFIG_ENV} 환경변수로 경로를 "
            f"지정하거나 상위 경로에 {CONFIG_NAME}을 두세요 "
            f"(형식: examples/site_filter.example.json)."
        )
    if not p.exists():
        raise SiteFilterNotConfigured(f"설정 파일 없음: {p}")
    criteria = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(criteria, dict):
        raise SiteFilterNotConfigured(f"설정 최상위는 객체여야 합니다: {p}")
    if unknown := set(criteria) - CRITERIA_KEYS:
        raise SiteFilterNotConfigured(
            f"알 수 없는 키 {sorted(unknown)} in {p}. 허용: {sorted(CRITERIA_KEYS)}"
        )
    return criteria


def build_where(
    alias: str = "l",
    criteria: dict | None = None,
    config_path: str | Path | None = None,
) -> tuple[str, list]:
    """선별 기준 → (SQL WHERE 절, psycopg 파라미터 리스트).

    alias: 필지 테이블 별칭.
    criteria: 기준 dict. None이면 설정 파일에서 로드.
    반환 WHERE 절은 'geom IS NOT NULL' 포함, 선행 'WHERE' 없음 (호출부가 붙임).

    alias는 SQL에 직접 삽입되므로 신뢰할 수 있는 값만 넘길 것 (식별자 검증함).
    """
    if not alias.isidentifier():
        raise ValueError(f"alias는 SQL 식별자여야 합니다: {alias!r}")
    f = load_criteria(config_path) if criteria is None else criteria

    clauses = [f"{alias}.geom IS NOT NULL"]
    params: list = []
    if f.get("min_garea") is not None and f.get("max_garea") is not None:
        clauses.append(f"{alias}.garea BETWEEN %s AND %s")
        params += [f["min_garea"], f["max_garea"]]
    if f.get("min_age") is not None:
        clauses.append(f"{alias}.age >= %s")
        params.append(f["min_age"])
    if f.get("zones"):
        clauses.append(f"{alias}.zone_nm = ANY(%s)")
        params.append(list(f["zones"]))
    if f.get("terrain"):
        clauses.append(f"{alias}.terrain_height_nm = %s")
        params.append(f["terrain"])
    if f.get("use_keywords"):
        ors = " OR ".join([f"{alias}.use_etc ILIKE %s"] * len(f["use_keywords"]))
        clauses.append(f"({ors})")
        params += [f"%{k}%" for k in f["use_keywords"]]
    return " AND ".join(clauses), params


if __name__ == "__main__":
    # self-check — 값이 아니라 구조를 검증한다 (임계값은 저장소에 없음)
    sample = {
        "min_garea": 100,
        "max_garea": 200,
        "min_age": 10,
        "zones": ["A지역", "B지역"],
        "terrain": "지형",
        "use_keywords": ["갑", "을"],
    }
    where, params = build_where(criteria=sample)
    for frag in ("l.geom IS NOT NULL", "l.garea BETWEEN", "l.age >=",
                 "l.zone_nm = ANY", "l.terrain_height_nm =", "l.use_etc ILIKE"):
        assert frag in where, (frag, where)
    assert params[:2] == [100, 200], params
    assert params[3] == ["A지역", "B지역"], params
    assert params[-2:] == ["%갑%", "%을%"], params

    # 부분 기준 — 빠진 항목은 절이 생기지 않는다
    w2, p2 = build_where(alias="x", criteria={"min_garea": 1, "max_garea": 2})
    assert "x.garea BETWEEN %s AND %s" in w2
    assert "terrain_height_nm" not in w2 and "age >=" not in w2, w2
    assert p2 == [1, 2], p2

    # 빈 기준이어도 geom 절은 남는다
    w3, _ = build_where(criteria={})
    assert w3 == "l.geom IS NOT NULL", w3

    # alias 검증
    try:
        build_where(alias="l; DROP TABLE lands--", criteria={})
    except ValueError:
        pass
    else:
        raise AssertionError("alias 검증 실패")

    # 설정 없으면 조용히 넘어가지 않는다
    try:
        load_criteria("/nonexistent/site_filter.json")
    except SiteFilterNotConfigured:
        pass
    else:
        raise AssertionError("미설정 시 예외 필요")

    print("site_filter self-check OK")
