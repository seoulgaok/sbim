"""BuildOptions 재배치 — 설계·표준·사업성 분리와 구 모양 이행 (#10 ①②).

99필드 한 창에 설계 선택·회사 표준·사업성이 섞여 있었고, 묶음이 대상이 아니라 단계로
잘려 있었다(구 GroundFloor가 주차·코어·동선·기둥을 21필드 한 서랍에 담았다).

저장된 설계안은 전부 구 경로다(reference/*/_build_options.json, DB jsonb). 읽는 자리에서
옮겨 받으므로 데이터 마이그레이션 없이 열린다 — 그 이행이 값을 흘리지 않는지가 이 파일이
지키는 것이다.
"""

import json
from pathlib import Path

import pytest

from seoulgaok_bim_core import BuildOptions

# 구 모양 13블록 — 대상별로 어디에 도착해야 하는가
LEGACY = {
    "massing": {"target_floor_count": 6, "first_floor_height": 3.6},
    "units": {"units_per_floor": 3, "cut_axis": "depth"},
    "core": {"type": 2, "composition": "stair"},
    "structure": {"system": "rahmen"},
    "windows": {"style": "open"},
    "exterior": {"style": "brick"},
    "parking": {
        "count": 7, "ratio_mode": "non_residential",
        "stall_width": 2.6, "stall_depth": 5.2, "aisle_width": 6.5,
    },
    "ground_floor": {
        "core_side": "ne", "core_rotation": 90, "core_entries": 2,
        "parking_axis": "inner", "parking_angle": 45, "road_edge": 1,
        "entry2": True, "tandem": False, "bk_offset": 5.5,
        "interior_aisle": True, "exit_road": 0, "road_setback": 1.5,
        "corridor_mode": "edge", "pedestrian_width": 1.8,
        "commercial_remainder": True,
        "max_span": 7.2, "cantilever": 1.4, "min_col_dist": 3.1,
        "preferred_min_span": 4.2,
    },
    "concrete": {"wall_thickness": 0.22, "price_per_m3": 190000},
    "schedule": {"construction_months": 14},
    "financing": {"land_loan_ltv": 0.7},
    "regulations": {"bcr_target": 58.0},
}

EXPECTED = [
    ("design.massing.target_floor_count", 6),
    ("design.massing.first_floor_height", 3.6),
    ("design.massing.commercial_remainder", True),     # 단계 서랍 → 매스
    ("design.units.units_per_floor", 3),
    ("design.units.cut_axis", "depth"),
    ("design.core.type", 2),
    ("design.core.composition", "stair"),
    ("design.core.core_side", "ne"),                   # 코어 자리가 코어로 모인다
    ("design.core.core_rotation", 90),
    ("design.core.core_entries", 2),
    ("design.parking.count", 7),
    ("design.parking.ratio_mode", "non_residential"),
    ("design.parking.parking_axis", "inner"),          # 주차 배치가 주차로 모인다
    ("design.parking.parking_angle", 45),
    ("design.parking.road_edge", 1),
    ("design.parking.entry2", True),
    ("design.parking.tandem", False),
    ("design.parking.bk_offset", 5.5),
    ("design.parking.interior_aisle", True),
    ("design.parking.exit_road", 0),
    ("design.parking.road_setback", 1.5),
    ("design.circulation.corridor_mode", "edge"),      # 동선이 제 집을 갖는다
    ("design.circulation.pedestrian_width", 1.8),
    ("design.exterior.style", "brick"),                # 한 필드 클래스 둘을 흡수
    ("design.exterior.window_style", "open"),
    ("design.structure", "rahmen"),                    # 한 필드 클래스를 스칼라로
    ("design.regulations.bcr_target", 58.0),
    ("standards.concrete.wall_thickness", 0.22),       # 회사 표준은 접히는 묶음으로
    ("standards.concrete.price_per_m3", 190000),
    ("standards.dimensions.stall_width", 2.6),         # 치수는 선택이 아니라 표준
    ("standards.dimensions.stall_depth", 5.2),
    ("standards.dimensions.aisle_width", 6.5),
    ("standards.dimensions.max_span", 7.2),
    ("standards.dimensions.cantilever", 1.4),
    ("standards.dimensions.min_col_dist", 3.1),
    ("standards.dimensions.preferred_min_span", 4.2),
    ("business.schedule.construction_months", 14),     # 사업성은 도면과 무관
    ("business.financing.land_loan_ltv", 0.7),
]


def _dig(obj, path):
    for part in path.split("."):
        obj = getattr(obj, part)
    return obj


@pytest.mark.parametrize(("path", "expected"), EXPECTED)
def test_legacy_field_lands_in_its_object(path, expected):
    assert _dig(BuildOptions.model_validate(LEGACY), path) == expected


def test_legacy_migration_loses_nothing():
    """구 13블록의 모든 값이 새 모양 어딘가에 있다 — 흘린 값이 없다."""
    got = BuildOptions.model_validate(LEGACY)
    flat = {k: v for block in LEGACY.values() for k, v in block.items()}
    dumped = json.dumps(got.model_dump(), ensure_ascii=False, sort_keys=True)
    missing = [
        k for k, v in flat.items()
        if k != "system" and f'"{k}":' not in dumped.replace(" ", "")
        and json.dumps(v, ensure_ascii=False) not in dumped
    ]
    assert missing == [], f"이행에서 사라진 필드: {missing}"


def test_new_shape_is_not_touched():
    """새 키가 있으면 이행기가 건드리지 않는다."""
    o = BuildOptions.model_validate({"design": {"core": {"type": 3}}})
    assert o.design.core.type == 3


def test_mixing_shapes_is_rejected():
    """섞어 주면 거부한다 — 조용한 반쪽 적용을 막는다."""
    with pytest.raises(Exception):
        BuildOptions.model_validate({"design": {"core": {"type": 3}}, "ground_floor": {"road_edge": 1}})


def test_unknown_legacy_key_still_rejected():
    """구 모양이라고 아무 키나 받지 않는다."""
    with pytest.raises(Exception):
        BuildOptions.model_validate({"ground_floor": {"nonexistent_field": 1}})


def test_structure_preset_follows_new_paths():
    """구조방식 프리셋이 새 경로(standards)로 채워진다."""
    o = BuildOptions.model_validate({"design": {"structure": "steel"}})
    assert o.base_floor_height == 3.4
    assert o.standards.dimensions.max_span > BuildOptions().standards.dimensions.max_span


def test_helpers_read_new_paths():
    o = BuildOptions.model_validate(
        {"design": {"massing": {"first_floor_height": 4.2, "floor_use": {1: "commercial"}},
                    "regulations": {"bcr_target": 55.0}}}
    )
    assert o.get_floor_height(1) == 4.2
    assert o.get_floor_use(1) == "commercial"
    assert o.get_first_floor_ratio() == 0.6
    assert o.get_upper_floor_ratio(0.5) == 0.55


def test_object_helpers_moved_to_their_owners():
    """bk_eff는 주차가, walk_width·aisle은 동선이 갖는다."""
    o = BuildOptions.model_validate({"ground_floor": {"bk_offset": 6.0, "pedestrian_width": 2.0}})
    assert o.design.parking.bk_eff() == 6.0
    assert o.design.circulation.walk_width() == 2.0
    assert o.design.circulation.aisle() == 2.5


REF_ROOTS = [
    Path("/Users/ichanghyeon/Desktop/seoulgaok/20260506_sbim/reference/sbim"),
    Path("/Users/ichanghyeon/Desktop/seoulgaok/20250724_volume_suggestion/reference/sbim"),
]


def test_every_stored_design_still_loads():
    """저장된 설계안 전수 — 구 경로로 박혀 있어도 열린다(로컬에 있을 때만).

    GT 파일은 giga 전용 평면 약칭을 함께 쓴다(`core_type`·`target_floor_count`·
    `units_by_level`) — sbim 필드가 아니라 giga가 `pipeline.py`에서 옮겨 넣는 값이라
    여기서도 같이 옮긴 뒤 검증한다.
    """
    files = [p for root in REF_ROOTS for p in sorted(root.glob("*/_build_options.json"))]
    if not files:
        pytest.skip("reference/ 없음 — gitignore 대상")
    failed = []
    for p in files:
        raw = json.loads(p.read_text())
        raw = {k: v for k, v in raw.items() if not k.startswith("_")}   # _gt_notes 등 GT 메모
        if (ct := raw.pop("core_type", None)) is not None:
            raw.setdefault("core", {})["type"] = ct
        if (fc := raw.pop("target_floor_count", None)) is not None:
            raw.setdefault("massing", {})["target_floor_count"] = fc
        if (ubl := raw.pop("units_by_level", None)) is not None:
            raw.setdefault("units", {})["units_by_level"] = ubl
        try:
            BuildOptions.model_validate(raw)
        except Exception as e:
            failed.append((p.parent.name, str(e).split("\n")[1][:70]))
    # 유일하게 허용되는 실패 — 이태원동은 구 parking_axis="core"를 심고 있고, 이 릴리스가
    # 그 값을 의도적으로 거부한다(#10 ⑤: 조용히 접지 않는다). giga 기록에서 지우면 사라진다.
    known = {("이태원동_303-22", "design.parking.parking_axis")}
    assert set(failed) <= known, f"열리지 않는 저장값: {[f for f in failed if f not in known]}"
    assert failed, "이태원동의 core 거부가 사라졌다 — 기록이 정리됐으면 이 테스트를 지워라"
