"""GroundFloor→Core.core_rotation — 코어 배향 절대 회전각 (#4), core_axis 제거 (#10 ⑤).

코어는 점대칭이 아니라(계단·EV 한쪽 편재, 복도 한 면 접합) 0·90·180·270이 전부 다른
결과를 낸다. 구 core_axis(road/depth)는 절반만 지정해 같은 축 위 180° 뒤집기를 표현할 수 없었고,
이제 제거됐다. 회전각으로 옮길 수 없으니(road는 0인지 180인지 모른다) 값으로 옮기는 대신
버린다 — 비면 첫수표가 정한다(#13). 거부하면 구 저장값이 통째로 안 열린다.
"""

import pytest
from pydantic import ValidationError

from seoulgaok_bim_core.options import Core


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_four_orientations_accepted(rotation):
    assert Core(core_rotation=rotation).core_rotation == rotation


def test_default_defers_to_first_move():
    assert Core().core_rotation is None


@pytest.mark.parametrize("rotation", [45, 360, -90])
def test_off_grid_rotation_rejected(rotation):
    with pytest.raises(ValidationError):
        Core(core_rotation=rotation)


def test_core_axis_is_gone():
    assert "core_axis" not in Core.model_fields


@pytest.mark.parametrize("axis", ["road", "depth"])
def test_legacy_core_axis_is_dropped_not_rejected(axis):
    """구 저장값이 심은 값 — 버리고 첫수표에 맡긴다. 거부하면 그 설계안이 안 열린다."""
    c = Core.model_validate({"core_axis": axis, "type": 2})
    assert c.core_rotation is None
    assert c.type == 2
    assert not hasattr(c, "core_axis")


@pytest.mark.parametrize(("axis", "rotation"), [("road", 180), ("depth", 270)])
def test_core_rotation_survives_alongside_legacy_axis(axis, rotation):
    """둘 다 있으면 정밀한 쪽(core_rotation)이 남는다."""
    c = Core.model_validate({"core_axis": axis, "core_rotation": rotation})
    assert c.core_rotation == rotation
