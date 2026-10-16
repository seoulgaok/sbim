defmodule Sbim.Ifc.FormatTest do
  @moduledoc "STEP 표기 — fixtures/ifc/format.json(ifcopenshell 0.8.5 가 쓴 실수·문자열)과 같은가."
  use ExUnit.Case, async: true

  alias Sbim.Ifc.Step

  @fx Path.expand("../../../fixtures/ifc/format.json", __DIR__) |> File.read!() |> Jason.decode!()

  test "실수 — %.17G + 소수점" do
    bad =
      for [bits, want] <- @fx["reals"],
          <<v::float>> = <<bits::64>>,
          got = Step.real(v),
          got != want,
          do: {v, got, want}

    assert bad == [], "#{length(bad)}개 다름: #{inspect(Enum.take(bad, 5))}"
  end

  test "문자열 — '' · \\\\ · \\X2\\ · \\X4\\" do
    for [s, want] <- @fx["strings"], do: assert(IO.iodata_to_binary(Step.str(s)) == want, s)
  end

  test "GlobalId 압축 — 정수 UUID 1 은 0000…01" do
    g = Step.counter_gid()
    assert g.() == "0000000000000000000001"
    assert g.() == "0000000000000000000002"
    assert String.length(Step.random_gid()) == 22
  end
end
