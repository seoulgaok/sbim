defmodule Sbim.Ifc.GeometryCheck do
  @moduledoc """
  형상 온전성 검사 — python/seoulgaok_bim_core/geometry_check.py 의 Elixir 판.

  2026-10-08 현장: 받은 IFC 를 아키캐드에서 열었더니 기둥 하나가 위아래로 끝없이 뻗어 있었다(부재 하나의
  높이가 터진 것). 그런 값을 **조용히 IFC 로 써 보내지 않게** 층 표고에서 봉투를 세우고 크게 벗어난 것만 잡는다.
  """

  alias Sbim.Ifc.Py

  # 봉투 여유 — 옥탑·파라펫·지하 여유를 넉넉히 덮는다
  @z_margin 30.0
  # 한 필지 모델의 평면 반경 한계 (메시는 상대좌표라 원점 근처에 있어야 한다)
  @xy_limit 300.0
  # userData 가 높이로 쓰는 키
  @z_keys ~w(base_z top_z z0 z1 sill)

  defmodule Error do
    defexception [:message, :bad]
  end

  @doc "층 표고에서 세운 z 봉투 {아래, 위}. 층 정보가 없으면 넉넉한 기본값."
  def storey_envelope(scheme) do
    zs =
      for fp <- scheme["floor_plans"] || [],
          d = fp["data"] || %{},
          z0 = d["floor_bottom_height"],
          not is_nil(z0),
          do: {z0 * 1.0, z0 * 1.0 + Py.py_or(d["floor_height"], 0) * 1.0}

    case zs do
      [] -> {-20.0, 100.0}
      _ -> {(zs |> Enum.map(&elem(&1, 0)) |> Enum.min()) - @z_margin, (zs |> Enum.map(&elem(&1, 1)) |> Enum.max()) + @z_margin}
    end
  end

  @doc "터진 형상을 사람이 읽을 줄로. 정상이면 []."
  def check(scheme) do
    {zlo, zhi} = storey_envelope(scheme)
    rng = "허용 #{Py.fmt_f(zlo, 1)}~#{Py.fmt_f(zhi, 1)}m"

    for fp <- scheme["floor_plans"] || [],
        fid = (fp["data"] || %{})["floor_id"],
        {bucket, groups} <- fp["geom"] || %{},
        g <- groups || [],
        bg <- if(is_list(g), do: g, else: [g]),
        is_map(bg),
        line <- check_one(bg, fid, bucket, zlo, zhi, rng),
        do: line
  end

  defp check_one(bg, fid, bucket, zlo, zhi, rng) do
    ud = bg["userData"] || %{}

    zbad =
      for k <- @z_keys, v = ud[k], is_number(v), not (zlo <= v and v <= zhi),
        do: "#{Py.str(fid)}층 #{bucket}: #{k}=#{Py.fmt_f(v, 1)}m — #{rng}"

    arr = get_in(bg, ["data", "attributes", "position", "array"]) || []

    mesh =
      if arr == [] do
        []
      else
        zs = arr |> Enum.drop(2) |> Enum.take_every(3)
        xs = Enum.take_every(arr, 3)
        ys = arr |> Enum.drop(1) |> Enum.take_every(3)

        zl =
          if zs != [] and (Enum.min(zs) < zlo or Enum.max(zs) > zhi),
            do: ["#{Py.str(fid)}층 #{bucket}: 메시 z #{Py.fmt_f(Enum.min(zs), 1)}~#{Py.fmt_f(Enum.max(zs), 1)}m — #{rng}"],
            else: []

        mx = fn l -> l |> Enum.map(&abs/1) |> Enum.max() end

        xy =
          if xs != [] and (mx.(xs) > @xy_limit or mx.(ys) > @xy_limit),
            do: ["#{Py.str(fid)}층 #{bucket}: 메시가 원점에서 #{Py.fmt_f(max(mx.(xs), mx.(ys)), 0)}m 떨어짐 — 한계 300m"],
            else: []

        zl ++ xy
      end

    zbad ++ mesh
  end

  @doc "터진 형상이 있으면 `Error` 를 던진다. 조용히 내보내지 않는다."
  def raise_if_insane!(scheme, limit \\ 6) do
    case check(scheme) do
      [] ->
        :ok

      bad ->
        more = if length(bad) > limit, do: "\n  … 외 #{length(bad) - limit}건", else: ""

        raise Error,
          bad: bad,
          message:
            "형상이 층 표고 봉투를 벗어났습니다 (#{length(bad)}건) — IFC로 내보내지 않습니다.\n  " <>
              Enum.join(Enum.take(bad, limit), "\n  ") <>
              more <>
              "\n엔진 출력(scheme.json)을 먼저 확인하세요. 이대로 내보내면 받는 쪽에서 모델 전체를 의심하게 됩니다."
    end
  end
end
