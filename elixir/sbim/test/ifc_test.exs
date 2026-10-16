defmodule Sbim.IfcTest do
  @moduledoc """
  Elixir 판 IFC 가 파이썬 판(fixtures/ifc/<샘플>.ifc.gz — python/scripts/gen_ifc_fixtures.py)과 같은 파일인가.

  같은 GlobalId 수열(`Step.counter_gid/0`)·같은 시각으로 쓰고 FILE_NAME 줄(만든 프로그램 이름)만 빼고 줄 단위로 맞춘다.
  면적·둘레는 순수 Elixir(`Geom.Plain`)로도 GEOS 와 같은 식이라 같다. 승강기 카 오프셋만 마지막 자리가 갈릴 수 있어
  그 개체의 실수는 1e-9 m 안이면 같다고 본다(엔진은 GEOS 를 넘겨 그것까지 같다).
  """
  use ExUnit.Case, async: true

  alias Sbim.Ifc.Step

  @root Path.expand("../../..", __DIR__)
  @stamp "2026-01-01T00:00:00"

  for path <- Path.wildcard(Path.join(@root, "fixtures/ifc/sample-*.ifc.gz")) do
    @name Path.basename(path, ".ifc.gz")

    test "#{@name} — 파이썬 판과 같은 파일" do
      src = Path.join(@root, "examples/samples/#{@name}")
      scheme = src |> Path.join("scheme.json") |> File.read!() |> Jason.decode!()
      units = src |> Path.join("units.json") |> File.read!() |> Jason.decode!()
      got = Sbim.Ifc.generate_ifc(scheme, units, gid: Step.counter_gid(), time_stamp: @stamp)
      want = Path.join(@root, "fixtures/ifc/#{@name}.ifc.gz") |> File.read!() |> :zlib.gunzip()
      compare(got, want)
    end
  end

  defp compare(got, want) do
    g = got |> String.split("\n") |> Enum.reject(&String.starts_with?(&1, "FILE_NAME("))
    w = want |> String.split("\n") |> Enum.reject(&String.starts_with?(&1, "FILE_NAME("))

    diffs =
      Enum.zip(g, w)
      |> Enum.with_index(1)
      |> Enum.reject(fn {{a, b}, _} -> a == b or near?(a, b) end)

    first =
      Enum.take(diffs, 3)
      |> Enum.map_join("\n", fn {{a, b}, i} ->
        "  줄 #{i}\n    got:  #{String.slice(a, 0, 300)}\n    want: #{String.slice(b, 0, 300)}"
      end)

    assert diffs == [] and length(g) == length(w),
           "#{length(diffs)}줄 다름 (got #{length(g)}줄 · want #{length(w)}줄)\n#{first}\n#{counts(got, want)}"
  end

  # 실수만 다르고 차이가 1e-9 안이면 같다고 본다(승강기 카 오프셋 — 모듈 문서)
  @num ~r/-?\d+\.\d*(?:E[-+]\d+)?/
  defp near?(a, b) do
    String.replace(a, @num, "N") == String.replace(b, @num, "N") and
      Enum.zip(Regex.scan(@num, a), Regex.scan(@num, b))
      |> Enum.all?(fn {[x], [y]} -> abs(f(x) - f(y)) < 1.0e-9 end)
  end

  defp f(s),
    do: s |> String.replace(~r/\.(E|$)/, ".0\\1") |> String.replace("E", "e") |> String.to_float()

  defp counts(got, want) do
    c = fn s ->
      Regex.scan(~r/^#\d+=([A-Z0-9]+)\(/m, s) |> Enum.frequencies_by(&Enum.at(&1, 1))
    end

    {cg, cw} = {c.(got), c.(want)}

    (Map.keys(cg) ++ Map.keys(cw))
    |> Enum.uniq()
    |> Enum.filter(&(cg[&1] != cw[&1]))
    |> Enum.map_join(", ", &"#{&1} #{cg[&1] || 0}/#{cw[&1] || 0}")
    |> then(&"개수 다른 타입(got/want): #{&1}")
  end
end
