"""Pydantic types — scheme.json / units.json 데이터 계약의 **정본**.

이 파일이 정본이다. typescript/src/types.ts 는 손으로 맞춘 TS 판이고
tests/test_types_parity.py 가 두 쪽의 필드 집합이 같은지 지킨다.
schema/scheme.schema.json·units.schema.json 은 여기서 생성된다
(scripts/gen_build_options.py) — 손으로 고치지 않는다.

규율: 생성기가 새 키·userData kind를 방출하려면 **여기에 먼저** 정의하고 TS 를
맞춘 뒤 sbim을 푸시하고, 소비처가 물어간다.

userData 계열은 검증 강제 없음(extra=allow·전 필드 기본값) — 계약 문서화 목적.
좌표계: 링·점은 EPSG:5186 절대, 메시 positions만 parcel_center 상대.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, SerializerFunctionWrapHandler, model_serializer

from .errors import CompileError
from .options import CoreType


class _Base(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)  # 알려지지 않은 필드 허용 · 밑줄 별칭


# --- BufferGeometry (THREE.js 직렬화 형식) ----------------------------------


class BufferAttributeData(_Base):
    itemSize: int
    type: str  # e.g. "Float32Array"
    array: list[float]


class _BufferAttributes(_Base):
    position: BufferAttributeData
    normal: BufferAttributeData
    uv: Optional[BufferAttributeData] = None


class _BufferIndex(_Base):
    type: str  # e.g. "Uint32Array"
    array: list[int]


class _BufferGeometryInner(_Base):
    attributes: _BufferAttributes
    index: _BufferIndex


class _BufferGeometryMetadata(_Base):
    version: float
    type: str
    generator: str


class BufferGeometryData(_Base):
    metadata: _BufferGeometryMetadata
    uuid: str
    type: Literal["BufferGeometry"]
    data: _BufferGeometryInner
    # LOD300 부재 메타 (three.js 표준 필드) — kind 판별 dict.
    # 형태는 아래 *UserData 모델들 참조 (TS PartUserData 유니언과 동일 계약)
    userData: Optional[dict] = None


# --- LOD300 부재 userData (kind 판별) — 경량 문서화 모델 ---------------------
# 생성기 방출부(geometry.py·units.py·stairs.py)가 정본. 검증 강제 없음.

Point2 = tuple[float, float]
Ring = list[Point2]


class MaterialLayer(_Base):
    name: str = ""
    t: float = 0            # 두께 (m)


class WallUserData(_Base):
    kind: Literal["wall"] = "wall"
    # 벽 구실 exterior|unit_boundary|partition|core — 엔진은 세대 안 칸막이에 "partition" 만 낸다(#549, 2026-10-16).
    # 없으면 exterior 불리언으로.
    role: Optional[str] = None
    p0: Point2 = (0, 0)     # 벽 중심선 양끝 (EPSG 절대)
    p1: Point2 = (0, 0)
    t: float = 0            # 구조 두께 — 중심선 양쪽 t/2
    t_total: Optional[float] = None    # 총두께(구조+단열+마감) — 개구는 이걸로
    offset_out: Optional[float] = None  # 기준선→외피 (IFC 레이어셋 offset)
    exterior: bool = False
    base_z: float = 0
    top_z: float = 0
    quad: Optional[Ring] = None        # 마이터 확정 quad (emitter 단일 소스)
    layers: list[MaterialLayer] = []


class SlabUserData(_Base):
    kind: Literal["slab"] = "slab"
    outline: Ring = []
    t: float = 0
    t_struct: Optional[float] = None
    top_z: float = 0        # 상면 z — 두께는 하향 점유
    role: str = "interfloor"           # interfloor | foundation | roof
    layers: Optional[list[MaterialLayer]] = None


class ColumnUserData(_Base):
    kind: Literal["column"] = "column"
    center: Point2 = (0, 0)
    size: float = 0
    base_z: float = 0
    top_z: float = 0
    transfer: bool = False  # 전이보와 만나는 기둥
    on_beams: int | None = None  # 이 기둥 위를 지나는 보 개수 — 구조 프레임 술어(≥1). None=미방출


class BeamUserData(_Base):
    kind: Literal["beam"] = "beam"
    p0: Point2 = (0, 0)
    p1: Point2 = (0, 0)
    w: float = 0
    h: float = 0            # 춤 — top_z에서 하향
    top_z: float = 0
    role: str = "transfer"  # transfer(필로티 외곽 전이보) | sloped(사선꺾임) | girder(기둥↔기둥 주보) | beam(작은보)


class HostWallRef(_Base):
    p0: Point2 = (0, 0)
    p1: Point2 = (0, 0)
    t: float = 0
    t_total: Optional[float] = None


class DoorUserData(_Base):
    kind: Literal["door"] = "door"
    p0: Point2 = (0, 0)
    p1: Point2 = (0, 0)
    width: float = 0
    height: float = 0
    unit_id: Optional[str] = None
    door_type: Optional[str] = None    # 공동현관 | 욕실 | 옥상 | None=세대현관
    fire_exit: Optional[bool] = None
    swing_into: Optional[Point2] = None  # 스윙이 향할 실내 기준점
    host_wall: Optional[HostWallRef] = None


class WindowUserData(_Base):
    kind: Literal["window"] = "window"
    p0: Point2 = (0, 0)
    p1: Point2 = (0, 0)
    width: float = 0
    height: float = 0
    sill: float = 0         # 창대 바닥 z — 절대 m (층 바닥 기준 아님: 층 바닥 + 0.9). 층 기준은 sill - floor_bottom_height
    wall_t: Optional[float] = None
    wall_total: Optional[float] = None  # 개구는 총두께로 뚫어야 단열 띠까지
    type: Optional[str] = None
    unit_id: Optional[str] = None
    host_wall: Optional[HostWallRef] = None


class CoveringUserData(_Base):
    kind: Literal["covering"] = "covering"
    role: str = "ceiling"   # ceiling | flooring
    t: float = 0
    top_z: float = 0
    outline: Ring = []
    layers: Optional[list[MaterialLayer]] = None


class RailingUserData(_Base):
    kind: Literal["railing"] = "railing"
    base_z: float = 0
    top_z: float = 0
    wall_top_z: float = 0   # 하부 낮은벽 상단 (0 = 동자+손스침만)
    bar: float = 0          # 손스침 단면
    lines: list[Ring] = []  # 난간 중심선 — parcel_center 상대(메시 좌표계, p0·p1 과 달리 절대 아님). posts 도 같다


class StairMemberUserData(_Base):
    kind: Literal["stair_member"] = "stair_member"
    part: str = "tread"     # tread | riser | landing
    index: int = 0
    z0: float = 0
    z1: float = 0


class StairLayoutItem(_Base):
    """코어 6타입 정답지 배치 — flight quad = [시작변0,시작변1,끝변1,끝변0],
    p0→p3 = 진행(오름) 방향."""
    role: str = "flight"    # flight | landing
    quad: Ring = []
    n: Optional[int] = None  # flight 단수


class StairUserData(_Base):
    kind: Literal["stair"] = "stair"
    quad: Ring = []
    riser: float = 0
    tread: float = 0
    n_risers: int = 0
    waist: float = 0
    flights: int = 0
    layout: Optional[list[StairLayoutItem]] = None  # 있으면 arms/quad보다 우선
    arms: Optional[list[Ring]] = None   # (구) ㄱ자 3분해 — layout 없는 scheme용
    runs: Optional[list[float]] = None


# --- Floor / FloorPlan -----------------------------------------------------


class FloorData(_Base):
    floor_id: int
    floor_area: float
    floor_height: float
    floor_bottom_height: float
    floor_name: Optional[str] = None   # 옥탑층·지붕층 등 특수 층
    parking_count: Optional[int] = None


_GeomBucket = list[list[BufferGeometryData]]


class FloorGeometry(_Base):
    walls: _GeomBucket
    floors: _GeomBucket
    roof: Optional[_GeomBucket] = None
    windows: Optional[_GeomBucket] = None
    parapets: Optional[_GeomBucket] = None      # userData.kind="railing"
    columns: Optional[_GeomBucket] = None
    parking_stalls: Optional[_GeomBucket] = None
    doors: Optional[_GeomBucket] = None         # userData.kind="door"
    beams: Optional[_GeomBucket] = None         # userData.kind="beam"
    stairs: Optional[_GeomBucket] = None        # kind="stair"|"stair_member"
    coverings: Optional[_GeomBucket] = None     # userData.kind="covering"


class FloorPlan(_Base):
    data: FloorData
    geom: FloorGeometry


# --- Scheme (top-level) ----------------------------------------------------


class SchemeData(_Base):
    lot_area: float
    build_area: float
    far: float
    bcr: float
    pnu: int | str


class CoreLayout(_Base):
    """코어 내부 분할 — 링은 EPSG 절대."""
    ev: Optional[Ring] = None
    stair: Optional[Ring] = None
    corridor: Optional[Ring] = None
    ev_front: Optional[Ring] = None


class EngineStamp(_Base):
    """이 설계안을 만든 엔진 빌드 도장 — 서버 결과를 추적·재현한다. 전부 문자열.
    같은 소스라도 CPU 아키텍처가 다르면 컴파일 분기가 갈릴 수 있어 platform 을 남긴다."""
    engine_commit: str = Field(description="엔진 저장소 커밋 SHA — 이 도면을 만든 빌드")
    platform: str = Field(description='엔진이 돈 플랫폼 — "linux-x86_64" · "darwin-arm64" 등')
    python: str = Field(description="엔진 파이썬 버전 문자열")
    compiled_at: str = Field(description="컴파일 시각 — ISO-8601 UTC")


class ColumnSection(_Base):
    """기둥 실단면 하나 — _column_centers의 같은 자리 기둥을 정사각이 아니라 이 단면으로 그린다.
    w는 빔 축 방향, d는 그 가로, angle_deg는 w 축의 각(도)."""
    center: Point2 = Field(description="기둥 중심 (EPSG:5186 절대) — _column_centers와 같은 프레임·같은 순서")
    w: float = Field(description="단면 치수 (m) — 빔 축 방향")
    d: float = Field(description="단면 치수 (m) — 빔 축의 가로")
    angle_deg: float = Field(description="w 축의 각 (도)")


class LegalCheck(_Base):
    """법규 체크리스트 한 항목의 판정 실값 — key는 giga legal_checklist.yaml 의 key(변경 금지,
    그래프 노드 id)."""
    key: str
    group: str
    item: str
    status: str = Field(description="'적용' | '해당없음' | '검토' | '참고' 또는 실값 포함('적용 (확폭 12㎡)')")
    apply: str = Field(description="적용 내용 — 산출값 채워진 문장")
    law: str = Field(description="근거 조문")
    note: Optional[str] = None


def _spatial(alias: str, description: str | None = None):
    """밑줄 키 필드 — pydantic 은 `_` 로 시작하는 이름을 private 로 보므로 alias 로 받는다."""
    return Field(default=None, alias=alias, description=description)


class SchemeSpatial(_Base):
    """scheme.json 최상위 밑줄 키 — 생성기 scheme 방출부 방출 계약. 전부 옵셔널(구 scheme 호환).

    JSON 키는 `_core_layout` 처럼 밑줄로 시작하고(alias), 파이썬 속성은 밑줄을 뗀 이름이다
    (`scheme.core_layout`). 덤프는 늘 alias 로 나가고(serialize_by_alias), 입력에 없던 키는
    덤프에서도 빠진다 — 「없음 = 구 scheme」과 `_compile_errors` 의 「없음 vs []」를 지킨다.
    """

    model_config = ConfigDict(
        extra="allow", validate_by_name=True, validate_by_alias=True, serialize_by_alias=True,
    )

    core_layout: Optional[CoreLayout] = _spatial("_core_layout")
    parking_stalls: Optional[list[Ring]] = _spatial("_parking_stalls")
    column_centers: Optional[list[Point2]] = _spatial("_column_centers")
    basement_outline: Optional[Ring] = _spatial("_basement_outline")
    floor_outlines: Optional[dict[str, Ring]] = _spatial(
        "_floor_outlines", "층별 footprint ring — 복도(=층외곽−세대−코어) 유도 기준")
    pedestrian_path: Optional[Ring] = _spatial(
        "_pedestrian_path", "보행 출입로 (도로→코어) — 보행 경로 산출. 1F 전용")
    pedestrian_paths: Optional[list[Ring]] = _spatial(
        "_pedestrian_paths", "보행 출입로 전부 — 코어 문 2개(#35)면 2개. [0] === _pedestrian_path (호환)")
    halls: Optional[dict[str, list[Ring]]] = _spatial(
        "_halls",
        "DH 공용 홀 — {level: ring[]}. 코어 복도 띠를 양옆으로 늘인 팔·EV 로비(연희 75-9 GT T자 홀 — "
        "코어로 갈라진 2조각이라 링 목록). 세대에서 차감된 공용, 접면 연결계 = 코어 복도 ∪ 홀")
    penthouse_outline: Optional[Ring] = _spatial(
        "_penthouse_outline", "옥탑(계단탑) 외곽 — 옥탑층·지붕층 평면이 공유")
    common_footprint: Optional[Ring] = _spatial("_common_footprint", "전층 교집합 — 코어 탐색공간")
    validation: Optional[list[str]] = _spatial("_validation", "준법 위반·경고 메모")
    column_size: Optional[float] = _spatial(
        "_column_size",
        "기둥 단면 한 변 (m) — Concrete.column_size 확정값. 도면 재구성이 scheme만 보고도 "
        "같은 크기를 그리도록 방출(폴백 이원화 방지).")
    column_sections: Optional[list[ColumnSection]] = _spatial(
        "_column_sections",
        "기둥 실단면 목록 — _column_centers와 같은 좌표 프레임·같은 순서. 있음이면 소비처는 "
        "정사각 대신 이것으로 그린다(얇은 단면 기둥을 정사각으로 그리면 주차 칸을 문다). "
        "없음 = _column_size 정사각 폴백 (구 scheme).")
    north_ref_edges: Optional[list[tuple[Point2, Point2]]] = _spatial(
        "_north_ref_edges",
        "정북일조 기준선 (EPSG:5186 절대, 변마다 [p1,p2]) — 3D 뷰어 천공면. 북향 변마다 별도 "
        "엣지(상업 인접 면제·도로 인접은 중심선 offset), 매스 깎기(apply_north_setback)와 "
        "동일 기준. 면제면 [].")
    north_datum_offset: Optional[float] = _spatial(
        "_north_datum_offset",
        "정북일조 기산면 보정 (m) — 영 119조①5호 나목: 높이는 본 대지와 북측 인접대지의 평균 "
        "수평면 기준. z0 − 본 대지 지표면 = 고저차의 1/2. 천공면 그리기: 유효높이 h' = z − 이 값 "
        "(경사지에서 프로파일이 수직으로 이동). 미방출·null이면 0(평지 가정).")
    legal_checks: Optional[list[LegalCheck]] = _spatial(
        "_legal_checks",
        "법규 체크리스트 33항목 판정 실값 (giga legal_checklist.yaml SSOT, #16). 합격/불합격이 "
        "아니라 적용여부 + 산출값이다 — 엔진은 규제를 생성 단계에서 지켜버리므로(사선은 매스를 "
        "깎고, 미충족은 compile_errors) 완성 설계에 '미달' 항목이 존재할 수 없다. law-graph가 "
        "결정 노드에서 근거 조문으로 엣지를 이을 때 이 실값을 쓴다. 구 scheme엔 없다 — 소비처는 "
        "부재를 \"구 버전\"으로 처리할 것.")
    compile_errors: Optional[list[CompileError]] = _spatial(
        "_compile_errors",
        "엔진이 이 설계안을 스스로 거절한 사유 (errors.py CompileError — type·reason·details·"
        "suggestion). 없음 또는 [] = 컴파일 통과. 하나 이상이면 설계는 저장됐지만 경고와 함께 "
        "보여야 한다.")
    engine_stamp: Optional[EngineStamp] = _spatial(
        "_engine_stamp",
        "이 설계안을 만든 엔진 빌드 도장 (EngineStamp) — 서버 결과를 추적·재현한다. 전부 문자열. "
        "구 scheme엔 없다 — 소비처는 부재를 \"구 버전\"으로 처리할 것.")
    mep: Optional[list["MepItem"]] = _spatial(
        "_mep",
        "설비 (제안 2026-10-16, #549 — 엔진 미방출). 계통별 평면도(위생·냉난방·환기·가스·전기)의 "
        "재료. 처음엔 기기(kind: \"device\") 자리만이어도 도면이 된다. 좌표 EPSG 절대.")

    @model_serializer(mode="wrap")
    def _omit_unset_spatial(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        """입력에 없던 밑줄 키는 덤프에도 없다 — 없음(구 scheme)이 null 로 바뀌지 않는다."""
        out = handler(self)
        spatial = {}
        for name, f in SchemeSpatial.model_fields.items():
            for key in (f.alias, name):
                if key in out:
                    v = out.pop(key)
                    if name in self.model_fields_set:
                        spatial[key] = v
        out.update(spatial)                      # 밑줄 키는 data·floor_plans 뒤에 둔다
        return out


class Scheme(SchemeSpatial):
    """scheme.json — data·floor_plans·unit_ids + 밑줄 키(SchemeSpatial)."""
    data: SchemeData
    floor_plans: list[FloorPlan]
    unit_ids: list[str]
    resolved_options: Optional["ResolvedOptions"] = Field(
        default=None, description="엔진이 실제로 쓴 속성 창 값 + 출처. 구 scheme엔 없다.")


# --- resolved_options (엔진이 채운 속성 창) -----------------------------------


class _ResolvedMassing(_Base):
    mass_axis: Optional[Literal["road", "sunlight"]] = None
    target_floor_count: Optional[int] = None


class _ResolvedUnits(_Base):
    # 층마다 세대 수가 다르면(예: 3·3·2·1·1) units_per_floor 는 null — 되먹임은 units_by_level 로.
    units_per_floor: Optional[int] = None
    units_by_level: Optional[dict[int, int]] = None


class _ResolvedCore(_Base):
    type: Optional[CoreType] = None
    core_side: Optional[Literal["n", "ne", "e", "se", "s", "sw", "w", "nw", "c"]] = None
    core_rotation: Optional[Literal[0, 90, 180, 270]] = None
    core_mirror: Optional[bool] = None


class _ResolvedParking(_Base):
    parking_angle: Optional[Literal[45, 60, 90]] = None
    tandem: Optional[bool] = None
    parking_graph: Optional[list[tuple[str, str]]] = None   # 엔진이 실제로 푼 버블 (방위, road|yard|aisle)


class ResolvedDesign(_Base):
    """`BuildOptions.design`과 같은 중첩 모양 — 첫수표가 채우는 필드(`empty: "auto"`)만.
    잎 집합은 `options.AUTO_FIELDS`와 같다(tests/test_auto_fields.py가 지킨다)."""
    massing: Optional[_ResolvedMassing] = None
    units: Optional[_ResolvedUnits] = None
    core: Optional[_ResolvedCore] = None
    parking: Optional[_ResolvedParking] = None


class ResolvedOptions(_Base):
    """엔진이 실제로 쓴 속성 창 값 + 필드별 출처 — 엔진이 방출, 소비처가 표시.

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
    design: ResolvedDesign
    source: dict[str, Literal["user", "prior"]] = {}


# --- Unit -------------------------------------------------------------------


class UnitGeometry(_Base):
    boundary: list[BufferGeometryData]


class UnitData(_Base):
    id: str
    name: str = ""
    price: float = 0
    floor_id: int
    floor_height: float = 0
    floor_bottom_height: float = 0
    area_net: float = 0           # 전용 (발코니 차감 후 — 주차 산정 기준)
    area_common: float = 0        # 공용 (계단·EV·복도 지분 안분)
    land_portion: float = 0
    area_contract: float = 0      # 분양 = net + common
    area_veranda: float = 0       # 베란다 — 위층 step-back 슬래브 (건축법 정의)
    area_balcony: float = 0       # 발코니 — 외벽 캔틸레버 (목적: 전용 임계 하향 → 주차 절감)
    balcony_depth: float = 0      # 발코니 실효 폭 (m, ≤ 1.5 법정)
    area_service: float = 0       # legacy alias = area_veranda (호환용, 신규 코드는 area_veranda 사용)


class Unit(_Base):
    geom: UnitGeometry
    data: UnitData


# --- units.json (생성기 직렬화 실계약) ----------------------------------------
# 위 Unit/UnitData(flat area_*)는 BuildingVisualizer 레거시 경로용.
# 생성기 units.json 레코드는 아래 UnitRecord(중첩 area{})다 — 신규 코드는 이쪽.


class UnitAreaBreakdown(_Base):
    net: Optional[float] = None
    common: Optional[float] = None
    land_portion: Optional[float] = None
    contract: Optional[float] = None
    veranda: Optional[float] = None
    veranda_eq: Optional[float] = None
    balcony: Optional[float] = None
    balcony_depth: Optional[float] = None
    service: Optional[float] = None
    actual_use: Optional[float] = None
    duplex_upper: Optional[float] = None


class UnitRoom(_Base):
    """방 최소 의미론 — 벽·문 기하는 geom userData가 따로 옴.

    엔진은 욕실·주방과, 그 외 남는 면적을 거실 하나로 낸다(#549, 2026-10-16). 침실·현관·발코니·다용도실·복도 는 제안."""
    use: str = ""           # 욕실 | 주방 | 거실 | 침실 | 현관 | 발코니 | 다용도실 | 복도
    polygon: Ring = []
    floor_finish: Optional[str] = None   # 바닥 마감 이름 — 제안, 미방출
    ceiling_h: Optional[float] = None    # 천장고 m — 제안, 미방출


class UnitFixture(_Base):
    """세대 안 가구·기구 (제안 2026-10-16, #549 — 엔진 미방출).

    소비처는 kind 별 2D 기호·3D 상자만 그린다 — 종류 이름과 자리·치수면 된다.
    kind 어휘(BIMx 샘플): 싱크·쿡탑·인덕션·후드·냉장고·세탁기·상부장·하부장·아일랜드식탁·
    세면대·대변기·샤워부스·젠다이·신발장·침대·소파·의자·식탁."""
    kind: str
    origin: Point2 = (0, 0)          # 발자국 기준점(EPSG 절대) — w×d 사각의 왼쪽 아래
    angle_deg: Optional[float] = None  # w 축의 각(도, 반시계) — 없으면 0
    w: float = 0
    d: float = 0
    h: Optional[float] = None        # 없으면 종류 기본값
    room_index: Optional[int] = None  # rooms 인덱스


class MepItem(_Base):
    """설비 항목 하나 (제안 2026-10-16, #549 — 엔진 미방출). 배관·덕트는 path, 기기는 origin.

    system: water|drain|heating|vent|gas|elec · kind: pipe|duct|device · 좌표 EPSG 절대."""
    system: str
    kind: str
    name: Optional[str] = None       # 급수분배기 · 전열교환기 · 배기팬 · 보일러 …
    floor_id: Optional[int] = None
    origin: Optional[Point2] = None
    path: Optional[Ring] = None
    size: Optional[float] = None     # 지름·폭 m


class UnitRecord(_Base):
    """units.json 레코드 — 생성기 units 직렬화 계약."""
    id: str
    floor: int
    floor_height: Optional[float] = None
    floor_bottom_height: Optional[float] = None
    price: float = 0
    area: UnitAreaBreakdown = UnitAreaBreakdown()
    # 메시 — DB 저장 시 Json 이라 모양 미보장(TS `unknown`). 실제 units.json 은 BufferGeometryData 의 **리스트**라
    # UnitGeometry 로 받으면 샘플이 안 열린다(2026-10-16 확인).
    geom: Optional[Any] = None
    polygon: Optional[Ring] = None      # 주층 단일 ring (호환용)
    duplex_upper_polygon: Optional[Ring] = None
    balcony_polygons: Optional[list[Ring]] = None
    polygons_by_floor: Optional[dict[str, Ring]] = None  # 층 점유 (생성기 계약 ③)
    rooms: Optional[list[UnitRoom]] = None
    fixtures: Optional[list[UnitFixture]] = None   # 가구·기구 — 제안(#549), 미방출


# --- site.json (제안 2026-10-16, #549 덧붙임 — 엔진 미방출) ---------------------------------


class SiteInfo(_Base):
    """설계안 폴더의 `site.json` — 필지·도로·외곽선. 키 이름·좌표(EPSG:5186 절대)는 엔진 building_info 와 같다.

    scheme.json 에 없어 에디터가 대지 경계·도로·정북 한계선을 못 그리던 것을 채운다. TS `SiteInfo` 와 같은 모양."""
    parcel_polygon: Ring = []
    parcel_center: Point2 = (0, 0)
    road_polygon: Optional[list[Ring]] = None
    road_polygon_wide: Optional[list[Ring]] = None
    road_centerlines: Optional[list[Ring]] = None
    road_centerline_widths: Optional[list[float]] = None
    effective_parcel_outline: Optional[Ring] = None
    buildable_outline: Optional[Ring] = None
    footprint_outline: Optional[Ring] = None
    north_datum_offset: Optional[float] = None
    raw_parcel_area: Optional[float] = None
    effective_parcel_area: Optional[float] = None
    road_widening_area: Optional[float] = None
    corner_cut_area: Optional[float] = None


# --- 설계안 묶음(.sbim) manifest.json — bundle.py ------------------------------------


class BundleManifest(_Base):
    """`.sbim`(설계안 JSON 들의 zip) 안의 manifest.json. 꼴·항목 규칙은 bundle.py 머리말. TS `BundleManifest` 와 같은 모양."""
    format: Literal["sbim-bundle"] = "sbim-bundle"
    bundle_version: int = 1
    sbim_version: str
    # ISO 8601 UTC 초 단위 — 2026-10-16T03:00:00Z
    created_at: str
    land_ids: list[str] = []
    design_id: Optional[str] = None
    # scheme.json 의 `_engine_stamp` 를 옮겨 적는다 — 어느 엔진 판이 낸 안인지
    engine_stamp: Optional[dict] = None
    # {항목 이름: sha256 hex} — manifest 자신은 빼고 묶은 항목 전부
    files: dict[str, str]


# --- Surroundings ----------------------------------------------------------


class SurroundingGeometry(_Base):
    boundary: list[BufferGeometryData]


class SurroundingData(_Base):
    address: Optional[str] = None
    height: float
    floor: int


class SurroundingBuilding(_Base):
    geom: SurroundingGeometry
    data: SurroundingData


Scheme.model_rebuild()
