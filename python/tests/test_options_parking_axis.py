"""GroundFloor.parking_axis — 축은 둘, 「자동」은 하나 (#10 ③④).

#9로 내부 차로 배치 방식 넷(inner_perp·par·single·court)에 이름을 줬다가 되돌렸다.
소장 GT 30필지 실측에서 **대지 안쪽 12필지 중 9필지가 직각과 평행을 섞는다** — 소장은
방식을 고르는 게 아니라 한 방식 안에서 섞는다. 고르지 않는 것에 이름을 주면 과분류다.

「자동」의 표기도 하나로 접었다. 구 저장값의 "auto"는 받아서 None으로 옮긴다.
"""

import pytest
from pydantic import ValidationError

from seoulgaok_bim_core import Parking
from seoulgaok_bim_core.options import ParkingAxis
from typing import get_args


def test_default_is_none():
    """기본값은 None — 「자동」의 표기는 하나뿐이다."""
    assert Parking().parking_axis is None


def test_axes_are_two():
    """축은 둘 — 도로에 기대느냐, 대지 안에 차로를 내느냐."""
    assert set(get_args(ParkingAxis)) == {"road", "inner"}


@pytest.mark.parametrize("axis", ["road", "inner", None])
def test_accepted(axis):
    assert Parking(parking_axis=axis).parking_axis == axis


def test_legacy_auto_folds_to_none():
    """구 _build_options.json 51건이 "auto"를 심고 있다 — 거부하지 않고 옮겨 받는다."""
    assert Parking(parking_axis="auto").parking_axis is None


def test_legacy_auto_folds_in_nested_load():
    g = Parking.model_validate({"parking_axis": "auto", "parking_angle": 45})
    assert (g.parking_axis, g.parking_angle) == (None, 45)


@pytest.mark.parametrize(
    "axis",
    ["inner_perp", "inner_par", "inner_single", "inner_court", "core", "mass", "AUTO", ""],
)
def test_removed_and_unknown_values_rejected(axis):
    """#9의 inner_*와 구 core는 값이 아니다 — 되살아나면 여기서 걸린다.

    core는 조용히 접지 않고 **거부한다**. 이태원동 303-22에 사람이 심어둔 값이라
    말없이 None으로 바꾸면 그 의도가 사라진다 — giga 기록에서 먼저 지워야 한다.
    """
    with pytest.raises(ValidationError):
        Parking(parking_axis=axis)


def test_auto_metadata_is_machine_readable():
    """무엇을 비워도 되는지를 산문이 아니라 스키마가 말한다(#10 ③)."""
    extra = Parking.model_fields["parking_axis"].json_schema_extra
    assert extra == {"auto": True}
