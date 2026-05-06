"""Scheme 편집 연산. DeerFlow agent가 자연어로 호출."""

from __future__ import annotations

from .types import FloorPlan, Scheme

# TODO: 모든 함수는 새 Scheme을 반환 (immutable). 원본은 수정하지 않음.


def get_floor(scheme: Scheme, floor_id: int) -> FloorPlan | None:
    """floor_id로 FloorPlan 조회."""
    for fp in scheme.floor_plans:
        if fp.data.floor_id == floor_id:
            return fp
    return None


def remove_floor(scheme: Scheme, floor_id: int) -> Scheme:
    """특정 층 제거."""
    new_scheme = scheme.model_copy(deep=True)
    new_scheme.floor_plans = [fp for fp in new_scheme.floor_plans if fp.data.floor_id != floor_id]
    return new_scheme


# --- 향후 추가 예정 (LoD 200 룰) ----------------------------------------------
# def move_core(scheme: Scheme, direction: Literal["left","right","up","down"]) -> Scheme: ...
# def set_floor_type(scheme: Scheme, floor_id: int, type_: str) -> Scheme: ...
# def set_unit_count(scheme: Scheme, floor_id: int, count: int) -> Scheme: ...
# def add_window(scheme: Scheme, floor_id: int, wall_id: str, offset: float) -> Scheme: ...
# def layout_parking(scheme: Scheme, mode: Literal["piloti","underground"]) -> Scheme: ...
