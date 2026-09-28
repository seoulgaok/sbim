"""속성 창 정리(2026-09-28) — 지운 키는 받아 버리고, 옮긴 키는 새 자리로 옮겨 받는다.

원칙: 옵션 = 설계자가 두는 **수**만. 법은 상수, 대수는 결과, 법규 보정은 regulations.
저장된 설계안(파일·DB jsonb)은 옛 키를 심고 있어, 거부하면 통째로 안 열린다 —
그래서 새 모양(design/standards/business)으로 와도, 옛 평평한 모양(ground_floor …)으로
와도 같은 새 모양으로 떨어져야 한다. 이 파일이 지키는 것이 그 이행이다.
"""

import pytest

from seoulgaok_bim_core import BuildOptions
from seoulgaok_bim_core.options import (
    Circulation, Core, Dimensions, Massing, Parking, RegulationOverrides, UnitSpec,
)

# 새 모양인데 옛 키가 섞인 저장값
NEW_SHAPE_WITH_OLD_KEYS = {
    "design": {
        "massing": {"target_floor_count": 5, "commercial_remainder": True},
        "units": {"units_per_floor": 4, "cut_axis": "road"},
        "core": {"type": 1, "core_side": "s", "core_along": "mid", "composition": "stair"},
        "parking": {
            "count": 6, "type": "perpendicular", "bk_offset": 5.5,
            "interior_aisle": True, "tandem": True,
            "road_setback": 0.5, "ratio_mode": "non_residential",
        },
        "circulation": {"corridor_mode": "edge", "pedestrian_width": 1.8},
        "regulations": {"far_target": 230.0, "bcr_target": 55.0},
    },
    "standards": {"dimensions": {"stall_width": 2.6, "stall_depth": 5.2,
                                 "aisle_width": 6.5, "max_span": 7.5}},
}

# 옛 평평한 모양(구 13블록 — ground_floor 서랍)
OLD_FLAT = {
    "massing": {"target_floor_count": 5},
    "core": {"type": 1, "composition": "stair"},
    "parking": {"count": 6, "ratio_mode": "non_residential", "stall_depth": 5.2},
    "ground_floor": {
        "core_side": "s", "core_along": "mid", "core_mirror": True,
        "interior_aisle": True, "bk_offset": 5.5, "commercial_remainder": True,
        "road_setback": 0.5, "pedestrian_width": 1.8, "parallel": False,
        "corridor_mode": "edge", "max_span": 7.5,
    },
    "regulations": {"far_target": 230.0},
}


@pytest.mark.parametrize("raw", [NEW_SHAPE_WITH_OLD_KEYS, OLD_FLAT], ids=["new", "flat"])
def test_old_keys_land_in_new_shape(raw):
    o = BuildOptions.model_validate(raw)
    d = o.model_dump()
    # 지운 키는 사라진다
    assert "commercial_remainder" not in d["design"]["massing"]
    assert "cut_axis" not in d["design"]["units"]
    assert not {"core_along", "composition"} & set(d["design"]["core"])
    assert not {"count", "type", "bk_offset", "interior_aisle",
                "road_setback", "ratio_mode"} & set(d["design"]["parking"])
    assert "pedestrian_width" not in d["design"]["circulation"]
    assert not {"stall_width", "stall_depth", "aisle_width"} & set(d["standards"]["dimensions"])
    # 흡수 · 개명 · 이동
    assert o.design.parking.parking_axis == "inner"
    assert o.design.regulations.far_limit_override == 230.0
    assert o.design.regulations.road_setback == 0.5
    assert o.design.regulations.pedestrian_width == 1.8
    assert o.design.regulations.ratio_mode == "non_residential"
    # 옮기지 않은 값은 그대로
    assert o.design.core.core_side == "s"
    assert o.design.circulation.corridor_mode == "edge"
    assert o.standards.dimensions.max_span == 7.5


def test_new_shape_bcr_rename():
    o = BuildOptions.model_validate(NEW_SHAPE_WITH_OLD_KEYS)
    assert o.design.regulations.bcr_limit_override == 55.0
    assert o.get_upper_floor_ratio(0.6) == 0.55


def test_flat_shape_keeps_new_fields_it_carries():
    o = BuildOptions.model_validate(OLD_FLAT)
    assert o.design.core.core_mirror is True
    assert o.design.parking.parallel is False


@pytest.mark.parametrize(("ia", "axis"), [(True, "inner"), (False, "road"), (None, None)])
def test_interior_aisle_becomes_parking_axis(ia, axis):
    assert Parking.model_validate({"interior_aisle": ia}).parking_axis == axis


def test_parking_axis_wins_over_interior_aisle():
    p = Parking.model_validate({"interior_aisle": True, "parking_axis": "road"})
    assert p.parking_axis == "road"


def test_interior_aisle_false_drops_diagonal_angle():
    """옛 엔진은 내부 차로가 아니면 각도를 안 읽었다 — road 로 옮기며 각도를 버려야 열린다."""
    p = Parking.model_validate({"interior_aisle": False, "parking_angle": 45})
    assert p.parking_axis == "road" and p.parking_angle is None


def test_interior_aisle_with_legacy_auto_axis():
    p = Parking.model_validate({"interior_aisle": True, "parking_axis": "auto"})
    assert p.parking_axis == "inner"


@pytest.mark.parametrize(("old", "new"), [("far_target", "far_limit_override"),
                                          ("bcr_target", "bcr_limit_override")])
def test_regulation_rename(old, new):
    r = RegulationOverrides.model_validate({old: 200.0})
    assert getattr(r, new) == 200.0
    assert old not in RegulationOverrides.model_fields


def test_new_regulation_name_wins():
    r = RegulationOverrides.model_validate({"far_target": 200.0, "far_limit_override": 250.0})
    assert r.far_limit_override == 250.0


def test_regulations_value_wins_over_old_place():
    o = BuildOptions.model_validate({"design": {
        "parking": {"road_setback": 0.5},
        "regulations": {"road_setback": 1.0},
    }})
    assert o.design.regulations.road_setback == 1.0


def test_old_place_merges_into_regulations_instance():
    from seoulgaok_bim_core.options import Design
    d = Design.model_validate({
        "parking": {"ratio_mode": "non_residential"},
        "regulations": RegulationOverrides(far_limit_override=210.0),
    })
    assert d.regulations.ratio_mode == "non_residential"
    assert d.regulations.far_limit_override == 210.0


@pytest.mark.parametrize(("cls", "name"), [
    (Massing, "commercial_remainder"), (UnitSpec, "cut_axis"),
    (Core, "core_along"), (Core, "composition"),
    (Parking, "count"), (Parking, "type"), (Parking, "bk_offset"),
    (Parking, "interior_aisle"), (Parking, "road_setback"), (Parking, "ratio_mode"),
    (Circulation, "pedestrian_width"),
    (Dimensions, "stall_width"), (Dimensions, "stall_depth"), (Dimensions, "aisle_width"),
])
def test_removed_field_is_not_in_schema(cls, name):
    assert name not in cls.model_fields


def test_bk_eff_is_stall_depth():
    assert Parking().bk_eff() == 5.0
    assert Parking.model_validate({"bk_offset": 7.0}).bk_eff() == 5.0


def test_walk_width_reads_regulations():
    o = BuildOptions.model_validate({"design": {"circulation": {"pedestrian_width": None}}})
    assert o.design.regulations.pedestrian_width is None
    assert o.design.regulations.walk_width("multi_family") == 1.7
    assert BuildOptions().design.regulations.walk_width() == 1.5


def test_unknown_key_still_rejected():
    """받아서 버리는 건 지운 키뿐이다 — 오타는 여전히 거부한다."""
    with pytest.raises(Exception):
        BuildOptions.model_validate({"design": {"parking": {"parking_axiss": "road"}}})
