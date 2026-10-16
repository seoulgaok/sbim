defmodule Sbim.Ifc.Py do
  @moduledoc """
  ifc.py 가 기대는 파이썬 수 규칙 — 이름·키·수량이 파이썬 판과 글자 하나까지 같아야 해서 따로 둔다.

  - `round0/1` = `round(x)`: 정수로, 정확히 반인 값은 짝수 쪽(은행가 반올림). Elixir `round/1` 은 0에서 먼 쪽이다.
  - `round_n/2` = `round(x, n)`: 이진 실수의 **정확한 값**을 십진 n자리로 반올림(반은 짝수)한 뒤 가장 가까운 실수.
  - `fmt_f/2` = `f"{x:.nf}"`: 같은 반올림으로 n자리 문자열.
  셋 다 실수를 분수로 풀어 정수 산술로 한다 — 부동소수 곱셈으로 하면 경계에서 한 자리씩 어긋난다.
  """

  import Bitwise

  @doc "`float(val) if val is not None else float(default)` — 못 바꾸면 default."
  def num(nil, default), do: default * 1.0
  def num(v, _default) when is_number(v), do: v * 1.0

  def num(v, default) when is_binary(v) do
    case Float.parse(String.trim(v)) do
      {f, ""} -> f
      _ -> default * 1.0
    end
  end

  def num(_v, default), do: default * 1.0

  @doc "`round(x)` — 정수, 반은 짝수 쪽."
  def round0(x) when is_integer(x), do: x
  def round0(x) when is_float(x), do: x |> exact() |> half_even(1)

  @doc "`round(x, n)` — 실수. 0 은 +0.0 으로(키로 쓸 때 -0.0 과 갈리지 않게 — 파이썬 dict 는 둘을 같은 키로 본다)."
  def round_n(x, n) when is_integer(x), do: x * 1.0 |> round_n(n)

  def round_n(x, n) when is_float(x) do
    p = Integer.pow(10, n)

    case x |> exact() |> half_even(p) do
      0 -> 0.0
      k -> k / p
    end
  end

  @doc "`f\"{x:.nf}\"`"
  def fmt_f(x, n) when is_integer(x), do: fmt_f(x * 1.0, n)

  def fmt_f(x, n) when is_float(x) do
    <<s::1, _::63>> = <<x::float>>
    k = x |> exact() |> half_even(Integer.pow(10, n)) |> abs()
    digits = k |> Integer.to_string() |> String.pad_leading(n + 1, "0")
    {ip, fp} = String.split_at(digits, String.length(digits) - n)
    if(s == 1, do: "-", else: "") <> ip <> if(n > 0, do: "." <> fp, else: "")
  end

  @doc "`f\"{i:0nd}\"`"
  def pad(i, n) when is_integer(i), do: i |> Integer.to_string() |> String.pad_leading(n, "0")

  @doc "f-string 안의 `{v}` — None·정수·문자열(ifc.py 이름에 들어가는 값들)."
  def str(nil), do: "None"
  def str(true), do: "True"
  def str(false), do: "False"
  def str(v) when is_binary(v), do: v
  def str(v) when is_integer(v), do: Integer.to_string(v)
  def str(v) when is_float(v), do: :erlang.float_to_binary(v, [:short])

  @doc "파이썬 진릿값 — None·False·0·0.0·\"\"·[]·{} 은 거짓."
  def truthy?(v) when v in [nil, false, 0, "", [], %{}], do: false
  def truthy?(v) when is_float(v), do: v != 0.0
  def truthy?(_), do: true

  @doc "`a or b`"
  def py_or(a, b), do: if(truthy?(a), do: a, else: b)

  # x = 부호 × 분자 / 분모 (분모는 2의 거듭제곱)
  defp exact(x) do
    <<s::1, e::11, m::52>> = <<x::float>>
    {mant, ex} = if e == 0, do: {m, -1074}, else: {m + (1 <<< 52), e - 1075}
    sign = if s == 1, do: -1, else: 1
    if ex >= 0, do: {sign, mant <<< ex, 1}, else: {sign, mant, 1 <<< -ex}
  end

  # (부호 × num/den) × scale 을 정수로 — 정확히 반이면 짝수 쪽
  defp half_even({sign, num, den}, scale) do
    n = num * scale
    q = div(n, den)
    r = rem(n, den)

    q =
      cond do
        2 * r > den -> q + 1
        2 * r < den -> q
        rem(q, 2) == 1 -> q + 1
        true -> q
      end

    sign * q
  end
end
