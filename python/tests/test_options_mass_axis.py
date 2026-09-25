"""Massing.mass_axis — 매스 작업축(도로축/일조발생라인) (#15).

상층 매스를 반듯하게 세울 기준 방향. 지금은 엔진이 두 축으로 쌓아 보고 반듯함·면적
점수로 혼자 고르는데, 같은 점수로 이태원동 303-22(소장 일조축)는 맞고 삼선동3가
31-1(소장 도로축)은 틀린다. 필지의 설계 의도라 속성 창 값이다 — 비면 첫수표가 정한다.
"""

import pytest
from pydantic import ValidationError

from seoulgaok_bim_core.options import Massing


def test_default_defers_to_first_move():
    assert Massing().mass_axis is None


@pytest.mark.parametrize("axis", ["road", "sunlight"])
def test_both_axes_accepted(axis):
    assert Massing(mass_axis=axis).mass_axis == axis


@pytest.mark.parametrize("bad", ["north", "depth", "auto", ""])
def test_other_values_rejected(bad):
    with pytest.raises(ValidationError):
        Massing(mass_axis=bad)


@pytest.mark.parametrize("axis", [None, "road", "sunlight"])
def test_round_trip(axis):
    m = Massing(mass_axis=axis)
    assert Massing.model_validate(m.model_dump()).mass_axis == axis
    assert Massing.model_validate_json(m.model_dump_json()).mass_axis == axis
