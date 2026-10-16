defmodule Sbim.BundleTest do
  @moduledoc "설계안 묶음(.sbim) — 파이썬이 묶은 정답(fixtures/bundle/)을 풀고, 여기서 묶은 것을 다시 푼다."
  use ExUnit.Case, async: true

  @root Path.expand("../../..", __DIR__)
  @src Path.join(@root, "examples/samples/sample-small")

  defp files, do: Map.new(~w(scheme.json units.json), &{&1, File.read!(Path.join(@src, &1))})

  test "파이썬 정답을 푼다 — manifest·sha·site" do
    {:ok, %{manifest: m, files: f}} =
      @root
      |> Path.join("fixtures/bundle/sample-small.sbim")
      |> File.read!()
      |> Sbim.Bundle.unpack()

    assert m["format"] == "sbim-bundle" and m["created_at"] == "2026-01-01T00:00:00Z"
    assert Map.keys(f) |> Enum.sort() == ~w(scheme.json site.json units.json)
    assert f["scheme.json"] == File.read!(Path.join(@src, "scheme.json"))
  end

  test "묶고 풀면 바이트 그대로 · engine_stamp 옮김" do
    bin =
      Sbim.Bundle.pack(files(),
        land_ids: ["1"],
        design_id: "d",
        created_at: "2026-01-01T00:00:00Z"
      )

    {:ok, %{manifest: m, files: f}} = Sbim.Bundle.unpack(bin)
    assert f == files()

    assert m["land_ids"] == ["1"] and m["design_id"] == "d" and
             m["sbim_version"] == to_string(Application.spec(:sbim, :vsn))

    assert m["engine_stamp"] ==
             files()["scheme.json"] |> JSON.decode!() |> Map.get("_engine_stamp")
  end

  test "빠짐·모르는 항목·손상은 거부" do
    assert_raise ArgumentError, fn ->
      Sbim.Bundle.pack(Map.delete(files(), "units.json"), land_ids: [])
    end

    assert_raise ArgumentError, fn ->
      Sbim.Bundle.pack(Map.put(files(), "surroundings.json", "[]"), land_ids: [])
    end

    {:ok, list} = :zip.unzip(Sbim.Bundle.pack(files(), land_ids: []), [:memory])
    bad = Enum.map(list, fn {n, b} -> if n == ~c"units.json", do: {n, "[]"}, else: {n, b} end)
    {:ok, {_, bin}} = :zip.create(~c"x", bad, [:memory])
    assert {:error, "sha256 어긋남: units.json"} = Sbim.Bundle.unpack(bin)
    assert {:error, "zip 이 아니다" <> _} = Sbim.Bundle.unpack("nope")
  end
end
