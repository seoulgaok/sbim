defmodule Sbim.Ifc.Step do
  @moduledoc """
  IFC4 STEP(ISO-10303-21) 쓰기 — ifcopenshell `file.create_entity`·`file.write` 의 Elixir 판.

  - `create(f, "IfcWall", GlobalId: g, Name: "…")` 는 개체 번호를 하나 매기고 그 줄을 바로 쓴다.
    속성은 이름으로 받아 `Sbim.Ifc.Schema` 의 자리 순서로 늘어놓는다(STEP 은 자리로 쓴다). 빠진 속성은
    `$`, 유도 속성은 `*`. 반환값 `%Ref{}` 는 다른 개체의 속성 값으로 넣으면 `#번호` 가 된다.
  - 값 타입(IfcLabel·IfcReal …)은 `typed/2` — 번호를 안 먹고 줄 안에 `IFCREAL(…)` 로 들어간다
    (ifcopenshell 도 같다: 정답 파일에서 IfcPropertySingleValue 번호가 연달아 붙는다).
  - 개체는 만든 순서대로 번호가 붙고 그 순서로 쓴다 — 파이썬과 같은 순서로 만들면 같은 파일이 된다.

  표기는 ifcopenshell 0.8.5 가 쓴 그대로를 정답 파일(fixtures/ifc/format.ifc)에서 맞췄다.
  - 실수: printf `%.17G` 에 소수점이 없으면 `.` 를 넣는다 — `0.`·`3.`·`0.20000000000000001`·`1.E-300`·`1.E+17`.
  - 문자열: `'` → `''`, `\\` → `\\\\`, 0x20~0x7E 밖 글자는 이어진 덩어리마다 `\\X2\\…\\X0\\`(UTF-16 4자리).
    문자열에 BMP 밖 글자가 하나라도 있으면 그 문자열의 덩어리는 전부 `\\X4\\`(8자리)다.

  상태(번호·줄)는 ETS 에 둔다 — 파이썬 판이 클로저로 한 파일 핸들을 공유하는 꼴을 그대로 옮기기 위해서다.
  `new/1` 을 부른 프로세스가 표를 갖는다(private). 다 쓰면 `to_iodata/2` 뒤 `close/1`.
  """

  alias Sbim.Ifc.Schema

  defmodule Ref do
    @moduledoc "만든 개체 — `id` 는 STEP 번호, `attrs` 는 넣은 속성(읽기용: 층 placement·표고 등)."
    defstruct [:id, :type, attrs: %{}]
  end

  defstruct [:tab, :seq, :gid]

  @type t :: %__MODULE__{}

  @doc """
  새 파일. `gid:` 는 GlobalId 를 내는 0인자 함수(기본: ifcopenshell.guid.new 와 같은 무작위 22자).
  정답과 맞출 때는 `counter_gid/0` 처럼 결정적인 것을 넘긴다.
  """
  def new(opts \\ []) do
    %__MODULE__{
      tab: :ets.new(:sbim_ifc, [:ordered_set, :private]),
      seq: :counters.new(1, []),
      gid: Keyword.get(opts, :gid, &random_gid/0)
    }
  end

  def close(%__MODULE__{tab: tab}), do: :ets.delete(tab)

  @doc "GlobalId 하나."
  def gid(%__MODULE__{gid: g}), do: g.()

  @doc "개체 하나를 만든다. `attrs` 는 키워드(속성 이름 원자 → 값)."
  def create(%__MODULE__{tab: tab, seq: seq}, type, attrs \\ []) do
    {step, spec} = Schema.entity!(type)
    attrs = Map.new(attrs)
    known = MapSet.new(spec, &elem(&1, 0))

    for {k, _} <- attrs, not MapSet.member?(known, k),
        do: raise(ArgumentError, "#{type} 에 #{k} 속성이 없다")

    :counters.add(seq, 1, 1)
    id = :counters.get(seq, 1)

    body =
      spec
      |> Enum.map(fn
        {_k, :derived} -> "*"
        {k, kind} -> value(Map.get(attrs, k), kind)
      end)
      |> Enum.intersperse(",")

    :ets.insert(tab, {id, ["#", Integer.to_string(id), "=", step, "(", body, ");\n"]})
    %Ref{id: id, type: type, attrs: attrs}
  end

  @doc "값 타입 인스턴스 — `typed(\"IfcReal\", 0.17)` → `IFCREAL(0.17)`. 번호를 안 먹는다."
  def typed(type, v) do
    {step, kind} = Schema.type!(type)
    {:typed, [step, "(", value(v, kind), ")"]}
  end

  @doc "열거값 — `enum(\"ELEMENT\")` 처럼 쓸 수도 있지만, 스키마가 :enum 인 속성엔 문자열을 그대로 넣어도 된다."
  def enum(name), do: {:enum, name}

  @doc """
  STEP 파일 전체(iodata). `time_stamp` 는 FILE_NAME 의 시각(ISO 8601 초 단위 — 기본 지금 로컬 시각).
  `description` 은 FILE_DESCRIPTION 의 ViewDefinition 목록.
  """
  def to_iodata(%__MODULE__{tab: tab}, opts \\ []) do
    stamp = Keyword.get_lazy(opts, :time_stamp, &local_stamp/0)
    desc = Keyword.get(opts, :description, [])
    sys = Keyword.get(opts, :originating_system, "sbim #{Application.spec(:sbim, :vsn)} (Elixir)")

    [
      "ISO-10303-21;\nHEADER;\n",
      "FILE_DESCRIPTION((",
      desc |> Enum.map(&str/1) |> Enum.intersperse(","),
      "),'2;1');\n",
      "FILE_NAME('',",
      str(stamp),
      ",(''),(''),",
      str(sys),
      ",",
      str(sys),
      ",'');\n",
      "FILE_SCHEMA(('IFC4'));\nENDSEC;\nDATA;\n",
      :ets.foldr(fn {_id, line}, acc -> [line | acc] end, [], tab),
      "ENDSEC;\nEND-ISO-10303-21;\n"
    ]
  end

  # ── 값 → STEP 표기 ─────────────────────────────────────────────────────────

  defp value(nil, _kind), do: "$"
  defp value(%Ref{id: id}, _kind), do: ["#", Integer.to_string(id)]
  defp value({:typed, io}, _kind), do: io
  defp value({:enum, name}, _kind), do: [".", name, "."]
  defp value(v, :enum) when is_binary(v), do: [".", v, "."]
  defp value(v, :real) when is_number(v), do: real(v)
  defp value(v, :integer) when is_integer(v), do: Integer.to_string(v)
  defp value(true, k) when k in [:bool, :logical], do: ".T."
  defp value(false, k) when k in [:bool, :logical], do: ".F."
  defp value(:unknown, :logical), do: ".U."
  defp value(v, :string) when is_binary(v), do: str(v)

  defp value(v, {:list, k}) when is_list(v) or is_tuple(v) do
    items = if is_tuple(v), do: Tuple.to_list(v), else: v
    ["(", items |> Enum.map(&value(&1, k)) |> Enum.intersperse(","), ")"]
  end

  defp value(v, kind), do: raise(ArgumentError, "STEP 값으로 못 쓴다: #{inspect(v)} (#{inspect(kind)})")

  @doc """
  실수 — printf `%.17G` + 소수점 보장(ifcopenshell 0.8.5). 정수가 오면 실수로 쓴다(ifcopenshell 도
  REAL 속성의 int 를 `3.` 로 쓴다).
  """
  def real(v) when is_integer(v), do: real(v * 1.0)

  def real(v) when is_float(v) do
    # %.16e 는 C printf 라 정확히 반올림된 17자리다(io_lib ~e 는 20자리 문자열을 다시 반올림해 어긋날 수 있다)
    [mant, exp] = v |> :erlang.float_to_binary(scientific: 16) |> String.split("e")
    {sign, mant} = if String.starts_with?(mant, "-"), do: {"-", String.slice(mant, 1..-1//1)}, else: {"", mant}
    digits = String.replace(mant, ".", "")
    e = String.to_integer(exp)

    body =
      if e >= -4 and e < 17 do
        {ip, fp} =
          if e >= 0,
            do: String.split_at(digits, e + 1),
            else: {"0", String.duplicate("0", -e - 1) <> digits}

        ip <> "." <> String.trim_trailing(fp, "0")
      else
        {d0, rest} = String.split_at(digits, 1)
        es = e |> abs() |> Integer.to_string() |> String.pad_leading(2, "0")
        d0 <> "." <> String.trim_trailing(rest, "0") <> "E" <> if(e < 0, do: "-", else: "+") <> es
      end

    sign <> body
  end

  @doc "문자열 — STEP 따옴표 안 표기(ifcopenshell 0.8.5 규칙, 모듈 문서)."
  def str(s) when is_binary(s) do
    cps = String.to_charlist(s)
    wide? = Enum.any?(cps, &(&1 > 0xFFFF))
    ["'", encode(cps, wide?, []), "'"]
  end

  defp encode([], _w, acc), do: Enum.reverse(acc)
  defp encode([?' | t], w, acc), do: encode(t, w, ["''" | acc])
  defp encode([?\\ | t], w, acc), do: encode(t, w, ["\\\\" | acc])
  defp encode([c | t], w, acc) when c >= 0x20 and c <= 0x7E, do: encode(t, w, [<<c>> | acc])

  defp encode(cps, w, acc) do
    {run, rest} = Enum.split_while(cps, &(&1 < 0x20 or &1 > 0x7E))
    hex = if w, do: Enum.map(run, &hex(&1, 8)), else: Enum.flat_map(run, &utf16/1) |> Enum.map(&hex(&1, 4))
    encode(rest, w, [[if(w, do: "\\X4\\", else: "\\X2\\"), hex, "\\X0\\"] | acc])
  end

  defp utf16(c) when c > 0xFFFF do
    c = c - 0x10000
    [0xD800 + Bitwise.bsr(c, 10), 0xDC00 + Bitwise.band(c, 0x3FF)]
  end

  defp utf16(c), do: [c]

  defp hex(n, w), do: n |> Integer.to_string(16) |> String.pad_leading(w, "0")

  # ── GlobalId ───────────────────────────────────────────────────────────────

  @chars ~c"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$" |> List.to_tuple()

  @doc "UUID 16바이트 → IFC GlobalId 22자 (ifcopenshell.guid.compress)."
  def compress(<<b0, rest::binary-15>>) do
    tail = for <<v::24 <- rest>>, into: "", do: b64(v, 4)
    b64(b0, 2) <> tail
  end

  defp b64(v, n),
    do: for(i <- (n - 1)..0//-1, into: "", do: <<elem(@chars, rem(div(v, Integer.pow(64, i)), 64))>>)

  @doc "무작위 GlobalId — uuid4 를 압축(ifcopenshell.guid.new)."
  def random_gid do
    <<a::48, _::4, b::12, _::2, c::62>> = :crypto.strong_rand_bytes(16)
    compress(<<a::48, 4::4, b::12, 2::2, c::62>>)
  end

  @doc "1, 2, 3 … 을 UUID 정수로 압축하는 결정적 GlobalId — 정답 파일(gen_ifc_fixtures.py)과 같은 수열."
  def counter_gid do
    c = :counters.new(1, [])

    fn ->
      :counters.add(c, 1, 1)
      compress(<<:counters.get(c, 1)::128>>)
    end
  end

  defp local_stamp do
    {{y, mo, d}, {h, mi, s}} = :calendar.local_time()
    :io_lib.format("~4..0B-~2..0B-~2..0BT~2..0B:~2..0B:~2..0B", [y, mo, d, h, mi, s]) |> IO.iodata_to_binary()
  end
end
