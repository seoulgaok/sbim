# 생성 파일 — 손으로 고치지 마라.
# 정본: python/seoulgaok_bim_core/options.py (_LEGACY_TOP·_GF_TO·… · fixtures/migrations.json 과 같다)
# 생성: cd python && uv run python scripts/gen_build_options.py

defmodule Sbim.Migrations do
  @moduledoc ~S"""
  옛 저장값을 새 모양으로 옮기는 표 — fixtures/migrations.json 과 같다. 표만 있고 적용 로직은
  없다(파이썬은 `BuildOptions._migrate_legacy_shape`·각 모델의 before validator). 표로 못 적는
  규칙(주차 버블 구 노드 접기 등)은 fixtures/build_options/ 케이스가 정답을 준다.
  """

  @doc "구 13블록 평면 모양의 최상위 키 — 하나라도 있으면 구 모양이다."
  def legacy_top_blocks, do: ["massing", "units", "core", "structure", "windows", "parking", "ground_floor", "concrete", "schedule", "financing", "exterior", "regulations"]

  @doc "구 `ground_floor.<키>` → 새 묶음(core·parking·regulations·circulation·dimensions)."
  def ground_floor_to, do: %{
    "core_side" => "core",
    "core_rotation" => "core",
    "core_axis" => "core",
    "core_entries" => "core",
    "core_mirror" => "core",
    "parallel" => "parking",
    "multi_road" => "parking",
    "parking_axis" => "parking",
    "parking_angle" => "parking",
    "road_edge" => "parking",
    "entry2" => "parking",
    "tandem" => "parking",
    "exit_road" => "parking",
    "parking_graph" => "parking",
    "interior_aisle" => "parking",
    "road_setback" => "regulations",
    "pedestrian_width" => "regulations",
    "corridor_mode" => "circulation",
    "max_span" => "dimensions",
    "cantilever" => "dimensions",
    "min_col_dist" => "dimensions"
  }

  @doc "구 `ground_floor` 에서 지운 키 — 옮길 자리가 없다."
  def ground_floor_dropped, do: ["bk_offset", "commercial_remainder", "core_along", "preferred_min_span"]

  @doc "주차 칸·차로 치수 — 주차장법 상수라 받아서 버린다."
  def parking_dims_dropped, do: ["stall_width", "stall_depth", "aisle_width"]

  @doc "구 이름 → 새 이름(뜻은 같다)."
  def renamed, do: %{
    "entry2" => "multi_road"
  }

  @doc "구 regulations 이름 → 새 이름(`far_target` → `far_limit_override`)."
  def regulations_renamed, do: %{
    "far_target" => "far_limit_override",
    "bcr_target" => "bcr_limit_override"
  }

  @doc "옛 자리 → `design.regulations` 로 옮긴 필드 — [묶음, 필드] 쌍."
  def moved_to_regulations, do: [
    ["parking", "road_setback"],
    ["parking", "ratio_mode"],
    ["circulation", "pedestrian_width"]
  ]

  @doc "묶음별 지운 키 — 받아서 버린다."
  def dropped, do: %{
    "financing" => ["presale_start_offset", "presale_period", "deposit_pct", "mid_pct", "balance_pct"]
  }

  @doc "코어 유형 번호 개번 표(2026-09) — 옛 번호 → 새 번호. 값 집합이 1~7 로 같아 검증에 안 걸린다."
  def core_type_old_to_new, do: %{
    1 => 2,
    2 => 1,
    3 => 4,
    4 => 5,
    5 => 7,
    6 => 6,
    7 => 3
  }

  @doc "옛 번호 하나 → 새 번호. nil(auto)은 그대로, 표에 없는 번호는 KeyError."
  def core_type_old_to_new(nil), do: nil
  def core_type_old_to_new(old) when is_integer(old), do: Map.fetch!(core_type_old_to_new(), old)
end
