"""CompileError schema — sBIM Spatial CSP 위반 데이터 모델.

단일 진실 (Single Source of Truth):
  - giga가 이 schema로 발화 (logic은 giga/shared/constraints/)
  - api.py response_model
  - nextbase TS mirror (typescript/src/errors.ts 자동 동기)

부정 변증법:
  silent invalid 금지. 모든 도메인 명제 위반은 explicit CompileError로 표면화.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


CompileErrorType = Literal[
    "ZoningError",       # 용적률·건폐율 한도 초과
    "EnvelopeError",     # 정북사선·가각전제
    "AccessError",       # 4m 도로 미달 (건축법 44조)
    "ParkingError",      # 법정 주차 > 가능 stall
    "CirculationError",  # 코어 진입 동선 / 4각 충돌
    "StructureError",    # 기둥 stall 침범
    "HabitabilityError", # 도시형생활주택 net 14㎡ 미달
    "GeometryError",     # polygon degenerate / self-intersect
]


class CompileError(BaseModel):
    """sBIM 도메인 명제 위반 — invalid design 발화.

    type: 카테고리 (8 카테고리). nextbase TypeScript에서 discriminated union.
    reason: 사람이 읽는 짧은 설명.
    details: 위반 수치 / polygon 정보 (디버깅·LLM용).
    suggestion: BuildOptions 조정 힌트 (사용자/LLM이 따라 재컴파일).
    """
    model_config = ConfigDict(extra="forbid")

    type: CompileErrorType
    reason: str
    details: dict[str, Any] = {}
    suggestion: str | None = None
