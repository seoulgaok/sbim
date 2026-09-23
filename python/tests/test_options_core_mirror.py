"""Core.core_mirror — 코어 좌우 뒤집기(반대 손잡이).

코어는 점대칭도 선대칭도 아니라(계단·EV 한쪽 편재, 복도 한 면 접합) 회전 네 방위만으로는
거울 모양을 못 만든다. 회전 180°는 가로·세로를 함께 뒤집어 복도 면까지 옮기고, 거울은 복도
면을 둔 채 좌우만 바꾼다. core_rotation(4) × core_mirror(2)가 코어가 변에 앉는 여덟 자세를
전부 적는다 — 둘은 따로 고른다.
"""

import pytest

from seoulgaok_bim_core.options import Core


@pytest.mark.parametrize("mirror", [True, False])
def test_both_hands_accepted(mirror):
    assert Core(core_mirror=mirror).core_mirror is mirror


def test_default_defers_to_first_move():
    assert Core().core_mirror is None


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_mirror_is_independent_of_rotation(rotation):
    """여덟 자세 — 회전과 뒤집기는 서로를 덮지 않는다."""
    c = Core(core_rotation=rotation, core_mirror=True)
    assert (c.core_rotation, c.core_mirror) == (rotation, True)


def test_mirror_survives_legacy_core_axis_drop():
    """구 core_axis 를 버리는 이행층이 새 필드를 같이 지우면 안 된다."""
    c = Core.model_validate({"core_axis": "road", "core_mirror": True})
    assert c.core_mirror is True
    assert c.core_rotation is None
