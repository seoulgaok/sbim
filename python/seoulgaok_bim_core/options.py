"""BuildOptions — 다세대주택 파라메트릭 설계 입력 (sbim 단일 진실).

컴파일러가 실제 읽는 필드만 정의. 미구현 카테고리는 빠짐.
필드 추가는 컴파일러 구현과 함께. docstring drift 방지 위해 Field description이 곧 LLM 스키마.
"""

from __future__ import annotations

import logging
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


FloorUse = Literal[
    "piloti", "residential", "commercial", "rooftop_garden",
    "basement_parking", "basement_storage",
]







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




ParkingRatioMode = Literal["multi_family", "non_residential"]




CorridorMode = Literal["carve", "edge"]

# 절대 방위 여덟(EPSG) — core_side 에서 c(매스 안쪽, 방위가 아니다)를 뺀 꼴.
Dir8 = Literal["n", "ne", "e", "se", "s", "sw", "w", "nw"]


ExteriorStyle = Literal["white", "sandstone", "brick", "concrete"]



def _drop(data, keys):
    """지운 키는 **받아서 버린다** — 거부하면 그 키를 심은 저장 설계안·DB jsonb가 통째로
    안 열린다(core_axis 선례 #13). 모델 인스턴스·비 dict 입력은 그대로 둔다."""
    if isinstance(data, dict) and any(k in data for k in keys):
        data = {k: v for k, v in data.items() if k not in keys}
    return data


# ═════════════════════════════════════════════════════════════════════
# Massing — 매스
# ═════════════════════════════════════════════════════════════════════


class Massing(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_floor_count: Optional[int] = Field(
        default=None,
        json_schema_extra={"empty": "auto"},
        description=(
            "목표 층수. 사선제한으로 미달 가능. "
            "None=첫수표가 정한다(사선·일조·FAR 한계까지 쌓는다)."
        ),
    )
    first_floor_height: Optional[float] = Field(
        default=None,
        json_schema_extra={"empty": "default"},
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
    mass_axis: Optional[Literal["road", "sunlight"]] = Field(
        default=None,
        json_schema_extra={"empty": "auto"},
        description=(
            "상층 매스를 반듯하게 세울 기준 방향 — road=주접도변(도로 경계선)과 나란히, "
            "sunlight=일조발생라인(정북 인접 대지경계선)과 나란히. "
            "None=첫수표가 정한다."
        ),
    )

    @model_validator(mode="before")
    @classmethod
    def _drop_removed(cls, data):
        """`commercial_remainder` 제거 — 근생을 그리지 않고 공사비 숫자만 바꿨다(2026-09-28)."""
        return _drop(data, ("commercial_remainder",))


# ═════════════════════════════════════════════════════════════════════
# UnitSpec — 세대 프로그램
# ═════════════════════════════════════════════════════════════════════


class UnitSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    units_per_floor: Optional[int] = Field(
        default=None,
        json_schema_extra={"empty": "auto"},
        description=(
            "기준 층당 세대 수. None=첫수표가 정한다 — 층마다 (바닥−코어)/max_net_area 를 "
            "반올림한 수(최소 1): 전용 상한 안에서 가장 큰 세대(building-generator #436)."
        ),
    )
    units_by_level: dict[int, int] = Field(
        default_factory=dict,
        json_schema_extra={"empty": "auto"},
        description=(
            "층별 세대 수 override. 예: {1: 0, 2: 4, 3: 4, 4: 4, 5: 3}. "
            "1층=피로티면 0. units_per_floor보다 우선. 빈 층은 첫수표가 정한다."
        ),
    )
    max_net_area: Optional[float] = Field(
        default=60.0,
        json_schema_extra={"empty": "default"},
        description=(
            "세대 전용면적 상한(㎡, 발코니 제외). 넘는 세대가 나오면 컴파일 에러 "
            "UnitAreaExceeded. "
            "기본 60 = 소형주택 선(2026-08-28 변경, 이전 기본은 84). "
            "단지형 다세대(도시형생활주택 전용 85㎡ 이하)로 지을 땐 84, "
            "면적 제한 없는 용도는 None. "
            "상한이 없으면 분할 실패가 조용히 통과한다 — 실측: 상한 없이 돌린 "
            "9,067세대 중 84 초과 722(8.0%), 최대 5,431㎡(층 전체가 1세대)."
        ),
    )

    @model_validator(mode="before")
    @classmethod
    def _drop_removed(cls, data):
        """`cut_axis` 제거 — 엔진이 읽지 않았다(2026-09-28)."""
        return _drop(data, ("cut_axis",))

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
    """코어 — 무엇을(type) 어디에(core_side) 어느 방향으로(core_rotation) 어느 손잡이로
    (core_mirror) 앉히는가.

    치수는 입력이 아니라 매스+세대프로그램에서 derive된다(삼전 정답: 계단·EV가 16.4m
    분리 = 세대 배치 결과). 자리와 배향은 고르는 것이고, 값이 없으면 첫수표가 정한다.
    """

    model_config = ConfigDict(extra="forbid")

    type: Optional[CoreType] = Field(
        default=None,
        json_schema_extra={"empty": "auto"},
        description=(
            "코어 형상 타입 (DWG→sbim 코어 라이브러리 — giga core_library.json이 진실). "
            "None=첫수표가 정한다(매스 형상). "
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
    core_side: Optional[
        Literal["n", "ne", "e", "se", "s", "sw", "w", "nw", "c"]
    ] = Field(
        default=None,
        json_schema_extra={"empty": "auto"},
        description=(
            "코어 자리 (EPSG 절대 방위). 정방위(n·e·s·w)=매스의 그 변 가운데, "
            "대각(ne·nw·se·sw)=그 모서리, c=매스 안쪽(주접도 프레임 축을 따라 매스 "
            "경계에서 1.5m 이상 떨어진 자리 — 상층은 코어 양쪽에 편복도가 선다). "
            "그 자리에 코어가 안 들면 폴백 없이 "
            "CoreTypeInfeasible. None=첫수표가 정한다."
        ),
    )
    core_rotation: Optional[Literal[0, 90, 180, 270]] = Field(
        default=None,
        json_schema_extra={"empty": "auto"},
        description=(
            "코어 배향 — core_side로 정해진 변 기준 절대 회전각. "
            "c일 때 기준 변은 주접도 변이다. "
            "0=코어 기준자세 그대로 변에 밀착, 90/180/270=그만큼 회전. "
            "코어는 점대칭이 아니라(계단·EV 한쪽 편재, 복도 한 면 접합, 출입구 "
            "면이 방향별로 달라 0·90·180·270이 전부 다른 결과) 절반 지정인 "
            "구 core_axis(road/depth)로는 같은 축 위 180° 뒤집기를 표현할 수 없어 "
            "네 방위를 전부 받는다. 라이브러리 형상 가로세로와 무관한 앉은 변 "
            "기준 절대 표현이라 코어 형상이 바뀌어도 뜻이 유지된다. "
            "None=첫수표가 정한다."
        ),
    )
    core_mirror: Optional[bool] = Field(
        default=None,
        json_schema_extra={"empty": "auto"},
        description=(
            "코어 좌우 뒤집기 — true=코어 기준자세를 거울처럼 뒤집은 모양(앉은 변에서 "
            "봐서 계단·EV의 좌우가 바뀐 반대 손잡이)으로 앉힌 뒤 core_rotation만큼 "
            "돌린다. 회전 네 방위로는 이 모양이 안 나온다 — 회전 180°는 가로·세로를 "
            "함께 뒤집어 복도 면까지 옮기지만, 거울은 복도 면을 그대로 두고 좌우만 "
            "바꾼다. 회전과 함께 코어가 변에 앉는 여덟 자세를 전부 적는다. "
            "false=기준자세 그대로. None=첫수표가 정한다."
        ),
    )
    core_entries: Optional[int] = Field(
        default=None,
        json_schema_extra={"empty": "default"},
        description=(
            "코어(복도) 보행 출입구 수 1|2. 2=코어 문 반대편에도 문 — 보행로가 도로에서 "
            "꼬이는 필지(합정동 441-31). None=문 하나(엔진이 둘째 문을 스스로 켜지 않는다 "
            "— 2가 필요하면 옵션으로 준다). scheme `_pedestrian_paths`로 전부 방출."
        ),
    )

    @model_validator(mode="before")
    @classmethod
    def _drop_removed(cls, data):
        """지운 키를 버린다 — 거부하면 구 `_build_options.json`·DB가 안 열린다.

        - `core_axis`(road/depth, #13): 절반 지정이라(road↔{0,180}, depth↔{90,270})
          회전각으로 옮길 수 없다. 한쪽으로 접으면 없던 정밀도를 지어내는 것이라 비운다.
        - `core_along`(2026-09-28): core_side 와 겹쳤다 — 정방위가 곧 변 가운데다.
        - `composition`: EV 유무는 법(6층부터)이 정한다. 엔진이 읽지 않았다.
        """
        return _drop(data, ("core_axis", "core_along", "composition"))


# ═════════════════════════════════════════════════════════════════════
# Parking — 주차 (대수·배치)
# ═════════════════════════════════════════════════════════════════════


class Parking(BaseModel):
    """주차 — 어떤 축으로 어디에 깔까. 대수는 결과다(법정 대수는 regulations.ratio_mode).

    법정 수치(칸 2.5×5.0·차로 6.0·총 8대 캡·그룹 5대 등)는 옵션이 아니라 엔진 상수다
    (주차장법 시행규칙 — 법이 정하면 상수, 설계자가 고르면 옵션).
    """

    model_config = ConfigDict(extra="forbid")

    parking_angle: Optional[Literal[45, 60, 90]] = Field(
        default=None,
        json_schema_extra={"empty": "auto"},
        description=(
            "내부 차로 주차 각도. 45/60=사선(fishbone) — 차로폭은 "
            "주차장법 시행규칙 11조⑤1호 법정값(45° 3.5m·60° 4.0m), 연접(back) 없음, "
            "막다른 차로라 일방 진입·후진 퇴출 전제. 90=직각(차로 6m). "
            "None=첫수표가 정한다(현행 90). 사선 순차 평가는 2026-09-19에 제거됐다. "
            "외부 도로변 주차는 항상 직각(11조⑤2호 — 도로를 차로로 쓰는 형식은 "
            "직각·평행뿐)이라 inner 모드에만 의미."
        ),
    )
    parallel: Optional[bool] = Field(
        default=None,
        json_schema_extra={"empty": "law"},
        description=(
            "평행주차 열 — None=법 폴백(직각 배치가 법정 대수에 못 미칠 때만 평행 열을 쓴다, "
            "첫수표 행 아님). True=평행 열을 형태로 선택. False=쓰지 않음."
        ),
    )
    tandem: Optional[bool] = Field(
        default=None,
        json_schema_extra={"empty": "auto"},
        description=(
            "연접(직렬 2단) 백칸 허용 (제11조⑤4호). 법 행: 법정 대수 ≤ 8 이면 허용"
            "(11조⑤4호), None=첫수표가 정한다."
        ),
    )
    exit_road: Optional[int] = Field(
        default=None,
        json_schema_extra={"empty": "law"},
        description="보행통로 출구 도로변 인덱스 (필지 폴리곤 기준). None=자동(최근접 도로변).",
    )
    parking_graph: Optional[list[tuple[Dir8, Literal["road", "yard", "aisle"]]]] = Field(
        default=None,
        min_length=1,
        json_schema_extra={"empty": "auto"},
        description=(
            "주차 버블 — (진입 도로 방위, road|yard|aisle) 튜플의 배열. 위상만 적는다 — "
            "칸 수·면 자리·정렬은 대수가 결과이듯 엔진이 정한다. 배열은 명령 순서가 아니라 "
            "하나의 그림이다 — 엔진이 전체를 보고 한 번에 푼다(보행로 띠는 늘 먼저 선다). "
            "셋 다 「도로와 이어진다」가 뜻 안에 있다 — 도로와 끊긴 마당은 yard 가 아니다. "
            "긋는 것은 목뿐이다 — 목은 차가 지나가기만 하는 통로라 차 한 폭(2.5m)이면 "
            "되고, 6m 차로는 긋지 않는다(칸이 들어오면 그 앞 6m 박스들의 합집합이 차로가 "
            "된다 — 소장이 차로 면적을 아끼는 방식). 방위는 항상 dir8(null 없음)이며 "
            "칸이 모인 쪽이 아니라 그 차로가 도로에서 갈라져 나오는 자리다 — 필지에서 본 "
            "접도 구간의 방향으로 도로를 고른다(core_side 와 같은 규칙): 정방위(n·e·s·w)="
            "그 변의 가운데, 대각(ne·se·sw·nw)=그 모서리 쪽 끝(주접도도 그 방위로 적는다). "
            "road=도로 자체가 차로 — 대지 안에 차로 없음, 칸은 도로에 붙은 한 줄. "
            "aisle=도로에서 대지 안으로 곧게 이어지는 목(차 한 폭~6m) — 칸은 목 양옆에 "
            "붙고, 칸 앞 6m 박스들이 차로가 된다. "
            "yard=도로에서 들어오는 목 끝에서 여러 방향으로 칸이 붙는 것 — 목 끝 둘레에서 "
            "칸 앞 박스들이 마당이 된다. "
            "같은 도로에 둘 이상: road + 같은 방위 yard/aisle 이면 앞줄은 그 차로 자리를 "
            "비우고 깐다(목이 앞줄을 가른다). 대지 안 노드 뒤 같은 방위 대지 안 노드는 앞 "
            "노드의 차로를 지나서 든다. 한 도로에 둘 이상이면 대각으로 어느 끝인지 가른다. "
            "버블은 선호 — 법정 대수 미달일 때만, 모자란 칸에 한해 버블 밖 도로에 덧붙인다. "
            "예: 성북 [[\"n\",\"road\"],[\"sw\",\"yard\"]] — 북측 도로 앞 줄과 남서측 "
            "도로에서 들어가는 마당 · 연희 [[\"nw\",\"yard\"],[\"sw\",\"yard\"]] — 같은 "
            "서쪽 도로의 북쪽 끝·남쪽 끝에서 든 마당 둘 · 화곡 1033-19 의 두 대안 "
            "[[\"w\",\"yard\"]](서쪽 작은 마당에 칸이 세 면)과 [[\"w\",\"aisle\"]](같은 "
            "자리 곧은 차로 두 줄). None=첫수표가 정한다."
        ),
    )

    @model_validator(mode="before")
    @classmethod
    def _fold_legacy(cls, data):
        """구 저장값을 옮겨 받는다 — 거부하면 그 값을 심은 설계안이 통째로 깨진다.

        - 구 `parking_graph` 노드(dict) → (방위, road|yard|aisle) 튜플(2026-09-29 개편):
          kind 는 둘째 값으로, road 노드의 road_side 는 첫 값으로 옮긴다. 방위는 항상 8방위다
          (null 제거) — road_side 없는 노드를 만나면 방위를 지어내지 않고 그 그래프
          전체를 버린다(None). stalls·rows·via·tandem·align 은 대수·면 자리·정렬이 결과라
          옮길 자리가 없다 — 버린다.
        - `parking_axis`·`road_edge`·`multi_road`·`interior_aisle`(2026-10-05 삭제):
          주차 버블 parking_graph 가 뜻을 대신 가져갔다 — building-generator 도 어디서도
          읽지 않으니 옮길 자리가 없어 버린다. 구 `"auto"`·`"core"` 값도 같이 묻는다.
        - `count`(대수는 결과) · `type`(deprecated, 각도·축의 세 번째 이름) ·
          `bk_offset`(백칸은 칸 깊이 바로 뒤 — 법정 상수)은 버린다.
        """
        if not isinstance(data, dict):
            return data
        graph = data.get("parking_graph")
        if isinstance(graph, list) and graph and any(
            isinstance(n, dict) for n in graph
        ):
            folded = []
            for n in graph:
                if isinstance(n, dict):
                    side = n.get("road_side")
                    if n.get("kind") not in ("road", "yard", "aisle") or side is None:
                        folded = None
                        break
                    folded.append((side, n["kind"]))
                else:
                    folded.append(n)
            if folded is None:
                data = {k: v for k, v in data.items() if k != "parking_graph"}
            else:
                data = {**data, "parking_graph": folded}
        return _drop(data, ("count", "type", "bk_offset",
                            "parking_axis", "road_edge", "multi_road", "interior_aisle"))

    def bk_eff(self, stall_depth: float = 5.0) -> float:
        """백칸 밴드 시작 깊이 = 칸 깊이(법정 5.0). bk_offset 을 지워 옵션이 아니다 —
        소비처 호출부를 깨지 않으려고 시그니처만 남긴다."""
        return stall_depth


# ═════════════════════════════════════════════════════════════════════
# Circulation — 동선 (복도·보행로)
# ═════════════════════════════════════════════════════════════════════


class Circulation(BaseModel):
    """동선 — 복도·보행로를 어떻게 낼까. 보행로 폭은 법규 보정(regulations)으로 갔다."""

    model_config = ConfigDict(extra="forbid")

    corridor_mode: CorridorMode = Field(
        default="carve",
        description="보행통로 라우팅 — carve=최단, edge=필지 변 추종.",
    )


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
    """구조 치수 표준 — 사업마다 고르는 값이 아니라 회사가 정해 두는 값.

    주차 칸·차로 치수(2.5×5.0·6.0)는 주차장법 상수라 엔진이 갖는다 — 옵션이 아니다.
    """

    model_config = ConfigDict(extra="forbid")

    max_span: float = Field(default=8.0, description="기둥 최대 간격 (m).")
    cantilever: float = Field(
        default=3.0,
        description=(
            "코너 캔틸레버 한계 (m). 매스 코너에서 가장 가까운 지지(기둥·벽)까지의 거리를 "
            "축별로 재어 수직·벽따라 중 큰 쪽이 이 값 이하여야 한다. "
            "GT 1층 203장 중 193장이 3 m 이하(실측)."
        ),
    )
    min_col_dist: float = Field(default=3.0, description="기둥 최소 간격 (m).")

    @model_validator(mode="before")
    @classmethod
    def _drop_removed(cls, data):
        """주차 칸·차로 치수 제거 — 주차장법 상수다(2026-09-28).
        `preferred_min_span` 제거 — 엔진이 읽지 않았다(2026-10-08)."""
        return _drop(data, (*_PARKING_DIMS, "preferred_min_span"))


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
# RegulationOverrides — 법규 보정
# ═════════════════════════════════════════════════════════════════════


class RegulationOverrides(BaseModel):
    """법규 보정 — 법이 정하는 값을 필지 사정으로 덮어쓴다. 평소엔 전부 비워 둔다.

    수(설계자가 고르는 것)가 아니라 법(용도지역 룩업·조례·시행령)이 틀리거나 완화된
    예외 필지에서만 쓴다. 그래서 설계 묶음과 따로 모았다(2026-09-28).
    """

    model_config = ConfigDict(extra="forbid")

    far_limit_override: Optional[float] = Field(
        default=None,
        json_schema_extra={"empty": "law"},
        description=(
            "용적률 법정 한도 덮어쓰기 (%) — 지구단위계획·완화 등 용도지역 룩업이 틀린 "
            "예외 필지용. None=법이 정한다. (구 이름 far_target)"
        ),
    )
    bcr_limit_override: Optional[float] = Field(
        default=None,
        json_schema_extra={"empty": "law"},
        description=(
            "건폐율 법정 한도 덮어쓰기 (%) — 지구단위계획·완화 등 용도지역 룩업이 틀린 "
            "예외 필지용. None=법이 정한다. (구 이름 bcr_target)"
        ),
    )
    setback_overrides: dict[str, float] = Field(
        default_factory=dict,
        description="방향별 후퇴거리 (m). 예: {'north': 1.5, 'side': 0.8}.",
    )
    road_setback: Optional[float] = Field(
        default=None,
        json_schema_extra={"empty": "law"},
        description=(
            "주차구획 전면선의 주도로 경계 셋백 (m). None=도로산입 derive — "
            "주차장법 시행규칙 11조⑤2호: 직각주차 차로는 도로 포함 6m 이상, "
            "미달분(max(0, 6−실측 도로폭))만큼 후퇴. 12m↑ 도로·폭 미상은 0. "
            "명시(0 포함) 시 그 값 — 설계자가 도로 여건상 밀착·완화를 판단한 "
            "의도 기록 (GT 실측: 6m 미만 이면도로에서도 경계 밀착 다수). "
            "(구 자리 parking.road_setback)"
        ),
    )
    pedestrian_width: Optional[float] = Field(
        default=1.5,
        json_schema_extra={"empty": "default"},
        description=(
            "보행통로 폭 (m). 기본 1.5 (시행령 41조 다세대 유효너비 하한). "
            "None=용도별 derive (다세대 1.5 등). (구 자리 circulation.pedestrian_width)"
        ),
    )
    ratio_mode: ParkingRatioMode = Field(
        default="multi_family",
        description=(
            "법정 주차대수 산정 기준 (서울시 주차장 조례). "
            "multi_family=공동주택(도시형생활주택·다세대): "
            "30㎡↓ 0.5대, 30~60㎡ 0.8대, 60㎡↑ 1.0대, 합계 올림. "
            "non_residential=비공동주택(근생·다가구·다중): "
            "60㎡↓ 0.5대, 60㎡↑ 0.7대, 합계 반올림. (구 자리 parking.ratio_mode)"
        ),
    )

    @model_validator(mode="before")
    @classmethod
    def _rename_legacy(cls, data):
        """구 이름 `far_target`·`bcr_target` → `*_limit_override`. 새 이름이 이미 있으면
        그쪽이 이긴다. 「목표」가 아니라 법정 한도를 바꾸는 값이라 이름을 뜻에 맞췄다."""
        if isinstance(data, dict) and any(k in data for k in _REG_RENAMED):
            data = dict(data)
            for old, new in _REG_RENAMED.items():
                if old in data:
                    v = data.pop(old)
                    if data.get(new) is None:
                        data[new] = v
        return data

    def walk_width(self, use: str | None = None) -> float:
        """보행통로 폭 — 명시 > 용도 derive > 기본 1.2 (용도별 규정)."""
        if self.pedestrian_width is not None:
            return self.pedestrian_width
        table = {"multi_family": 1.5, "dagagu": 1.1, "retail": 1.5}
        return table.get(use or "", 1.2)

    def aisle(self, use: str | None = None) -> float:
        """그룹 분리 차로 간격 = max(법정 하한 2.5, 보행폭)."""
        return max(2.5, self.walk_width(use))


_REG_RENAMED = {"far_target": "far_limit_override", "bcr_target": "bcr_limit_override"}
# 옛 자리 → regulations 로 옮긴 필드 (묶음, 필드)
_TO_REGULATIONS = (("parking", "road_setback"), ("parking", "ratio_mode"),
                   ("circulation", "pedestrian_width"))

# ═════════════════════════════════════════════════════════════════════
# Design · Standards · Business — 속성 창을 세 묶음으로
# ═════════════════════════════════════════════════════════════════════


class Design(BaseModel):
    """이 설계에서 고르는 것.

    비울 수 있는 필드는 전부 비웠을 때 누가 정하는지를 `json_schema_extra={"empty": …}`
    하나로 적는다 — `auto`=첫수표가 채운다(ResolvedDesign 에 나온다), `law`=법이 정한다,
    `default`=적힌 sbim 기본값. `AUTO_FIELDS`가 auto 집합이다.

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

    @model_validator(mode="before")
    @classmethod
    def _move_to_regulations(cls, data):
        """옛 자리(parking.road_setback·parking.ratio_mode·circulation.pedestrian_width)로
        오면 regulations 로 옮겨 받는다. regulations 에 이미 값이 있으면 그쪽이 이긴다."""
        if not isinstance(data, dict):
            return data
        moves = [(sec, f) for sec, f in _TO_REGULATIONS
                 if isinstance(data.get(sec), dict) and f in data[sec]]
        if not moves:
            return data
        data = dict(data)
        reg = data.get("regulations")
        if isinstance(reg, BaseModel):       # 모델 인스턴스면 명시한 값만 펴서 합친다
            reg = reg.model_dump(exclude_unset=True)
        reg = dict(reg or {})
        for sec, f in moves:
            data[sec] = dict(data[sec])
            reg.setdefault(f, data[sec].pop(f))
        data["regulations"] = reg
        return data


def _empty_markers() -> dict[str, str]:
    """design 의 `"<묶음>.<필드>"` → 비웠을 때 누가 정하나(auto|law|default)."""
    out = {}
    for sec, f in Design.model_fields.items():
        if isinstance(f.annotation, type) and issubclass(f.annotation, BaseModel):
            for name, ff in f.annotation.model_fields.items():
                extra = ff.json_schema_extra
                if isinstance(extra, dict) and "empty" in extra:
                    out[f"{sec}.{name}"] = extra["empty"]
    return out


EMPTY_MARKERS: dict[str, str] = _empty_markers()
# 첫수표가 채우는 필드 — types.ResolvedDesign 의 잎과 같아야 한다(test_auto_fields.py)
AUTO_FIELDS: frozenset[str] = frozenset(k for k, v in EMPTY_MARKERS.items() if v == "auto")


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


_log = logging.getLogger(__name__)

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
    "core_entries": "core", "core_mirror": "core",
    "parallel": "parking", "multi_road": "parking",
    "parking_axis": "parking", "parking_angle": "parking", "road_edge": "parking",
    "entry2": "parking", "tandem": "parking", "exit_road": "parking",   # entry2→multi_road
    "parking_graph": "parking",
    "interior_aisle": "parking",            # Parking 이 parking_axis 로 흡수한다
    "road_setback": "regulations", "pedestrian_width": "regulations",
    "corridor_mode": "circulation",
    "max_span": "dimensions", "cantilever": "dimensions",
    "min_col_dist": "dimensions",
}
# 지운 필드 — 옮길 곳이 없어 이행층에서 바로 버린다(2026-09-28 정리)
_GF_DROPPED = {"bk_offset", "commercial_remainder", "core_along", "preferred_min_span"}
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

        구 모양 안에서 구 `ground_floor.<k>` 와 신 거처(`core`·`parking`·`regulations`)의
        같은 키가 함께 오면 **신 위치가 이긴다**(사용자가 채운 칸은 존중) — 값이 다르면
        경고 로그 한 줄만 남기고 거부하지 않는다(구 모양을 보내는 호출자를 깨지 않는다).
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
            for k in _PARKING_DIMS:                 # 주차장법 상수 — 버린다
                park.pop(k, None)
            design["parking"] = park
        for k, v in (data.get("ground_floor") or {}).items():
            k = _RENAMED.get(k, k)
            if k in _GF_DROPPED:
                continue
            target = _GF_TO.get(k)
            if target is None:                      # 모르는 키는 parking에 남겨 거부되게 둔다
                design.setdefault("parking", {})[k] = v
            elif target == "dimensions":
                dims[k] = v
            else:
                slot = design.setdefault(target, {})
                if k in slot:                       # 신 위치가 이미 채워졌다 — 신 우선
                    if slot[k] != v:
                        _log.warning(
                            "legacy ground_floor.%s=%r ignored: %s.%s=%r already set",
                            k, v, target, k, slot[k])
                    continue
                slot[k] = v
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
        """상층 면적 비율. 건폐율 법정 한도 덮어쓰기(bcr_limit_override) 우선."""
        if self.design.regulations.bcr_limit_override is not None:
            return self.design.regulations.bcr_limit_override / 100
        return default
