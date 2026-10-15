defmodule Sbim do
  @moduledoc """
  sbim 데이터 표준의 Elixir 판 — 정본 pydantic(python/seoulgaok_bim_core)에서 생성한다.

  - `Sbim.Options.BuildOptions` 와 그 묶음 — 속성 창. 기본값은 fixtures `empty.expected` 와 같다.
  - `Sbim.Scheme.*` — scheme.json·units.json·surroundings.json 계약(Scheme·UnitRecord·SurroundingBuilding).
  - `Sbim.Migrations` — 옛 저장값을 옮기는 표. `Sbim.Presets` — 구조방식 프리셋.

  lib/sbim/generated/ 는 생성 파일이다 — `cd python && uv run python scripts/gen_build_options.py`.
  각 모델은 `from_map/1`(문자열 키 map → struct)·`to_map/1` 을 갖고, 본체는 `Sbim.Codec` 이다.
  """
end
