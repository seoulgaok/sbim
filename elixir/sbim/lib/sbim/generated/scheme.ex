# 생성 파일 — 손으로 고치지 마라.
# 정본: python/seoulgaok_bim_core/types.py (pydantic Scheme·UnitRecord·SurroundingBuilding)
# 생성: cd python && uv run python scripts/gen_build_options.py
#
# 네 스키마(schema/scheme·units·surroundings·site.schema.json)의 `$defs` 를 이름으로 합쳤다.
# 기본값은 전부 nil 이고 to_map 은 nil 인 선택 필드를 뺀다 — 밑줄 키의 「없음 ≠ null」.
# 값은 Jason 이 준 그대로(정수·실수를 강제하지 않는다). units.json 은 아직 구
# `Unit(geom/data)` 모양이라 UnitRecord 로 안 읽힌다.

defmodule Sbim.Scheme.BufferAttributeData do
  @type t :: %__MODULE__{
          itemSize: integer(),
          type: String.t(),
          array: [number()],
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    itemSize: nil,
    type: nil,
    array: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"itemSize", :itemSize, :value},
        {"type", :type, :value},
        {"array", :array, :value}
      ],
      required: ["itemSize", "type", "array"],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.BufferAttributes do
  @type t :: %__MODULE__{
          position: Sbim.Scheme.BufferAttributeData.t(),
          normal: Sbim.Scheme.BufferAttributeData.t(),
          uv: Sbim.Scheme.BufferAttributeData.t() | nil,
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    position: nil,
    normal: nil,
    uv: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"position", :position, {:model, Sbim.Scheme.BufferAttributeData}},
        {"normal", :normal, {:model, Sbim.Scheme.BufferAttributeData}},
        {"uv", :uv, {:model, Sbim.Scheme.BufferAttributeData}}
      ],
      required: ["position", "normal"],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.BufferIndex do
  @type t :: %__MODULE__{
          type: String.t(),
          array: [integer()],
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    type: nil,
    array: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"type", :type, :value},
        {"array", :array, :value}
      ],
      required: ["type", "array"],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.BufferGeometryInner do
  @type t :: %__MODULE__{
          attributes: Sbim.Scheme.BufferAttributes.t(),
          index: Sbim.Scheme.BufferIndex.t(),
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    attributes: nil,
    index: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"attributes", :attributes, {:model, Sbim.Scheme.BufferAttributes}},
        {"index", :index, {:model, Sbim.Scheme.BufferIndex}}
      ],
      required: ["attributes", "index"],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.BufferGeometryMetadata do
  @type t :: %__MODULE__{
          version: number(),
          type: String.t(),
          generator: String.t(),
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    version: nil,
    type: nil,
    generator: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"version", :version, :value},
        {"type", :type, :value},
        {"generator", :generator, :value}
      ],
      required: ["version", "type", "generator"],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.BufferGeometryData do
  @type t :: %__MODULE__{
          metadata: Sbim.Scheme.BufferGeometryMetadata.t(),
          uuid: String.t(),
          type: String.t(),
          data: Sbim.Scheme.BufferGeometryInner.t(),
          userData: map() | nil,
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    metadata: nil,
    uuid: nil,
    type: nil,
    data: nil,
    userData: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"metadata", :metadata, {:model, Sbim.Scheme.BufferGeometryMetadata}},
        {"uuid", :uuid, :value},
        {"type", :type, :value},
        {"data", :data, {:model, Sbim.Scheme.BufferGeometryInner}},
        {"userData", :userData, :value}
      ],
      required: ["metadata", "uuid", "type", "data"],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.ColumnSection do
  @moduledoc ~S"""
  기둥 실단면 하나 — _column_centers의 같은 자리 기둥을 정사각이 아니라 이 단면으로 그린다.
  w는 빔 축 방향, d는 그 가로, angle_deg는 w 축의 각(도).
  """

  @type t :: %__MODULE__{
          center: [number()],
          w: number(),
          d: number(),
          angle_deg: number(),
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    # 기둥 중심 (EPSG:5186 절대) — _column_centers와 같은 프레임·같은 순서
    center: nil,
    # 단면 치수 (m) — 빔 축 방향
    w: nil,
    # 단면 치수 (m) — 빔 축의 가로
    d: nil,
    # w 축의 각 (도)
    angle_deg: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"center", :center, :value},
        {"w", :w, :value},
        {"d", :d, :value},
        {"angle_deg", :angle_deg, :value}
      ],
      required: ["center", "w", "d", "angle_deg"],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.CompileError do
  @moduledoc ~S"""
  sBIM 도메인 명제 위반 — invalid design 발화.

  type: 위반 종류. 프론트엔드 TypeScript에서 discriminated union.
  reason: 사람이 읽는 짧은 설명.
  details: 위반 수치 / polygon 정보 (디버깅·LLM용).
  suggestion: BuildOptions 조정 힌트 (사용자/LLM이 따라 재컴파일).
  """

  @type t :: %__MODULE__{
          type: String.t(),
          reason: String.t(),
          details: map(),
          suggestion: String.t() | nil
        }

  defstruct [
    # 값: "UnitsInfeasible" | "UnitUnreachable" | "UnitAreaExceeded" | "ParkingSufficiency" | "FloorCountInfeasible" | "CoreTypeInfeasible"
    type: nil,
    reason: nil,
    details: nil,
    suggestion: nil
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `{:error, {:unknown_keys, 경로, 키들}}` 다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null)."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"type", :type, :value},
        {"reason", :reason, :value},
        {"details", :details, :value},
        {"suggestion", :suggestion, :value}
      ],
      required: ["type", "reason"],
      extra?: false,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.CoreLayout do
  @moduledoc ~S"""
  코어 내부 분할 — 링은 EPSG 절대.
  """

  @type t :: %__MODULE__{
          ev: [[number()]] | nil,
          stair: [[number()]] | nil,
          corridor: [[number()]] | nil,
          ev_front: [[number()]] | nil,
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    ev: nil,
    stair: nil,
    corridor: nil,
    ev_front: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"ev", :ev, :value},
        {"stair", :stair, :value},
        {"corridor", :corridor, :value},
        {"ev_front", :ev_front, :value}
      ],
      required: [],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.EngineStamp do
  @moduledoc ~S"""
  이 설계안을 만든 엔진 빌드 도장 — 서버 결과를 추적·재현한다. 전부 문자열.
  같은 소스라도 CPU 아키텍처가 다르면 컴파일 분기가 갈릴 수 있어 platform 을 남긴다.
  """

  @type t :: %__MODULE__{
          engine_commit: String.t(),
          platform: String.t(),
          python: String.t(),
          compiled_at: String.t(),
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    # 엔진 저장소 커밋 SHA — 이 도면을 만든 빌드
    engine_commit: nil,
    # 엔진이 돈 플랫폼 — "linux-x86_64" · "darwin-arm64" 등
    platform: nil,
    # 엔진 파이썬 버전 문자열
    python: nil,
    # 컴파일 시각 — ISO-8601 UTC
    compiled_at: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"engine_commit", :engine_commit, :value},
        {"platform", :platform, :value},
        {"python", :python, :value},
        {"compiled_at", :compiled_at, :value}
      ],
      required: ["engine_commit", "platform", "python", "compiled_at"],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.FloorData do
  @type t :: %__MODULE__{
          floor_id: integer(),
          floor_area: number(),
          floor_height: number(),
          floor_bottom_height: number(),
          floor_name: String.t() | nil,
          parking_count: integer() | nil,
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    floor_id: nil,
    floor_area: nil,
    floor_height: nil,
    floor_bottom_height: nil,
    floor_name: nil,
    parking_count: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"floor_id", :floor_id, :value},
        {"floor_area", :floor_area, :value},
        {"floor_height", :floor_height, :value},
        {"floor_bottom_height", :floor_bottom_height, :value},
        {"floor_name", :floor_name, :value},
        {"parking_count", :parking_count, :value}
      ],
      required: ["floor_id", "floor_area", "floor_height", "floor_bottom_height"],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.FloorGeometry do
  @type t :: %__MODULE__{
          walls: [[Sbim.Scheme.BufferGeometryData.t()]],
          floors: [[Sbim.Scheme.BufferGeometryData.t()]],
          roof: [[Sbim.Scheme.BufferGeometryData.t()]] | nil,
          windows: [[Sbim.Scheme.BufferGeometryData.t()]] | nil,
          parapets: [[Sbim.Scheme.BufferGeometryData.t()]] | nil,
          columns: [[Sbim.Scheme.BufferGeometryData.t()]] | nil,
          parking_stalls: [[Sbim.Scheme.BufferGeometryData.t()]] | nil,
          doors: [[Sbim.Scheme.BufferGeometryData.t()]] | nil,
          beams: [[Sbim.Scheme.BufferGeometryData.t()]] | nil,
          stairs: [[Sbim.Scheme.BufferGeometryData.t()]] | nil,
          coverings: [[Sbim.Scheme.BufferGeometryData.t()]] | nil,
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    walls: nil,
    floors: nil,
    roof: nil,
    windows: nil,
    parapets: nil,
    columns: nil,
    parking_stalls: nil,
    doors: nil,
    beams: nil,
    stairs: nil,
    coverings: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"walls", :walls, {:list, {:list, {:model, Sbim.Scheme.BufferGeometryData}}}},
        {"floors", :floors, {:list, {:list, {:model, Sbim.Scheme.BufferGeometryData}}}},
        {"roof", :roof, {:list, {:list, {:model, Sbim.Scheme.BufferGeometryData}}}},
        {"windows", :windows, {:list, {:list, {:model, Sbim.Scheme.BufferGeometryData}}}},
        {"parapets", :parapets, {:list, {:list, {:model, Sbim.Scheme.BufferGeometryData}}}},
        {"columns", :columns, {:list, {:list, {:model, Sbim.Scheme.BufferGeometryData}}}},
        {"parking_stalls", :parking_stalls, {:list, {:list, {:model, Sbim.Scheme.BufferGeometryData}}}},
        {"doors", :doors, {:list, {:list, {:model, Sbim.Scheme.BufferGeometryData}}}},
        {"beams", :beams, {:list, {:list, {:model, Sbim.Scheme.BufferGeometryData}}}},
        {"stairs", :stairs, {:list, {:list, {:model, Sbim.Scheme.BufferGeometryData}}}},
        {"coverings", :coverings, {:list, {:list, {:model, Sbim.Scheme.BufferGeometryData}}}}
      ],
      required: ["walls", "floors"],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.FloorPlan do
  @type t :: %__MODULE__{
          data: Sbim.Scheme.FloorData.t(),
          geom: Sbim.Scheme.FloorGeometry.t(),
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    data: nil,
    geom: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"data", :data, {:model, Sbim.Scheme.FloorData}},
        {"geom", :geom, {:model, Sbim.Scheme.FloorGeometry}}
      ],
      required: ["data", "geom"],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.LegalCheck do
  @moduledoc ~S"""
  법규 체크리스트 한 항목의 판정 실값 — key는 giga legal_checklist.yaml 의 key(변경 금지,
  그래프 노드 id).
  """

  @type t :: %__MODULE__{
          key: String.t(),
          group: String.t(),
          item: String.t(),
          status: String.t(),
          apply: String.t(),
          law: String.t(),
          note: String.t() | nil,
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    key: nil,
    group: nil,
    item: nil,
    # '적용' | '해당없음' | '검토' | '참고' 또는 실값 포함('적용 (확폭 12㎡)')
    status: nil,
    # 적용 내용 — 산출값 채워진 문장
    apply: nil,
    # 근거 조문
    law: nil,
    note: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"key", :key, :value},
        {"group", :group, :value},
        {"item", :item, :value},
        {"status", :status, :value},
        {"apply", :apply, :value},
        {"law", :law, :value},
        {"note", :note, :value}
      ],
      required: ["key", "group", "item", "status", "apply", "law"],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.MepItem do
  @moduledoc ~S"""
  설비 항목 하나 (제안 2026-10-16, #549 — 엔진 미방출). 배관·덕트는 path, 기기는 origin.

  system: water|drain|heating|vent|gas|elec · kind: pipe|duct|device · 좌표 EPSG 절대.
  """

  @type t :: %__MODULE__{
          system: String.t(),
          kind: String.t(),
          name: String.t() | nil,
          floor_id: integer() | nil,
          origin: [number()] | nil,
          path: [[number()]] | nil,
          size: number() | nil,
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    system: nil,
    kind: nil,
    name: nil,
    floor_id: nil,
    origin: nil,
    path: nil,
    size: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"system", :system, :value},
        {"kind", :kind, :value},
        {"name", :name, :value},
        {"floor_id", :floor_id, :value},
        {"origin", :origin, :value},
        {"path", :path, :value},
        {"size", :size, :value}
      ],
      required: ["system", "kind"],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.ResolvedCore do
  @type t :: %__MODULE__{
          type: 1 | 2 | 3 | 4 | 5 | 6 | 7 | nil,
          core_side: String.t() | nil,
          core_rotation: 0 | 90 | 180 | 270 | nil,
          core_mirror: boolean() | nil,
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    type: nil,
    # 값: "n" | "ne" | "e" | "se" | "s" | "sw" | "w" | "nw" | "c"
    core_side: nil,
    core_rotation: nil,
    core_mirror: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"type", :type, :value},
        {"core_side", :core_side, :value},
        {"core_rotation", :core_rotation, :value},
        {"core_mirror", :core_mirror, :value}
      ],
      required: [],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.ResolvedMassing do
  @type t :: %__MODULE__{
          mass_axis: String.t() | nil,
          target_floor_count: integer() | nil,
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    # 값: "road" | "sunlight"
    mass_axis: nil,
    target_floor_count: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"mass_axis", :mass_axis, :value},
        {"target_floor_count", :target_floor_count, :value}
      ],
      required: [],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.ResolvedParking do
  @type t :: %__MODULE__{
          parking_angle: 45 | 60 | 90 | nil,
          tandem: boolean() | nil,
          parking_graph: [[String.t()]] | nil,
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    parking_angle: nil,
    tandem: nil,
    parking_graph: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"parking_angle", :parking_angle, :value},
        {"tandem", :tandem, :value},
        {"parking_graph", :parking_graph, :value}
      ],
      required: [],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.ResolvedUnits do
  @type t :: %__MODULE__{
          units_per_floor: integer() | nil,
          units_by_level: %{optional(String.t()) => integer()} | nil,
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    units_per_floor: nil,
    units_by_level: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"units_per_floor", :units_per_floor, :value},
        {"units_by_level", :units_by_level, :value}
      ],
      required: [],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.ResolvedDesign do
  @moduledoc ~S"""
  `BuildOptions.design`과 같은 중첩 모양 — 첫수표가 채우는 필드(`empty: "auto"`)만.
  잎 집합은 `options.AUTO_FIELDS`와 같다(tests/test_auto_fields.py가 지킨다).
  """

  @type t :: %__MODULE__{
          massing: Sbim.Scheme.ResolvedMassing.t() | nil,
          units: Sbim.Scheme.ResolvedUnits.t() | nil,
          core: Sbim.Scheme.ResolvedCore.t() | nil,
          parking: Sbim.Scheme.ResolvedParking.t() | nil,
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    massing: nil,
    units: nil,
    core: nil,
    parking: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"massing", :massing, {:model, Sbim.Scheme.ResolvedMassing}},
        {"units", :units, {:model, Sbim.Scheme.ResolvedUnits}},
        {"core", :core, {:model, Sbim.Scheme.ResolvedCore}},
        {"parking", :parking, {:model, Sbim.Scheme.ResolvedParking}}
      ],
      required: [],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.ResolvedOptions do
  @moduledoc ~S"""
  엔진이 실제로 쓴 속성 창 값 + 필드별 출처 — 엔진이 방출, 소비처가 표시.

  사용자가 비운(None) 칸을 첫수표가 채우면 그 값이 여기 적힌다. 소비처는 전문가 칸의
  자동값을 흐리게 「자동 (s · 90° · 2형)」으로 보여 주고, 누르면 그 값으로 고정한다.
  source 키는 "<묶음>.<필드>"(예: "core.core_side"), 값은 user(사용자가 준 값) |
  prior(첫수표가 채운 값). design 에 없는 필드는 source 에도 없다.

  계약: 첫수표가 채우는 필드(`AUTO_FIELDS` — 층수·층별 세대 수 포함)는 전부 design 에
  나온다. source=="prior" 인 값은 결코 null 이 아니다 — 단 "units.units_per_floor" 는
  모든 층의 세대 수가 같을 때만 채우고, 다르면 null 이며 source 에도 없다. design 을
  (null 잎을 버리고) 요청의 design 에 합쳐 되먹이면 같은 결과(세대·전용면적·주차 대수·
  compile_errors)가 재현된다. 소비처는 source 를 되보내지 않는다(BuildOptions 는
  extra="forbid"). 비우면 법이 정하는 필드(`law` — exit_road·한도 덮어쓰기·road_setback)와
  적힌 기본값이 정하는 필드(`default`)는 여기 없다 — 비워 두는 것이 재현되는 선택이다.
  """

  @type t :: %__MODULE__{
          design: Sbim.Scheme.ResolvedDesign.t(),
          source: %{optional(String.t()) => String.t()},
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    design: nil,
    source: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"design", :design, {:model, Sbim.Scheme.ResolvedDesign}},
        {"source", :source, :value}
      ],
      required: ["design"],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.SchemeData do
  @type t :: %__MODULE__{
          lot_area: number(),
          build_area: number(),
          far: number(),
          bcr: number(),
          pnu: integer() | String.t(),
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    lot_area: nil,
    build_area: nil,
    far: nil,
    bcr: nil,
    pnu: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"lot_area", :lot_area, :value},
        {"build_area", :build_area, :value},
        {"far", :far, :value},
        {"bcr", :bcr, :value},
        {"pnu", :pnu, :value}
      ],
      required: ["lot_area", "build_area", "far", "bcr", "pnu"],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.Scheme do
  @moduledoc ~S"""
  scheme.json — data·floor_plans·unit_ids + 밑줄 키(SchemeSpatial).
  """

  @type t :: %__MODULE__{
          _core_layout: Sbim.Scheme.CoreLayout.t() | nil,
          _parking_stalls: [[[number()]]] | nil,
          _column_centers: [[number()]] | nil,
          _basement_outline: [[number()]] | nil,
          _floor_outlines: %{optional(String.t()) => [[number()]]} | nil,
          _pedestrian_path: [[number()]] | nil,
          _pedestrian_paths: [[[number()]]] | nil,
          _halls: %{optional(String.t()) => [[[number()]]]} | nil,
          _penthouse_outline: [[number()]] | nil,
          _common_footprint: [[number()]] | nil,
          _validation: [String.t()] | nil,
          _column_size: number() | nil,
          _column_sections: [Sbim.Scheme.ColumnSection.t()] | nil,
          _north_ref_edges: [[[number()]]] | nil,
          _north_datum_offset: number() | nil,
          _legal_checks: [Sbim.Scheme.LegalCheck.t()] | nil,
          _compile_errors: [Sbim.Scheme.CompileError.t()] | nil,
          _engine_stamp: Sbim.Scheme.EngineStamp.t() | nil,
          _mep: [Sbim.Scheme.MepItem.t()] | nil,
          data: Sbim.Scheme.SchemeData.t(),
          floor_plans: [Sbim.Scheme.FloorPlan.t()],
          unit_ids: [String.t()],
          resolved_options: Sbim.Scheme.ResolvedOptions.t() | nil,
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    _core_layout: nil,
    _parking_stalls: nil,
    _column_centers: nil,
    _basement_outline: nil,
    # 층별 footprint ring — 복도(=층외곽−세대−코어) 유도 기준
    _floor_outlines: nil,
    # 보행 출입로 (도로→코어) — 보행 경로 산출. 1F 전용
    _pedestrian_path: nil,
    # 보행 출입로 전부 — 코어 문 2개(#35)면 2개. [0] === _pedestrian_path (호환)
    _pedestrian_paths: nil,
    # DH 공용 홀 — {level: ring[]}. 코어 복도 띠를 양옆으로 늘인 팔·EV 로비(연희 75-9 GT T자 홀
    # — 코어로 갈라진 2조각이라 링 목록). 세대에서 차감된 공용, 접면 연결계 = 코어 복도 ∪ 홀
    _halls: nil,
    # 옥탑(계단탑) 외곽 — 옥탑층·지붕층 평면이 공유
    _penthouse_outline: nil,
    # 전층 교집합 — 코어 탐색공간
    _common_footprint: nil,
    # 준법 위반·경고 메모
    _validation: nil,
    # 기둥 단면 한 변 (m) — Concrete.column_size 확정값. 도면 재구성이 scheme만 보고도 같은
    # 크기를 그리도록 방출(폴백 이원화 방지).
    _column_size: nil,
    # 기둥 실단면 목록 — _column_centers와 같은 좌표 프레임·같은 순서. 있음이면 소비처는 정사각
    # 대신 이것으로 그린다(얇은 단면 기둥을 정사각으로 그리면 주차 칸을 문다). 없음 =
    # _column_size 정사각 폴백 (구 scheme).
    _column_sections: nil,
    # 정북일조 기준선 (EPSG:5186 절대, 변마다 [p1,p2]) — 3D 뷰어 천공면. 북향 변마다 별도
    # 엣지(상업 인접 면제·도로 인접은 중심선 offset), 매스 깎기(apply_north_setback)와 동일
    # 기준. 면제면 [].
    _north_ref_edges: nil,
    # 정북일조 기산면 보정 (m) — 영 119조①5호 나목: 높이는 본 대지와 북측 인접대지의 평균 수평면
    # 기준. z0 − 본 대지 지표면 = 고저차의 1/2. 천공면 그리기: 유효높이 h' = z − 이 값
    # (경사지에서 프로파일이 수직으로 이동). 미방출·null이면 0(평지 가정).
    _north_datum_offset: nil,
    # 법규 체크리스트 33항목 판정 실값 (giga legal_checklist.yaml SSOT, #16). 합격/불합격이
    # 아니라 적용여부 + 산출값이다 — 엔진은 규제를 생성 단계에서 지켜버리므로(사선은 매스를
    # 깎고, 미충족은 compile_errors) 완성 설계에 '미달' 항목이 존재할 수 없다. law-graph가 결정
    # 노드에서 근거 조문으로 엣지를 이을 때 이 실값을 쓴다. 구 scheme엔 없다 — 소비처는 부재를
    # "구 버전"으로 처리할 것.
    _legal_checks: nil,
    # 엔진이 이 설계안을 스스로 거절한 사유 (errors.py CompileError —
    # type·reason·details·suggestion). 없음 또는 [] = 컴파일 통과. 하나 이상이면 설계는
    # 저장됐지만 경고와 함께 보여야 한다.
    _compile_errors: nil,
    # 이 설계안을 만든 엔진 빌드 도장 (EngineStamp) — 서버 결과를 추적·재현한다. 전부 문자열. 구
    # scheme엔 없다 — 소비처는 부재를 "구 버전"으로 처리할 것.
    _engine_stamp: nil,
    # 설비 (제안 2026-10-16, #549 — 엔진 미방출). 계통별 평면도(위생·냉난방·환기·가스·전기)의
    # 재료. 처음엔 기기(kind: "device") 자리만이어도 도면이 된다. 좌표 EPSG 절대.
    _mep: nil,
    data: nil,
    floor_plans: nil,
    unit_ids: nil,
    # 엔진이 실제로 쓴 속성 창 값 + 출처. 구 scheme엔 없다.
    resolved_options: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"_core_layout", :_core_layout, {:model, Sbim.Scheme.CoreLayout}},
        {"_parking_stalls", :_parking_stalls, :value},
        {"_column_centers", :_column_centers, :value},
        {"_basement_outline", :_basement_outline, :value},
        {"_floor_outlines", :_floor_outlines, :value},
        {"_pedestrian_path", :_pedestrian_path, :value},
        {"_pedestrian_paths", :_pedestrian_paths, :value},
        {"_halls", :_halls, :value},
        {"_penthouse_outline", :_penthouse_outline, :value},
        {"_common_footprint", :_common_footprint, :value},
        {"_validation", :_validation, :value},
        {"_column_size", :_column_size, :value},
        {"_column_sections", :_column_sections, {:list, {:model, Sbim.Scheme.ColumnSection}}},
        {"_north_ref_edges", :_north_ref_edges, :value},
        {"_north_datum_offset", :_north_datum_offset, :value},
        {"_legal_checks", :_legal_checks, {:list, {:model, Sbim.Scheme.LegalCheck}}},
        {"_compile_errors", :_compile_errors, {:list, {:model, Sbim.Scheme.CompileError}}},
        {"_engine_stamp", :_engine_stamp, {:model, Sbim.Scheme.EngineStamp}},
        {"_mep", :_mep, {:list, {:model, Sbim.Scheme.MepItem}}},
        {"data", :data, {:model, Sbim.Scheme.SchemeData}},
        {"floor_plans", :floor_plans, {:list, {:model, Sbim.Scheme.FloorPlan}}},
        {"unit_ids", :unit_ids, :value},
        {"resolved_options", :resolved_options, {:model, Sbim.Scheme.ResolvedOptions}}
      ],
      required: ["data", "floor_plans", "unit_ids"],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.SiteInfo do
  @moduledoc ~S"""
  설계안 폴더의 `site.json` — 필지·도로·외곽선. 키 이름·좌표(EPSG:5186 절대)는 엔진
  building_info 와 같다.

  scheme.json 에 없어 에디터가 대지 경계·도로·정북 한계선을 못 그리던 것을 채운다. TS `SiteInfo`
  와 같은 모양.
  """

  @type t :: %__MODULE__{
          parcel_polygon: [[number()]],
          parcel_center: [number()],
          road_polygon: [[[number()]]] | nil,
          road_polygon_wide: [[[number()]]] | nil,
          road_centerlines: [[[number()]]] | nil,
          road_centerline_widths: [number()] | nil,
          effective_parcel_outline: [[number()]] | nil,
          buildable_outline: [[number()]] | nil,
          footprint_outline: [[number()]] | nil,
          north_datum_offset: number() | nil,
          raw_parcel_area: number() | nil,
          effective_parcel_area: number() | nil,
          road_widening_area: number() | nil,
          corner_cut_area: number() | nil,
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    parcel_polygon: nil,
    parcel_center: nil,
    road_polygon: nil,
    road_polygon_wide: nil,
    road_centerlines: nil,
    road_centerline_widths: nil,
    effective_parcel_outline: nil,
    buildable_outline: nil,
    footprint_outline: nil,
    north_datum_offset: nil,
    raw_parcel_area: nil,
    effective_parcel_area: nil,
    road_widening_area: nil,
    corner_cut_area: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"parcel_polygon", :parcel_polygon, :value},
        {"parcel_center", :parcel_center, :value},
        {"road_polygon", :road_polygon, :value},
        {"road_polygon_wide", :road_polygon_wide, :value},
        {"road_centerlines", :road_centerlines, :value},
        {"road_centerline_widths", :road_centerline_widths, :value},
        {"effective_parcel_outline", :effective_parcel_outline, :value},
        {"buildable_outline", :buildable_outline, :value},
        {"footprint_outline", :footprint_outline, :value},
        {"north_datum_offset", :north_datum_offset, :value},
        {"raw_parcel_area", :raw_parcel_area, :value},
        {"effective_parcel_area", :effective_parcel_area, :value},
        {"road_widening_area", :road_widening_area, :value},
        {"corner_cut_area", :corner_cut_area, :value}
      ],
      required: [],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.SurroundingData do
  @type t :: %__MODULE__{
          address: String.t() | nil,
          height: number(),
          floor: integer(),
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    address: nil,
    height: nil,
    floor: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"address", :address, :value},
        {"height", :height, :value},
        {"floor", :floor, :value}
      ],
      required: ["height", "floor"],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.SurroundingGeometry do
  @type t :: %__MODULE__{
          boundary: [Sbim.Scheme.BufferGeometryData.t()],
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    boundary: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"boundary", :boundary, {:list, {:model, Sbim.Scheme.BufferGeometryData}}}
      ],
      required: ["boundary"],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.SurroundingBuilding do
  @type t :: %__MODULE__{
          geom: Sbim.Scheme.SurroundingGeometry.t(),
          data: Sbim.Scheme.SurroundingData.t(),
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    geom: nil,
    data: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"geom", :geom, {:model, Sbim.Scheme.SurroundingGeometry}},
        {"data", :data, {:model, Sbim.Scheme.SurroundingData}}
      ],
      required: ["geom", "data"],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.UnitAreaBreakdown do
  @type t :: %__MODULE__{
          net: number() | nil,
          common: number() | nil,
          land_portion: number() | nil,
          contract: number() | nil,
          veranda: number() | nil,
          veranda_eq: number() | nil,
          balcony: number() | nil,
          balcony_depth: number() | nil,
          service: number() | nil,
          actual_use: number() | nil,
          duplex_upper: number() | nil,
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    net: nil,
    common: nil,
    land_portion: nil,
    contract: nil,
    veranda: nil,
    veranda_eq: nil,
    balcony: nil,
    balcony_depth: nil,
    service: nil,
    actual_use: nil,
    duplex_upper: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"net", :net, :value},
        {"common", :common, :value},
        {"land_portion", :land_portion, :value},
        {"contract", :contract, :value},
        {"veranda", :veranda, :value},
        {"veranda_eq", :veranda_eq, :value},
        {"balcony", :balcony, :value},
        {"balcony_depth", :balcony_depth, :value},
        {"service", :service, :value},
        {"actual_use", :actual_use, :value},
        {"duplex_upper", :duplex_upper, :value}
      ],
      required: [],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.UnitFixture do
  @moduledoc ~S"""
  세대 안 가구·기구 (제안 2026-10-16, #549 — 엔진 미방출).

  소비처는 kind 별 2D 기호·3D 상자만 그린다 — 종류 이름과 자리·치수면 된다.
  kind 어휘(BIMx 샘플): 싱크·쿡탑·인덕션·후드·냉장고·세탁기·상부장·하부장·아일랜드식탁·
  세면대·대변기·샤워부스·젠다이·신발장·침대·소파·의자·식탁.
  """

  @type t :: %__MODULE__{
          kind: String.t(),
          origin: [number()],
          angle_deg: number() | nil,
          w: number(),
          d: number(),
          h: number() | nil,
          room_index: integer() | nil,
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    kind: nil,
    origin: nil,
    angle_deg: nil,
    w: nil,
    d: nil,
    h: nil,
    room_index: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"kind", :kind, :value},
        {"origin", :origin, :value},
        {"angle_deg", :angle_deg, :value},
        {"w", :w, :value},
        {"d", :d, :value},
        {"h", :h, :value},
        {"room_index", :room_index, :value}
      ],
      required: ["kind"],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.UnitRoom do
  @moduledoc ~S"""
  방 최소 의미론 — 벽·문 기하는 geom userData가 따로 옴.

  지금 엔진은 욕실·주방만 낸다. 거실·침실·현관·발코니·다용도실·복도 는 제안(#549).
  """

  @type t :: %__MODULE__{
          use: String.t(),
          polygon: [[number()]],
          floor_finish: String.t() | nil,
          ceiling_h: number() | nil,
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    use: nil,
    polygon: nil,
    floor_finish: nil,
    ceiling_h: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"use", :use, :value},
        {"polygon", :polygon, :value},
        {"floor_finish", :floor_finish, :value},
        {"ceiling_h", :ceiling_h, :value}
      ],
      required: [],
      extra?: true,
      omit_nil?: true
    }
  end
end

defmodule Sbim.Scheme.UnitRecord do
  @moduledoc ~S"""
  units.json 레코드 — 생성기 units 직렬화 계약.
  """

  @type t :: %__MODULE__{
          id: String.t(),
          floor: integer(),
          floor_height: number() | nil,
          floor_bottom_height: number() | nil,
          price: number(),
          area: Sbim.Scheme.UnitAreaBreakdown.t(),
          geom: term() | nil,
          polygon: [[number()]] | nil,
          duplex_upper_polygon: [[number()]] | nil,
          balcony_polygons: [[[number()]]] | nil,
          polygons_by_floor: %{optional(String.t()) => [[number()]]} | nil,
          rooms: [Sbim.Scheme.UnitRoom.t()] | nil,
          fixtures: [Sbim.Scheme.UnitFixture.t()] | nil,
          extra: %{optional(String.t()) => term()}
        }

  defstruct [
    id: nil,
    floor: nil,
    floor_height: nil,
    floor_bottom_height: nil,
    price: nil,
    area: nil,
    geom: nil,
    polygon: nil,
    duplex_upper_polygon: nil,
    balcony_polygons: nil,
    polygons_by_floor: nil,
    rooms: nil,
    fixtures: nil,
    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다
    extra: %{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `extra` 에 담는다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 인 선택 필드는 뺀다(없음 ≠ null); extra 는 펼친다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"id", :id, :value},
        {"floor", :floor, :value},
        {"floor_height", :floor_height, :value},
        {"floor_bottom_height", :floor_bottom_height, :value},
        {"price", :price, :value},
        {"area", :area, {:model, Sbim.Scheme.UnitAreaBreakdown}},
        {"geom", :geom, :value},
        {"polygon", :polygon, :value},
        {"duplex_upper_polygon", :duplex_upper_polygon, :value},
        {"balcony_polygons", :balcony_polygons, :value},
        {"polygons_by_floor", :polygons_by_floor, :value},
        {"rooms", :rooms, {:list, {:model, Sbim.Scheme.UnitRoom}}},
        {"fixtures", :fixtures, {:list, {:model, Sbim.Scheme.UnitFixture}}}
      ],
      required: ["id", "floor"],
      extra?: true,
      omit_nil?: true
    }
  end
end
