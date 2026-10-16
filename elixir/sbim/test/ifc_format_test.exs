defmodule Sbim.Ifc.FormatTest do
  @moduledoc "STEP 표기 — fixtures/ifc/format.json(ifcopenshell 0.9.0 이 쓴 실수·문자열)과 같은가."
  use ExUnit.Case, async: true

  alias Sbim.Ifc.Step

  @fx Path.expand("../../../fixtures/ifc/format.json", __DIR__) |> File.read!() |> Jason.decode!()

  test "실수 :shortest — ifcopenshell 0.9.0(format.json)" do
    bad =
      for [bits, want] <- @fx["reals"],
          <<v::float>> = <<bits::64>>,
          got = Step.real(v, :shortest),
          got != want,
          do: {v, got, want}

    assert bad == [], "#{length(bad)}개 다름: #{inspect(Enum.take(bad, 5))}"
  end

  test "실수 :g17 — ifcopenshell 0.8.5 (그 판이 쓴 줄에서 옮김)" do
    for {v, want} <- [
          {0.0, "0."},
          {-0.0, "-0."},
          {3.0, "3."},
          {0.1, "0.10000000000000001"},
          {1.0e-5, "1.0000000000000001E-05"},
          {1.5e-4, "0.00014999999999999999"},
          {1.0e17, "1.E+17"},
          {1.0e-300, "1.E-300"},
          {4.9406564584124654e-324, "4.9406564584124654E-324"}
        ],
        do: assert(Step.real(v, :g17) == want, inspect(v))
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
