defmodule Sbim.FixturesTest do
  @moduledoc """
  생성 모듈이 정본의 정답(fixtures/·examples/samples/)과 같은가.

  fixtures/README 는 소비처가 `input` 을 넣는다고 적지만 여기는 `expected` 를 넣는다 — 생성 모듈엔
  이행 로직이 없어 구 모양 `input` 은 모르는 키로 거부된다. `expected` 가 그대로 돌아오는 것과
  빈 struct 가 `empty` 와 같은 것(= 기본값 사고 가드)을 본다.
  """
  use ExUnit.Case, async: true

  alias Sbim.Options.BuildOptions

  @root Path.expand("../../..", __DIR__)

  defp read!(rel), do: @root |> Path.join(rel) |> File.read!() |> Jason.decode!()

  # ── 1. fixtures/build_options/*.json — expected 가 from_map → to_map 으로 그대로 돌아온다 ──

  for path <- Path.wildcard(Path.join(@root, "fixtures/build_options/*.json")) do
    @case Path.basename(path, ".json")

    test "build_options/#{@case} — expected round-trips" do
      %{"expected" => expected} = read!("fixtures/build_options/#{@case}.json")
      assert {:ok, %BuildOptions{} = opts} = BuildOptions.from_map(expected)
      assert BuildOptions.to_map(opts) === expected
    end
  end

  test "build_options — 스키마에 없는 키는 거부한다(Options 모델은 전부 additionalProperties: false)" do
    assert {:error, {:unknown_keys, [], ["bogus"]}} = BuildOptions.from_map(%{"bogus" => 1})

    assert {:error, {:unknown_keys, ["design", "parking"], ["parking_axis"]}} =
             BuildOptions.from_map(%{"design" => %{"parking" => %{"parking_axis" => "auto"}}})
  end

  # ── 2. 빈 struct = empty.json 의 expected — max_span 8.0/8.1 같은 기본값 사고를 이것이 잡는다 ──

  test "%BuildOptions{} |> to_map() == empty.expected" do
    %{"expected" => expected} = read!("fixtures/build_options/empty.json")
    assert BuildOptions.to_map(%BuildOptions{}) === expected
    assert %BuildOptions{}.standards.dimensions.max_span == 8.1
  end

  # ── 3. examples/samples — scheme.json·surroundings.json round-trip(밑줄 키·extra 포함) ──
  # units.json 샘플은 구 `Unit(geom/data)` 모양이라 UnitRecord 로 안 맞는다 — 건너뛴다.

  @schemes [
    "examples/samples/scheme.json",
    "examples/samples/sample-small/scheme.json",
    "examples/samples/sample-medium/scheme.json",
    "examples/samples/sample-large/scheme.json"
  ]

  for rel <- @schemes do
    @rel rel

    test "#{@rel} round-trips" do
      raw = read!(@rel)
      assert {:ok, %Sbim.Scheme.Scheme{} = scheme} = Sbim.Scheme.Scheme.from_map(raw)
      assert Sbim.Scheme.Scheme.to_map(scheme) === raw

      # 스키마에 없는 최상위 키(sample-*: `_core_candidates`)만 extra 에 남는다
      known = Enum.map(Sbim.Scheme.Scheme.__shape__().fields, &elem(&1, 0))
      assert Map.keys(scheme.extra) |> Enum.sort() == (Map.keys(raw) -- known) |> Enum.sort()
    end
  end

  test "examples/samples/surroundings.json round-trips" do
    raw = read!("examples/samples/surroundings.json")
    buildings = Enum.map(raw, &Sbim.Scheme.SurroundingBuilding.from_map!/1)
    assert Enum.map(buildings, &Sbim.Scheme.SurroundingBuilding.to_map/1) === raw
    assert Enum.all?(buildings, &(&1.extra == %{}))
  end

  test "scheme — 밑줄 키는 없음 ≠ null" do
    base = %{"data" => %{}, "floor_plans" => [], "unit_ids" => []}
    {:ok, s} = Sbim.Scheme.Scheme.from_map(base)
    refute Map.has_key?(Sbim.Scheme.Scheme.to_map(s), "_compile_errors")

    {:ok, s} = Sbim.Scheme.Scheme.from_map(Map.put(base, "_compile_errors", []))
    assert Sbim.Scheme.Scheme.to_map(s)["_compile_errors"] == []
  end

  # ── 4. 표 ──

  test "core_type_old_to_new/1 == fixtures/core_type_renumber.json" do
    %{"old_to_new" => table} = read!("fixtures/core_type_renumber.json")

    for {old, new} <- table do
      assert Sbim.Migrations.core_type_old_to_new(String.to_integer(old)) == new
    end

    assert map_size(Sbim.Migrations.core_type_old_to_new()) == map_size(table)
    assert Sbim.Migrations.core_type_old_to_new(nil) == nil
  end

  test "migrations·presets 표 == fixtures/migrations.json·presets.json" do
    mig = read!("fixtures/migrations.json")
    assert Sbim.Migrations.legacy_top_blocks() == mig["legacy_top_blocks"]
    assert Sbim.Migrations.ground_floor_to() == mig["ground_floor_to"]
    assert Sbim.Migrations.ground_floor_dropped() == mig["ground_floor_dropped"]
    assert Sbim.Migrations.parking_dims_dropped() == mig["parking_dims_dropped"]
    assert Sbim.Migrations.renamed() == mig["renamed"]
    assert Sbim.Migrations.regulations_renamed() == mig["regulations_renamed"]
    assert Sbim.Migrations.moved_to_regulations() == mig["moved_to_regulations"]
    assert Sbim.Migrations.dropped() == mig["dropped"]

    %{"structure_preset" => preset} = read!("fixtures/presets.json")
    assert Sbim.Presets.structure_preset() == preset
    assert Sbim.Presets.structure_preset("steel") == preset["steel"]
    assert Sbim.Presets.structure_preset("timber") == nil
  end
end
