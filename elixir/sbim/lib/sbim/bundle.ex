defmodule Sbim.Bundle do
  @moduledoc """
  설계안 묶음(.sbim) — python/seoulgaok_bim_core/bundle.py 의 Elixir 판. 꼴·항목 규칙은 그 머리말이 정본이다.

  `.sbim` = zip. 루트에 `manifest.json`(첫 항목) · `scheme.json`·`units.json`(필수) · `site.json`(선택).
  manifest.files = {항목 이름: sha256 hex}. JSON 은 받은 바이트 그대로 담는다(엔진이 storage 에 올린 파일과 같은 sha).
  시험은 파이썬이 묶은 정답(fixtures/bundle/)을 여기서 풀어 본다.
  """

  @version 1
  @manifest "manifest.json"
  @required ["scheme.json", "units.json"]
  @entries @required ++ ["site.json"]

  @doc """
  `%{"scheme.json" => 바이트, "units.json" => 바이트, "site.json" => 바이트?}` → .sbim 바이트.
  옵션: `land_ids:`(필수) · `design_id:` · `created_at:`(ISO 8601 UTC, 기본 지금).
  """
  def pack(files, opts) do
    case Map.keys(files) -- @entries do
      [] ->
        :ok

      bad ->
        raise ArgumentError, "묶을 수 없는 항목: #{inspect(Enum.sort(bad))} — #{inspect(@entries)} 만"
    end

    case Enum.reject(@required, &Map.has_key?(files, &1)) do
      [] -> :ok
      miss -> raise ArgumentError, "필수 항목 없음: #{inspect(miss)}"
    end

    names = Enum.filter(@entries, &Map.has_key?(files, &1))
    stamp = files |> Map.fetch!("scheme.json") |> JSON.decode!() |> Map.get("_engine_stamp")

    manifest =
      ordered([
        {"format", "sbim-bundle"},
        {"bundle_version", @version},
        {"sbim_version", to_string(Application.spec(:sbim, :vsn))},
        {"created_at", Keyword.get_lazy(opts, :created_at, &now/0)},
        {"land_ids", Keyword.fetch!(opts, :land_ids)},
        {"design_id", Keyword.get(opts, :design_id)},
        {"engine_stamp", stamp},
        {"files", ordered(for n <- names, do: {n, sha(files[n])})}
      ])

    {:raw, mio} = manifest

    entries = [
      {~c"manifest.json", IO.iodata_to_binary(mio)}
      | for(n <- names, do: {String.to_charlist(n), files[n]})
    ]

    {:ok, {_, bin}} = :zip.create(~c"bundle.sbim", entries, [:memory])
    bin
  end

  @doc "`.sbim` 바이트 → `{:ok, %{manifest: 맵, files: %{이름 => 바이트}}}` · 빠짐·sha 어긋남·모르는 판은 `{:error, 이유}`."
  def unpack(bin) do
    with {:ok, list} <- unzip(bin),
         files = Map.new(list, fn {n, b} -> {to_string(n), b} end),
         {:ok, mb} <- fetch(files, @manifest, "manifest.json 없음"),
         {:ok, m} <- decode(mb),
         :ok <- known(m),
         {:ok, out} <- verified(files, m["files"] || %{}),
         :ok <- has_required(out) do
      {:ok, %{manifest: m, files: out}}
    end
  end

  defp unzip(bin) do
    case :zip.unzip(bin, [:memory]) do
      {:ok, l} -> {:ok, l}
      {:error, e} -> {:error, "zip 이 아니다: #{inspect(e)}"}
    end
  end

  defp fetch(files, n, why),
    do: if(Map.has_key?(files, n), do: {:ok, files[n]}, else: {:error, why})

  defp decode(b) do
    {:ok, JSON.decode!(b)}
  rescue
    _ -> {:error, "manifest.json 이 JSON 이 아니다"}
  end

  defp known(%{"format" => "sbim-bundle", "bundle_version" => v})
       when is_integer(v) and v <= @version, do: :ok

  defp known(m), do: {:error, "모르는 묶음: #{m["format"]} v#{m["bundle_version"]}"}

  defp verified(files, shas) do
    Enum.reduce_while(shas, {:ok, %{}}, fn {n, s}, {:ok, acc} ->
      cond do
        not Map.has_key?(files, n) -> {:halt, {:error, "manifest 에 있는데 묶음에 없음: #{n}"}}
        sha(files[n]) != s -> {:halt, {:error, "sha256 어긋남: #{n}"}}
        true -> {:cont, {:ok, Map.put(acc, n, files[n])}}
      end
    end)
  end

  defp has_required(out) do
    case Enum.reject(@required, &Map.has_key?(out, &1)) do
      [] -> :ok
      [n | _] -> {:error, "필수 항목 없음: #{n}"}
    end
  end

  defp sha(b), do: :crypto.hash(:sha256, b) |> Base.encode16(case: :lower)

  # 키 순서를 지키는 JSON 객체(파이썬 model_dump_json 과 같은 순서 — 사람이 읽기 좋게)
  defp ordered(kvs),
    do:
      {:raw,
       [
         "{",
         kvs
         |> Enum.map(fn {k, v} -> [JSON.encode!(k), ":", enc(v)] end)
         |> Enum.intersperse(","),
         "}"
       ]}

  defp enc({:raw, io}), do: io
  defp enc(v), do: JSON.encode!(v)

  defp now do
    {{y, mo, d}, {h, mi, s}} = :calendar.universal_time()

    :io_lib.format("~4..0B-~2..0B-~2..0BT~2..0B:~2..0B:~2..0BZ", [y, mo, d, h, mi, s])
    |> IO.iodata_to_binary()
  end
end
