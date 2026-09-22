"""GroundFloor→Core.core_rotation — 코어 배향 절대 회전각 (#4), core_axis 제거 (#10 ⑤).

코어는 점대칭이 아니라(계단·EV 한쪽 편재, 복도 한 면 접합) 0·90·180·270이 전부 다른
결과를 낸다. 구 core_axis(road/depth)는 절반만 지정해 같은 축 위 180° 뒤집기를 표현할 수
없었고, 이제 제거됐다 — 무손실 변환이 안 되므로 조용히 접지 않고 거부한다.
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
def test_legacy_core_axis_rejected_with_a_way_out(axis):
    """구 17필지가 심은 값 — 버리면 배향 의도가 사라지고, 접으면 다른 도면이 나온다."""
    with pytest.raises(ValidationError, match="measure_core_rotation"):
        Core(core_axis=axis)
