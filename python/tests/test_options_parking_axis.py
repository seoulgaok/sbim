"""GroundFloor.parking_axis — 내부 차로 배치 방식에 이름을 준다 (#8 ⑨, 1단계).

giga 어휘(aaro/inner.py)에는 내부 차로를 까는 방식이 넷 구현돼 있는데(직교 열·평행 열·
경계 한 줄·회전 마당) sbim에는 이름이 없었다 — 엔진은 스스로 정할 수 있는데 사용자는
줄 수 없었다. 값 추가라 기존에 심긴 옵션은 뜻도 통과 여부도 바뀌지 않는다.
"""

from typing import get_args

import pytest
from pydantic import ValidationError

from seoulgaok_bim_core import (
    GroundFloor,
    InnerLayout,
    ParkingAxis,
    split_parking_axis,
)

LEGACY = ["road", "core", "inner", "auto"]
NEW = ["inner_perp", "inner_par", "inner_single", "inner_court"]


def test_default_is_auto():
    assert GroundFloor().parking_axis == "auto"


@pytest.mark.parametrize("axis", LEGACY + [None])
def test_legacy_values_still_accepted(axis):
    assert GroundFloor(parking_axis=axis).parking_axis == axis


@pytest.mark.parametrize("axis", NEW)
def test_new_values_accepted(axis):
    assert GroundFloor(parking_axis=axis).parking_axis == axis


@pytest.mark.parametrize("axis", ["inner_diag", "court", "INNER", ""])
def test_unknown_value_rejected(axis):
    with pytest.raises(ValidationError):
        GroundFloor(parking_axis=axis)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, (None, None)),
        ("auto", (None, None)),          # 「자동」의 두 표기를 한 곳에서 접는다
        ("road", ("road", None)),
        ("core", ("core", None)),
        ("inner", ("inner", None)),      # 내부 차로, 방식은 엔진이
        ("inner_perp", ("inner", "perp")),
        ("inner_par", ("inner", "par")),
        ("inner_single", ("inner", "single")),
        ("inner_court", ("inner", "court")),
    ],
)
def test_split(value, expected):
    assert split_parking_axis(value) == expected


@pytest.mark.parametrize("value", ["inner_", "inner_diag", "mass", "court"])
def test_split_rejects_unknown(value):
    with pytest.raises(ValueError):
        split_parking_axis(value)


def test_every_literal_value_splits():
    """Literal과 분해 함수가 따로 놀지 않는다 — 값을 늘리면 여기서 걸린다."""
    layouts = set(get_args(InnerLayout))
    for value in get_args(ParkingAxis):
        axis, layout = split_parking_axis(value)
        assert axis in (None, "road", "core", "inner")
        assert layout is None or layout in layouts


def test_every_layout_has_a_name():
    """라이브러리에 있는데 속성 창에 없으면 버그 — 네 방식 모두 값이 있다."""
    named = {split_parking_axis(v)[1] for v in get_args(ParkingAxis)} - {None}
    assert named == set(get_args(InnerLayout))


# ── 방식 × 각도 — 곱해지지 않는 조합 (#8 ⑧) ──

def test_court_ignores_angle():
    assert GroundFloor(parking_axis="inner_court").parking_angle is None
    with pytest.raises(ValidationError, match="각도와 무관"):
        GroundFloor(parking_axis="inner_court", parking_angle=45)


@pytest.mark.parametrize("angle", [None, 90])
def test_par_allows_right_angle(angle):
    assert GroundFloor(parking_axis="inner_par", parking_angle=angle).parking_angle == angle


@pytest.mark.parametrize("angle", [45, 60])
def test_par_rejects_slant(angle):
    with pytest.raises(ValidationError, match="직각뿐"):
        GroundFloor(parking_axis="inner_par", parking_angle=angle)


@pytest.mark.parametrize("angle", [None, 45, 60, 90])
def test_perp_takes_any_angle(angle):
    assert GroundFloor(parking_axis="inner_perp", parking_angle=angle).parking_angle == angle


@pytest.mark.parametrize("axis", LEGACY)
@pytest.mark.parametrize("angle", [None, 45, 60, 90])
def test_legacy_combinations_unchanged(axis, angle):
    """기존 값에는 새 검증을 걸지 않는다 — 심긴 옵션이 어느 날 거부되면 안 된다."""
    g = GroundFloor(parking_axis=axis, parking_angle=angle)
    assert (g.parking_axis, g.parking_angle) == (axis, angle)
