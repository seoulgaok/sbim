"""Pydantic types — scheme.json / units.json 데이터 계약 (typescript/src/types.ts와 동기).

규율: 생성기가 새 키·userData kind를 방출하려면 **여기와 TS에 먼저** 정의하고
sbim을 푸시한 뒤 소비처가 물어간다. schema/*.json은 walls/floors/roof 시절의
산물 — 현재 정본은 types.ts + 이 파일이다.

userData 계열은 검증 강제 없음(extra=allow·전 필드 기본값) — 계약 문서화 목적.
좌표계: 링·점은 EPSG:5186 절대, 메시 positions만 parcel_center 상대.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class _Base(BaseModel):
    model_config = ConfigDict(extra="allow")  # 알려지지 않은 필드 허용


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
    sill: float = 0         # 창대 높이 (층 바닥 기준)
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
    lines: list[Ring] = []


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


class Scheme(_Base):
    """scheme.json — 밑줄 키(SchemeSpatial 상당)는 extra=allow로 통과.

    생성기가 방출하는 밑줄 키 계약(TS SchemeSpatial 동일):
    _core_layout(CoreLayout)·_parking_stalls·_column_centers·_basement_outline·
    _floor_outlines·_pedestrian_path·_pedestrian_paths(보행로 전부, [0]=_pedestrian_path —
    코어 문 2개 #35)·_halls({level: ring} D4 편복도(공용) — 접면 연결계 = 복도∪편복도)·
    _penthouse_outline·_common_footprint·_validation·_north_ref_edges·_north_datum_offset·
    _column_size·_legal_checks(법규 33항목 판정 실값 — key는 legal_checklist.yaml, #16)."""
    data: SchemeData
    floor_plans: list[FloorPlan]
    unit_ids: list[str]


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
    """방 최소 의미론(욕실·주방) — 벽·문 기하는 geom userData가 따로 옴."""
    use: str = ""           # 욕실 | 주방
    polygon: Ring = []


class UnitRecord(_Base):
    """units.json 레코드 — 생성기 units 직렬화 계약."""
    id: str
    floor: int
    floor_height: Optional[float] = None
    floor_bottom_height: Optional[float] = None
    price: float = 0
    area: UnitAreaBreakdown = UnitAreaBreakdown()
    geom: Optional[UnitGeometry] = None
    polygon: Optional[Ring] = None      # 주층 단일 ring (호환용)
    duplex_upper_polygon: Optional[Ring] = None
    balcony_polygons: Optional[list[Ring]] = None
    polygons_by_floor: Optional[dict[str, Ring]] = None  # 층 점유 (생성기 계약 ③)
    rooms: Optional[list[UnitRoom]] = None


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
