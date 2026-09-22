"""GroundFloor.core_rotation — 코어 배향 절대 회전각 (#4).

legacy core_axis(road/depth) ↔ 신규 core_rotation(0/90/180/270) 이행 계약:
- core_axis만 있으면(구 _build_options.json 17필지) 뜻 그대로 절반 지정으로 유지.
- core_rotation만 있으면 core_axis로 자동 동기화(0/180→road, 90/270→depth) —
  core_axis를 읽는 구 소비처와 호환.
- 둘 다 주고 모순되면 거부(road↔{0,180}, depth↔{90,270}).
"""

import pytest
from pydantic import ValidationError

from seoulgaok_bim_core.options import Core


@pytest.mark.parametrize("axis", ["road", "depth"])
def test_legacy_core_axis_unchanged(axis):
    """core_axis만 주면 core_rotation은 None — 뜻이 조용히 바뀌지 않는다."""
    g = Core(core_axis=axis)
    assert g.core_axis == axis
    assert g.core_rotation is None


@pytest.mark.parametrize(
    ("rotation", "axis"),
    [(0, "road"), (90, "depth"), (180, "road"), (270, "depth")],
)
def test_core_rotation_syncs_core_axis(rotation, axis):
    """core_rotation만 주면 legacy core_axis로 동기화 — 구 소비처 호환."""
    g = Core(core_rotation=rotation)
    assert g.core_rotation == rotation
    assert g.core_axis == axis


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_core_rotation_consistent_with_axis(rotation):
    """둘 다 주고 일관(같은 coarse)이면 통과."""
    coarse = "road" if rotation in (0, 180) else "depth"
    g = Core(core_axis=coarse, core_rotation=rotation)
    assert g.core_rotation == rotation
    assert g.core_axis == coarse


@pytest.mark.parametrize(
    ("axis", "rotation"), [("road", 90), ("road", 270), ("depth", 0), ("depth", 180)]
)
def test_core_axis_rotation_contradiction_rejected(axis, rotation):
    """둘 다 주고 모순이면 거부 — 병존이 아니라 대체/이행."""
    with pytest.raises(ValidationError):
        Core(core_axis=axis, core_rotation=rotation)
