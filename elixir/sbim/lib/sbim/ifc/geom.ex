defmodule Sbim.Ifc.Geom do
  @moduledoc """
  ifc.py 가 shapely 로 재는 셋 — 다각형 면적·둘레, 승강기 카의 안쪽 오프셋(`buffer(-0.2)`).

  `Sbim.Ifc.generate_ifc/3` 의 `geom:` 으로 갈아 끼운다. 파이썬과 **비트까지** 같게 하려면 같은 GEOS 를
  쓰는 구현을 넘긴다(엔진은 GEOS NIF 가 있다). 기본값 `Sbim.Ifc.Geom.Plain` 은 순수 Elixir 다 —
  면적·둘레는 GEOS 와 같은 식이라 같고, 오프셋만 GEOS 와 마지막 자리가 갈릴 수 있다.

  점은 `{x, y}` 실수 튜플, 링은 닫지 않은 목록(ifc.py `_ring_xy` 가 주는 꼴)이다.
  """

  @doc "`Polygon(pts).area` — 점이 셋 미만이면 :error(shapely 가 예외를 던지는 자리)."
  @callback area([{float, float}]) :: {:ok, float} | :error
  @doc "`Polygon(pts).exterior.length`"
  @callback perimeter([{float, float}]) :: {:ok, float} | :error
  @doc "`Polygon(pts).buffer(-d)` 의 바깥 링(닫지 않음). 비면 :empty, 여러 조각이면 가장 큰 것."
  @callback inset([{float, float}], float) :: {:ok, [{float, float}]} | :empty | :error

  defmodule Plain do
    @moduledoc """
    순수 Elixir 판 — GEOS 3.13 `Area::ofRingSigned`·`Length::ofLine` 과 같은 식·같은 순서.
    `inset/2` 는 볼록 다각형만(승강로 사각형): 변을 안으로 민 직선끼리의 교점, 시계 방향, 원래 0번 꼭짓점부터 —
    shapely 2.1.2 / GEOS 3.13.1 실측과 같은 꼴(값은 마지막 자리가 갈릴 수 있다).
    """
    @behaviour Sbim.Ifc.Geom

    @impl true
    def area(pts) when length(pts) < 3, do: :error

    def area([{x0, _} | _] = pts) do
      ring = List.to_tuple(pts ++ [hd(pts)])
      n = tuple_size(ring)

      sum =
        Enum.reduce(1..(n - 2)//1, 0.0, fn i, s ->
          {xi, _} = elem(ring, i)
          {_, y1} = elem(ring, i + 1)
          {_, y2} = elem(ring, i - 1)
          s + (xi - x0) * (y2 - y1)
        end)

      {:ok, abs(sum / 2.0)}
    end

    @impl true
    def perimeter(pts) when length(pts) < 3, do: :error

    def perimeter(pts) do
      {len, _} =
        Enum.reduce(tl(pts) ++ [hd(pts)], {0.0, hd(pts)}, fn {x1, y1} = p, {l, {x0, y0}} ->
          dx = x1 - x0
          dy = y1 - y0
          {l + :math.sqrt(dx * dx + dy * dy), p}
        end)

      {:ok, len}
    end

    @impl true
    def inset(pts, _d) when length(pts) < 3, do: :error

    def inset(pts, d) do
      {:ok, a} = signed(pts)
      n = length(pts)
      v = List.to_tuple(pts)
      # 안쪽 = 반시계 링의 왼쪽
      s = if a > 0, do: 1.0, else: -1.0

      offset = fn i ->
        {x0, y0} = elem(v, rem(i, n))
        {x1, y1} = elem(v, rem(i + 1, n))
        dx = x1 - x0
        dy = y1 - y0
        l = :math.sqrt(dx * dx + dy * dy)
        nx = -dy / l * s * d
        ny = dx / l * s * d
        {{x0 + nx, y0 + ny}, {dx, dy}}
      end

      corners =
        for i <- 0..(n - 1) do
          {p, r} = offset.(i + n - 1)
          {q, s2} = offset.(i)
          cross(p, r, q, s2)
        end

      # 너무 밀어 뒤집혔으면(방향이 바뀌었으면) 빈 것
      case signed(corners) do
        {:ok, b} when b * a > 0 ->
          {:ok, if(a > 0, do: [hd(corners) | Enum.reverse(tl(corners))], else: corners)}

        _ ->
          :empty
      end
    end

    defp signed(pts) do
      ring = pts ++ [hd(pts)]

      s =
        ring
        |> Enum.chunk_every(2, 1, :discard)
        |> Enum.reduce(0.0, fn [{x0, y0}, {x1, y1}], acc -> acc + (x0 * y1 - x1 * y0) end)

      {:ok, s / 2.0}
    end

    # 직선 p + t r 과 q + u s 의 교점
    defp cross({px, py}, {rx, ry}, {qx, qy}, {sx, sy}) do
      den = rx * sy - ry * sx
      t = ((qx - px) * sy - (qy - py) * sx) / den
      {px + t * rx, py + t * ry}
    end
  end
end
