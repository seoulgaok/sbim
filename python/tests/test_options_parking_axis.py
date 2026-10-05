"""parking_axis·road_edge·multi_road — 주차 버블이 뜻을 대신 가져간 세 필드의 삭제.

버블이 「어느 도로에 어떤 종류로 주차하나」를 정하므로 주 배치 축·주접도 변 번호·
다중도로 여부는 버블이 대신한다. building-generator 는 이 셋을 어디서도 읽지 않고
(PR #346) REF 48 필지가 전부 버블 경로로 깐다.

공유 참조 REF·204 저장값에는 이 키가 남아 있을 수 있다 — 거부하지 않고 **조용히
버린다**(거부하면 그 키를 심은 설계안·DB jsonb가 통째로 안 열린다).
"""

import pytest

from seoulgaok_bim_core import BuildOptions, Parking

REMOVED = {"parking_axis", "road_edge", "multi_road", "interior_aisle"}


def test_removed_fields_are_not_in_schema():
    assert not REMOVED & set(Parking.model_fields)


# 구 값도 같이 묻는다 — "auto"(구 저장값 51건)·"core"(이태원동 303-22)는 더 이상
# 접거나 거부하지 않고 키째 버린다.
@pytest.mark.parametrize("old", [
    {"parking_axis": "inner"},
    {"parking_axis": "auto"},
    {"parking_axis": "core"},
    {"road_edge": 1},
    {"multi_road": True},
    {"interior_aisle": True},
])
def test_removed_keys_are_dropped(old):
    """버리는 것을 단언한다 — 검증 실패가 아니라 조용히 사라져야 한다."""
    p = Parking.model_validate({**old, "parking_graph": [["n", "road"]]})
    assert p.parking_graph == [("n", "road")]
    assert not set(old) & set(p.model_dump())


def test_removed_keys_dropped_in_both_shapes():
    """새 모양(design.parking)과 구 평면 모양(ground_floor) 어디서 와도 같이 버려진다."""
    new = BuildOptions.model_validate({
        "design": {"parking": {"parking_axis": "auto", "road_edge": 2, "multi_road": True}},
    })
    flat = BuildOptions.model_validate({
        "ground_floor": {"parking_axis": "inner", "road_edge": 1, "entry2": True},
    })
    for o in (new, flat):
        dumped = o.design.parking.model_dump()
        assert not (REMOVED | {"entry2"}) & set(dumped)


def test_typo_still_rejected():
    """받아서 버리는 건 지운 키뿐이다 — 오타는 여전히 거부한다."""
    with pytest.raises(Exception):
        Parking.model_validate({"parking_axiss": "road"})
