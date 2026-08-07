"""CompileError schema — sBIM Spatial CSP 위반 데이터 모델.

단일 진실 (Single Source of Truth):
  - 생성기가 이 schema로 발화 (logic은 생성기 제약 모듈)
  - api.py response_model
  - 프론트엔드 TS mirror (typescript/src/errors.ts 자동 동기)

부정 변증법:
  silent invalid 금지. 모든 도메인 명제 위반은 explicit CompileError로 표면화.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


# 생성기(giga)가 **실제로 방출하는** 이름이 정본이다.
#
# 구 어휘는 규제 영역별 분류였다(ZoningError·EnvelopeError·AccessError·
# ParkingError·CirculationError·StructureError·HabitabilityError·GeometryError
# — "어떤 법을 어겼나"). 생성기는 그걸 쓰지 않고 "무엇이 안 됐나" 축으로 자기
# 이름을 붙여 왔고, 결과적으로 **교집합 0**인 두 어휘가 생겨 이 Literal은 아무도
# 안 쓰는 죽은 계약이 됐다. nextbase는 compile_errors를 `CompileError[]`로 타입
# 지정하면서 실제로는 개수와 reason만 소비해, **타입은 통과하는데 값은 계약 밖**인
# 상태였다(SbimStudio.tsx:685).
#
# 죽은 계약을 살아있는 쪽에 맞춘다. "무엇이 안 됐나"가 사용자에게도 유용한
# 분류다 — 에러마다 붙일 UI 행동이 이름에서 바로 나온다(세대 수 늘리기 버튼,
# 주차 패널 점프, 도달 불가 세대 하이라이트).
CompileErrorType = Literal[
    "UnitsInfeasible",      # units_by_level로 명시한 세대 수를 그 층에 못 넣음
    "UnitUnreachable",      # 문에서 폭 1.2m 경로로 못 닿는 전용 면적 (도달률 < 90%)
    "UnitAreaExceeded",     # 세대 전용면적 > units.max_net_area (기본 84㎡)
    "ParkingSufficiency",   # 법정 주차대수 > 이 대지에 배치 가능한 stall 수
    "FloorCountInfeasible", # 목표 층수를 정북일조·용적률 아래 못 세움
]


class CompileError(BaseModel):
    """sBIM 도메인 명제 위반 — invalid design 발화.

    type: 위반 종류. 프론트엔드 TypeScript에서 discriminated union.
    reason: 사람이 읽는 짧은 설명.
    details: 위반 수치 / polygon 정보 (디버깅·LLM용).
    suggestion: BuildOptions 조정 힌트 (사용자/LLM이 따라 재컴파일).
    """
    model_config = ConfigDict(extra="forbid")

    type: CompileErrorType
    reason: str
    details: dict[str, Any] = {}
    suggestion: str | None = None
