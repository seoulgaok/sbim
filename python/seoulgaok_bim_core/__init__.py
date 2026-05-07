"""Seoulgaok BIM core — Python types, IO, operations, validators."""

from .options import (
    BuildOptions,
    Massing,
    RegulationOverrides,
    UnitSpec,
)
from .types import (
    BufferAttributeData,
    BufferGeometryData,
    FloorData,
    FloorGeometry,
    FloorPlan,
    Scheme,
    SchemeData,
    SurroundingBuilding,
    SurroundingData,
    SurroundingGeometry,
    Unit,
    UnitData,
    UnitGeometry,
)

__version__ = "0.0.3"

__all__ = [
    # Output types (Scheme 등)
    "BufferAttributeData",
    "BufferGeometryData",
    "FloorData",
    "FloorGeometry",
    "FloorPlan",
    "Scheme",
    "SchemeData",
    "SurroundingBuilding",
    "SurroundingData",
    "SurroundingGeometry",
    "Unit",
    "UnitData",
    "UnitGeometry",
    # Input options (BuildOptions 등)
    "BuildOptions",
    "Massing",
    "UnitSpec",
    "RegulationOverrides",
]
