"""Seoulgaok BIM core — Python types, IO, operations, validators."""

from .config import build_options, load_overrides as load_config
from .errors import CompileError, CompileErrorType
from .site_filter import (
    SiteFilterNotConfigured,
    build_where as build_site_where,
    load_criteria as load_site_criteria,
)
from .options import (
    BuildOptions,
    Concrete,
    Core,
    Financing,
    Massing,
    GroundFloor,
    Parking,
    RegulationOverrides,
    Schedule,
    Structure,
    UnitSpec,
    Windows,
)
from .types import (
    BeamUserData,
    BufferAttributeData,
    BufferGeometryData,
    ColumnUserData,
    CoreLayout,
    CoveringUserData,
    DoorUserData,
    FloorData,
    FloorGeometry,
    FloorPlan,
    HostWallRef,
    MaterialLayer,
    RailingUserData,
    Scheme,
    SchemeData,
    SlabUserData,
    StairLayoutItem,
    StairMemberUserData,
    StairUserData,
    SurroundingBuilding,
    SurroundingData,
    SurroundingGeometry,
    Unit,
    UnitAreaBreakdown,
    UnitData,
    UnitGeometry,
    UnitRecord,
    UnitRoom,
    WallUserData,
    WindowUserData,
)

__version__ = "0.0.13"

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
    # units.json 실계약 (생성기 직렬화)
    "UnitRecord",
    "UnitAreaBreakdown",
    "UnitRoom",
    # scheme 공간 계약
    "CoreLayout",
    # LOD300 userData (kind 판별)
    "MaterialLayer",
    "HostWallRef",
    "WallUserData",
    "SlabUserData",
    "ColumnUserData",
    "BeamUserData",
    "DoorUserData",
    "WindowUserData",
    "CoveringUserData",
    "RailingUserData",
    "StairUserData",
    "StairMemberUserData",
    "StairLayoutItem",
    # Input options (BuildOptions 등)
    "BuildOptions",
    "Massing",
    "UnitSpec",
    "Core",
    "Structure",
    "Windows",
    "GroundFloor",
    "Parking",
    "Concrete",
    "Schedule",
    "Financing",
    "RegulationOverrides",
    # CompileError (CSP 명제 위반)
    "CompileError",
    "CompileErrorType",
    # 원클릭 대상 필지 필터
    "build_options",
    "generate_ifc",
    "load_ifc",
    "load_config",
    "SiteFilterNotConfigured",
    "build_site_where",
    "load_site_criteria",
]


def generate_ifc(*args, **kwargs):
    """scheme + units → IFC4 파일. ifcopenshell 필요 (선택 의존).

    무거운 의존이라 지연 import 한다 — 미설치 환경에서 패키지 import 자체가
    깨지면 안 된다.
    """
    try:
        from .ifc import generate_ifc as _impl
    except ModuleNotFoundError as e:  # pragma: no cover
        raise ModuleNotFoundError(
            "IFC 내보내기에는 ifcopenshell이 필요합니다: "
            "pip install -e ./python[ifc]"
        ) from e
    return _impl(*args, **kwargs)


def load_ifc(path):
    """IFC4 → (scheme, units). generate_ifc가 쓴 파일을 되읽는다.

    ifcopenshell 필요 (선택 의존) — generate_ifc와 같은 이유로 지연 import.
    """
    try:
        from .ifc import load_ifc as _impl
    except ModuleNotFoundError as e:  # pragma: no cover
        raise ModuleNotFoundError(
            "IFC 읽기에는 ifcopenshell이 필요합니다: pip install -e ./python[ifc]"
        ) from e
    return _impl(path)
