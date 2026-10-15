# 생성 파일 — 손으로 고치지 마라.
# 정본: python/seoulgaok_bim_core/options.py (STRUCTURE_PRESET · fixtures/presets.json 과 같다)
# 생성: cd python && uv run python scripts/gen_build_options.py

defmodule Sbim.Presets do
  @moduledoc ~S"""
  구조방식 → 벽 두께·스팬·기둥 간격 기본값. BuildOptions 의 after-validator 가 명시하지 않은
  `standards.concrete.wall_thickness`·`standards.dimensions.max_span`·`min_col_dist` 를 이 표로
  채운다 — 생성된 defstruct 기본값에는 기본 구조(`design.structure`)의 몫이 이미 들어 있다.
  """

  @doc "구조방식 전부 — {구조: %{wall_thickness, max_span, min_col_dist}}."
  def structure_preset, do: %{
    "wall" => %{
      "wall_thickness" => 0.2,
      "max_span" => 8.1,
      "min_col_dist" => 3.0
    },
    "rahmen" => %{
      "wall_thickness" => 0.15,
      "max_span" => 8.1,
      "min_col_dist" => 3.0
    },
    "steel" => %{
      "wall_thickness" => 0.12,
      "max_span" => 12.0,
      "min_col_dist" => 6.0
    }
  }

  @doc "구조방식 하나 — 모르는 이름은 nil."
  def structure_preset("wall"), do: %{"wall_thickness" => 0.2, "max_span" => 8.1, "min_col_dist" => 3.0}
  def structure_preset("rahmen"), do: %{"wall_thickness" => 0.15, "max_span" => 8.1, "min_col_dist" => 3.0}
  def structure_preset("steel"), do: %{"wall_thickness" => 0.12, "max_span" => 12.0, "min_col_dist" => 6.0}
  def structure_preset(_), do: nil
end
