"""BuildOptions — 다세대주택 파라메트릭 설계 입력 (sbim 단일 진실).

컴파일러(volume_suggestion)가 실제 읽는 필드만 정의. 미구현 카테고리는 빠짐.
필드 추가는 컴파일러 구현과 함께. docstring drift 방지 위해 Field description이 곧 LLM 스키마.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


FloorUse = Literal[
    "piloti", "residential", "commercial", "rooftop_garden",
    "basement_parking", "basement_storage",
]


# ═════════════════════════════════════════════════════════════════════
# Massing — 매스
# ═════════════════════════════════════════════════════════════════════


class Massing(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_floor_count: Optional[int] = Field(
        default=None,
        description="목표 층수. None=사선·일조·FAR 한계까지 자동 stack. 사선제한으로 미달 가능.",
    )
    floor_height: float = Field(
        default=3.3,
        description="기준 층고 (m). 다세대 표준 3.0~3.3.",
    )
    first_floor_height: Optional[float] = Field(
        default=None,
        description="1층 층고 (m). 필로티 4m+ 권장. None이면 floor_height와 동일.",
    )
    floor_use: dict[int, FloorUse] = Field(
        default_factory=dict,
        description=(
            "층번호 → 용도. 예: {1: 'piloti'}. "
            "미지정 시 1층=piloti, 그 외=residential."
        ),
    )


# ═════════════════════════════════════════════════════════════════════
# UnitSpec — 세대
# ═════════════════════════════════════════════════════════════════════


class UnitSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    units_per_floor: Optional[int] = Field(
        default=None,
        description="기준 층당 세대 수. None=면적 기반 자동(45㎡/세대).",
    )
    units_by_level: dict[int, int] = Field(
        default_factory=dict,
        description=(
            "층별 세대 수 override. 예: {1: 0, 2: 4, 3: 4, 4: 4, 5: 3}. "
            "1층=피로티면 0. units_per_floor보다 우선."
        ),
    )

    def get_units_for_level(
        self, level: int, floor_use: FloorUse | None = None
    ) -> int:
        """우선순위: units_by_level > 비주거 층=0 > units_per_floor > 0."""
        if level in self.units_by_level:
            return self.units_by_level[level]
        if floor_use in (
            "piloti", "commercial",
            "basement_parking", "basement_storage", "rooftop_garden",
        ):
            return 0
        return self.units_per_floor or 0


# ═════════════════════════════════════════════════════════════════════
# Core — 코어 (계단·EV)
# ═════════════════════════════════════════════════════════════════════


class Core(BaseModel):
    model_config = ConfigDict(extra="forbid")

    width: Optional[float] = Field(
        default=None,
        description=(
            "코어(계단·EV) 너비 (m, 로컬 X축 = 건물 장변 방향). "
            "None=자동(units_per_floor 기반). "
            "프리셋: 2.8(계단만) / 5.0(계단+EV)."
        ),
    )
    depth: Optional[float] = Field(
        default=None,
        description=(
            "코어 깊이 (m, 로컬 Y축). None=자동. "
            "다세대 기준 5.5 권장."
        ),
    )


# ═════════════════════════════════════════════════════════════════════
# Windows — 외벽 창문
# ═════════════════════════════════════════════════════════════════════


WindowStyle = Literal["open", "standard", "closed"]
WindowPattern = Literal["punched", "horizontal_strip", "corner"]
WindowAlignment = Literal["aligned", "varied"]


class Windows(BaseModel):
    model_config = ConfigDict(extra="forbid")

    style: WindowStyle = Field(
        default="open",
        description=(
            "창 스타일 (크기·WWR·sill 톤). "
            "open=통창형(WWR↑·낮은 sill·높은 창), "
            "standard=다세대 표준, "
            "closed=보수형(WWR↓·작은 창)."
        ),
    )
    pattern: WindowPattern = Field(
        default="corner",
        description=(
            "창 배치 디자인 언어. "
            "punched=벽에 구멍식 통창(다세대 표준), "
            "horizontal_strip=가로 띠 창(르 코르뷔지에 fenêtre en longueur), "
            "corner=코너 통창 강조(모더니즘)."
        ),
    )
    alignment: WindowAlignment = Field(
        default="aligned",
        description=(
            "층별 창 위치 정렬. "
            "aligned=모든 층 같은 위치(차분, 전통), "
            "varied=층별 jitter(자연 리듬)."
        ),
    )
    seed: Optional[int] = Field(
        default=None,
        description=(
            "varied jitter용 random seed. None=land 단위로 결정적 자동. "
            "같은 seed면 같은 패턴 재현. aligned면 영향 없음."
        ),
    )


# ═════════════════════════════════════════════════════════════════════
# Pillars — 필로티 기둥
# ═════════════════════════════════════════════════════════════════════


class Pillars(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: Optional[int] = Field(
        default=None,
        description=(
            "1층 필로티 기둥 개수. None=자동(외곽 길이 기반). "
            "프리셋: 4(코너), 6(코너+장변 중간), 8(코너+장변 분할)."
        ),
    )
    size: Optional[float] = Field(
        default=None,
        description="기둥 한 변 크기 (m). None=0.4 (다세대 철골 표준).",
    )


# ═════════════════════════════════════════════════════════════════════
# Parking — 1층 piloti 주차장
# ═════════════════════════════════════════════════════════════════════


ParkingType = Literal["perpendicular", "parallel", "angled_60", "angled_45"]
ParkingRatioMode = Literal["multi_family", "non_residential"]


class Parking(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: Optional[int] = Field(
        default=None,
        description=(
            "주차 stall 수 명시. None=가능한 만큼 자동 배치. "
            "법정 대수는 ratio_mode·세대별 전용면적 기반으로 별도 산출."
        ),
    )
    stall_width: float = Field(
        default=2.5,
        description="stall 너비 (m). 법정 일반형 2.5, 확장형 2.6.",
    )
    stall_depth: float = Field(
        default=5.0,
        description="stall 길이 (m). 법정 일반형 5.0.",
    )
    aisle_width: float = Field(
        default=6.0,
        description="통로 너비 (m). 직각주차 양방향 6.0.",
    )
    type: ParkingType = Field(
        default="perpendicular",
        description="배치 형식. perpendicular=직각주차(default).",
    )
    ratio_mode: ParkingRatioMode = Field(
        default="multi_family",
        description=(
            "법정 주차대수 산정 기준 (서울시 주차장 조례). "
            "multi_family=공동주택(도시형생활주택·다세대): "
            "30㎡↓ 0.5대, 30~60㎡ 0.8대, 60㎡↑ 1.0대, 합계 올림. "
            "non_residential=비공동주택(근생·다가구·다중): "
            "60㎡↓ 0.5대, 60㎡↑ 0.7대, 합계 반올림."
        ),
    )


# ═════════════════════════════════════════════════════════════════════
# Concrete — 콘크리트 두께·단가
# ═════════════════════════════════════════════════════════════════════


class Concrete(BaseModel):
    model_config = ConfigDict(extra="forbid")

    wall_thickness: float = Field(
        default=0.20,
        description="외벽 두께 (m). 다세대 표준 0.20 (단열 포함).",
    )
    slab_thickness: float = Field(
        default=0.20,
        description="슬래브 두께 (m). 5층↑ 표준 0.20.",
    )
    interior_wall_thickness: float = Field(
        default=0.10,
        description="내벽 두께 (m). 표준 0.10. LOD 200엔 미반영.",
    )
    column_size: float = Field(
        default=0.40,
        description="기둥 단면 한 변 (m). 다세대 철골 표준 0.40 정사각.",
    )
    price_per_m3: int = Field(
        default=3_500_000,
        description=(
            "콘크리트 ㎥당 단가 (원). 다세대 표준 350만원. "
            "공사비 = total_m3 × price_per_m3."
        ),
    )


# ═════════════════════════════════════════════════════════════════════
# Exterior — 외장재 색상 (시각화 전용, 비용·구조 영향 X)
# ═════════════════════════════════════════════════════════════════════


ExteriorStyle = Literal["white", "sandstone", "brick", "concrete"]


class Exterior(BaseModel):
    model_config = ConfigDict(extra="forbid")

    style: ExteriorStyle = Field(
        default="brick",
        description=(
            "외장재 preset (외벽·천장/테라스 색 페어). "
            "white=화이트·라이트그레이, sandstone=사암·웜그레이, "
            "brick=벽돌브라운·라이트그레이(default), concrete=노출콘크리트·짙은회색. "
            "visualizer가 hex로 매핑."
        ),
    )


# ═════════════════════════════════════════════════════════════════════
# RegulationOverrides — 법규 오버라이드
# ═════════════════════════════════════════════════════════════════════


class RegulationOverrides(BaseModel):
    model_config = ConfigDict(extra="forbid")

    far_target: Optional[float] = Field(
        default=None,
        description="목표 용적률 (%). zone 한도 이하만. None=zone 한도 사용.",
    )
    bcr_target: Optional[float] = Field(
        default=None,
        description="목표 건폐율 (%). None=zone 한도 사용.",
    )
    setback_overrides: dict[str, float] = Field(
        default_factory=dict,
        description="방향별 후퇴거리 (m). 예: {'north': 1.5, 'side': 0.8}.",
    )


# ═════════════════════════════════════════════════════════════════════
# Spatial Layout — 1층 piloti의 코어·기둥·주차·입구 직접 지정 (round-trip)
# ═════════════════════════════════════════════════════════════════════
#
# 모든 좌표계: sBIM Local CRS
#   origin = parcel_center (lat/lng → projected EPSG:5186)
#   +x = 동, +y = 북
#   unit = meter
#
# scheme.json output의 `_core_layout` / `_parking_stalls` / `_column_centers`
# 형식과 동일 → compile 결과를 그대로 BuildOptions input으로 재사용 가능.
# 사용자/LLM이 GUI에서 drag로 편집한 결과도 같은 형식.
#
# None 또는 빈 값이면 컴파일러가 자동 결정 (현재 동작).
# ═════════════════════════════════════════════════════════════════════


class CoreLayout(BaseModel):
    """코어 세분 polygon — EV·계단·복도. parcel_center 상대 local m."""
    model_config = ConfigDict(extra="forbid")

    ev: list[tuple[float, float]] = Field(
        default_factory=list,
        description="EV polygon (closed ring). 예: [[x1,y1], [x2,y2], ...].",
    )
    stair: list[tuple[float, float]] = Field(
        default_factory=list,
        description="계단 polygon (closed ring).",
    )
    corridor: list[tuple[float, float]] = Field(
        default_factory=list,
        description="복도 polygon (closed ring). 각 세대가 corridor edge 공유 필요.",
    )


class Entrance(BaseModel):
    """보행자 입구 — 도로 → 코어 동선 (선분).

    LOD 200: 시각·평면도 표시용. compile 영향 X (다음 라운드 4각 검증 도입 시).
    """
    model_config = ConfigDict(extra="forbid")

    line: list[tuple[float, float]] = Field(
        default_factory=list,
        description=(
            "도로면 → 코어 진입 동선. [(start_x, start_y), (end_x, end_y)]. "
            "start는 도로면, end는 코어 경계 권장."
        ),
    )


class SpatialLayout(BaseModel):
    """선택 spatial input — scheme.json output 형식 그대로 받음 (round-trip).

    각 필드 None/빈 값 → 컴파일러 자동 결정 (현재 동작 유지).
    명시 → 컴파일러가 그대로 사용 + 충돌 검증.

    좌표계: parcel_center 원점, +x 동, +y 북, 단위 m (sBIM Local CRS).
    """
    model_config = ConfigDict(extra="forbid")

    core_layout: Optional[CoreLayout] = Field(
        default=None,
        description=(
            "코어 EV/계단/복도 polygon. None=자동 (Core.width·depth 기반). "
            "명시 시 Core.width·depth 무시하고 직접 사용."
        ),
    )
    column_centers: list[tuple[float, float]] = Field(
        default_factory=list,
        description=(
            "필로티 기둥 중심점 list. 빈 list=자동 (Pillars.count 기반). "
            "명시 시 Pillars.count 무시하고 직접 사용."
        ),
    )
    parking_stalls: list[list[tuple[float, float]]] = Field(
        default_factory=list,
        description=(
            "주차 stall polygon list. 각 stall = closed ring (보통 4점). "
            "빈 list=자동 (Parking.count + grid packing). "
            "명시 시 Parking.count 무시하고 직접 사용."
        ),
    )
    entrance: Optional[Entrance] = Field(
        default=None,
        description="보행자 입구 (도로→코어 동선). None=시각 표시 안 함.",
    )


# ═════════════════════════════════════════════════════════════════════
# Top-level — BuildOptions
# ═════════════════════════════════════════════════════════════════════


class BuildOptions(BaseModel):
    """다세대주택 파라메트릭 설계 입력.

    컴파일러가 실제 읽는 필드만 포함. 모든 필드 default 시 자동 결정.
    LangChain @tool에 args_schema=BuildOptions로 등록 시 자연어 → BuildOptions 자동.
    """

    model_config = ConfigDict(extra="forbid")

    land_ids: list[str] = Field(
        default_factory=list,
        description=(
            "합필 필지 PNU 리스트 (19자리). 단일 필지면 [pnu] 1개. "
            "다중 필지는 합필(union) 전제 — 컴파일러가 geometry union 후 처리."
        ),
    )
    primary_land_id: str = Field(
        default="",
        description=(
            "대표 필지 PNU. 보고서·Studio의 '대표 주소' 출처. "
            "land_ids 중 하나여야 함. 빈 문자열이면 land_ids[0] 사용."
        ),
    )

    massing: Massing = Field(default_factory=Massing)
    units: UnitSpec = Field(default_factory=UnitSpec)
    core: Core = Field(default_factory=Core)
    pillars: Pillars = Field(default_factory=Pillars)
    windows: Windows = Field(default_factory=Windows)
    parking: Parking = Field(default_factory=Parking)
    concrete: Concrete = Field(default_factory=Concrete)
    exterior: Exterior = Field(default_factory=Exterior)
    regulations: RegulationOverrides = Field(default_factory=RegulationOverrides)
    spatial: SpatialLayout = Field(
        default_factory=SpatialLayout,
        description=(
            "1층 piloti의 코어·기둥·주차·입구 polygon 직접 지정 (round-trip). "
            "각 필드 비우면 자동, 명시하면 그대로 사용."
        ),
    )

    # ─── 헬퍼 ───────────────────────────────────────────────────────

    def get_floor_use(self, level: int) -> FloorUse:
        """특정 층의 용도. floor_use override > 1층=piloti > residential."""
        if level in self.massing.floor_use:
            return self.massing.floor_use[level]
        if level == 1:
            return "piloti"
        return "residential"

    def get_floor_height(self, level: int) -> float:
        """층별 층고. 1층은 first_floor_height 우선."""
        if level == 1 and self.massing.first_floor_height is not None:
            return self.massing.first_floor_height
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
        """상층 면적 비율. bcr_target 우선."""
        if self.regulations.bcr_target is not None:
            return self.regulations.bcr_target / 100
        return default
