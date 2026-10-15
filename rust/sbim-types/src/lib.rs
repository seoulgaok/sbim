//! sbim-types — sbim 계약의 Rust 판.
//!
//! 정본은 pydantic(`python/seoulgaok_bim_core/options.py` · `types.py`)이고 `src/` 의 나머지 네 파일은
//! 거기서 **생성**한다 — 손으로 고치지 마라.
//!
//!     cd python && uv run python scripts/gen_build_options.py          # 쓴다
//!     cd python && uv run python scripts/gen_build_options.py --check  # 갈리면 1
//!
//! 손판은 이 파일과 `Cargo.toml` · `tests/fixtures.rs` 뿐이다.
//!
//! - [`build_options`] — 속성 창 `BuildOptions` 와 그 묶음(design · standards · business).
//!   `Default` 는 `fixtures/build_options/empty.json` 의 정규화된 기본값이다.
//! - [`scheme`] — `scheme.json` · `units.json` · `surroundings.json` 레코드. 모르는 키는 `extra` 로 지나보낸다.
//! - [`migrations`] — 옛 저장값을 새 모양으로 옮기는 **표**(`fixtures/migrations.json`). 접는 로직은 없다.
//! - [`presets`] — 구조방식별 프리셋(`fixtures/presets.json`).

pub mod build_options;
pub mod migrations;
pub mod presets;
pub mod scheme;
