# 생성 파일 — 손으로 고치지 마라.
# 정본: python/seoulgaok_bim_core/options.py (pydantic BuildOptions)
# 생성: cd python && uv run python scripts/gen_build_options.py
#
# 기본값은 fixtures/build_options/empty.json 의 expected(after-validator 가 채운 정규화
# 기본값)다 — `%Sbim.Options.BuildOptions{} |> to_map()` 이 그 expected 와 같다.
# 이행 로직은 없다 — 파이썬은 지운 키를 받아서 버리지만 여기 from_map 은 스키마에 없는 키를
# 거부한다. 옛 저장값은 Sbim.Migrations 의 표를 먼저 적용한 뒤 from_map 에 넣는다.

defmodule Sbim.Options.BathFinish do
  @moduledoc ~S"""
  욕실 마감 넷 — `UnitRoom.floor_finish·wall_finish·ceiling_finish·ceiling_h` 로 그대로 나간다.

  용도마다 모델이 따로인 이유: 언어별 방출기(emit_rust)가 한 모델에 한 기본값만 허용한다 —
  모양은 셋이 같다.
  """

  @type t :: %__MODULE__{
          floor: String.t(),
          wall: String.t(),
          ceiling: String.t(),
          ceiling_h: number()
        }

  defstruct [
    # 바닥 마감 이름.
    floor: "바닥타일 300×300",
    # 벽 마감 이름.
    wall: "벽타일 300×600",
    # 천장 마감 이름 — 점검구 있는 판.
    ceiling: "SMC 천장판",
    # 천장고 (m) — 바닥 마감면에서 천장 마감면까지.
    ceiling_h: 2.2
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `{:error, {:unknown_keys, 경로, 키들}}` 다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 은 null 로 낸다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"floor", :floor, :value},
        {"wall", :wall, :value},
        {"ceiling", :ceiling, :value},
        {"ceiling_h", :ceiling_h, :value}
      ],
      required: [],
      extra?: false,
      omit_nil?: false
    }
  end
end

defmodule Sbim.Options.Financing do
  @moduledoc ~S"""
  PF 대출(토지담보·시설자금·준공담보)과 분양 스케줄 의도.

  이자 = 대출액 × 금리 × 기간/12. 분양수입은 계약/중도/잔금으로 월별 분배.

  **금융 조건에는 기본값이 없다(None).** 사업자·시점마다 다른 협상 결과이고,
  남의 조건을 조용히 물려받아 사업성을 계산하는 것이 값이 비는 것보다 위험하다.
  값은 설정 파일에서 주입한다 — config.py / examples/sbim_config.example.json.

  from seoulgaok_bim_core import build_options
  opts = build_options() # sbim_config.json의 financing 블록 적용
  """

  @type t :: %__MODULE__{
          land_loan_ltv: number() | nil,
          land_loan_rate: number() | nil,
          fac_loan_ltv: number() | nil,
          fac_loan_rate: number() | nil,
          fac_efficiency: number() | nil,
          post_loan_rate: number() | nil,
          post_months: number() | nil,
          handling_fee_rate: number() | nil,
          handling_fee_on: boolean()
        }

  defstruct [
    # 토지담보 LTV.
    land_loan_ltv: nil,
    # 토지담보 연이자율.
    land_loan_rate: nil,
    # 시설자금 LTV (직접공사비 기준).
    fac_loan_ltv: nil,
    # 시설자금 연이자율.
    fac_loan_rate: nil,
    # 시설자금 기성고 평균 실사용률 (이자 효율).
    fac_efficiency: nil,
    # 준공담보 연이자율 (담보 확정 → 토지담보 수준).
    post_loan_rate: nil,
    # 준공 후 기간 (개월). 비아파트 = 준공 후 이 기간에 균등 분양·매각.
    post_months: nil,
    # 대출 취급수수료율 (토담+시설 대출액).
    handling_fee_rate: nil,
    # 취급수수료 적용 여부. True=적용.
    handling_fee_on: false
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `{:error, {:unknown_keys, 경로, 키들}}` 다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 은 null 로 낸다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"land_loan_ltv", :land_loan_ltv, :value},
        {"land_loan_rate", :land_loan_rate, :value},
        {"fac_loan_ltv", :fac_loan_ltv, :value},
        {"fac_loan_rate", :fac_loan_rate, :value},
        {"fac_efficiency", :fac_efficiency, :value},
        {"post_loan_rate", :post_loan_rate, :value},
        {"post_months", :post_months, :value},
        {"handling_fee_rate", :handling_fee_rate, :value},
        {"handling_fee_on", :handling_fee_on, :value}
      ],
      required: [],
      extra?: false,
      omit_nil?: false
    }
  end
end

defmodule Sbim.Options.Schedule do
  @moduledoc ~S"""
  사업 일정 의도 — 인허가·심의 단계와 단계별 기간.

  핵심: 착공 전 총 기간(기본설계+심의+허가+실시설계+시공사선정+착공신고)이
  토지담보 PF 이자 기간이 된다. 6층↑이면 건축심의·구조굴토심의로 기간이
  늘어 이자가 증가 — 이 비용을 사업성에 정직하게 반영하기 위한 layer.

  원칙: 심의 토글은 None=자동유도(층수·지하 기반), 명시 시 override.
  단계 기간은 설계자 조정용 default(개월). 공사기간은 기하 derive.
  """

  @type t :: %__MODULE__{
          arch_review: boolean() | nil,
          struct_review: boolean() | nil,
          civil_supervision: boolean() | nil,
          other_survey_cost: number() | nil,
          basic_design: number(),
          arch_review_mo: number(),
          build_permit: number(),
          exec_design: number(),
          struct_review_mo: number(),
          constructor_select: number(),
          constr_notice: number(),
          construction_months: integer() | nil,
          start_year_month: String.t() | nil
        }

  defstruct [
    # 건축심의 시행 여부. None=자동(지상 6층↑ 또는 대로변 건축선후퇴 시 True, 5층 이하 False).
    # 착공 전 기간에 arch_review_mo 가산.
    arch_review: nil,
    # 구조·굴토심의 시행 여부. None=자동(6층↑ 기본 True). 실시설계와 병렬 수행 — 둘 중 긴 쪽이
    # 종료 시점.
    struct_review: nil,
    # 토목감리 적용 여부. None=자동(지하 2개층↑ True). 비용 항목.
    civil_supervision: nil,
    # 기타조사비 (만원) — 문화재·지하철안전도 등 필지별 특수건. None=0.
    other_survey_cost: nil,
    # 기본설계 기간 (개월).
    basic_design: 2.0,
    # 건축심의 기간 (개월). arch_review=True일 때만 가산.
    arch_review_mo: 1.5,
    # 건축허가 기간 (개월).
    build_permit: 1.0,
    # 실시설계 기간 (개월).
    exec_design: 1.0,
    # 구조·굴토심의 기간 (개월). 실시설계와 병렬.
    struct_review_mo: 1.5,
    # 시공사 선정 기간 (개월).
    constructor_select: 1.5,
    # 착공신고 기간 (개월).
    constr_notice: 0.5,
    # 공사기간 (개월). None=2+지상층+지하층×2 자동 derive.
    construction_months: nil,
    # 사업 시작 연월 'YYYY-MM' (기본설계 착수 시점). 재무 숫자엔 영향 없고 현금흐름 달력 라벨용.
    # None=상대 개월(N개월차).
    start_year_month: nil
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `{:error, {:unknown_keys, 경로, 키들}}` 다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 은 null 로 낸다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"arch_review", :arch_review, :value},
        {"struct_review", :struct_review, :value},
        {"civil_supervision", :civil_supervision, :value},
        {"other_survey_cost", :other_survey_cost, :value},
        {"basic_design", :basic_design, :value},
        {"arch_review_mo", :arch_review_mo, :value},
        {"build_permit", :build_permit, :value},
        {"exec_design", :exec_design, :value},
        {"struct_review_mo", :struct_review_mo, :value},
        {"constructor_select", :constructor_select, :value},
        {"constr_notice", :constr_notice, :value},
        {"construction_months", :construction_months, :value},
        {"start_year_month", :start_year_month, :value}
      ],
      required: [],
      extra?: false,
      omit_nil?: false
    }
  end
end

defmodule Sbim.Options.Business do
  @moduledoc ~S"""
  사업성 — 도면과 무관한 값. 소비 UI는 접어 둘 수 있다.
  """

  @type t :: %__MODULE__{
          schedule: Sbim.Options.Schedule.t(),
          financing: Sbim.Options.Financing.t()
        }

  defstruct [
    schedule: %Sbim.Options.Schedule{},
    financing: %Sbim.Options.Financing{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `{:error, {:unknown_keys, 경로, 키들}}` 다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 은 null 로 낸다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"schedule", :schedule, {:model, Sbim.Options.Schedule}},
        {"financing", :financing, {:model, Sbim.Options.Financing}}
      ],
      required: [],
      extra?: false,
      omit_nil?: false
    }
  end
end

defmodule Sbim.Options.Circulation do
  @moduledoc ~S"""
  동선 — 복도·보행로를 어떻게 낼까. 보행로 폭은 법규 보정(regulations)으로 갔다.
  """

  @type t :: %__MODULE__{
          corridor_mode: String.t()
        }

  defstruct [
    # 보행통로 라우팅 — carve=최단, edge=필지 변 추종.
    # 값: "carve" | "edge"
    corridor_mode: "carve"
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `{:error, {:unknown_keys, 경로, 키들}}` 다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 은 null 로 낸다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"corridor_mode", :corridor_mode, :value}
      ],
      required: [],
      extra?: false,
      omit_nil?: false
    }
  end
end

defmodule Sbim.Options.Concrete do
  @type t :: %__MODULE__{
          wall_thickness: number(),
          slab_thickness: number(),
          interior_wall_thickness: number(),
          party_wall_thickness: number(),
          basement_wall_thickness: number(),
          railing_post_size: number(),
          railing_clear: number(),
          parapet_wall_height: number(),
          column_size: number(),
          foundation_thickness: number(),
          insulation_thickness: number(),
          finish_thickness: number(),
          finish_name: String.t(),
          transfer_beam_width: number(),
          transfer_beam_depth: number(),
          beam_size: number(),
          stair_riser_max: number(),
          stair_tread: number(),
          stair_waist: number(),
          price_per_m3: integer()
        }

  defstruct [
    # 외벽 두께 (m). 다세대 표준 0.20 (단열 포함).
    wall_thickness: 0.2,
    # 층간 슬래브 두께 (m). 실무 스펙 150 (기초는 foundation_thickness 별도).
    slab_thickness: 0.15,
    # 세대 **내부** 칸막이 두께 (m). 표준 0.10 (방 분할용).
    interior_wall_thickness: 0.1,
    # 세대 간 경계벽·공용부(복도·계단실) 경계벽 두께 (m). 실무 표준 0.20. 법정 하한은
    # 다세대(건축허가)면 건축법 계열 경계벽 기준(철근콘크리트조 10cm 이상)이고, 주택건설기준
    # 14조①1의 15cm는 사업계획승인(30세대 이상) 대상에만 적용된다 — 어느 쪽이든 0.20은 충족.
    # 참조 도면(상도동 214-82) 실측도 전 층 철콘200 단일 — 외벽과 **구조체 두께가 같고** 외기
    # 접면만 단열·마감이 덧붙어 410이 된다. 코어 벽이 층마다 달라 보이는 건 단열 유무 차이지
    # 구조체 차이가 아니다.
    party_wall_thickness: 0.2,
    # 지하 외벽(옹벽) 두께 (m). 토압을 받아 지상 외벽보다 두껍다 — 참조 도면 실측 지하1층
    # '철근콘크리트 300' 6장.
    basement_wall_thickness: 0.3,
    # 난간 간살(동자) 단면 한 변 (m). 실무 φ20~50 각살 — 기본 50mm.
    railing_post_size: 0.05,
    # 난간 간살 사이 **안목치수** (m). 중심간 피치 = railing_post_size + 이 값. 법정: 우리
    # 대상(도시형생활주택 30세대 미만 = 건축허가)에는 살 간격 규정이 **없다** — 건축법 시행령
    # 40조①은 높이 1.2m만 규정하고, 안목 10cm 규정인 주택건설기준 18조②2는 같은 영
    # 3조(적용범위)상 사업계획승인(30세대 이상) 대상에만 적용된다. 0.12는 영유아 끼임 방지 안전
    # 관행 범위의 값이며, 30세대 이상 단지를 다루게 되면 0.10으로 낮춰야 한다.
    railing_clear: 0.12,
    # 옥상·노대 난간 중 **콘크리트 저벽** 높이 (m). 기본 0 = 금속 난간만(동자+상단 손스침
    # 바)으로 법정고 1.2m를 만든다 (시행령 40조①). 저벽(방수턱 등)을 원하면 값을 준다 — 그만큼
    # 동자 구간이 짧아진다.
    parapet_wall_height: 0.0,
    # 기둥 단면 한 변 (m). 실무 스펙 600 정사각 — 1층 필로티, 전이보와 접합.
    column_size: 0.6,
    # 기초(흙 접함) 슬래브 두께 (m). 층간 슬래브와 별도 — 두께가 다르다.
    foundation_thickness: 0.6,
    # 외벽 외단열 두께 (m). 참조 도면 실측 '[외벽] 철콘200 // EPS200'.
    insulation_thickness: 0.2,
    # 외부 마감 두께 (m). 재료마다 10~50mm — 기본 STO 10mm.
    finish_thickness: 0.01,
    # 외부 마감재 이름 (IFC 레이어셋 명명에 사용).
    finish_name: "STO",
    # 전이보 폭 (m). 필로티 천장(2층 바닥) 600×800 — 실무 스펙.
    transfer_beam_width: 0.6,
    # 전이보 춤 (m). 윗층 하중을 기둥/벽으로 전달 — 기둥과 만나야 함.
    transfer_beam_depth: 0.8,
    # 일반 보·일조사선 꺾임부 전이보 단면 (m). 600×600 정사각.
    beam_size: 0.6,
    # 계단 단높이 상한 (m). 주택 계단 법정 0.18 — 실단높이 = 층고/단수.
    stair_riser_max: 0.18,
    # 계단 단너비(디딤판 깊이) (m).
    stair_tread: 0.26,
    # 계단판(waist) 두께 (m). 기본 150mm.
    stair_waist: 0.15,
    # 콘크리트 ㎥당 단가 (원). 다세대 표준 350만원. 공사비 = total_m3 × price_per_m3.
    price_per_m3: 3500000
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `{:error, {:unknown_keys, 경로, 키들}}` 다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 은 null 로 낸다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"wall_thickness", :wall_thickness, :value},
        {"slab_thickness", :slab_thickness, :value},
        {"interior_wall_thickness", :interior_wall_thickness, :value},
        {"party_wall_thickness", :party_wall_thickness, :value},
        {"basement_wall_thickness", :basement_wall_thickness, :value},
        {"railing_post_size", :railing_post_size, :value},
        {"railing_clear", :railing_clear, :value},
        {"parapet_wall_height", :parapet_wall_height, :value},
        {"column_size", :column_size, :value},
        {"foundation_thickness", :foundation_thickness, :value},
        {"insulation_thickness", :insulation_thickness, :value},
        {"finish_thickness", :finish_thickness, :value},
        {"finish_name", :finish_name, :value},
        {"transfer_beam_width", :transfer_beam_width, :value},
        {"transfer_beam_depth", :transfer_beam_depth, :value},
        {"beam_size", :beam_size, :value},
        {"stair_riser_max", :stair_riser_max, :value},
        {"stair_tread", :stair_tread, :value},
        {"stair_waist", :stair_waist, :value},
        {"price_per_m3", :price_per_m3, :value}
      ],
      required: [],
      extra?: false,
      omit_nil?: false
    }
  end
end

defmodule Sbim.Options.Core do
  @moduledoc ~S"""
  코어 — 무엇을(type) 어디에(core_side) 어느 방향으로(core_rotation) 어느 손잡이로
  (core_mirror) 앉히는가.

  치수는 입력이 아니라 매스+세대프로그램에서 derive된다(삼전 정답: 계단·EV가 16.4m
  분리 = 세대 배치 결과). 자리와 배향은 고르는 것이고, 값이 없으면 첫수표가 정한다.
  """

  @type t :: %__MODULE__{
          type: 1 | 2 | 3 | 4 | 5 | 6 | 7 | nil,
          core_side: String.t() | nil,
          core_rotation: 0 | 90 | 180 | 270 | nil,
          core_mirror: boolean() | nil,
          core_entries: integer() | nil
        }

  defstruct [
    # 코어 형상 타입 (DWG→sbim 코어 라이브러리 — giga core_library.json이 진실). None=첫수표가
    # 정한다(매스 형상). 이름은 외곽 형태(세장형·정방형·ㄱ자형)로 가르고, 외곽이 같은 것은
    # 괄호의 계단 형식으로 갈린다. 1=세장형(꺾은계단, 2.8×6.8)·2=세장형(직선계단,
    # 2.8×8.05)·3=세장형·편복도(직선계단, 2.8×10.15, 복도 내장, 층당 5~7세대 — 류상호 '코어 유형
    # 추가' 2026-09; 도면 실측 2.78×9.95로 라이브러리 재추출 대기)·4=정방형(꺾은계단,
    # 5.2×4.7)·5=정방형(직선계단, 5.2×4.7)·6=정방형(ㄱ자계단, 5.3×4.95 — ㄱ자는 외곽이 아니라
    # 계단 모양)·7=ㄱ자형(EV측면, 4.8×5.9 — 외곽이 ㄱ자로 파인 유일한 유형). 대부분 type2(세장
    # 타워, 회전 fit), 넓은 단독 장변접도만 type4/5. 번호는 2026-09 DWG 시트 순서로
    # 재배열됐다(building-generator #190) — 옛 번호로 저장된 값은 migrate_core_type()으로
    # 옮긴다.
    # empty: auto
    type: nil,
    # 코어 자리 (EPSG 절대 방위). 정방위(n·e·s·w)=매스의 그 변 가운데, 대각(ne·nw·se·sw)=그
    # 모서리, c=매스 안쪽(주접도 프레임 축을 따라 매스 경계에서 1.5m 이상 떨어진 자리 — 상층은
    # 코어 양쪽에 편복도가 선다). 그 자리에 코어가 안 들면 폴백 없이 CoreTypeInfeasible.
    # None=첫수표가 정한다.
    # 값: "n" | "ne" | "e" | "se" | "s" | "sw" | "w" | "nw" | "c" · empty: auto
    core_side: nil,
    # 코어 배향 — core_side로 정해진 변 기준 절대 회전각. c일 때 기준 변은 주접도 변이다. 0=코어
    # 기준자세 그대로 변에 밀착, 90/180/270=그만큼 회전. 코어는 점대칭이 아니라(계단·EV 한쪽
    # 편재, 복도 한 면 접합, 출입구 면이 방향별로 달라 0·90·180·270이 전부 다른 결과) 절반
    # 지정인 구 core_axis(road/depth)로는 같은 축 위 180° 뒤집기를 표현할 수 없어 네 방위를 전부
    # 받는다. 라이브러리 형상 가로세로와 무관한 앉은 변 기준 절대 표현이라 코어 형상이 바뀌어도
    # 뜻이 유지된다. None=첫수표가 정한다.
    # empty: auto
    core_rotation: nil,
    # 코어 좌우 뒤집기 — true=코어 기준자세를 거울처럼 뒤집은 모양(앉은 변에서 봐서 계단·EV의
    # 좌우가 바뀐 반대 손잡이)으로 앉힌 뒤 core_rotation만큼 돌린다. 회전 네 방위로는 이 모양이
    # 안 나온다 — 회전 180°는 가로·세로를 함께 뒤집어 복도 면까지 옮기지만, 거울은 복도 면을
    # 그대로 두고 좌우만 바꾼다. 회전과 함께 코어가 변에 앉는 여덟 자세를 전부 적는다.
    # false=기준자세 그대로. None=첫수표가 정한다.
    # empty: auto
    core_mirror: nil,
    # 코어(복도) 보행 출입구 수 1|2. 2=코어 문 반대편에도 문 — 보행로가 도로에서 꼬이는
    # 필지(합정동 441-31). None=문 하나(엔진이 둘째 문을 스스로 켜지 않는다 — 2가 필요하면
    # 옵션으로 준다). scheme `_pedestrian_paths`로 전부 방출.
    # empty: default
    core_entries: nil
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `{:error, {:unknown_keys, 경로, 키들}}` 다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 은 null 로 낸다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"type", :type, :value},
        {"core_side", :core_side, :value},
        {"core_rotation", :core_rotation, :value},
        {"core_mirror", :core_mirror, :value},
        {"core_entries", :core_entries, :value}
      ],
      required: [],
      extra?: false,
      omit_nil?: false
    }
  end
end

defmodule Sbim.Options.Exterior do
  @moduledoc ~S"""
  외장 — 외벽 마감과 창 스타일. 한 필드 클래스 둘(Windows·Exterior)을 합쳤다.
  """

  @type t :: %__MODULE__{
          style: String.t(),
          window_style: String.t()
        }

  defstruct [
    # 외장재 preset (외벽·천장/테라스 색 페어). white=화이트·라이트그레이,
    # sandstone=사암·웜그레이, brick=벽돌브라운·라이트그레이(default),
    # concrete=노출콘크리트·짙은회색. 소비처 렌더러가 hex로 매핑.
    # 값: "white" | "sandstone" | "brick" | "concrete"
    style: "brick",
    # 창 크기 의도 — 법정 채광면적(거실 바닥의 1/10)을 몇 배로 잡을지의 배율. open=넉넉(1.8배),
    # standard=표준(1.35배), closed=최소(1.05배). 창의 위치·개수는 세대가 접한 외벽에서
    # 컴파일러가 derive한다.
    # 값: "open" | "standard" | "closed"
    window_style: "open"
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `{:error, {:unknown_keys, 경로, 키들}}` 다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 은 null 로 낸다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"style", :style, :value},
        {"window_style", :window_style, :value}
      ],
      required: [],
      extra?: false,
      omit_nil?: false
    }
  end
end

defmodule Sbim.Options.Massing do
  @type t :: %__MODULE__{
          target_floor_count: integer() | nil,
          first_floor_height: number() | nil,
          floor_use: %{optional(String.t()) => String.t()},
          mass_axis: String.t() | nil
        }

  defstruct [
    # 목표 층수. 사선제한으로 미달 가능. None=첫수표가 정한다(사선·일조·FAR 한계까지 쌓는다).
    # empty: auto
    target_floor_count: nil,
    # 1층 층고 (m). None이면 1층이 필로티(기본)일 때 3.5 — 주차 유효높이 2.3 + 보·설비 — 그 밖의
    # 용도는 구조방식 기본 층고(벽식 3.0/라멘 3.3/철골 3.4).
    # empty: default
    first_floor_height: nil,
    # 층번호 → 용도. 예: {1: 'piloti'}. 미지정 시 1층=piloti, 그 외=residential.
    floor_use: %{},
    # 상층 매스를 반듯하게 세울 기준 방향 — road=주접도변(도로 경계선)과 나란히,
    # sunlight=일조발생라인(정북 인접 대지경계선)과 나란히. None=첫수표가 정한다.
    # 값: "road" | "sunlight" · empty: auto
    mass_axis: nil
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `{:error, {:unknown_keys, 경로, 키들}}` 다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 은 null 로 낸다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"target_floor_count", :target_floor_count, :value},
        {"first_floor_height", :first_floor_height, :value},
        {"floor_use", :floor_use, :value},
        {"mass_axis", :mass_axis, :value}
      ],
      required: [],
      extra?: false,
      omit_nil?: false
    }
  end
end

defmodule Sbim.Options.Parking do
  @moduledoc ~S"""
  주차 — 어떤 축으로 어디에 깔까. 대수는 결과다(법정 대수는 regulations.ratio_mode).

  법정 수치(칸 2.5×5.0·차로 6.0·총 8대 캡·그룹 5대 등)는 옵션이 아니라 엔진 상수다
  (주차장법 시행규칙 — 법이 정하면 상수, 설계자가 고르면 옵션).
  """

  @type t :: %__MODULE__{
          parking_angle: 45 | 60 | 90 | nil,
          parallel: boolean() | nil,
          tandem: boolean() | nil,
          exit_road: integer() | nil,
          parking_graph: [[String.t()]] | nil
        }

  defstruct [
    # 내부 차로 주차 각도. 45/60=사선(fishbone) — 차로폭은 주차장법 시행규칙 11조⑤1호 법정값(45°
    # 3.5m·60° 4.0m), 연접(back) 없음, 막다른 차로라 일방 진입·후진 퇴출 전제. 90=직각(차로 6m).
    # None=첫수표가 정한다(현행 90). 사선 순차 평가는 2026-09-19에 제거됐다. 외부 도로변 주차는
    # 항상 직각(11조⑤2호 — 도로를 차로로 쓰는 형식은 직각·평행뿐)이라 inner 모드에만 의미.
    # empty: auto
    parking_angle: nil,
    # 평행주차 열 — None=법 폴백(직각 배치가 법정 대수에 못 미칠 때만 평행 열을 쓴다, 첫수표 행
    # 아님). True=평행 열을 형태로 선택. False=쓰지 않음.
    # empty: law
    parallel: nil,
    # 연접(직렬 2단) 백칸 허용 (제11조⑤4호). 법 행: 법정 대수 ≤ 8 이면 허용(11조⑤4호),
    # None=첫수표가 정한다.
    # empty: auto
    tandem: nil,
    # 보행통로 출구 도로변 인덱스 (필지 폴리곤 기준). None=자동(최근접 도로변).
    # empty: law
    exit_road: nil,
    # 주차 버블 — (진입 도로 방위, road|yard|aisle) 튜플의 배열. 위상만 적는다 — 칸 수·면
    # 자리·정렬은 대수가 결과이듯 엔진이 정한다. 배열은 명령 순서가 아니라 하나의 그림이다 —
    # 엔진이 전체를 보고 한 번에 푼다(보행로 띠는 늘 먼저 선다). 셋 다 「도로와 이어진다」가 뜻
    # 안에 있다 — 도로와 끊긴 마당은 yard 가 아니다. 긋는 것은 목뿐이다 — 목은 차가 지나가기만
    # 하는 통로라 차 한 폭(2.5m)이면 되고, 6m 차로는 긋지 않는다(칸이 들어오면 그 앞 6m 박스들의
    # 합집합이 차로가 된다 — 소장이 차로 면적을 아끼는 방식). 방위는 항상 dir8(null 없음)이며
    # 칸이 모인 쪽이 아니라 그 차로가 도로에서 갈라져 나오는 자리다 — 필지에서 본 접도 구간의
    # 방향으로 도로를 고른다(core_side 와 같은 규칙): 정방위(n·e·s·w)=그 변의 가운데,
    # 대각(ne·se·sw·nw)=그 모서리 쪽 끝(주접도도 그 방위로 적는다). road=도로 자체가 차로 — 대지
    # 안에 차로 없음, 칸은 도로에 붙은 한 줄. aisle=도로에서 대지 안으로 곧게 이어지는 목(차 한
    # 폭~6m) — 칸은 목 양옆에 붙고, 칸 앞 6m 박스들이 차로가 된다. yard=도로에서 들어오는 목
    # 끝에서 여러 방향으로 칸이 붙는 것 — 목 끝 둘레에서 칸 앞 박스들이 마당이 된다. 같은 도로에
    # 둘 이상: road + 같은 방위 yard/aisle 이면 앞줄은 그 차로 자리를 비우고 깐다(목이 앞줄을
    # 가른다). 대지 안 노드 뒤 같은 방위 대지 안 노드는 앞 노드의 차로를 지나서 든다. 한 도로에
    # 둘 이상이면 대각으로 어느 끝인지 가른다. 버블은 선호 — 법정 대수 미달일 때만, 모자란 칸에
    # 한해 버블 밖 도로에 덧붙인다. 예: 성북 [["n","road"],["sw","yard"]] — 북측 도로 앞 줄과
    # 남서측 도로에서 들어가는 마당 · 연희 [["nw","yard"],["sw","yard"]] — 같은 서쪽 도로의 북쪽
    # 끝·남쪽 끝에서 든 마당 둘 · 화곡 1033-19 의 두 대안 [["w","yard"]](서쪽 작은 마당에 칸이
    # 세 면)과 [["w","aisle"]](같은 자리 곧은 차로 두 줄). None=첫수표가 정한다.
    # empty: auto
    parking_graph: nil
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `{:error, {:unknown_keys, 경로, 키들}}` 다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 은 null 로 낸다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"parking_angle", :parking_angle, :value},
        {"parallel", :parallel, :value},
        {"tandem", :tandem, :value},
        {"exit_road", :exit_road, :value},
        {"parking_graph", :parking_graph, :value}
      ],
      required: [],
      extra?: false,
      omit_nil?: false
    }
  end
end

defmodule Sbim.Options.RegulationOverrides do
  @moduledoc ~S"""
  법규 보정 — 법이 정하는 값을 필지 사정으로 덮어쓴다. 평소엔 전부 비워 둔다.

  수(설계자가 고르는 것)가 아니라 법(용도지역 룩업·조례·시행령)이 틀리거나 완화된
  예외 필지에서만 쓴다. 그래서 설계 묶음과 따로 모았다(2026-09-28).
  """

  @type t :: %__MODULE__{
          far_limit_override: number() | nil,
          bcr_limit_override: number() | nil,
          setback_overrides: %{optional(String.t()) => number()},
          road_setback: number() | nil,
          pedestrian_width: number() | nil,
          ratio_mode: String.t()
        }

  defstruct [
    # 용적률 법정 한도 덮어쓰기 (%) — 지구단위계획·완화 등 용도지역 룩업이 틀린 예외 필지용.
    # None=법이 정한다. (구 이름 far_target)
    # empty: law
    far_limit_override: nil,
    # 건폐율 법정 한도 덮어쓰기 (%) — 지구단위계획·완화 등 용도지역 룩업이 틀린 예외 필지용.
    # None=법이 정한다. (구 이름 bcr_target)
    # empty: law
    bcr_limit_override: nil,
    # 방향별 후퇴거리 (m). 예: {'north': 1.5, 'side': 0.8}.
    setback_overrides: %{},
    # 주차구획 전면선의 주도로 경계 셋백 (m). None=도로산입 derive — 주차장법 시행규칙 11조⑤2호:
    # 직각주차 차로는 도로 포함 6m 이상, 미달분(max(0, 6−실측 도로폭))만큼 후퇴. 12m↑ 도로·폭
    # 미상은 0. 명시(0 포함) 시 그 값 — 설계자가 도로 여건상 밀착·완화를 판단한 의도 기록 (GT
    # 실측: 6m 미만 이면도로에서도 경계 밀착 다수). (구 자리 parking.road_setback)
    # empty: law
    road_setback: nil,
    # 보행통로 폭 (m). 기본 1.5 (시행령 41조 다세대 유효너비 하한). None=용도별 derive (다세대
    # 1.5 등). (구 자리 circulation.pedestrian_width)
    # empty: default
    pedestrian_width: 1.5,
    # 법정 주차대수 산정 기준 (서울시 주차장 조례).
    # multi_family=공동주택(도시형생활주택·다세대): 30㎡↓ 0.5대, 30~60㎡ 0.8대, 60㎡↑ 1.0대,
    # 합계 올림. non_residential=비공동주택(근생·다가구·다중): 60㎡↓ 0.5대, 60㎡↑ 0.7대, 합계
    # 반올림. (구 자리 parking.ratio_mode)
    # 값: "multi_family" | "non_residential"
    ratio_mode: "multi_family"
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `{:error, {:unknown_keys, 경로, 키들}}` 다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 은 null 로 낸다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"far_limit_override", :far_limit_override, :value},
        {"bcr_limit_override", :bcr_limit_override, :value},
        {"setback_overrides", :setback_overrides, :value},
        {"road_setback", :road_setback, :value},
        {"pedestrian_width", :pedestrian_width, :value},
        {"ratio_mode", :ratio_mode, :value}
      ],
      required: [],
      extra?: false,
      omit_nil?: false
    }
  end
end

defmodule Sbim.Options.UnitSpec do
  @type t :: %__MODULE__{
          units_per_floor: integer() | nil,
          units_by_level: %{optional(String.t()) => integer()},
          max_net_area: number() | nil
        }

  defstruct [
    # 기준 층당 세대 수. None=첫수표가 정한다 — 층마다 (바닥−코어)/max_net_area 를 반올림한
    # 수(최소 1): 전용 상한 안에서 가장 큰 세대(building-generator #436).
    # empty: auto
    units_per_floor: nil,
    # 층별 세대 수 override. 예: {1: 0, 2: 4, 3: 4, 4: 4, 5: 3}. 1층=피로티면 0.
    # units_per_floor보다 우선. 빈 층은 첫수표가 정한다.
    # empty: auto
    units_by_level: %{},
    # 세대 전용면적 상한(㎡, 발코니 제외). 넘는 세대가 나오면 컴파일 에러 UnitAreaExceeded. 기본
    # 60 = 소형주택 선(2026-08-28 변경, 이전 기본은 84). 단지형 다세대(도시형생활주택 전용 85㎡
    # 이하)로 지을 땐 84, 면적 제한 없는 용도는 None. 상한이 없으면 분할 실패가 조용히 통과한다
    # — 실측: 상한 없이 돌린 9,067세대 중 84 초과 722(8.0%), 최대 5,431㎡(층 전체가 1세대).
    # empty: default
    max_net_area: 60.0
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `{:error, {:unknown_keys, 경로, 키들}}` 다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 은 null 로 낸다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"units_per_floor", :units_per_floor, :value},
        {"units_by_level", :units_by_level, :value},
        {"max_net_area", :max_net_area, :value}
      ],
      required: [],
      extra?: false,
      omit_nil?: false
    }
  end
end

defmodule Sbim.Options.Design do
  @moduledoc ~S"""
  이 설계에서 고르는 것.

  비울 수 있는 필드는 전부 비웠을 때 누가 정하는지를 `json_schema_extra={"empty": …}`
  하나로 적는다 — `auto`=첫수표가 채운다(ResolvedDesign 에 나온다), `law`=법이 정한다,
  `default`=적힌 sbim 기본값. `AUTO_FIELDS`가 auto 집합이다.

  묶음은 **대상**이다(매스·세대·코어·주차·동선·외장) — 단계로 자르면 같은 대상의
  속성이 두 집에 나뉘어 산다(구 GroundFloor가 주차·코어·동선·기둥을 한 서랍에 담았다).
  """

  @type t :: %__MODULE__{
          massing: Sbim.Options.Massing.t(),
          units: Sbim.Options.UnitSpec.t(),
          core: Sbim.Options.Core.t(),
          parking: Sbim.Options.Parking.t(),
          circulation: Sbim.Options.Circulation.t(),
          exterior: Sbim.Options.Exterior.t(),
          structure: String.t(),
          regulations: Sbim.Options.RegulationOverrides.t()
        }

  defstruct [
    massing: %Sbim.Options.Massing{},
    units: %Sbim.Options.UnitSpec{},
    core: %Sbim.Options.Core{},
    parking: %Sbim.Options.Parking{},
    circulation: %Sbim.Options.Circulation{},
    exterior: %Sbim.Options.Exterior{},
    # 구조 방식 — wall=벽식(현행 다세대 표준)·rahmen=라멘(기둥·보)·steel=철골. 층고와 벽
    # 두께·스팬 기본값이 여기서 derive된다(Standards에서 override 가능). 한 필드 클래스였던
    # Structure를 스칼라로 폈다.
    # 값: "wall" | "rahmen" | "steel"
    structure: "wall",
    regulations: %Sbim.Options.RegulationOverrides{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `{:error, {:unknown_keys, 경로, 키들}}` 다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 은 null 로 낸다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"massing", :massing, {:model, Sbim.Options.Massing}},
        {"units", :units, {:model, Sbim.Options.UnitSpec}},
        {"core", :core, {:model, Sbim.Options.Core}},
        {"parking", :parking, {:model, Sbim.Options.Parking}},
        {"circulation", :circulation, {:model, Sbim.Options.Circulation}},
        {"exterior", :exterior, {:model, Sbim.Options.Exterior}},
        {"structure", :structure, :value},
        {"regulations", :regulations, {:model, Sbim.Options.RegulationOverrides}}
      ],
      required: [],
      extra?: false,
      omit_nil?: false
    }
  end
end

defmodule Sbim.Options.Dimensions do
  @moduledoc ~S"""
  구조 치수 표준 — 사업마다 고르는 값이 아니라 회사가 정해 두는 값.

  주차 칸·차로 치수(2.5×5.0·6.0)는 주차장법 상수라 엔진이 갖는다 — 옵션이 아니다.
  """

  @type t :: %__MODULE__{
          max_span: number(),
          cantilever: number(),
          min_col_dist: number()
        }

  defstruct [
    # 기둥 최대 간격 (m). 소장 템플릿 T꺾임 8.1 수용, 2026-10-11 선장 결정.
    max_span: 8.1,
    # 코너 캔틸레버 한계 (m). 매스 코너에서 가장 가까운 지지(기둥·벽)까지의 거리를 축별로 재어
    # 수직·벽따라 중 큰 쪽이 이 값 이하여야 한다. GT 1층 203장 중 193장이 3 m 이하(실측).
    cantilever: 3.0,
    # 기둥 최소 간격 (m).
    min_col_dist: 3.0
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `{:error, {:unknown_keys, 경로, 키들}}` 다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 은 null 로 낸다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"max_span", :max_span, :value},
        {"cantilever", :cantilever, :value},
        {"min_col_dist", :min_col_dist, :value}
      ],
      required: [],
      extra?: false,
      omit_nil?: false
    }
  end
end

defmodule Sbim.Options.KitchenFinish do
  @moduledoc ~S"""
  주방 마감 넷 — 오픈키친이라 거실과 같은 바닥·천장, 싱크 상부만 타일.
  """

  @type t :: %__MODULE__{
          floor: String.t(),
          wall: String.t(),
          ceiling: String.t(),
          ceiling_h: number()
        }

  defstruct [
    # 바닥 마감 이름.
    floor: "강마루10",
    # 벽 마감 이름.
    wall: "실크벽지 (싱크 상부 벽타일)",
    # 천장 마감 이름.
    ceiling: "실크벽지",
    # 천장고 (m).
    ceiling_h: 2.3
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `{:error, {:unknown_keys, 경로, 키들}}` 다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 은 null 로 낸다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"floor", :floor, :value},
        {"wall", :wall, :value},
        {"ceiling", :ceiling, :value},
        {"ceiling_h", :ceiling_h, :value}
      ],
      required: [],
      extra?: false,
      omit_nil?: false
    }
  end
end

defmodule Sbim.Options.LivingFinish do
  @moduledoc ~S"""
  거실 마감 넷 — 욕실·주방 외 남는 면적 전부(침실 분할 전). 천장고 2.3 은 층고 2.9·슬래브
  150·바닥 구성 120 뒤의 값.
  """

  @type t :: %__MODULE__{
          floor: String.t(),
          wall: String.t(),
          ceiling: String.t(),
          ceiling_h: number()
        }

  defstruct [
    # 바닥 마감 이름.
    floor: "강마루10",
    # 벽 마감 이름.
    wall: "실크벽지",
    # 천장 마감 이름.
    ceiling: "실크벽지",
    # 천장고 (m).
    ceiling_h: 2.3
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `{:error, {:unknown_keys, 경로, 키들}}` 다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 은 null 로 낸다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"floor", :floor, :value},
        {"wall", :wall, :value},
        {"ceiling", :ceiling, :value},
        {"ceiling_h", :ceiling_h, :value}
      ],
      required: [],
      extra?: false,
      omit_nil?: false
    }
  end
end

defmodule Sbim.Options.Finishes do
  @moduledoc ~S"""
  실내 마감 표준 — 방 용도마다 하나. 엔진이 `units.rooms[]` 의 마감 넷을 여기서
  채운다(building-generator #577).

  착공신고 마감재료표(건축법 시행규칙 별표 4의2)와 내역서 마감 공종(수장·타일·미장, 금액의 약 35
  %)의 전제.
  기본값은 **초안**이다 — 류상호 BIMx 샘플(2026-07, 욕실 바닥 방통40/타일10 · 벽 방수석고보드 위
  타일)과
  구의동 57-93 slab layers(강마루10)에서 뽑았고 소장 확인 전이다. 사업마다 고르는 값이 아니라
  회사가 정해 두는 값이라
  `standards` 에 둔다. 지금 엔진이 내는 방은 욕실·주방·거실 셋뿐이라 그 셋만 있다 — 침실·현관이
  생기면 같은 꼴로 늘린다.
  """

  @type t :: %__MODULE__{
          bath: Sbim.Options.BathFinish.t(),
          kitchen: Sbim.Options.KitchenFinish.t(),
          living: Sbim.Options.LivingFinish.t()
        }

  defstruct [
    # 욕실.
    bath: %Sbim.Options.BathFinish{},
    # 주방.
    kitchen: %Sbim.Options.KitchenFinish{},
    # 거실.
    living: %Sbim.Options.LivingFinish{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `{:error, {:unknown_keys, 경로, 키들}}` 다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 은 null 로 낸다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"bath", :bath, {:model, Sbim.Options.BathFinish}},
        {"kitchen", :kitchen, {:model, Sbim.Options.KitchenFinish}},
        {"living", :living, {:model, Sbim.Options.LivingFinish}}
      ],
      required: [],
      extra?: false,
      omit_nil?: false
    }
  end
end

defmodule Sbim.Options.Standards do
  @moduledoc ~S"""
  회사 표준 — 사업마다 안 건드리는 값. 소비 UI는 접어 둘 수 있다.
  """

  @type t :: %__MODULE__{
          concrete: Sbim.Options.Concrete.t(),
          dimensions: Sbim.Options.Dimensions.t(),
          finishes: Sbim.Options.Finishes.t()
        }

  defstruct [
    concrete: %Sbim.Options.Concrete{},
    dimensions: %Sbim.Options.Dimensions{},
    finishes: %Sbim.Options.Finishes{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `{:error, {:unknown_keys, 경로, 키들}}` 다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 은 null 로 낸다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"concrete", :concrete, {:model, Sbim.Options.Concrete}},
        {"dimensions", :dimensions, {:model, Sbim.Options.Dimensions}},
        {"finishes", :finishes, {:model, Sbim.Options.Finishes}}
      ],
      required: [],
      extra?: false,
      omit_nil?: false
    }
  end
end

defmodule Sbim.Options.BuildOptions do
  @moduledoc ~S"""
  다세대주택 파라메트릭 설계 입력 — 속성 창.

  세 묶음이다: `design`(이 설계에서 고르는 것) · `standards`(회사 표준) ·
  `business`(사업성). 도면 하나를 만들 때 마주하는 건 `design`뿐이다.

  구 평면 모양(`ground_floor`·`concrete`·`schedule` …)으로 들어와도 받아서 옮긴다.
  """

  @type t :: %__MODULE__{
          land_ids: [String.t()],
          primary_land_id: String.t(),
          design: Sbim.Options.Design.t(),
          standards: Sbim.Options.Standards.t(),
          business: Sbim.Options.Business.t()
        }

  defstruct [
    # 합필 필지 PNU 리스트 (19자리). 단일 필지면 [pnu] 1개. 다중 필지는 합필(union) 전제 —
    # 컴파일러가 geometry union 후 처리.
    land_ids: [],
    # 대표 필지 PNU. 보고서·Studio의 '대표 주소' 출처. land_ids 중 하나여야 함. 빈 문자열이면
    # land_ids[0] 사용.
    primary_land_id: "",
    design: %Sbim.Options.Design{},
    standards: %Sbim.Options.Standards{},
    business: %Sbim.Options.Business{}
  ]

  @doc "문자열 키 map → struct(중첩 재귀). 스키마에 없는 키는 `{:error, {:unknown_keys, 경로, 키들}}` 다."
  @spec from_map(map()) :: {:ok, t()} | {:error, term()}
  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)

  @spec from_map!(map()) :: t()
  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)

  @doc "struct → 문자열 키 map(중첩 재귀). nil 은 null 로 낸다."
  @spec to_map(t()) :: map()
  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)

  @doc false
  def __shape__ do
    %{
      fields: [
        {"land_ids", :land_ids, :value},
        {"primary_land_id", :primary_land_id, :value},
        {"design", :design, {:model, Sbim.Options.Design}},
        {"standards", :standards, {:model, Sbim.Options.Standards}},
        {"business", :business, {:model, Sbim.Options.Business}}
      ],
      required: [],
      extra?: false,
      omit_nil?: false
    }
  end
end
