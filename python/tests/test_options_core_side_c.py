"""Core.core_side 의 c — 매스 안쪽 (새 어휘, 2026-09-24).

엔진이 지금 읽는 c: 주접도 프레임 축을 따라 매스 경계에서 1.5m 이상 떨어진 자리,
기준 변=주접도 변, 그런 자리가 없으면 변에 붙은 코어로 폴백하지 않고
CoreTypeInfeasible 로 실패, 상층은 코어 양쪽 편복도. 계약 설명도 이 뜻을 적어야 한다.
"""

from seoulgaok_bim_core.options import Core


def test_c_description_says_mass_interior():
    desc = Core.model_fields["core_side"].description
    assert "매스 안쪽" in desc, f"c 설명이 새 뜻(매스 안쪽)을 담지 않는다: {desc}"
    for keyword in ("1.5m", "주접도", "CoreTypeInfeasible", "편복도"):
        assert keyword in desc, f"c 설명에 '{keyword}'가 없다: {desc}"


def test_core_rotation_mentions_main_road_frame_for_c():
    desc = Core.model_fields["core_rotation"].description
    assert "주접도" in desc, f"core_rotation 설명에 c의 기준 변(주접도 변)이 없다: {desc}"
