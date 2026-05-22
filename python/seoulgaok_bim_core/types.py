"""Pydantic types for Seoulgaok BIM scheme.json data model.

JSON Schema 단일 진실은 `schema/*.json`에 있음.
이 파일은 JSON Schema와 동기화되어야 함 (수동 또는 datamodel-codegen).
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


# --- Floor / FloorPlan -----------------------------------------------------


class FloorData(_Base):
    floor_id: int
    floor_area: float
    floor_height: float
    floor_bottom_height: float


class FloorGeometry(_Base):
    walls: list[list[BufferGeometryData]]
    floors: list[list[BufferGeometryData]]
    roof: Optional[list[list[BufferGeometryData]]] = None


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


class Scheme(_Base):
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
