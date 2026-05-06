"""BuildOptions — 다세대주택 파라메트릭 설계 입력 (sbim 단일 진실).

Pydantic v2 BaseModel. 각 Field의 description이 LLM에게 전달되는 schema.
docstring 따로 관리 안 함 — Field description이 곧 LLM 입력.

흐름:
    BuildOptions (입력) ──→ volume_suggestion 컴파일 ──→ Scheme (출력)

설계 사고:
    1. BusinessGoals  — 분양/임대, 평형, 자가
    2. Massing        — 층수·층고·1층용도·옥상
    3. CoreSpec       — 코어 위치·계단·EV
    4. UnitSpec       — 세대 수·평면·베이·발코니 (층별 override 가능)
    5. FacadeSpec     — 재료·창 패턴
    6. ParkingSpec    — 방식·대수
    7. AmenitiesSpec  — 부속 시설
    8. RegulationOverrides — 사선·일조·BCR·FAR 수동 조정
    9. FinancialSpec  — 시공비·분양가·LTV
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# ═════════════════════════════════════════════════════════════════════
# 타입 별칭
# ═════════════════════════════════════════════════════════════════════

BusinessModel = Literal["sale", "rental", "mixed", "self_use"]
TargetSegment = Literal["studio", "one_room", "small_family", "middle_family", "luxury"]
FloorUse = Literal[
    "piloti", "residential", "commercial", "rooftop_garden",
    "rooftop_unit", "basement_parking", "basement_storage",
]
CorePosition = Literal[
    "auto", "central", "left", "right", "north", "south",
    "near_corner", "near_road",
]
CoreType = Literal["stair_only", "stair_ev", "double_stair"]
CorridorType = Literal["auto", "central_corridor", "single_loaded", "double_loaded"]
PlanType = Literal[
    "studio", "one_one", "one_room", "two_room", "three_room", "penthouse",
]
BalconyMode = Literal["expanded", "non_expanded", "none"]
FacadeMaterial = Literal[
    "brick", "exposed_concrete", "stucco", "metal_panel",
    "ceramic_panel", "composite", "wood",
]
WindowPattern = Literal[
    "grid", "ribbon", "punched", "vertical_strip", "asymmetric",
]
ParkingMode = Literal[
    "auto", "piloti", "underground", "mechanical", "surface", "ev_only",
]


# ═════════════════════════════════════════════════════════════════════
# 1. BusinessGoals — 모든 결정의 출발점
# ═════════════════════════════════════════════════════════════════════


class BusinessGoals(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: BusinessModel = Field(
        default="sale",
        description="분양/임대/혼합/자가. 자가 사용 펜트하우스면 'self_use'.",
    )
    target_segment: TargetSegment = Field(
        default="small_family",
        description=(
            "타겟 평형. studio=18~25㎡, one_room=26~40, small_family=41~60, "
            "middle_family=61~85, luxury=86㎡+."
        ),
    )
    self_use_floor: Optional[int] = Field(
        default=None,
        description="자가 거주층 (예: 6 = 6층 펜트하우스 거주). None이면 전체 분양/임대.",
    )
    target_total_units: Optional[int] = Field(
        default=None,
        description="전체 세대 수 목표. None이면 면적 기반 자동.",
    )
    target_avg_unit_area: Optional[float] = Field(
        default=None,
        description="평균 전용면적 (㎡). None이면 segment 기반 default.",
    )
    budget_construction: Optional[float] = Field(
        default=None,
        description="시공비 예산 한도 (원). None이면 무제한.",
    )


# ═════════════════════════════════════════════════════════════════════
# 2. Massing — 매스
# ═════════════════════════════════════════════════════════════════════


class Massing(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_floor_count: Optional[int] = Field(
        default=None,
        description="목표 층수. None이면 사선·일조·FAR 한계까지 자동 stack.",
    )
    floor_height: float = Field(
        default=3.3,
        description="기준 층고 (m). 다세대 표준 3.0~3.3.",
    )
    first_floor_height: Optional[float] = Field(
        default=None,
        description="1층 층고 (m). 필로티는 4m+ 권장. None이면 floor_height와 동일.",
    )
    rooftop_floor_height: Optional[float] = Field(
        default=None,
        description="옥상층 (펜트하우스) 층고 (m). None이면 floor_height.",
    )
    floor_use: dict[int, FloorUse] = Field(
        default_factory=dict,
        description=(
            "층번호 → 용도. 예: {1: 'piloti', 6: 'rooftop_unit'}. "
            "미지정 시 1층=piloti, 그 외=residential."
        ),
    )
    has_basement: bool = Field(
        default=False,
        description="지하층 여부 (지하주차 등).",
    )
    has_rooftop_unit: bool = Field(
        default=False,
        description="최상층을 펜트하우스로 활용 (작게 + 테라스).",
    )
    far_utilization_target: float = Field(
        default=0.95,
        description="FAR 활용률 목표 (0~1). 1.0=한도 모두 사용, 0.9=90%만.",
        ge=0,
        le=1,
    )


# ═════════════════════════════════════════════════════════════════════
# 3. CoreSpec — 코어
# ═════════════════════════════════════════════════════════════════════


class CoreSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    position: CorePosition = Field(
        default="auto",
        description="코어 위치 정책. 'auto'면 필지 형상 기반 자동 결정.",
    )
    custom_position: Optional[tuple[float, float]] = Field(
        default=None,
        description="수동 좌표 (x, y) — position 무시하고 직접 지정.",
    )
    core_type: CoreType = Field(
        default="stair_ev",
        description=(
            "stair_only(계단만)·stair_ev(계단+EV, 6층 이상 필수)·double_stair(2개 계단)."
        ),
    )
    stair_size: tuple[float, float] = Field(
        default=(3.0, 5.5),
        description="계단실 크기 (width, depth) m. 법정 1.2m 통과 폭 포함.",
    )
    elevator_size: tuple[float, float] = Field(
        default=(2.0, 2.5),
        description="EV 사이즈 (width, depth) m. 표준 8인승.",
    )
    corridor_type: CorridorType = Field(
        default="auto",
        description="편복도 / 중복도 / 자동.",
    )
    corridor_width: float = Field(
        default=1.2,
        description="복도 폭 (m). 법정 1.2m 이상.",
    )


# ═════════════════════════════════════════════════════════════════════
# 4. UnitSpec — 세대 (층별 override 지원)
# ═════════════════════════════════════════════════════════════════════


class UnitSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # 균등 default
    units_per_floor: Optional[int] = Field(
        default=None,
        description="기준 층당 세대 수. None이면 면적 기반 자동.",
    )
    plan_mix: Optional[list[PlanType]] = Field(
        default=None,
        description="기준 평면 mix. 예: ['two_room','two_room','three_room']. None=균등.",
    )
    bay_count: Optional[int] = Field(
        default=None,
        description="기준 베이 수. 2bay=일반, 3bay=고급. None=평형별 default.",
    )

    # 층별 override
    units_by_level: dict[int, int] = Field(
        default_factory=dict,
        description=(
            "층별 세대 수 override. 예: {1: 0, 2: 4, 3: 4, 4: 4, 5: 3, 6: 1}. "
            "1층=피로티면 0, 5층=사선제한, 6층=펜트하우스."
        ),
    )
    plan_mix_by_level: dict[int, list[PlanType]] = Field(
        default_factory=dict,
        description="층별 평면 mix override (예: 옥상층은 ['penthouse']).",
    )
    bay_count_by_level: dict[int, int] = Field(
        default_factory=dict,
        description="층별 베이 override.",
    )

    # 발코니
    balcony_mode: BalconyMode = Field(
        default="expanded",
        description="확장형(거실·방이 흡수) / 비확장형 / 없음.",
    )
    balcony_depth: float = Field(
        default=1.5,
        description="발코니 깊이 (m). 0이면 없음.",
    )
    balcony_depth_by_level: dict[int, float] = Field(
        default_factory=dict,
        description="층별 발코니 깊이 (옥상=테라스로 깊게 가능).",
    )

    has_alpha_room: bool = Field(default=False, description="알파룸 (소형 별실) 여부.")
    has_dress_room: bool = Field(default=False, description="드레스룸 여부.")

    # ─── 헬퍼 ─────────────────────────────────────────────────────

    def get_units_for_level(
        self, level: int, floor_use: FloorUse | None = None
    ) -> int:
        """특정 층의 세대 수.

        우선순위: units_by_level > 비주거 층=0 > units_per_floor > 0.
        """
        if level in self.units_by_level:
            return self.units_by_level[level]
        if floor_use in (
            "piloti", "commercial", "basement_parking",
            "basement_storage", "rooftop_garden",
        ):
            return 0
        return self.units_per_floor or 0

    def get_plan_mix_for_level(self, level: int) -> list[PlanType] | None:
        if level in self.plan_mix_by_level:
            return self.plan_mix_by_level[level]
        return self.plan_mix

    def get_bay_count_for_level(self, level: int) -> int | None:
        if level in self.bay_count_by_level:
            return self.bay_count_by_level[level]
        return self.bay_count

    def get_balcony_depth_for_level(self, level: int) -> float:
        if level in self.balcony_depth_by_level:
            return self.balcony_depth_by_level[level]
        return self.balcony_depth


# ═════════════════════════════════════════════════════════════════════
# 5. FacadeSpec — 외관
# ═════════════════════════════════════════════════════════════════════


class FacadeSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary_material: FacadeMaterial = Field(
        default="brick",
        description="주재료. 다세대 표준은 brick.",
    )
    accent_material: Optional[FacadeMaterial] = Field(
        default=None,
        description="포인트 재료 (저층부 등).",
    )
    window_pattern: WindowPattern = Field(
        default="punched",
        description=(
            "grid=균등격자, ribbon=가로 띠창, punched=구멍창, "
            "vertical_strip=세로 띠창, asymmetric=비대칭."
        ),
    )
    window_to_wall_ratio: dict[str, float] = Field(
        default_factory=dict,
        description="면별 창 면적 비율. 예: {'south': 0.5, 'north': 0.2}. 채광 1/10 자동.",
    )
    primary_color: str = Field(
        default="#FFFFFF",
        description="주색 헥스 코드.",
    )


# ═════════════════════════════════════════════════════════════════════
# 6. ParkingSpec — 주차
# ═════════════════════════════════════════════════════════════════════


class ParkingSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: ParkingMode = Field(
        default="auto",
        description="필지 면적·세대 수 기반 자동. piloti=200㎡ 미만 권장.",
    )
    additional_count: int = Field(
        default=0,
        description="법정 외 추가 주차 대수.",
    )
    ev_charging_ratio: float = Field(
        default=0.05,
        description="전기차 충전 비율 (의무 5%).",
        ge=0,
        le=1,
    )


# ═════════════════════════════════════════════════════════════════════
# 7. AmenitiesSpec — 부속 시설
# ═════════════════════════════════════════════════════════════════════


class AmenitiesSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rooftop_garden: bool = Field(default=False, description="옥상정원.")
    common_lounge: bool = Field(default=False, description="1층 공용 라운지.")
    bicycle_storage: bool = Field(default=True, description="자전거 거치대.")
    parcel_locker: bool = Field(default=True, description="택배함.")
    cctv: bool = Field(default=True, description="CCTV (사실상 의무).")


# ═════════════════════════════════════════════════════════════════════
# 8. RegulationOverrides — 법규 오버라이드
# ═════════════════════════════════════════════════════════════════════


class RegulationOverrides(BaseModel):
    model_config = ConfigDict(extra="forbid")

    setback_overrides: dict[str, float] = Field(
        default_factory=dict,
        description="방향별 후퇴거리 (m). 예: {'north': 1.5, 'side': 0.8}.",
    )
    far_target: Optional[float] = Field(
        default=None,
        description="목표 용적률 (%). zone 한도 이하만. None=zone 한도.",
    )
    bcr_target: Optional[float] = Field(
        default=None,
        description="목표 건폐율 (%). None=zone 한도.",
    )
    height_limit: Optional[float] = Field(
        default=None,
        description="수동 높이 한계 (m). None=사선·일조 자동.",
    )


# ═════════════════════════════════════════════════════════════════════
# 9. FinancialSpec — 시공·수익
# ═════════════════════════════════════════════════════════════════════


class FinancialSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    construction_cost_per_sqm: Optional[float] = Field(
        default=None,
        description="시공비 단가 (원/㎡). None이면 시장 평균.",
    )
    sale_price_per_sqm: Optional[float] = Field(
        default=None,
        description="분양가 단가 (원/㎡). None이면 인근 시세.",
    )
    rental_per_sqm_monthly: Optional[float] = Field(
        default=None,
        description="월 임대료 (원/㎡).",
    )
    pf_ltv: float = Field(
        default=0.7,
        description="PF 대출 LTV. 통상 0.6~0.8.",
        ge=0,
        le=1,
    )
    target_yield: Optional[float] = Field(
        default=None,
        description="목표 수익률 (%). None이면 분석만.",
    )


# ═════════════════════════════════════════════════════════════════════
# Top-level — BuildOptions
# ═════════════════════════════════════════════════════════════════════


class BuildOptions(BaseModel):
    """다세대주택 파라메트릭 설계 입력 — 단일 진실.

    모든 카테고리는 default일 때 자동 결정. 채울수록 사용자 의도 반영.

    LangChain @tool에 args_schema=BuildOptions로 등록 시 자연어 → BuildOptions 자동.
    Pydantic Field description이 LLM에게 전달되는 schema. docstring 따로 관리 X.
    """

    model_config = ConfigDict(extra="forbid")

    land_id: str = Field(
        default="",
        description="필지 ID (PNU 또는 land_id).",
    )

    business: BusinessGoals = Field(default_factory=BusinessGoals)
    massing: Massing = Field(default_factory=Massing)
    core: CoreSpec = Field(default_factory=CoreSpec)
    units: UnitSpec = Field(default_factory=UnitSpec)
    facade: FacadeSpec = Field(default_factory=FacadeSpec)
    parking: ParkingSpec = Field(default_factory=ParkingSpec)
    amenities: AmenitiesSpec = Field(default_factory=AmenitiesSpec)
    regulations: RegulationOverrides = Field(default_factory=RegulationOverrides)
    financial: FinancialSpec = Field(default_factory=FinancialSpec)

    notes: str = Field(default="", description="주석 (디버깅·로깅용).")

    # ─── 편의 메서드 ────────────────────────────────────────────────

    def get_floor_use(self, level: int) -> FloorUse:
        """특정 층의 용도. 명시 안 됐으면 룰."""
        if level in self.massing.floor_use:
            return self.massing.floor_use[level]
        if level == 1:
            return "piloti"
        if (
            level == self.massing.target_floor_count
            and self.massing.has_rooftop_unit
        ):
            return "rooftop_unit"
        return "residential"

    def get_floor_height(self, level: int) -> float:
        """층별 층고 (1층·옥상 별도 가능)."""
        if level == 1 and self.massing.first_floor_height is not None:
            return self.massing.first_floor_height
        if (
            level == self.massing.target_floor_count
            and self.massing.rooftop_floor_height is not None
        ):
            return self.massing.rooftop_floor_height
        return self.massing.floor_height

    def get_first_floor_ratio(self, default: float = 0.15) -> float:
        """1층 면적 비율. 필로티는 작게, 상가는 크게."""
        floor_use_1 = self.get_floor_use(1)
        if floor_use_1 == "piloti":
            return default
        if floor_use_1 == "commercial":
            return 0.6
        return default

    def get_upper_floor_ratio(self, default: float) -> float:
        """상층 면적 비율."""
        if self.regulations.bcr_target is not None:
            return self.regulations.bcr_target / 100
        return default
