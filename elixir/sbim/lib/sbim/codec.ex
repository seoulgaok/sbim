defmodule Sbim.Codec do
  @moduledoc """
  생성 모듈(lib/sbim/generated/)의 `from_map`·`to_map` 본체. 모듈은 `__shape__/0` 로 필드 모양만
  주고, 여기서 문자열 키 map ↔ struct 를 재귀로 오간다.

  값은 Jason 이 준 그대로다 — 숫자·문자열을 강제하거나 Literal 을 검증하지 않는다(검증은 정본
  pydantic 의 몫, 여기는 모양 계약). `__shape__` 의 필드 타입은 `:value`(그대로) ·
  `{:model, 모듈}` · `{:list, 타입}` · `{:map, 타입}` 넷뿐이다.
  """

  @type path :: [String.t() | non_neg_integer()]

  @doc """
  문자열 키 map → struct. 없는 키는 struct 기본값, `null` 은 nil. 스키마에 없는 키는 모듈이
  `extra?: true` 면 `extra` 에, 아니면 `{:error, {:unknown_keys, 경로, 키들}}`.
  """
  @spec decode(module(), term(), path()) :: {:ok, struct()} | {:error, term()}
  def decode(mod, map, path \\ [])

  def decode(mod, map, path) when is_map(map) and not is_struct(map) do
    shape = mod.__shape__()

    with {:ok, fields, rest} <- fields(shape.fields, map, path, []),
         {:ok, fields} <- extra(shape, rest, fields, path) do
      {:ok, struct!(mod, fields)}
    end
  end

  def decode(_mod, v, path), do: {:error, {:not_a_map, Enum.reverse(path), v}}

  @spec decode!(module(), term()) :: struct()
  def decode!(mod, map) do
    case decode(mod, map) do
      {:ok, s} -> s
      {:error, reason} -> raise ArgumentError, "#{inspect(mod)}.from_map: #{inspect(reason)}"
    end
  end

  defp fields([], map, _path, acc), do: {:ok, acc, map}

  defp fields([{key, atom, type} | more], map, path, acc) do
    case Map.fetch(map, key) do
      :error ->
        fields(more, map, path, acc)

      {:ok, v} ->
        with {:ok, dv} <- value(type, v, [key | path]) do
          fields(more, Map.delete(map, key), path, [{atom, dv} | acc])
        end
    end
  end

  defp extra(%{extra?: true}, rest, fields, _path), do: {:ok, [{:extra, rest} | fields]}
  defp extra(_shape, rest, fields, _path) when map_size(rest) == 0, do: {:ok, fields}

  defp extra(_shape, rest, _fields, path),
    do: {:error, {:unknown_keys, Enum.reverse(path), Enum.sort(Map.keys(rest))}}

  defp value(_type, nil, _path), do: {:ok, nil}
  defp value(:value, v, _path), do: {:ok, v}
  defp value({:model, mod}, v, path), do: decode(mod, v, path)

  defp value({:list, t}, v, path) when is_list(v) do
    v |> Enum.with_index() |> map_ok(fn {x, i} -> value(t, x, [i | path]) end)
  end

  defp value({:list, _t}, v, path), do: {:error, {:not_a_list, Enum.reverse(path), v}}

  defp value({:map, t}, v, path) when is_map(v) do
    with {:ok, pairs} <-
           map_ok(v, fn {k, x} ->
             with {:ok, dx} <- value(t, x, [k | path]), do: {:ok, {k, dx}}
           end) do
      {:ok, Map.new(pairs)}
    end
  end

  defp value({:map, _t}, v, path), do: {:error, {:not_a_map, Enum.reverse(path), v}}

  defp map_ok(enum, fun) do
    Enum.reduce_while(enum, {:ok, []}, fn x, {:ok, acc} ->
      case fun.(x) do
        {:ok, y} -> {:cont, {:ok, [y | acc]}}
        err -> {:halt, err}
      end
    end)
    |> case do
      {:ok, acc} -> {:ok, Enum.reverse(acc)}
      err -> err
    end
  end

  @doc """
  struct → 문자열 키 map. `omit_nil?: true` 모듈은 nil 인 선택 필드를 뺀다(없음 ≠ null) —
  required 는 늘 낸다. `extra` 는 펼친다(스키마 필드가 이긴다).
  """
  @spec encode(struct()) :: map()
  def encode(%mod{} = s) do
    shape = mod.__shape__()

    base =
      Enum.reduce(shape.fields, %{}, fn {key, atom, type}, acc ->
        v = Map.fetch!(s, atom)

        if is_nil(v) and shape.omit_nil? and key not in shape.required,
          do: acc,
          else: Map.put(acc, key, encode_value(type, v))
      end)

    if shape.extra?, do: Map.merge(s.extra, base), else: base
  end

  defp encode_value(_t, nil), do: nil
  defp encode_value(:value, v), do: v
  defp encode_value({:model, _mod}, %_{} = s), do: encode(s)
  defp encode_value({:list, t}, l) when is_list(l), do: Enum.map(l, &encode_value(t, &1))

  defp encode_value({:map, t}, m) when is_map(m),
    do: Map.new(m, fn {k, v} -> {k, encode_value(t, v)} end)

  defp encode_value(_t, v), do: v
end
