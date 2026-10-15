// 생성 파일 — 손으로 고치지 마라.
// 정본: python/seoulgaok_bim_core/options.py (pydantic)
// 생성: cd python && uv run python scripts/gen_build_options.py
//
// 구조방식(design.structure)별 프리셋 — fixtures/presets.json 과 같다. 사용자가 비운 칸만 채운다
// (파이썬 BuildOptions after validator: model_fields_set 에 없을 때).

/// 구조방식 하나가 채우는 값.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Preset {
    pub wall_thickness: f64,
    pub max_span: f64,
    pub min_col_dist: f64,
}

/// (구조방식 이름, 프리셋) — 이름은 `build_options::Structure` 의 값과 같다.
pub const STRUCTURE_PRESET: &[(&str, Preset)] = &[
    ("wall", Preset { wall_thickness: 0.2, max_span: 8.1, min_col_dist: 3.0 }),
    ("rahmen", Preset { wall_thickness: 0.15, max_span: 8.1, min_col_dist: 3.0 }),
    ("steel", Preset { wall_thickness: 0.12, max_span: 12.0, min_col_dist: 6.0 }),
];

/// 구조방식 이름으로 프리셋을 찾는다 — 모르는 이름은 `None`.
pub fn structure_preset(name: &str) -> Option<Preset> {
    STRUCTURE_PRESET.iter().find(|(n, _)| *n == name).map(|(_, p)| *p)
}
