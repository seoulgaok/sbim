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







CoreComposition = Literal["stair", "stair_elevator"]
CoreType = Literal[1, 2, 3, 4, 5, 6, 7]

# 코어 유형 번호는 2026-09에 DWG 템플릿 시트 순서로 재배열됐다
# (building-generator #190). 값 집합은 1~7 그대로라 **스키마 검증으로는 걸리지
# 않는다** — 옛 번호로 저장된 core.type은 이 표로 옮겨야 뜻이 유지된다.
CORE_TYPE_RENUMBER_2026_09: dict[int, int] = {1: 2, 2: 1, 3: 4, 4: 5, 5: 7, 6: 6, 7: 3}


def migrate_core_type(old: Optional[CoreType]) -> Optional[CoreType]:
    """옛 번호 `Core.type` → 새 번호. None(auto)은 그대로 둔다."""
    if old is None:
        return None
    try:
        return CORE_TYPE_RENUMBER_2026_09[old]
    except KeyError:
        raise ValueError(f"코어 유형 번호가 아니다: {old!r}") from None




WindowStyle = Literal["open", "standard", "closed"]

# pattern·alignment·seed 제거 — 창 배치가 WWR·jitter 랜덤에서 **법정 채광면적
# 역산**으로 바뀌며(피난방화규칙 17조① 거실 바닥의 1/10, 세대가 실제로 접한
# 외벽에만) 디자인 언어 입력이 소비처를 잃었다. 컴파일러가 안 읽는 필드는 두지
# 않는다. DB 잔재는 프론트엔드 DB 마이그레이션에서 제거됨.




StructureSystem = Literal["wall", "rahmen", "steel"]

# 구조방식 → 기하 기본값(명시 override 없을 때만). 벽식=현행 기본값(회귀0).
# 라멘/철골은 하중을 기둥이 받아 벽이 얇아짐(전용↑), 철골은 장스팬(넓은 주차·기둥간격).
# 층고는 base_floor_height property에서 별도 derive. 실적치는 보정 노브.
STRUCTURE_PRESET = {
    "wall":   {"wall_thickness": 0.20, "max_span": 8.0,  "min_col_dist": 3.0},
    "rahmen": {"wall_thickness": 0.15, "max_span": 8.0,  "min_col_dist": 3.0},
    "steel":  {"wall_thickness": 0.12, "max_span": 12.0, "min_col_dist": 6.0},
}




ParkingType = Literal["perpendicular", "parallel", "angled_60", "angled_45"]
ParkingRatioMode = Literal["multi_family", "non_residential"]




CorridorMode = Literal["carve", "edge"]

# 주차 행 배치 축. 축은 둘이다 — 도로에 기대느냐(road), 대지 안에 차로를 내느냐(inner).
# 내부 차로 안쪽을 어떤 방식으로 까는지는 **고르는 게 아니라 섞는 것**이라 값이 아니다
# (소장 GT 30필지 중 대지 안쪽 12필지의 9필지가 직각과 평행을 섞는다 — #10 ④).
# None = 자동. 「자동」의 표기는 None 하나뿐이고, legacy "auto"는 받아서 None으로 접는다.
ParkingAxis = Literal["road", "inner"]










ExteriorStyle = Literal["white", "sandstone", "brick", "concrete"]



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
    commercial_remainder: bool = Field(
        default=False,
        description="주차 배치 후 잔여 1층 면적을 근생(상가)으로 전환.",
    )

    # ─── derive 헬퍼 (옵션이 아니라 계산 — 옵션화 금지) ───────────────


# ═════════════════════════════════════════════════════════════════════
# UnitSpec — 세대 프로그램
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
    max_net_area: Optional[float] = Field(
        default=60.0,
        description=(
            "세대 전용면적 상한(㎡, 발코니 제외). 초과하면 컴파일 에러 "
            "UnitAreaExceeded — 탐색은 층당 세대수를 늘려 회피한다. "
            "기본 60 = 소형주택 선(2026-08-28 변경, 이전 기본은 84). "
            "단지형 다세대(도시형생활주택 전용 85㎡ 이하)로 지을 땐 84, "
            "면적 제한 없는 용도는 None. "
            "상한이 없으면 분할 실패가 조용히 통과한다 — 실측: 상한 없이 돌린 "
            "9,067세대 중 84 초과 722(8.0%), 최대 5,431㎡(층 전체가 1세대)."
        ),
    )

    model_config = ConfigDict(extra="forbid")

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
# Core — 코어 (형상·자리·배향)
# ═════════════════════════════════════════════════════════════════════


class Core(BaseModel):
    """코어 — 무엇을(type) 어디에(core_side) 어느 방향으로(core_rotation) 앉히는가.

    치수는 입력이 아니라 매스+세대프로그램에서 derive된다(삼전 정답: 계단·EV가 16.4m
    분리 = 세대 배치 결과). 자리와 배향은 고르는 것이고, 값이 없으면 첫수표가 정한다.
    """

    model_config = ConfigDict(extra="forbid")

    type: Optional[CoreType] = Field(
        default=None,
        description=(
            "코어 형상 타입 (DWG→sbim 코어 라이브러리 — giga core_library.json이 진실). "
            "None=auto(매스 형상 prior). "
            "이름은 외곽 형태(세장형·정방형·ㄱ자형)로 가르고, 외곽이 같은 것은 "
            "괄호의 계단 형식으로 갈린다. "
            "1=세장형(꺾은계단, 2.8×6.8)·2=세장형(직선계단, 2.8×8.05)·"
            "3=세장형·편복도(직선계단, 2.8×10.15, 복도 내장, 층당 5~7세대 — 류상호 "
            "'코어 유형 추가' 2026-09; 도면 실측 2.78×9.95로 라이브러리 재추출 대기)·"
            "4=정방형(꺾은계단, 5.2×4.7)·5=정방형(직선계단, 5.2×4.7)·"
            "6=정방형(ㄱ자계단, 5.3×4.95 — ㄱ자는 외곽이 아니라 계단 모양)·"
            "7=ㄱ자형(EV측면, 4.8×5.9 — 외곽이 ㄱ자로 파인 유일한 유형). "
            "대부분 type2(세장 타워, 회전 fit), 넓은 단독 장변접도만 type4/5. "
            "번호는 2026-09 DWG 시트 순서로 재배열됐다(building-generator #190) — "
            "옛 번호로 저장된 값은 migrate_core_type()으로 옮긴다."
        ),
    )
    composition: CoreComposition = Field(
        default="stair_elevator",
        description=(
            "코어 구성 의도 — 계단·EV 유무. 코어 치수/형상 derive의 입력(세대수와 함께). "
            "stair=계단실만, stair_elevator=계단+승강기."
        ),
    )
    core_side: Optional[
        Literal["n", "ne", "e", "se", "s", "sw", "w", "nw", "c"]
    ] = Field(
        default=None,
        description=(
            "코어 방위 — common(전층 교집합)의 어느 자리인가 (동서남북 8방향 "
            "+ c=중앙, EPSG 절대 방위). 대각=모서리·정방위=변 중간에서 common "
            "장변에 snap, 배향은 snap된 변에서 derive. c=중심 최근접 변 후보 "
            "(명시적 중앙 의도). None=첫수표가 정한다."
        ),
    )
    core_rotation: Optional[Literal[0, 90, 180, 270]] = Field(
        default=None,
        description=(
            "코어 배향 — core_side로 정해진 변 기준 절대 회전각. "
            "0=코어 기준자세 그대로 변에 밀착, 90/180/270=그만큼 회전. "
            "코어는 점대칭이 아니라(계단·EV 한쪽 편재, 복도 한 면 접합, 출입구 "
            "면이 방향별로 달라 0·90·180·270이 전부 다른 결과) 절반 지정인 "
            "구 core_axis(road/depth)로는 같은 축 위 180° 뒤집기를 표현할 수 없어 "
            "네 방위를 전부 받는다. 라이브러리 형상 가로세로와 무관한 앉은 변 "
            "기준 절대 표현이라 코어 형상이 바뀌어도 뜻이 유지된다. "
            "None=첫수표가 정한다."
        ),
    )
    core_entries: Optional[int] = Field(
        default=None,
        description=(
            "코어(복도) 보행 출입구 수 1|2. 2=코어 문 반대편에도 문 — 보행로가 도로에서 "
            "꼬이는 필지(합정동 441-31). None=자동: 둘째 문의 보행로가 첫째보다 뚜렷이 "
            "짧을 때만 2. scheme `_pedestrian_paths`로 전부 방출. (multi_road는 차량 진입 옵션 — 별개)"
        ),
    )

    @model_validator(mode="before")
    @classmethod
    def _drop_legacy_core_axis(cls, data):
        """구 `core_axis`(road/depth)는 제거됐다 — 들어오면 버린다 (#13).

        절반 지정이라(road↔{0,180}, depth↔{90,270}) 회전각으로 옮길 수 없다. 한쪽으로
        접으면 없던 정밀도를 지어내는 것이라, 값으로 못 옮기는 대신 비운다 — 비면
        첫수표가 정한다. 거부하지 않는 건 구 `_build_options.json`이 이 값을 심고 있어
        저장된 설계안이 통째로 안 열리기 때문이다.
        """
        if isinstance(data, dict) and "core_axis" in data:
            data = {k: v for k, v in data.items() if k != "core_axis"}
        return data


# ═════════════════════════════════════════════════════════════════════
# Parking — 주차 (대수·배치)
# ═════════════════════════════════════════════════════════════════════


class Parking(BaseModel):
    """주차 — 몇 대를 어떤 축으로 어디에 깔까. 치수는 Standards.dimensions로 갔다.

    법정 수치(칸 2.5×5.0·총 8대 캡·그룹 5대 등)는 옵션이 아니라 엔진 상수다
    (주차장법 시행규칙 — 법이 정하면 상수, 설계자가 고르면 옵션).
    """

    model_config = ConfigDict(extra="forbid")

    count: Optional[int] = Field(
        default=None,
        description=(
            "주차 stall 수 명시. None=가능한 만큼 자동 배치. "
            "법정 대수는 ratio_mode·세대별 전용면적 기반으로 별도 산출."
        ),
    )
    type: ParkingType = Field(
        default="perpendicular",
        description=(
            "[deprecated] 배치 형식. perpendicular=직각주차(default). "
            "parking_angle·parking_axis와 같은 것을 가리키는 세 번째 이름이다 — "
            "각도는 parking_angle, 축은 parking_axis가 정본."
        ),
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
    parking_axis: Optional[ParkingAxis] = Field(
        default=None,
        json_schema_extra={"auto": True},
        description=(
            "주차 행 배치 축 — road=주접도 프레임(도로에 기대 깐다), "
            "inner=대지 안에 차로를 내고 그 차로 기준으로 깐다 — 까는 방식(직각·평행·"
            "경계 한 줄·회전 마당과 그 섞음)은 첫수표가 정한다. "
            "None=첫수표가 정한다. 대부분 None. "
            "legacy \"auto\"는 None과 같은 뜻이라 받아서 접는다. "
            "구 \"core\"(코어 격자 정렬)는 제거됐다 — REF 30필지에서 엔진이 한 번도 고르지 "
            "않았고, 뜻은 매스 격자 정렬인데 이름이 구현(코어 사각형에서 방향을 빌림)을 "
            "드러냈다. 건물이 비뚤면 road/inner 안에서 기울여 깐다(#10 ④⑤)."
        ),
    )
    parking_angle: Optional[Literal[45, 60, 90]] = Field(
        default=None,
        description=(
            "내부차로(interior_aisle) 주차 각도. 45/60=사선(fishbone) — 차로폭은 "
            "주차장법 시행규칙 11조⑤1호 법정값(45° 3.5m·60° 4.0m), 연접(back) 없음, "
            "막다른 차로라 일방 진입·후진 퇴출 전제. 90=직각(차로 6m). "
            "None=첫수표가 정한다(현행 90). 사선 순차 평가는 2026-09-19에 제거됐다. "
            "외부 도로변 주차는 항상 직각(11조⑤2호 — 도로를 차로로 쓰는 형식은 "
            "직각·평행뿐)이라 inner 모드에만 의미."
        ),
    )
    road_edge: Optional[int] = Field(
        default=None,
        description="주접도 변 인덱스 (필지 폴리곤 기준). None=최장 접도변 자동.",
    )
    multi_road: Optional[bool] = Field(
        default=None,
        json_schema_extra={"auto": True},
        description=(
            "다중도로 주차 — 주접도 외 잔여 접도변(넓은급→긴변, 최대 3)에 추가 주차. "
            "None=첫수표가 정한다. (구 이름 entry2 — '인접 2차 진입'에서 ≤3 도로로 "
            "일반화됐는데 이름이 2에 남아 있었다.)"
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
            "None=첫수표가 정한다. True=내부 차로로 그린다(평가 없음), False=금지. "
            "GT 추출은 이 값을 방출하지 않음 — 순수 사용자 의도."
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

    @model_validator(mode="before")
    @classmethod
    def _fold_legacy_auto(cls, data):
        """legacy `parking_axis="auto"` → None — 「자동」의 표기를 하나로 접는다(#10 ③).

        구 `_build_options.json`과 DB가 "auto"를 심고 있다(측정: 51건). 값을 거부하면
        그 저장값이 통째로 깨지므로, 같은 뜻인 None으로 옮겨 받는다. giga도 받자마자
        None으로 정규화하고 있었다(`prior.py`: "auto"는 무지정과 동일).
        """
        if isinstance(data, dict) and data.get("parking_axis") == "auto":
            data = {**data, "parking_axis": None}
        return data

    @model_validator(mode="after")
    def _angle_is_inner_only(self):
        """각도는 내부 차로에서만 뜻이 있다 — 스코프를 산문이 아니라 타입에서 막는다(#10 ⑧).

        외부 도로변 주차는 항상 직각이다(주차장법 시행규칙 11조⑤2호 — 도로를 차로로 쓰는
        형식은 직각·평행뿐). road 축에 45°를 주면 엔진이 조용히 무시하던 조합이었다.
        """
        if self.parking_axis == "road" and self.parking_angle not in (None, 90):
            raise ValueError(
                f"parking.parking_angle={self.parking_angle}은 inner 축에서만 씁니다 — "
                "외부 도로변 주차는 항상 직각입니다(주차장법 시행규칙 11조⑤2호)."
            )
        return self

    def bk_eff(self, stall_depth: float = 5.0) -> float:
        """백칸 밴드 시작 깊이 = max(BK, stall_depth)."""
        return max(self.bk_offset or stall_depth, stall_depth)


# ═════════════════════════════════════════════════════════════════════
# Circulation — 동선 (복도·보행로)
# ═════════════════════════════════════════════════════════════════════


class Circulation(BaseModel):
    """동선 — 복도를 어떻게 내고 보행로를 얼마로 둘까."""

    model_config = ConfigDict(extra="forbid")

    corridor_mode: CorridorMode = Field(
        default="carve",
        description="보행통로 라우팅 — carve=최단, edge=필지 변 추종.",
    )
    pedestrian_width: Optional[float] = Field(
        default=1.5,
        description="보행통로 폭 (m). 기본 1.5 (시행령 41조 다세대 유효너비 하한). None=용도별 derive (다세대 1.7 등).",
    )

    # ── 기둥 (K단계 — 구조 의도) ──

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
# Exterior — 외장 (외벽·창)
# ═════════════════════════════════════════════════════════════════════


class Exterior(BaseModel):
    """외장 — 외벽 마감과 창 스타일. 한 필드 클래스 둘(Windows·Exterior)을 합쳤다."""

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
    window_style: WindowStyle = Field(
        default="open",
        description=(
            "창 크기 의도 — 법정 채광면적(거실 바닥의 1/10)을 몇 배로 잡을지의 배율. "
            "open=넉넉(1.8배), standard=표준(1.35배), closed=최소(1.05배). "
            "창의 위치·개수는 세대가 접한 외벽에서 컴파일러가 derive한다."
        ),
    )


# ═════════════════════════════════════════════════════════════════════
# Dimensions — 회사 표준 치수 (주차 칸·스팬)
# ═════════════════════════════════════════════════════════════════════


class Dimensions(BaseModel):
    """치수 표준 — 사업마다 고르는 값이 아니라 회사가 정해 두는 값."""

    model_config = ConfigDict(extra="forbid")

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
    max_span: float = Field(default=8.0, description="기둥 최대 간격 (m).")
    cantilever: float = Field(default=1.2, description="코너 캔틸레버 한계 (m).")
    min_col_dist: float = Field(default=3.0, description="기둥 최소 간격 (m).")
    preferred_min_span: float = Field(
        default=4.2, description="엣지 분할 과밀 방지 하한 (m).")

    # ── 1층 용도 ──


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
# Schedule — 사업 일정
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
    # 합계 = 6.0 (심의 없는 기본 경로: 2 + 1 + 1 + 1.5 + 0.5).
    # 소장 aug28 지시 "사업기간 산정을 착공전 6개월, 공사 9개월로". 종전 합 8.0에서
    # 기본설계 3→2 · 시공사선정 2→1.5 · 착공신고 1→0.5로 줄였다 — 허가·실시설계는
    # 법정/실무 최소라 유지, 심의(건축 1.5·구조 1.5)는 법정 절차라 줄이지 않는다
    # (6층↑ 자동 ON이면 착공전이 8.0으로 늘어나는 게 정직하다).
    basic_design: float = Field(default=2.0, description="기본설계 기간 (개월).")
    arch_review_mo: float = Field(
        default=1.5, description="건축심의 기간 (개월). arch_review=True일 때만 가산.")
    build_permit: float = Field(default=1.0, description="건축허가 기간 (개월).")
    exec_design: float = Field(default=1.0, description="실시설계 기간 (개월).")
    struct_review_mo: float = Field(
        default=1.5, description="구조·굴토심의 기간 (개월). 실시설계와 병렬.")
    constructor_select: float = Field(
        default=1.5, description="시공사 선정 기간 (개월).")
    constr_notice: float = Field(default=0.5, description="착공신고 기간 (개월).")
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
# Financing — 금융 조건
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


# ═════════════════════════════════════════════════════════════════════
# RegulationOverrides — 법규 목표 override
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
# Design · Standards · Business — 속성 창을 세 묶음으로
# ═════════════════════════════════════════════════════════════════════


class Design(BaseModel):
    """이 설계에서 고르는 것. 값이 없으면 첫수표가 정한다.

    묶음은 **대상**이다(매스·세대·코어·주차·동선·외장) — 단계로 자르면 같은 대상의
    속성이 두 집에 나뉘어 산다(구 GroundFloor가 주차·코어·동선·기둥을 한 서랍에 담았다).
    """

    model_config = ConfigDict(extra="forbid")

    massing: Massing = Field(default_factory=Massing)
    units: UnitSpec = Field(default_factory=UnitSpec)
    core: Core = Field(default_factory=Core)
    parking: Parking = Field(default_factory=Parking)
    circulation: Circulation = Field(default_factory=Circulation)
    exterior: Exterior = Field(default_factory=Exterior)
    structure: StructureSystem = Field(
        default="wall",
        description=(
            "구조 방식 — wall=벽식(현행 다세대 표준)·rahmen=라멘(기둥·보)·steel=철골. "
            "층고와 벽 두께·스팬 기본값이 여기서 derive된다(Standards에서 override 가능). "
            "한 필드 클래스였던 Structure를 스칼라로 폈다."
        ),
    )
    regulations: RegulationOverrides = Field(default_factory=RegulationOverrides)


class Standards(BaseModel):
    """회사 표준 — 사업마다 안 건드리는 값. 소비 UI는 접어 둘 수 있다."""

    model_config = ConfigDict(extra="forbid")

    concrete: Concrete = Field(default_factory=Concrete)
    dimensions: Dimensions = Field(default_factory=Dimensions)


class Business(BaseModel):
    """사업성 — 도면과 무관한 값. 소비 UI는 접어 둘 수 있다."""

    model_config = ConfigDict(extra="forbid")

    schedule: Schedule = Field(default_factory=Schedule)
    financing: Financing = Field(default_factory=Financing)


# ── 구 평면 모양(13블록) → 새 모양 이행표 ──────────────────────────────
# 저장된 설계안은 전부 구 경로다(reference/*/_build_options.json, DB jsonb).
# 읽는 자리에서 옮겨 받는다 — 데이터 마이그레이션 없이 구 파일이 그대로 열린다.
_LEGACY_TOP = (
    "massing", "units", "core", "structure", "windows", "parking",
    "ground_floor", "concrete", "schedule", "financing", "exterior", "regulations",
)
# 구 ground_floor 21필드가 네 대상으로 흩어진다
_GF_TO = {
    "core_side": "core", "core_rotation": "core", "core_axis": "core",
    "core_entries": "core",
    "parking_axis": "parking", "parking_angle": "parking", "road_edge": "parking",
    "entry2": "parking", "tandem": "parking", "bk_offset": "parking",   # entry2→multi_road
    "interior_aisle": "parking", "exit_road": "parking", "road_setback": "parking",
    "corridor_mode": "circulation", "pedestrian_width": "circulation",
    "commercial_remainder": "massing",
    "max_span": "dimensions", "cantilever": "dimensions",
    "min_col_dist": "dimensions", "preferred_min_span": "dimensions",
}
_PARKING_DIMS = ("stall_width", "stall_depth", "aisle_width")
# 구 이름 → 새 이름 (뜻은 같다)
_RENAMED = {"entry2": "multi_road"}
# 폐기된 legacy 필드 — 저장값에 남아 있으면 조용히 버린다(소비처 0곳, 현 모델 미사용).
# 거부하면 DB jsonb에 그 키가 든 설계안이 안 열린다.
_DROPPED = {
    "financing": ("presale_start_offset", "presale_period",
                  "deposit_pct", "mid_pct", "balance_pct"),
}


class BuildOptions(BaseModel):
    """다세대주택 파라메트릭 설계 입력 — 속성 창.

    세 묶음이다: `design`(이 설계에서 고르는 것) · `standards`(회사 표준) ·
    `business`(사업성). 도면 하나를 만들 때 마주하는 건 `design`뿐이다.

    구 평면 모양(`ground_floor`·`concrete`·`schedule` …)으로 들어와도 받아서 옮긴다.
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

    design: Design = Field(default_factory=Design)
    standards: Standards = Field(default_factory=Standards)
    business: Business = Field(default_factory=Business)

    @model_validator(mode="before")
    @classmethod
    def _migrate_legacy_shape(cls, data):
        """구 13블록 평면 모양을 세 묶음으로 옮겨 받는다.

        저장된 설계안(파일·DB jsonb) 안에 구 경로가 박혀 있어, 거부하면 기존 데이터가
        통째로 깨진다. 새 키(design/standards/business)가 하나라도 있으면 새 모양으로
        보고 건드리지 않는다 — 섞어 주는 건 받지 않는다(조용한 반쪽 적용을 막는다).
        """
        if not isinstance(data, dict):
            return data
        if any(k in data for k in ("design", "standards", "business")):
            return data
        if not any(k in data for k in _LEGACY_TOP):
            return data

        d = {k: v for k, v in data.items() if k not in _LEGACY_TOP}
        design: dict = {}
        dims: dict = {}
        for name in ("massing", "units", "core", "regulations"):
            if isinstance(data.get(name), dict):
                design[name] = dict(data[name])
        if isinstance(data.get("structure"), dict):
            if data["structure"].get("system") is not None:
                design["structure"] = data["structure"]["system"]
        elif isinstance(data.get("structure"), str):
            design["structure"] = data["structure"]
        if isinstance(data.get("parking"), dict):
            park = dict(data["parking"])
            for k in _PARKING_DIMS:
                if k in park:
                    dims[k] = park.pop(k)
            design["parking"] = park
        for k, v in (data.get("ground_floor") or {}).items():
            k = _RENAMED.get(k, k)
            target = _GF_TO.get(k)
            if target is None:                      # 모르는 키는 parking에 남겨 거부되게 둔다
                design.setdefault("parking", {})[k] = v
            elif target == "dimensions":
                dims[k] = v
            else:
                design.setdefault(target, {})[k] = v
        for old, new in (("windows", "window_style"), ("exterior", "style")):
            val = (data.get(old) or {}).get("style")
            if val is not None:
                design.setdefault("exterior", {})[new] = val

        standards: dict = {}
        if isinstance(data.get("concrete"), dict):
            standards["concrete"] = data["concrete"]
        if dims:
            standards["dimensions"] = dims
        business = {}
        for k in ("schedule", "financing"):
            if isinstance(data.get(k), dict):
                business[k] = {kk: vv for kk, vv in data[k].items()
                               if kk not in _DROPPED.get(k, ())}

        if design:
            d["design"] = design
        if standards:
            d["standards"] = standards
        if business:
            d["business"] = business
        return d

    # ─── 헬퍼 ───────────────────────────────────────────────────────

    def get_floor_use(self, level: int) -> FloorUse:
        """특정 층의 용도. floor_use override > 1층=piloti > residential."""
        if level in self.design.massing.floor_use:
            return self.design.massing.floor_use[level]
        if level == 1:
            return "piloti"
        return "residential"

    @model_validator(mode="after")
    def _apply_structure_preset(self):
        """구조방식 → 벽두께·스팬 기본값 채움 (명시 override는 존중). 벽식=현행값이라 무변화."""
        preset = STRUCTURE_PRESET.get(self.design.structure)
        if preset:
            concrete, dims = self.standards.concrete, self.standards.dimensions
            if "wall_thickness" not in concrete.model_fields_set:
                concrete.wall_thickness = preset["wall_thickness"]
            if "max_span" not in dims.model_fields_set:
                dims.max_span = preset["max_span"]
            if "min_col_dist" not in dims.model_fields_set:
                dims.min_col_dist = preset["min_col_dist"]
        return self

    @property
    def base_floor_height(self) -> float:
        """기준 층고 — 구조방식에서 derive (벽식 3.0 / 라멘 3.3 / 철골 3.4m). raw 입력 아님."""
        return {"rahmen": 3.3, "steel": 3.4}.get(self.design.structure, 3.0)

    def get_floor_height(self, level: int) -> float:
        """층별 층고. 1층은 first_floor_height 우선, 그 외는 구조방식 derive."""
        if level == 1 and self.design.massing.first_floor_height is not None:
            return self.design.massing.first_floor_height
        return self.base_floor_height

    def get_first_floor_ratio(self, default: float = 0.15) -> float:
        """1층 면적 비율. 상가는 크게."""
        if self.get_floor_use(1) == "commercial":
            return 0.6
        return default

    def get_upper_floor_ratio(self, default: float) -> float:
        """상층 면적 비율. bcr_target 우선."""
        if self.design.regulations.bcr_target is not None:
            return self.design.regulations.bcr_target / 100
        return default
