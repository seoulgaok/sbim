"""BuildOptions — 다세대주택 파라메트릭 설계 입력 (sbim 단일 진실).

컴파일러가 실제 읽는 필드만 정의. 미구현 카테고리는 빠짐.
필드 추가는 컴파일러 구현과 함께. docstring drift 방지 위해 Field description이 곧 LLM 스키마.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    first_floor_height: Optional[float] = Field(
        default=None,
        description=(
            "1층 층고 (m). 필로티 4m+ 권장. "
            "None이면 구조방식 기본 층고(structure: 벽식 3.0/라멘 3.3)와 동일."
        ),
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
    cut_axis: Optional[Literal["road", "depth"]] = Field(
        default=None,
        description=(
            "세대 분할선 방향 — road=주접도변과 평행(기본 derive, 실측 12/18), "
            "depth=직교. 참조 필지 실측에서 갈리는 설계 의도."
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


CoreComposition = Literal["stair", "stair_elevator"]
CoreType = Literal[1, 2, 3, 4, 5, 6]


class Core(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # width/depth(코어 치수 raw scalar) 제거됨 — 코어 크기/형상은 입력이 아니라
    # **세대분할의 산출물**로 derive(삼전 정답: 계단·EV가 16.4m 분리 = 세대 배치 결과).
    # position/lateral(코어 위치 의도)도 제거됨 — 코어 위치는 입력이 아니라 common(전층
    # 교집합) 안에서 **세대 최대분할**을 실현하는 자리로 derive(servant는 served 최대화의 잔여).
    # 의도는 type(형상)·composition으로만 표현, 위치·치수는 매스+세대프로그램에서 유도.
    type: Optional[CoreType] = Field(
        default=None,
        description=(
            "코어 형상 타입 (DWG→sbim 6코어 라이브러리). None=auto(매스 형상 prior). "
            "1=좁은타워(직선계단)·2=좁은타워(꺾인계단)·3=좌우나란히(계단A)·"
            "4=좌우나란히(계단B)·5=ㄱ자(코너·EV측면)·6=넓은코어. "
            "대부분 type1(좁은 타워, 회전 fit), 넓은 단독 장변접도만 type3/4."
        ),
    )
    composition: CoreComposition = Field(
        default="stair_elevator",
        description=(
            "코어 구성 의도 — 계단·EV 유무. 코어 치수/형상 derive의 입력(세대수와 함께). "
            "stair=계단실만, stair_elevator=계단+승강기."
        ),
    )


# ═════════════════════════════════════════════════════════════════════
# Windows — 외벽 창문
# ═════════════════════════════════════════════════════════════════════


WindowStyle = Literal["open", "standard", "closed"]

# pattern·alignment·seed 제거 — 창 배치가 WWR·jitter 랜덤에서 **법정 채광면적
# 역산**으로 바뀌며(피난방화규칙 17조① 거실 바닥의 1/10, 세대가 실제로 접한
# 외벽에만) 디자인 언어 입력이 소비처를 잃었다. 컴파일러가 안 읽는 필드는 두지
# 않는다. DB 잔재는 프론트엔드 DB 마이그레이션에서 제거됨.


class Windows(BaseModel):
    model_config = ConfigDict(extra="forbid")

    style: WindowStyle = Field(
        default="open",
        description=(
            "창 크기 의도 — 법정 채광면적(거실 바닥의 1/10)을 몇 배로 잡을지의 배율. "
            "open=넉넉(1.8배), standard=표준(1.35배), closed=최소(1.05배). "
            "창의 위치·개수는 세대가 접한 외벽에서 컴파일러가 derive한다."
        ),
    )


# ═════════════════════════════════════════════════════════════════════
# Structure — 구조방식 (벽식 / 라멘)
# ═════════════════════════════════════════════════════════════════════


StructureSystem = Literal["wall", "rahmen", "steel"]

# 구조방식 → 기하 기본값(명시 override 없을 때만). 벽식=현행 기본값(회귀0).
# 라멘/철골은 하중을 기둥이 받아 벽이 얇아짐(전용↑), 철골은 장스팬(넓은 주차·기둥간격).
# 층고는 base_floor_height property에서 별도 derive. 실적치는 보정 노브.
STRUCTURE_PRESET = {
    "wall":   {"wall_thickness": 0.20, "max_span": 8.0,  "min_col_dist": 3.0},
    "rahmen": {"wall_thickness": 0.15, "max_span": 8.0,  "min_col_dist": 3.0},
    "steel":  {"wall_thickness": 0.12, "max_span": 12.0, "min_col_dist": 6.0},
}


class Structure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    system: StructureSystem = Field(
        default="wall",
        description=(
            "구조방식 — 기둥 전략·층고·벽두께·스팬을 derive하는 단일 설계 의도(개수 입력 폐기). "
            "wall=벽식(내력벽): 기둥 = 1층 필로티만(상층은 벽이 하중), 층고 3.0m, 외벽 0.20m. "
            "rahmen=라멘(기둥-보): 기둥 = 전층 구조격자, 층고 3.3m(보 춤↑→정북사선↑→상층면적↓), 외벽 0.15m. "
            "steel=철골: 전층 기둥·장스팬(12m), 층고 3.4m, 외벽 0.12m(건식). "
            "기둥 단면 크기는 concrete.column_size, 개수·위치는 buildable+코어에서 derive."
        ),
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
# GroundFloor — 1층 절차(13단계) 설계 의도
# ═════════════════════════════════════════════════════════════════════


CorridorMode = Literal["carve", "edge"]


class GroundFloor(BaseModel):
    """1층 배치 절차의 설계 의도 — 필지+도로에서 유도 안 되는 잔여만.

    원칙: 모든 필드 Optional/derive 기본값. None = 자동 유도.
    명시 필드가 줄수록 "필지+접도로+옵션 → 정답 유도"가 완성되는 것 —
    reference 정답 필지의 _build_options.json에서 dwg 역산으로 추출된다.
    법정 수치(칸 2.5×5.0·총 8대·그룹 5대 등)는 옵션이 아니라 엔진 상수
    (주차장법 시행규칙 — 법이 정하면 상수, 설계자가 고르면 옵션).
    """

    model_config = ConfigDict(extra="forbid")

    # ── 주차 (P단계) ──
    road_edge: Optional[int] = Field(
        default=None,
        description="주접도 변 인덱스 (필지 폴리곤 기준). None=최장 접도변 자동.",
    )
    entry2: Optional[bool] = Field(
        default=None,
        description=(
            "다중도로 주차 — 주접도 외 잔여 접도변(넓은급→긴변, 최대 3)에 추가 주차. "
            "None=법정 대수 부족 시 자동. (구 '인접 2차 진입'에서 ≤3 도로로 일반화.)"
        ),
    )
    tandem: Optional[bool] = Field(
        default=None,
        description="연접(직렬 2단) 백칸 허용 (제11조⑤4호). None=법정 대수 부족 시 자동.",
    )
    bk_offset: Optional[float] = Field(
        default=None,
        description="백칸 깊이 오프셋 BK (m). None=stall_depth (전면 바로 뒤).",
    )
    interior_aisle: Optional[bool] = Field(
        default=None,
        description=(
            "내부 6m 차로 주차 (internal 모드) — 주도로에서 직각으로 "
            "대지 내부에 6m 차로를 내고 양쪽 직각주차+평행 보강. 차로 확보 = "
            "8대 특례(주차장법 11조⑤) 밖 일반 부설주차장 → 총 8대 캡 비적용. "
            "None=자동(외부 도로변 배치가 필요 대수 미달일 때만 평가·대수 우위 "
            "채택), True=**우선 사용**(항상 평가, 법정 대수만 충족하면 외부보다 "
            "대수가 적어도 내부차로 채택 — 사용자 유도 버튼), False=금지. "
            "GT 추출은 이 값을 방출하지 않음(자동 트리거로 재현 — 순수 사용자 의도)."
        ),
    )
    parking_axis: Optional[Literal["road", "core", "auto"]] = Field(
        default="auto",
        description=(
            "주차 행 배치 축 — road=주접도 프레임, core=코어 그리드 정렬(회전 매스 대응), "
            "auto=둘 다 평가해 대수 최대 채택(#6 최적화). 대부분 auto."
        ),
    )
    exit_road: Optional[int] = Field(
        default=None,
        description="보행통로 출구 도로변 인덱스 (필지 폴리곤 기준). None=자동(최근접 도로변).",
    )
    road_setback: Optional[float] = Field(
        default=None,
        description=(
            "주차구획 전면선의 주도로 경계 셋백 (m). None=도로산입 derive — "
            "주차장법 시행규칙 11조⑤2호: 직각주차 차로는 도로 포함 6m 이상, "
            "미달분(max(0, 6−실측 도로폭))만큼 후퇴. 12m↑ 도로·폭 미상은 0. "
            "명시(0 포함) 시 그 값 — 설계자가 도로 여건상 밀착·완화를 판단한 "
            "의도 기록 (GT 실측: 6m 미만 이면도로에서도 경계 밀착 다수)."
        ),
    )

    # ── 코어 (R단계) ──
    core_side: Optional[
        Literal["n", "ne", "e", "se", "s", "sw", "w", "nw", "c"]
    ] = Field(
        default=None,
        description=(
            "코어 방위 — common(전층 교집합)의 어느 자리인가 (동서남북 8방향 "
            "+ c=중앙, EPSG 절대 방위). 대각=모서리·정방위=변 중간에서 common "
            "장변에 snap, 배향은 snap된 변에서 derive. c=중심 최근접 변 후보 "
            "(명시적 중앙 의도). None=estim argmax 자동."
        ),
    )
    core_axis: Optional[Literal["road", "depth"]] = Field(
        default=None,
        description=(
            "코어 장축 배향 — road=주접도변과 평행(눕힘), depth=직교(깊이 "
            "방향으로 세움). 정답 9필지 실측 6:3으로 갈려 derive 불가한 "
            "설계 의도. None=estim argmax 자동."
        ),
    )

    # ── 동선 (C단계) ──
    corridor_mode: CorridorMode = Field(
        default="carve",
        description="보행통로 라우팅 — carve=최단, edge=필지 변 추종.",
    )
    pedestrian_width: Optional[float] = Field(
        default=1.5,
        description="보행통로 폭 (m). 기본 1.5 (시행령 41조 다세대 유효너비 하한). None=용도별 derive (다세대 1.7 등).",
    )

    # ── 기둥 (K단계 — 구조 의도) ──
    max_span: float = Field(default=8.0, description="기둥 최대 간격 (m).")
    cantilever: float = Field(default=1.2, description="코너 캔틸레버 한계 (m).")
    min_col_dist: float = Field(default=3.0, description="기둥 최소 간격 (m).")
    preferred_min_span: float = Field(
        default=4.2, description="엣지 분할 과밀 방지 하한 (m).")

    # ── 1층 용도 ──
    commercial_remainder: bool = Field(
        default=False,
        description="주차 배치 후 잔여 1층 면적을 근생(상가)으로 전환.",
    )

    # ─── derive 헬퍼 (옵션이 아니라 계산 — 옵션화 금지) ───────────────

    def bk_eff(self, stall_depth: float = 5.0) -> float:
        """백칸 밴드 시작 깊이 = max(BK, stall_depth)."""
        return max(self.bk_offset or stall_depth, stall_depth)

    def walk_width(self, use: str | None = None) -> float:
        """보행통로 폭 — 명시 > 용도 derive > 기본 1.2 (용도별 규정)."""
        if self.pedestrian_width is not None:
            return self.pedestrian_width
        table = {"multi_family": 1.7, "dagagu": 1.1, "retail": 1.5}
        return table.get(use or "", 1.2)

    def aisle(self, use: str | None = None) -> float:
        """그룹 분리 차로 간격 = max(법정 하한 2.5, 보행폭)."""
        return max(2.5, self.walk_width(use))


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
        default=0.15,
        description="층간 슬래브 두께 (m). 실무 스펙 150 (기초는 foundation_thickness 별도).",
    )
    interior_wall_thickness: float = Field(
        default=0.10,
        description="세대 **내부** 칸막이 두께 (m). 표준 0.10 (방 분할용).",
    )
    party_wall_thickness: float = Field(
        default=0.20,
        description=(
            "세대 간 경계벽·공용부(복도·계단실) 경계벽 두께 (m). "
            "실무 표준 0.20. 법정 하한은 다세대(건축허가)면 건축법 계열 "
            "경계벽 기준(철근콘크리트조 10cm 이상)이고, 주택건설기준 14조①1의 "
            "15cm는 사업계획승인(30세대 이상) 대상에만 적용된다 — 어느 쪽이든 "
            "0.20은 충족. 참조 도면(상도동 "
            "214-82) 실측도 전 층 철콘200 단일 — 외벽과 **구조체 두께가 같고** "
            "외기 접면만 단열·마감이 덧붙어 410이 된다. 코어 벽이 층마다 달라 "
            "보이는 건 단열 유무 차이지 구조체 차이가 아니다."
        ),
    )
    basement_wall_thickness: float = Field(
        default=0.30,
        description=(
            "지하 외벽(옹벽) 두께 (m). 토압을 받아 지상 외벽보다 두껍다 — "
            "참조 도면 실측 지하1층 '철근콘크리트 300' 6장."
        ),
    )
    railing_post_size: float = Field(
        default=0.05,
        description="난간 간살(동자) 단면 한 변 (m). 실무 φ20~50 각살 — 기본 50mm.",
    )
    railing_clear: float = Field(
        default=0.12,
        description=(
            "난간 간살 사이 **안목치수** (m). 중심간 피치 = railing_post_size + 이 값. "
            "법정: 우리 대상(도시형생활주택 30세대 미만 = 건축허가)에는 살 간격 규정이 "
            "**없다** — 건축법 시행령 40조①은 높이 1.2m만 규정하고, 안목 10cm 규정인 "
            "주택건설기준 18조②2는 같은 영 3조(적용범위)상 사업계획승인(30세대 이상) "
            "대상에만 적용된다. 0.12는 영유아 끼임 방지 안전 관행 범위의 값이며, "
            "30세대 이상 단지를 다루게 되면 0.10으로 낮춰야 한다."
        ),
    )
    parapet_wall_height: float = Field(
        default=0.0,
        description=(
            "옥상·노대 난간 중 **콘크리트 저벽** 높이 (m). 기본 0 = 금속 난간만"
            "(동자+상단 손스침 바)으로 법정고 1.2m를 만든다 (시행령 40조①). "
            "저벽(방수턱 등)을 원하면 값을 준다 — 그만큼 동자 구간이 짧아진다."
        ),
    )
    column_size: float = Field(
        default=0.60,
        description="기둥 단면 한 변 (m). 실무 스펙 600 정사각 — 1층 필로티, 전이보와 접합.",
    )
    # ── LOD300 부재 치수 (실무 스펙 — 참조 IFC 실측) ──
    foundation_thickness: float = Field(
        default=0.60,
        description="기초(흙 접함) 슬래브 두께 (m). 층간 슬래브와 별도 — 두께가 다르다.",
    )
    insulation_thickness: float = Field(
        default=0.20,
        description="외벽 외단열 두께 (m). 참조 도면 실측 '[외벽] 철콘200 // EPS200'.",
    )
    finish_thickness: float = Field(
        default=0.01,
        description="외부 마감 두께 (m). 재료마다 10~50mm — 기본 STO 10mm.",
    )
    finish_name: str = Field(
        default="STO",
        description="외부 마감재 이름 (IFC 레이어셋 명명에 사용).",
    )
    transfer_beam_width: float = Field(
        default=0.60,
        description="전이보 폭 (m). 필로티 천장(2층 바닥) 600×800 — 실무 스펙.",
    )
    transfer_beam_depth: float = Field(
        default=0.80,
        description="전이보 춤 (m). 윗층 하중을 기둥/벽으로 전달 — 기둥과 만나야 함.",
    )
    beam_size: float = Field(
        default=0.60,
        description="일반 보·일조사선 꺾임부 전이보 단면 (m). 600×600 정사각.",
    )
    stair_riser_max: float = Field(
        default=0.18,
        description="계단 단높이 상한 (m). 주택 계단 법정 0.18 — 실단높이 = 층고/단수.",
    )
    stair_tread: float = Field(
        default=0.26,
        description="계단 단너비(디딤판 깊이) (m).",
    )
    stair_waist: float = Field(
        default=0.15,
        description="계단판(waist) 두께 (m). 기본 150mm.",
    )
    price_per_m3: int = Field(
        default=3_500_000,
        description=(
            "콘크리트 ㎥당 단가 (원). 다세대 표준 350만원. "
            "공사비 = total_m3 × price_per_m3."
        ),
    )


# ═════════════════════════════════════════════════════════════════════
# Schedule — 사업 일정·심의 의도 (착공 전 기간 → PF 이자)
# ═════════════════════════════════════════════════════════════════════


class Schedule(BaseModel):
    """사업 일정 의도 — 인허가·심의 단계와 단계별 기간.

    핵심: 착공 전 총 기간(기본설계+심의+허가+실시설계+시공사선정+착공신고)이
    토지담보 PF 이자 기간이 된다. 6층↑이면 건축심의·구조굴토심의로 기간이
    늘어 이자가 증가 — 이 비용을 사업성에 정직하게 반영하기 위한 layer.

    원칙: 심의 토글은 None=자동유도(층수·지하 기반), 명시 시 override.
    단계 기간은 설계자 조정용 default(개월). 공사기간은 기하 derive.
    """

    model_config = ConfigDict(extra="forbid")

    # ── 심의 토글 (None=자동유도) ──
    arch_review: Optional[bool] = Field(
        default=None,
        description=(
            "건축심의 시행 여부. None=자동(지상 6층↑ 또는 대로변 건축선후퇴 시 True, "
            "5층 이하 False). 착공 전 기간에 arch_review_mo 가산."
        ),
    )
    struct_review: Optional[bool] = Field(
        default=None,
        description=(
            "구조·굴토심의 시행 여부. None=자동(6층↑ 기본 True). "
            "실시설계와 병렬 수행 — 둘 중 긴 쪽이 종료 시점."
        ),
    )
    civil_supervision: Optional[bool] = Field(
        default=None,
        description="토목감리 적용 여부. None=자동(지하 2개층↑ True). 비용 항목.",
    )
    other_survey_cost: Optional[float] = Field(
        default=None,
        description="기타조사비 (만원) — 문화재·지하철안전도 등 필지별 특수건. None=0.",
    )

    # ── 단계 기간 (개월) — 설계자 조정용 default ──
    basic_design: float = Field(default=3.0, description="기본설계 기간 (개월).")
    arch_review_mo: float = Field(
        default=1.5, description="건축심의 기간 (개월). arch_review=True일 때만 가산.")
    build_permit: float = Field(default=1.0, description="건축허가 기간 (개월).")
    exec_design: float = Field(default=1.0, description="실시설계 기간 (개월).")
    struct_review_mo: float = Field(
        default=1.5, description="구조·굴토심의 기간 (개월). 실시설계와 병렬.")
    constructor_select: float = Field(
        default=2.0, description="시공사 선정 기간 (개월).")
    constr_notice: float = Field(default=1.0, description="착공신고 기간 (개월).")
    construction_months: Optional[int] = Field(
        default=None,
        description="공사기간 (개월). None=2+지상층+지하층×2 자동 derive.",
    )
    start_year_month: Optional[str] = Field(
        default=None,
        description=(
            "사업 시작 연월 'YYYY-MM' (기본설계 착수 시점). 재무 숫자엔 영향 없고 "
            "현금흐름 달력 라벨용. None=상대 개월(N개월차)."
        ),
    )


# ═════════════════════════════════════════════════════════════════════
# Financing — 금융·분양 구조 의도 (PF 대출·분양 스케줄)
# ═════════════════════════════════════════════════════════════════════


class Financing(BaseModel):
    """PF 대출(토지담보·시설자금·준공담보)과 분양 스케줄 의도.

    이자 = 대출액 × 금리 × 기간/12. 분양수입은 계약/중도/잔금으로 월별 분배.

    **금융 조건에는 기본값이 없다(None).** 사업자·시점마다 다른 협상 결과이고,
    남의 조건을 조용히 물려받아 사업성을 계산하는 것이 값이 비는 것보다 위험하다.
    값은 설정 파일에서 주입한다 — config.py / examples/sbim_config.example.json.

        from seoulgaok_bim_core import build_options
        opts = build_options()          # sbim_config.json의 financing 블록 적용
    """

    model_config = ConfigDict(extra="forbid")

    # ── PF 대출 — 전부 설정 주입. None이면 현금흐름 계산 시점에 터진다. ──
    land_loan_ltv: Optional[float] = Field(default=None, description="토지담보 LTV.")
    land_loan_rate: Optional[float] = Field(
        default=None, description="토지담보 연이자율.")
    fac_loan_ltv: Optional[float] = Field(
        default=None, description="시설자금 LTV (직접공사비 기준).")
    fac_loan_rate: Optional[float] = Field(
        default=None, description="시설자금 연이자율.")
    fac_efficiency: Optional[float] = Field(
        default=None, description="시설자금 기성고 평균 실사용률 (이자 효율).")
    post_loan_rate: Optional[float] = Field(
        default=None,
        description="준공담보 연이자율 (담보 확정 → 토지담보 수준).")
    post_months: Optional[float] = Field(
        default=None,
        description="준공 후 기간 (개월). 비아파트 = 준공 후 이 기간에 균등 분양·매각.")
    handling_fee_rate: Optional[float] = Field(
        default=None, description="대출 취급수수료율 (토담+시설 대출액).")
    handling_fee_on: bool = Field(
        default=False,
        description="취급수수료 적용 여부. True=적용.")

    def require(self, *names: str) -> None:
        """계산 직전 호출 — 필요한 금융 값이 비었으면 어디가 빈지 밝히고 중단."""
        if missing := [n for n in names if getattr(self, n) is None]:
            raise ValueError(
                f"금융 설정 누락: {missing}. sbim_config.json의 financing 블록에 "
                f"채우거나 build_options(financing={{...}})로 주입하세요 "
                f"(형식: examples/sbim_config.example.json)."
            )

    # ── 분양 스케줄 (비아파트 = 준공 후 매각) ──
    # 비아파트는 통상 준공 후 분양 → post_months 기간에 균등 매각.
    # 아래 계약/중도/잔금 필드는 legacy(아파트 선분양) — 현 모델 미사용.
    presale_start_offset: int = Field(
        default=0, description="[legacy] 분양 개시 = 착공 후 N개월.")
    presale_period: int = Field(default=6, description="[legacy] 분양 기간 (개월).")
    deposit_pct: float = Field(default=0.10, description="[legacy] 계약금 비율.")
    mid_pct: float = Field(default=0.60, description="[legacy] 중도금 비율.")
    balance_pct: float = Field(default=0.30, description="[legacy] 잔금 비율.")


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
    structure: Structure = Field(default_factory=Structure)
    windows: Windows = Field(default_factory=Windows)
    parking: Parking = Field(default_factory=Parking)
    ground_floor: GroundFloor = Field(default_factory=GroundFloor)
    concrete: Concrete = Field(default_factory=Concrete)
    schedule: Schedule = Field(default_factory=Schedule)
    financing: Financing = Field(default_factory=Financing)
    exterior: Exterior = Field(default_factory=Exterior)
    regulations: RegulationOverrides = Field(default_factory=RegulationOverrides)

    # ─── 헬퍼 ───────────────────────────────────────────────────────

    def get_floor_use(self, level: int) -> FloorUse:
        """특정 층의 용도. floor_use override > 1층=piloti > residential."""
        if level in self.massing.floor_use:
            return self.massing.floor_use[level]
        if level == 1:
            return "piloti"
        return "residential"

    @model_validator(mode="after")
    def _apply_structure_preset(self):
        """구조방식 → 벽두께·스팬 기본값 채움 (명시 override는 존중). 벽식=현행값이라 무변화."""
        preset = STRUCTURE_PRESET.get(self.structure.system)
        if preset:
            if "wall_thickness" not in self.concrete.model_fields_set:
                self.concrete.wall_thickness = preset["wall_thickness"]
            if "max_span" not in self.ground_floor.model_fields_set:
                self.ground_floor.max_span = preset["max_span"]
            if "min_col_dist" not in self.ground_floor.model_fields_set:
                self.ground_floor.min_col_dist = preset["min_col_dist"]
        return self

    @property
    def base_floor_height(self) -> float:
        """기준 층고 — 구조방식에서 derive (벽식 3.0 / 라멘 3.3 / 철골 3.4m). raw 입력 아님."""
        return {"rahmen": 3.3, "steel": 3.4}.get(self.structure.system, 3.0)

    def get_floor_height(self, level: int) -> float:
        """층별 층고. 1층은 first_floor_height 우선, 그 외는 구조방식 derive."""
        if level == 1 and self.massing.first_floor_height is not None:
            return self.massing.first_floor_height
        return self.base_floor_height

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
