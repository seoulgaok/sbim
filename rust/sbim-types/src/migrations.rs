// 생성 파일 — 손으로 고치지 마라.
// 정본: python/seoulgaok_bim_core/options.py (pydantic)
// 생성: cd python && uv run python scripts/gen_build_options.py
//
// 옛 저장값을 새 모양으로 옮기는 **표**(fixtures/migrations.json 과 같다). 접는 로직은 여기 없다 —
// 소비처가 이 표로 구현하고 fixtures/build_options/*.json(input → expected)을 정답으로 검사한다.
// 파이썬 구현은 options.py 의 `BuildOptions._migrate_legacy_shape` · 각 모델의 before validator.

/// 구 13블록 평평한 모양의 최상위 키 — 이 중 하나라도 있으면 옛 모양이다.
pub const LEGACY_TOP_BLOCKS: &[&str] = &["massing", "units", "core", "structure", "windows", "parking", "ground_floor", "concrete", "schedule", "financing", "exterior", "regulations"];

/// 구 `ground_floor` 의 키 → 새 묶음(core · parking · regulations · circulation · dimensions).
pub const GROUND_FLOOR_TO: &[(&str, &str)] = &[
    ("core_side", "core"),
    ("core_rotation", "core"),
    ("core_axis", "core"),
    ("core_entries", "core"),
    ("core_mirror", "core"),
    ("parallel", "parking"),
    ("multi_road", "parking"),
    ("parking_axis", "parking"),
    ("parking_angle", "parking"),
    ("road_edge", "parking"),
    ("entry2", "parking"),
    ("tandem", "parking"),
    ("exit_road", "parking"),
    ("parking_graph", "parking"),
    ("interior_aisle", "parking"),
    ("road_setback", "regulations"),
    ("pedestrian_width", "regulations"),
    ("corridor_mode", "circulation"),
    ("max_span", "dimensions"),
    ("cantilever", "dimensions"),
    ("min_col_dist", "dimensions"),
];

/// 구 `ground_floor` 에서 버리는 키.
pub const GROUND_FLOOR_DROPPED: &[&str] = &["bk_offset", "commercial_remainder", "core_along", "preferred_min_span"];

/// 구 `parking` 의 치수 키 — 법 상수라 버린다.
pub const PARKING_DIMS_DROPPED: &[&str] = &["stall_width", "stall_depth", "aisle_width"];

/// 이름만 바뀐 키(옛 → 새).
pub const RENAMED: &[(&str, &str)] = &[
    ("entry2", "multi_road"),
];

/// `regulations` 안에서 이름이 바뀐 키(옛 → 새).
pub const REGULATIONS_RENAMED: &[(&str, &str)] = &[
    ("far_target", "far_limit_override"),
    ("bcr_target", "bcr_limit_override"),
];

/// 다른 묶음에서 `regulations` 로 옮겨 간 키 — (옛 묶음, 키).
pub const MOVED_TO_REGULATIONS: &[(&str, &str)] = &[
    ("parking", "road_setback"),
    ("parking", "ratio_mode"),
    ("circulation", "pedestrian_width"),
];

/// 묶음별로 받아서 버리는 키 — (묶음, 키들).
pub const DROPPED: &[(&str, &[&str])] = &[
    ("financing", &["presale_start_offset", "presale_period", "deposit_pct", "mid_pct", "balance_pct"]),
];

/// 코어 유형 번호 개번 표(2026-09, building-generator #190) — (옛, 새). 값 집합이 1~7 로 같아
/// 검증으로는 못 가리니 저장값의 `core.type` 은 읽을 때 이 표로 옮긴다.
pub const CORE_TYPE_OLD_TO_NEW: &[(u8, u8)] = &[(1, 2), (2, 1), (3, 4), (4, 5), (5, 7), (6, 6), (7, 3)];

/// 옛 코어 번호 → 새 번호. 표에 없는 번호는 `None`(파이썬 `migrate_core_type` 은 ValueError).
pub fn core_type_old_to_new(old: u8) -> Option<u8> {
    CORE_TYPE_OLD_TO_NEW.iter().find(|(o, _)| *o == old).map(|(_, n)| *n)
}
