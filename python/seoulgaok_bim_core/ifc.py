"""IFC (Industry Foundation Classes) export — sbim 모델을 외부 BIM 도구로 추출.

전략: scheme.json/units에 **이미 삼각화된 BufferGeometry**(뷰어가 그리는 바로 그
메시)를 `IfcTriangulatedFaceSet`으로 1:1 변환한다. 따라서 벽·바닥·천장(지붕)·
창문·파라펫·기둥·주차구획까지 하나도 빠짐없이 IFC로 들어간다.

추가로:
  · 세대는 polygon으로 IfcSpace(룸) — NetFloorArea 수량 부착 (적산용).
  · 색·재질은 sbim 외장 옵션 + 뷰어 팔레트와 동일하게 IfcSurfaceStyle/IfcMaterial.
  · 건물 단위 Pset(대지·건축면적·용적률·건폐율·세대수).

위계: IfcProject → IfcSite → IfcBuilding → IfcBuildingStorey(층별)
  층별로 geom의 walls/floors/roof/windows/parapets/columns/parking_stalls →
  각각 IfcWall/IfcSlab/IfcWindow/IfcRailing/IfcColumn/IfcBuildingElementProxy.

좌표: 메시 geom은 parcel_center 상대 로컬(geom 생성 시 normalize), z는 절대.
세대 polygon은 EPSG:5186 절대 → parcel_center를 빼 동일 프레임으로 정렬.

범위: **건축 모델만.** 설비(MEP — 우수·오수·급수 계통, 위생기구)는 욕실·주방
배치에서 계통을 derive하는 별도 문제이고, 분야별 모델 분리 관행상으로도 다른
모델이다. 여기서는 다루지 않는다.

의존: ifcopenshell (선택 설치) — `pip install -e ./python[ifc]`
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Iterable, Sequence

import ifcopenshell
import ifcopenshell.guid

_COL_DEFAULT = 0.4

# ── 뷰어(BuildingMeshVisualizer)와 동일한 색 팔레트 ──
# 외장 preset: (외벽, 지붕) hex. sbim Exterior.style ↔ optionsMeta EXTERIOR_STYLES.
_EXTERIOR = {
    "white": (0xF5F5F5, 0xE0E0E0),
    "sandstone": (0xD4C4A8, 0xB8B0A4),
    "brick": (0x996633, 0xCCCCCC),
    "concrete": (0x9A9A9A, 0x666666),
    "beige": (0xD4C4A8, 0xB8B0A4),   # legacy alias
}
_C_FLOOR = 0x888888
_C_WINDOW = 0x6E9BB8
_C_PARAPET = 0xE8E3D8
_C_COLUMN = 0x4A4A4A
_C_PARKING = 0xFFFFFF


# ── 기하 헬퍼 (sbim 내부 — 외부 의존 없음) ─────────────────────────────
def compute_normal(v0, v1, v2):
    """Compute normal vector for a triangle"""
    edge1 = [v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2]]
    edge2 = [v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2]]
    normal = [
        edge1[1] * edge2[2] - edge1[2] * edge2[1],
        edge1[2] * edge2[0] - edge1[0] * edge2[2],
        edge1[0] * edge2[1] - edge1[1] * edge2[0]
    ]
    length = (normal[0]**2 + normal[1]**2 + normal[2]**2) ** 0.5
    if length > 0:
        normal = [n / length for n in normal]
    return normal


def create_buffer_geometry_data(positions: list, indices: list, normals: list = None) -> dict:
    """Create THREE.js BufferGeometry JSON format"""
    if normals is None:
        normals = [0.0] * len(positions)
        for i in range(0, len(indices), 3):
            if i + 2 < len(indices):
                i0, i1, i2 = indices[i], indices[i+1], indices[i+2]
                v0 = positions[i0*3:i0*3+3]
                v1 = positions[i1*3:i1*3+3]
                v2 = positions[i2*3:i2*3+3]
                if len(v0) == 3 and len(v1) == 3 and len(v2) == 3:
                    normal = compute_normal(v0, v1, v2)
                    for idx in [i0, i1, i2]:
                        normals[idx*3] += normal[0]
                        normals[idx*3+1] += normal[1]
                        normals[idx*3+2] += normal[2]

        for i in range(0, len(normals), 3):
            length = (normals[i]**2 + normals[i+1]**2 + normals[i+2]**2) ** 0.5
            if length > 0:
                normals[i] /= length
                normals[i+1] /= length
                normals[i+2] /= length

    geom = {
        "metadata": {"version": 4.5, "type": "BufferGeometry", "generator": "generate-building"},
        "uuid": str(uuid.uuid4()),
        "type": "BufferGeometry",
        "data": {
            "attributes": {
                "position": {"itemSize": 3, "type": "Float32Array", "array": positions},
                "normal": {"itemSize": 3, "type": "Float32Array", "array": normals}
            },
            "index": {"type": "Uint16Array", "array": indices}
        }
    }
    return geom


def _prism_geometry(corners, z0: float, z1: float, user_data: dict = None) -> dict:
    """수직 프리즘(옆면+상하캡) BufferGeometry — 면당 정점 비공유(플랫 노멀 유지).

    corners: [(x,y), ...] CCW 링(닫힘 없음). LOD300 부재(벽 세그먼트·기둥·보)의
    공통 솔리드. userData는 three.js BufferGeometry JSON 표준 필드로 병합.
    """
    n = len(corners)
    positions, normals, indices = [], [], []
    vi = 0
    # 옆면
    for i in range(n):
        x0, y0 = corners[i]
        x1, y1 = corners[(i + 1) % n]
        dx, dy = x1 - x0, y1 - y0
        ln = (dx * dx + dy * dy) ** 0.5 or 1.0
        # CCW 링 진행 방향 기준 오른쪽 = 외향
        nx, ny = dy / ln, -dx / ln
        positions.extend([x0, y0, z0, x1, y1, z0, x1, y1, z1, x0, y0, z1])
        normals.extend([nx, ny, 0.0] * 4)
        indices.extend([vi, vi + 1, vi + 2, vi, vi + 2, vi + 3])
        vi += 4
    # 캡 (fan 삼각화 — 부재 프리즘은 볼록 quad라 충분)
    for z, nz, rev in ((z0, -1.0, True), (z1, 1.0, False)):
        ring = list(reversed(corners)) if rev else corners
        base = vi
        for x, y in ring:
            positions.extend([x, y, z])
            normals.extend([0.0, 0.0, nz])
            vi += 1
        for i in range(1, n - 1):
            indices.extend([base, base + i, base + i + 1])
    return create_buffer_geometry_data(positions, indices, normals) | (
        {"userData": user_data} if user_data else {})


def railing_members(railing_ud, post: float = 0.04, clear: float = 0.10) -> list:
    """난간동자(수직 살) + 손스침 — IfcMember(POST/STRINGER) 분해용.

    간살 안목 <=0.10m — 주택건설기준 18조②2. 중심간 피치 = post + clear이고,
    실간격은 구간 길이를 균등 분할해 상한 이하로 맞춘다.
    반환: [{part, geom}] — part = "post" | "handrail".
    """
    if not railing_ud or not railing_ud.get("lines"):
        return []
    spacing = post + clear
    z0 = float(railing_ud.get("base_z", 0.0))
    z1 = float(railing_ud.get("top_z", z0 + 1.2))
    h = post / 2.0
    out = []
    for ln_pts in railing_ud["lines"]:
        for i in range(len(ln_pts) - 1):
            x0, y0 = ln_pts[i]
            x1, y1 = ln_pts[i + 1]
            dx, dy = x1 - x0, y1 - y0
            seg = (dx * dx + dy * dy) ** 0.5
            if seg < 0.3:
                continue
            ux, uy = dx / seg, dy / seg
            nx, ny = uy, -ux
            n_post = max(2, int(seg / spacing) + 1)      # 양끝 포함
            for k in range(n_post):
                t = seg * k / (n_post - 1)
                px, py = x0 + ux * t, y0 + uy * t
                corners = [(px - ux * h - nx * h, py - uy * h - ny * h),
                           (px + ux * h - nx * h, py + uy * h - ny * h),
                           (px + ux * h + nx * h, py + uy * h + ny * h),
                           (px - ux * h + nx * h, py - uy * h + ny * h)]
                out.append({"part": "post",
                            "geom": _prism_geometry(corners, z0, z1 - 0.05)})
            # 손스침 — 상단 가로재 (동자 위 5cm 띠)
            hc = [(x0 - nx * h, y0 - ny * h), (x1 - nx * h, y1 - ny * h),
                  (x1 + nx * h, y1 + ny * h), (x0 + nx * h, y0 + ny * h)]
            out.append({"part": "handrail",
                        "geom": _prism_geometry(hc, z1 - 0.05, z1)})
    return out


def _gid() -> str:
    return ifcopenshell.guid.new()


def _num(val, default: float) -> float:
    try:
        return float(val) if val is not None else float(default)
    except (TypeError, ValueError):
        return float(default)


def _rgb(f, hexval: int):
    return f.create_entity(
        "IfcColourRgb", Red=((hexval >> 16) & 0xFF) / 255.0,
        Green=((hexval >> 8) & 0xFF) / 255.0, Blue=(hexval & 0xFF) / 255.0)


# ── 메시 변환 ──────────────────────────────────────────────────────────
def _iter_geoms(group) -> Iterable[dict]:
    """geom 필드(예: [[geom_dict]] 또는 [[]])를 평탄화해 BufferGeometry dict만 yield."""
    if not group:
        return
    for sub in group:
        if isinstance(sub, dict):
            yield sub
        elif isinstance(sub, (list, tuple)):
            for g in sub:
                if isinstance(g, dict) and g.get("data"):
                    yield g


def _faceset(f, geom: dict, dz: float = 0.0):
    """BufferGeometry → IfcTriangulatedFaceSet. dz = 층 표고(지오메트리를 층
    상대 z로 — 아키캐드 층 배정 정석). 빈 경우 None."""
    try:
        attrs = geom["data"]["attributes"]
        pos = attrs["position"]["array"]
        idx = geom["data"]["index"]["array"]
    except (KeyError, TypeError):
        return None
    if not pos or not idx or len(pos) < 9 or len(idx) < 3:
        return None
    coords = [(float(pos[i]), float(pos[i + 1]), float(pos[i + 2]) - dz)
              for i in range(0, len(pos) - 2, 3)]
    n = len(coords)
    tris = []
    for i in range(0, len(idx) - 2, 3):
        a, b, c = idx[i], idx[i + 1], idx[i + 2]
        if a < n and b < n and c < n:
            tris.append((a + 1, b + 1, c + 1))   # IFC CoordIndex = 1-based
    if not tris:
        return None
    pl = f.create_entity("IfcCartesianPointList3D", CoordList=coords)
    return f.create_entity(
        "IfcTriangulatedFaceSet", Coordinates=pl, CoordIndex=tris, Closed=False)


def _shape_tess(f, ctx, facesets, style):
    items = [fs for fs in facesets if fs is not None]
    if not items:
        return None
    if style is not None:
        for it in items:
            f.create_entity("IfcStyledItem", Item=it, Styles=[style])
    rep = f.create_entity(
        "IfcShapeRepresentation", ContextOfItems=ctx, RepresentationIdentifier="Body",
        RepresentationType="Tessellation", Items=items)
    return f.create_entity("IfcProductDefinitionShape", Representations=[rep])


# ── 파라메트릭 솔리드 (세대 IfcSpace·지하 공간) ─────────────────────────
def _ring_xy(ring, cx, cy):
    pts = []
    for p in ring:
        xy = (float(p[0]) - cx, float(p[1]) - cy)
        if not pts or (abs(xy[0] - pts[-1][0]) > 1e-6 or abs(xy[1] - pts[-1][1]) > 1e-6):
            pts.append(xy)
    if len(pts) > 1 and abs(pts[0][0] - pts[-1][0]) < 1e-6 and abs(pts[0][1] - pts[-1][1]) < 1e-6:
        pts.pop()
    return pts


def _extruded_solid(f, pts, base_z, height):
    poly_pts = [f.create_entity("IfcCartesianPoint", Coordinates=(x, y)) for x, y in pts]
    poly_pts.append(poly_pts[0])
    polyline = f.create_entity("IfcPolyline", Points=poly_pts)
    profile = f.create_entity(
        "IfcArbitraryClosedProfileDef", ProfileType="AREA", OuterCurve=polyline)
    origin = f.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, base_z))
    position = f.create_entity("IfcAxis2Placement3D", Location=origin)
    direction = f.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))
    return f.create_entity(
        "IfcExtrudedAreaSolid", SweptArea=profile, Position=position,
        ExtrudedDirection=direction, Depth=max(height, 1e-3))


def _shape_solid(f, ctx, solid, style):
    if style is not None:
        f.create_entity("IfcStyledItem", Item=solid, Styles=[style])
    rep = f.create_entity(
        "IfcShapeRepresentation", ContextOfItems=ctx, RepresentationIdentifier="Body",
        RepresentationType="SweptSolid", Items=[solid])
    return f.create_entity("IfcProductDefinitionShape", Representations=[rep])


def _placement(f, parent=None, z=0.0):
    origin = f.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, float(z)))
    axis = f.create_entity("IfcAxis2Placement3D", Location=origin)
    return f.create_entity(
        "IfcLocalPlacement", PlacementRelTo=parent, RelativePlacement=axis)


def _on_storey(f, st):
    """요소 placement — 층 기준 z=0 (참조 IFC 정석).

    지오메트리 z는 **층 상대**로 넣는다(_elev를 빼서). 구 방식(−표고 보정 +
    절대 z)은 아키캐드가 보정 placement를 무시하고 층 위에 다시 얹어
    요소가 표고만큼 이중 상승했다(실측 확인)."""
    return _placement(f, st.ObjectPlacement)


def _elev(st) -> float:
    return float(st.Elevation or 0.0)


def _rel_aggregates(f, relating, related, name):
    items = [r for r in related if r is not None]
    if items:
        f.create_entity(
            "IfcRelAggregates", GlobalId=_gid(), Name=name,
            RelatingObject=relating, RelatedObjects=items)


def _rel_contained(f, structure, elements):
    items = [e for e in elements if e is not None]
    if items:
        f.create_entity(
            "IfcRelContainedInSpatialStructure", GlobalId=_gid(),
            RelatingStructure=structure, RelatedElements=items)


def _area_quantity(f, element, area, name="NetFloorArea", qto="Qto_SpaceBaseQuantities"):
    if not area or area <= 0:
        return
    q = f.create_entity("IfcQuantityArea", Name=name, AreaValue=float(area))
    eq = f.create_entity(
        "IfcElementQuantity", GlobalId=_gid(), Name=qto, Quantities=[q])
    f.create_entity(
        "IfcRelDefinesByProperties", GlobalId=_gid(),
        RelatedObjects=[element], RelatingPropertyDefinition=eq)


def _pset(f, element, name, props: dict):
    """부재 Pset — IFC 표준 속성 집합 (Pset_WallCommon 등).
    값 타입은 bool→IfcBoolean, int→IfcInteger, float→IfcReal, str→IfcLabel."""
    items = []
    for k, v in props.items():
        if v is None:
            continue
        kind = ("IfcBoolean" if isinstance(v, bool)
                else "IfcInteger" if isinstance(v, int)
                else "IfcReal" if isinstance(v, float) else "IfcLabel")
        items.append(f.create_entity(
            "IfcPropertySingleValue", Name=k,
            NominalValue=f.create_entity(kind, wrappedValue=v)))
    if not items:
        return
    ps = f.create_entity("IfcPropertySet", GlobalId=_gid(), Name=name,
                         HasProperties=items)
    f.create_entity("IfcRelDefinesByProperties", GlobalId=_gid(),
                    RelatedObjects=[element], RelatingPropertyDefinition=ps)


_QKIND = {"L": ("IfcQuantityLength", "LengthValue"),
          "A": ("IfcQuantityArea", "AreaValue"),
          "V": ("IfcQuantityVolume", "VolumeValue")}


def _qto(f, element, name, quants: list):
    """부재 수량 — Qto_WallBaseQuantities 등. quants=[(종류,이름,값)].
    적산 직결 — 참조 도면(ArchiCAD 출력)엔 수량 세트가 아예 없어 여기가 우위."""
    items = []
    for kind, qname, val in quants:
        if val is None or val <= 0:
            continue
        cls, attr = _QKIND[kind]
        items.append(f.create_entity(cls, Name=qname, **{attr: float(val)}))
    if not items:
        return
    eq = f.create_entity("IfcElementQuantity", GlobalId=_gid(),
                         Name=name, Quantities=items)
    f.create_entity("IfcRelDefinesByProperties", GlobalId=_gid(),
                    RelatedObjects=[element], RelatingPropertyDefinition=eq)


def _building_pset(f, building, data, n_units, style_name):
    def _pv(name, val, kind="IfcReal"):
        return f.create_entity(
            "IfcPropertySingleValue", Name=name,
            NominalValue=f.create_entity(kind, wrappedValue=val))
    props = []
    if data:
        if data.get("lot_area") is not None:
            props.append(_pv("대지면적(㎡)", float(data["lot_area"])))
        if data.get("build_area") is not None:
            props.append(_pv("건축면적(㎡)", float(data["build_area"])))
        if data.get("far") is not None:
            props.append(_pv("용적률(%)", float(data["far"])))
        if data.get("bcr") is not None:
            props.append(_pv("건폐율(%)", float(data["bcr"])))
        if data.get("pnu"):
            props.append(_pv("PNU", str(data["pnu"]), "IfcLabel"))
    if n_units:
        props.append(_pv("세대수", n_units, "IfcInteger"))
    if style_name:
        props.append(_pv("외장재", style_name, "IfcLabel"))
    if not props:
        return
    ps = f.create_entity(
        "IfcPropertySet", GlobalId=_gid(), Name="Pset_SBIM_사업개요",
        HasProperties=props)
    f.create_entity(
        "IfcRelDefinesByProperties", GlobalId=_gid(),
        RelatedObjects=[building], RelatingPropertyDefinition=ps)


def derive_parcel_center(scheme_json) -> list:
    """scheme의 절대좌표(EPSG) 링에서 대지 중심을 추정한다.

    generate_ifc는 메시(로컬 좌표)와 세대 polygon(절대 좌표)을 같은 프레임으로
    맞추기 위해 중심이 필요하다. 파이프라인이 parcel_center를 따로 들고 있으면
    그 값을 쓰는 게 정확하고, 없을 때의 대비책이다.
    """
    xs, ys = [], []

    def walk(o):
        if isinstance(o, (list, tuple)):
            if (len(o) == 2 and all(isinstance(v, (int, float))
                                    and not isinstance(v, bool) for v in o)
                    and abs(o[0]) > 1000 and abs(o[1]) > 1000):
                xs.append(float(o[0])); ys.append(float(o[1])); return
            for x in o:
                walk(x)
        elif isinstance(o, dict):
            for v in o.values():
                walk(v)

    for key, val in (scheme_json or {}).items():
        if key.startswith("_"):        # 절대좌표는 밑줄 키에 모여 있다
            walk(val)
    if not xs:
        raise ValueError(
            "scheme에서 절대좌표를 찾지 못했습니다. parcel_center를 직접 넘기세요."
        )
    return [(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2]


def generate_ifc(scheme_json, units, parcel_center=None, out_path=None, meta=None):
    """scheme_json + units → IFC4 파일 (전체 메시 + 세대 공간 + 재질·색·수량).

    건축 모델만 생성한다. 설비(우수·오수·급수 계통)는 분야별 모델 분리 관행에
    따라 별도 모델로 다루며, 이 함수의 범위 밖이다."""
    meta = meta or {}
    if out_path is None:
        raise TypeError("out_path는 필수입니다")
    if parcel_center is None:
        parcel_center = derive_parcel_center(scheme_json)
    cx, cy = float(parcel_center[0]), float(parcel_center[1])
    style_key = str(meta.get("exterior_style") or "brick")
    wall_hex, roof_hex = _EXTERIOR.get(style_key, _EXTERIOR["brick"])

    f = ifcopenshell.file(schema="IFC4")

    units_assignment = f.create_entity("IfcUnitAssignment", Units=[
        f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE"),
        f.create_entity("IfcSIUnit", UnitType="AREAUNIT", Name="SQUARE_METRE"),
        f.create_entity("IfcSIUnit", UnitType="VOLUMEUNIT", Name="CUBIC_METRE"),
    ])
    world_axis = f.create_entity(
        "IfcAxis2Placement3D",
        Location=f.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)))
    ctx = f.create_entity(
        "IfcGeometricRepresentationContext", ContextType="Model",
        CoordinateSpaceDimension=3, Precision=1e-5, WorldCoordinateSystem=world_axis)

    # ── 표면 스타일 (색·투명도) — 색별 1회 생성 후 재사용 ──
    _style_cache: dict[tuple, object] = {}

    def surface_style(hexval, transparency=0.0):
        key = (hexval, round(transparency, 2))
        if key not in _style_cache:
            shading = f.create_entity(
                "IfcSurfaceStyleShading", SurfaceColour=_rgb(f, hexval),
                Transparency=float(transparency))
            ss = f.create_entity(
                "IfcSurfaceStyle", Side="BOTH", Styles=[shading])
            _style_cache[key] = ss
        return _style_cache[key]

    # ── 재질 (적산용 semantic) — 이름별 1회, 요소 모아 끝에 일괄 연결 ──
    _mat_cache: dict[str, object] = {}
    _mat_members: dict[str, list] = {}

    def use_material(name, element):
        if element is None:
            return
        if name not in _mat_cache:
            _mat_cache[name] = f.create_entity("IfcMaterial", Name=name)
            _mat_members[name] = []
        _mat_members[name].append(element)

    location = str(meta.get("location") or "")
    pnu = str(meta.get("pnu") or "")
    project = f.create_entity(
        "IfcProject", GlobalId=_gid(), Name=location or "SBIM Volume",
        Description=f"PNU {pnu} · EPSG:5186 origin ({cx:.2f}, {cy:.2f})",
        RepresentationContexts=[ctx], UnitsInContext=units_assignment)
    site = f.create_entity(
        "IfcSite", GlobalId=_gid(), Name=location or "Site",
        Description=f"EPSG:5186 parcel_center ({cx:.3f}, {cy:.3f})",
        ObjectPlacement=_placement(f), CompositionType="ELEMENT")
    building = f.create_entity(
        "IfcBuilding", GlobalId=_gid(), Name="Building",
        ObjectPlacement=_placement(f, site.ObjectPlacement), CompositionType="ELEMENT")
    _rel_aggregates(f, project, [site], "Project→Site")
    _rel_aggregates(f, site, [building], "Site→Building")

    floor_plans = scheme_json.get("floor_plans", []) or []
    fdata = {fp.get("data", {}).get("floor_id"): fp.get("data", {}) for fp in floor_plans}

    # ── storey 생성 (지하 -1 포함, floor_id 순) ──
    storey_by_floor: dict[int, object] = {}
    storeys = []
    for fp in sorted(floor_plans, key=lambda p: p.get("data", {}).get("floor_id", 0)):
        d = fp.get("data", {})
        fid = d.get("floor_id")
        if fid is None:
            continue
        bottom = _num(d.get("floor_bottom_height"), (fid - 1) * 3.0)
        # floor_name = 옥탑층·지붕층 등 특수 층 (참조 도면 명명 규약)
        name = d.get("floor_name") or ("B1" if fid == -1 else f"{fid}F")
        st = f.create_entity(
            "IfcBuildingStorey", GlobalId=_gid(), Name=name,
            ObjectPlacement=_placement(f, building.ObjectPlacement, z=bottom),
            CompositionType="ELEMENT", Elevation=bottom)
        storey_by_floor[fid] = st
        storeys.append(st)
    _rel_aggregates(f, building, storeys, "Building→Storeys")

    # ── 타입 객체 — 같은 사양 부재를 IfcXxxType으로 묶는다 (아키캐드/레빗
    # 타입 단위 일괄 편집·일람표 기반) ──
    _type_reg: dict[tuple, list] = {}

    def _typed(element, tcls, name, predef="NOTDEFINED"):
        if element is not None:
            _type_reg.setdefault((tcls, name, predef), []).append(element)

    # ── LOD300 부재 승급 — userData 있는 벽은 변당 IfcWall(SweptSolid+레이어셋) ──
    _layerset_cache: dict[tuple, object] = {}

    def _layer_set_usage(layers, prefix, direction="AXIS2", offset=0.0):
        """레이어 리스트 → IfcMaterialLayerSetUsage (프리픽스+두께 튜플 캐시).
        벽=AXIS2(중심선 기준 -t/2), 슬라브=AXIS3(상면 기준 하향)."""
        key = (prefix,) + tuple(
            (l.get("name", "?"), round(float(l.get("t", 0)), 4))
            for l in (layers or []))
        if len(key) < 2:
            return None
        if key not in _layerset_cache:
            mls = [f.create_entity(
                       "IfcMaterialLayer",
                       Material=f.create_entity("IfcMaterial", Name=nm),
                       LayerThickness=t * 1000.0, Name=f"{nm}{round(t*1000)}")
                   for nm, t in key[1:]]
            # 참조 도면 명명 관행: '[외벽] // 철콘200 // EPS200 / STO10'
            label = " / ".join(f"{nm}{round(t*1000)}" for nm, t in key[1:])
            ls = f.create_entity(
                "IfcMaterialLayerSet", MaterialLayers=mls,
                LayerSetName=f"{prefix} {label}")
            _layerset_cache[key] = ls
        return f.create_entity(
            "IfcMaterialLayerSetUsage", ForLayerSet=_layerset_cache[key],
            LayerSetDirection=direction, DirectionSense="POSITIVE",
            OffsetFromReferenceLine=float(offset))

    def _associate_material(element, lsu):
        if lsu is not None:
            f.create_entity(
                "IfcRelAssociatesMaterial", GlobalId=_gid(),
                RelatedObjects=[element], RelatingMaterial=lsu)

    def _wall_entity(ud, st, fid, seq):
        """벽 userData → IfcWall: Axis(중심선) + Body(SweptSolid) + 레이어셋."""
        p0 = (float(ud["p0"][0]) - cx, float(ud["p0"][1]) - cy)
        p1 = (float(ud["p1"][0]) - cx, float(ud["p1"][1]) - cy)
        t = float(ud.get("t", 0.2))
        base_z, top_z = float(ud.get("base_z", 0)), float(ud.get("top_z", 3))
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        ln = (dx * dx + dy * dy) ** 0.5
        if ln < 1e-6:
            return None
        # 마이터 quad(emitter 확정, 단일 소스) 우선 — 없으면 t/2 연장 맞댐 폴백
        if ud.get("quad") and len(ud["quad"]) >= 4:
            corners = [(float(q[0]) - cx, float(q[1]) - cy) for q in ud["quad"]]
        else:
            ux, uy = dx / ln, dy / ln
            nx, ny, h = uy, -ux, t / 2.0
            a = (p0[0] - ux * h, p0[1] - uy * h)
            b = (p1[0] + ux * h, p1[1] + uy * h)
            corners = [(a[0] + nx * h, a[1] + ny * h),
                       (b[0] + nx * h, b[1] + ny * h),
                       (b[0] - nx * h, b[1] - ny * h),
                       (a[0] - nx * h, a[1] - ny * h)]
        solid = _extruded_solid(f, corners, base_z - _elev(st),
                                top_z - base_z)
        style = surface_style(wall_hex, 0.0)
        f.create_entity("IfcStyledItem", Item=solid, Styles=[style])
        body = f.create_entity(
            "IfcShapeRepresentation", ContextOfItems=ctx,
            RepresentationIdentifier="Body", RepresentationType="SweptSolid",
            Items=[solid])
        axis_pts = [f.create_entity("IfcCartesianPoint", Coordinates=p0),
                    f.create_entity("IfcCartesianPoint", Coordinates=p1)]
        axis = f.create_entity(
            "IfcShapeRepresentation", ContextOfItems=ctx,
            RepresentationIdentifier="Axis", RepresentationType="Curve2D",
            Items=[f.create_entity("IfcPolyline", Points=axis_pts)])
        shape = f.create_entity(
            "IfcProductDefinitionShape", Representations=[axis, body])
        wall = f.create_entity(
            "IfcWall", GlobalId=_gid(),
            Name=f"{'B1' if fid == -1 else str(fid)+'F'} 벽-{seq:02d}",
            ObjectPlacement=_on_storey(f, st),
            Representation=shape)
        # offset = 기준선(구조체 중심)→외피 (참조 도면 규약: 410 레이어셋에 +310)
        _off = float(ud.get("offset_out", t / 2.0)) * 1000.0
        _associate_material(wall, _layer_set_usage(
            ud.get("layers"), "[외벽]" if ud.get("exterior") else "[내벽]",
            direction="AXIS2", offset=_off))
        ext = bool(ud.get("exterior"))
        t_tot = float(ud.get("t_total", t))
        h = top_z - base_z
        _pset(f, wall, "Pset_WallCommon", {
            "IsExternal": ext,
            "LoadBearing": True,          # 벽식 구조 — 전 벽 내력
            "ExtendToStructure": True,
            "ThermalTransmittance": 0.17 if ext else None,  # EPS200 외단열 근사(W/㎡K)
        })
        _qto(f, wall, "Qto_WallBaseQuantities", [
            ("L", "Length", ln), ("L", "Height", h), ("L", "Width", t_tot),
            ("A", "NetSideArea", ln * h),
            ("V", "NetVolume", ln * h * t),   # 구조체(철콘) 물량 — 마감 제외
        ])
        _typed(wall, "IfcWallType",
               ("[외벽] " if ext else "[내벽] ") + f"{round(t_tot*1000)}",
               "SOLIDWALL")
        return wall

    _SLAB_ROLE = {  # role → (PredefinedType, 레이어셋 프리픽스)
        "foundation": ("BASESLAB", "[기초]"),
        "roof": ("ROOF", "[지붕]"),
        "interfloor": ("FLOOR", "[슬라브]"),
    }

    def _slab_entity(ud, st, fid, hexc):
        """슬라브 userData → IfcSlab(SweptSolid — outline을 top_z-t에서 t 압출)."""
        outline = ud.get("outline") or []
        if len(outline) < 3:
            return None
        t = float(ud.get("t", 0.15))
        top_z = float(ud.get("top_z", 0.0))
        pts = _ring_xy(outline, cx, cy)
        solid = _extruded_solid(f, pts, top_z - t - _elev(st), t)
        shape = _shape_solid(f, ctx, solid, surface_style(hexc, 0.0))
        predef, prefix = _SLAB_ROLE.get(ud.get("role"), _SLAB_ROLE["interfloor"])
        slab = f.create_entity(
            "IfcSlab", GlobalId=_gid(),
            Name=f"{'B1' if fid == -1 else str(fid)+'F'} {prefix[1:-1]}슬라브",
            ObjectPlacement=_on_storey(f, st),
            Representation=shape, PredefinedType=predef)
        _associate_material(slab, _layer_set_usage(
            ud.get("layers") or [{"name": "철근콘크리트", "t": t}], prefix,
            direction="AXIS3", offset=0.0))
        try:
            from shapely.geometry import Polygon as _SP
            area = _SP(pts).area
            per = _SP(pts).exterior.length
        except Exception:
            area = per = 0.0
        _pset(f, slab, "Pset_SlabCommon", {
            "IsExternal": ud.get("role") in ("roof", "foundation"),
            "LoadBearing": True,
            "PitchAngle": 0.0,
        })
        _qto(f, slab, "Qto_SlabBaseQuantities", [
            ("L", "Width", t), ("L", "Perimeter", per),
            ("A", "GrossArea", area), ("V", "GrossVolume", area * t),
        ])
        _typed(slab, "IfcSlabType", f"{prefix} {round(t*1000)}", predef)
        return slab

    def _column_entity(ud, st, fid, seq):
        """기둥 userData → IfcColumn (정사각 프로파일 SweptSolid)."""
        c = ud.get("center") or [cx, cy]
        half = float(ud.get("size", 0.6)) / 2.0
        x, y = float(c[0]) - cx, float(c[1]) - cy
        base_z, top_z = float(ud.get("base_z", 0)), float(ud.get("top_z", 3))
        pts = [(x - half, y - half), (x + half, y - half),
               (x + half, y + half), (x - half, y + half)]
        solid = _extruded_solid(f, pts, base_z - _elev(st),
                                top_z - base_z)
        shape = _shape_solid(f, ctx, solid, surface_style(_C_COLUMN, 0.0))
        col = f.create_entity(
            "IfcColumn", GlobalId=_gid(),
            Name=f"{fid}F 기둥-{seq:02d}"
                 + (" (전이)" if ud.get("transfer") else ""),
            ObjectPlacement=_on_storey(f, st),
            Representation=shape, PredefinedType="COLUMN")
        size = float(ud.get("size", 0.6))
        hgt = top_z - base_z
        _pset(f, col, "Pset_ColumnCommon", {
            "IsExternal": False, "LoadBearing": True,
            "Reference": f"C{round(size*1000)}x{round(size*1000)}",
        })
        _qto(f, col, "Qto_ColumnBaseQuantities", [
            ("L", "Length", hgt), ("A", "CrossSectionArea", size * size),
            ("A", "OuterSurfaceArea", 4 * size * hgt),
            ("V", "GrossVolume", size * size * hgt),
        ])
        _typed(col, "IfcColumnType",
               f"C{round(size*1000)}x{round(size*1000)}", "COLUMN")
        return col

    def _beam_entity(ud, st, fid, seq):
        """보 userData → IfcBeam (w×h 프로파일 — 축선 따라 하향 배치)."""
        p0 = (float(ud["p0"][0]) - cx, float(ud["p0"][1]) - cy)
        p1 = (float(ud["p1"][0]) - cx, float(ud["p1"][1]) - cy)
        w, h = float(ud.get("w", 0.6)), float(ud.get("h", 0.8))
        top_z = float(ud.get("top_z", 3.0))
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        ln = (dx * dx + dy * dy) ** 0.5
        if ln < 1e-6:
            return None
        ux, uy = dx / ln, dy / ln
        nx, ny, hw = uy, -ux, w / 2.0
        a = (p0[0] - ux * hw, p0[1] - uy * hw)
        b = (p1[0] + ux * hw, p1[1] + uy * hw)
        pts = [(a[0] + nx * hw, a[1] + ny * hw), (b[0] + nx * hw, b[1] + ny * hw),
               (b[0] - nx * hw, b[1] - ny * hw), (a[0] - nx * hw, a[1] - ny * hw)]
        solid = _extruded_solid(f, pts, top_z - h - _elev(st), h)
        shape = _shape_solid(f, ctx, solid, surface_style(_C_COLUMN, 0.0))
        role = "전이보" if ud.get("role") == "transfer" else "보"
        beam = f.create_entity(
            "IfcBeam", GlobalId=_gid(),
            Name=f"{fid}F {role}-{seq:02d} {round(w*1000)}x{round(h*1000)}",
            ObjectPlacement=_on_storey(f, st),
            Representation=shape, PredefinedType="BEAM")
        _pset(f, beam, "Pset_BeamCommon", {
            "IsExternal": False, "LoadBearing": True,
            "Reference": f"{'TG' if ud.get('role') == 'transfer' else 'G'}"
                         f"{round(w*1000)}x{round(h*1000)}",
        })
        _qto(f, beam, "Qto_BeamBaseQuantities", [
            ("L", "Length", ln), ("A", "CrossSectionArea", w * h),
            ("A", "OuterSurfaceArea", 2 * (w + h) * ln),
            ("V", "GrossVolume", w * h * ln),
        ])
        _typed(beam, "IfcBeamType",
               f"{'TG' if ud.get('role') == 'transfer' else 'G'}"
               f"{round(w*1000)}x{round(h*1000)}", "BEAM")
        return beam

    # ── 층별 메시 → 타입별 IFC 요소 ──
    # (geom 키, IFC 클래스, 색, 투명도, 재질명, predefined)
    GEOM_MAP = [
        ("walls", "IfcWall", wall_hex, 0.0, "철근콘크리트(외벽)", None),
        ("floors", "IfcSlab", _C_FLOOR, 0.0, "철근콘크리트(슬래브)", "FLOOR"),
        ("roof", "IfcSlab", roof_hex, 0.0, "철근콘크리트(지붕/천장)", "ROOF"),
        ("windows", "IfcWindow", _C_WINDOW, 0.55, "유리", None),
        ("parapets", "IfcRailing", _C_PARAPET, 0.0, "철근콘크리트(파라펫)", None),
        ("columns", "IfcColumn", _C_COLUMN, 0.0, "철근콘크리트(기둥)", "COLUMN"),
        ("beams", "IfcBeam", _C_COLUMN, 0.0, "철근콘크리트(보)", "BEAM"),
        ("doors", "IfcDoor", 0x8B6F47, 0.0, "목재(문)", None),
        ("stairs", "IfcStair", _C_PARAPET, 0.0, "철근콘크리트(계단)", None),
        ("coverings", "IfcCovering", 0xDCDCDC, 0.0, "마감", None),
        ("parking_stalls", "IfcBuildingElementProxy", _C_PARKING, 0.4, None, None),
    ]

    def _stair_pset(element, ud):
        """계단 치수 Pset — 단높이/단너비/단수/계단판 두께."""
        props = [f.create_entity(
                     "IfcPropertySingleValue", Name=nm,
                     NominalValue=f.create_entity(kind, wrappedValue=val))
                 for nm, val, kind in [
                     ("단높이(m)", float(ud.get("riser", 0)), "IfcReal"),
                     ("단너비(m)", float(ud.get("tread", 0)), "IfcReal"),
                     ("단수", int(ud.get("n_risers", 0)), "IfcInteger"),
                     ("계단판두께(m)", float(ud.get("waist", 0.15)), "IfcReal"),
                     ("flights", int(ud.get("flights", 2)), "IfcInteger")]]
        ps = f.create_entity(
            "IfcPropertySet", GlobalId=_gid(), Name="Pset_SBIM_계단",
            HasProperties=props)
        f.create_entity(
            "IfcRelDefinesByProperties", GlobalId=_gid(),
            RelatedObjects=[element], RelatingPropertyDefinition=ps)

    def _opening_entity(ud, st, fid, seq, wall_registry, is_window=False):
        """문 userData → IfcDoor + 호스트 IfcWall에 IfcOpeningElement(RelVoids).

        host_wall(p0,p1,t) 좌표키로 이 층 IfcWall을 찾아 벽에 구멍을 뚫는다 —
        없으면 문만 배치(레빗에서 뜬 문이지만 폴백으로 정직)."""
        p0 = (float(ud["p0"][0]) - cx, float(ud["p0"][1]) - cy)
        p1 = (float(ud["p1"][0]) - cx, float(ud["p1"][1]) - cy)
        w = float(ud.get("width", 0.9))
        hgt = float(ud.get("height", 2.1))
        base_z = float(fdata.get(fid, {}).get("floor_bottom_height", 0.0))
        if is_window:      # 창은 창대(sill) 높이에서 시작 — 절대 z로 방출됨
            base_z = float(ud.get("sill", base_z + 0.9))
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        ln = (dx * dx + dy * dy) ** 0.5
        if ln < 1e-6:
            return None
        ux, uy = dx / ln, dy / ln
        nx, ny = uy, -ux
        # 호스트 벽 — 두께+여유로 개구 박스
        host = ud.get("host_wall") or {}
        host_key = None
        if host:
            host_key = (tuple(round(v, 2) for v in host.get("p0", [])),
                        tuple(round(v, 2) for v in host.get("p1", [])))
        host_wall = wall_registry.get(host_key) if host_key else None
        if host_wall is not None:
            ot = float(host.get("t", 0.1)) / 2.0 + 0.05
            opts = [(p0[0] + nx * ot, p0[1] + ny * ot),
                    (p1[0] + nx * ot, p1[1] + ny * ot),
                    (p1[0] - nx * ot, p1[1] - ny * ot),
                    (p0[0] - nx * ot, p0[1] - ny * ot)]
            osolid = _extruded_solid(f, opts, base_z - _elev(st), hgt)
            oshape = f.create_entity(
                "IfcProductDefinitionShape", Representations=[
                    f.create_entity(
                        "IfcShapeRepresentation", ContextOfItems=ctx,
                        RepresentationIdentifier="Body",
                        RepresentationType="SweptSolid", Items=[osolid])])
            opening = f.create_entity(
                "IfcOpeningElement", GlobalId=_gid(),
                Name=f"{fid}F 개구-{seq:02d}",
                ObjectPlacement=_on_storey(f, st),
                Representation=oshape)
            f.create_entity(
                "IfcRelVoidsElement", GlobalId=_gid(),
                RelatingBuildingElement=host_wall, RelatedOpeningElement=opening)
        # 창짝·문짝 (얇은 패널)
        hw = 0.015 if is_window else 0.04
        dpts = [(p0[0] + nx * hw, p0[1] + ny * hw),
                (p1[0] + nx * hw, p1[1] + ny * hw),
                (p1[0] - nx * hw, p1[1] - ny * hw),
                (p0[0] - nx * hw, p0[1] - ny * hw)]
        dsolid = _extruded_solid(f, dpts, base_z - _elev(st), hgt)
        dshape = _shape_solid(
            f, ctx, dsolid,
            surface_style(_C_WINDOW, 0.55) if is_window
            else surface_style(0x8B6F47, 0.0))
        door = f.create_entity(
            "IfcWindow" if is_window else "IfcDoor", GlobalId=_gid(),
            Name=(f"{fid}F {ud.get('type') or '창'}-{seq:02d}"
                  f" ({ud.get('unit_id', '')})") if is_window else
                 (f"{fid}F {ud.get('door_type') or '세대'}문-{seq:02d}"
                  f" ({ud.get('unit_id', '')})"),
            ObjectPlacement=_on_storey(f, st),
            Representation=dshape,
            OverallHeight=hgt, OverallWidth=w)
        if host_wall is not None:
            f.create_entity(
                "IfcRelFillsElement", GlobalId=_gid(),
                RelatingOpeningElement=opening, RelatedBuildingElement=door)
        if is_window:
            _pset(f, door, "Pset_WindowCommon", {
                "IsExternal": True,
                "Reference": f"W{round(w*1000)}x{round(hgt*1000)}",
                "ThermalTransmittance": 1.5,   # 로이 복층유리 근사 (W/㎡K)
            })
            _qto(f, door, "Qto_WindowBaseQuantities", [
                ("L", "Width", w), ("L", "Height", hgt), ("A", "Area", w * hgt)])
            _typed(door, "IfcWindowType",
                   f"W{round(w*1000)}x{round(hgt*1000)}", "WINDOW")
            return door
        _fire = bool(ud.get("fire_exit"))
        _pset(f, door, "Pset_DoorCommon", {
            "IsExternal": False,
            "FireExit": _fire,                       # 계단실 방화문 (피난 경로)
            "FireRating": "을종" if _fire else None,
            "Reference": f"{'FD' if _fire else 'D'}{round(w*1000)}x{round(hgt*1000)}",
        })
        _qto(f, door, "Qto_DoorBaseQuantities", [
            ("L", "Width", w), ("L", "Height", hgt), ("A", "Area", w * hgt),
        ])
        _typed(door, "IfcDoorType",
               f"{'FD' if _fire else 'D'}{round(w*1000)}x{round(hgt*1000)}",
               "DOOR")
        return door
    for fp in floor_plans:
        d = fp.get("data", {})
        fid = d.get("floor_id")
        st = storey_by_floor.get(fid)
        geom = fp.get("geom", {}) or {}
        if st is None:
            continue
        elems = []
        wall_registry: dict[tuple, object] = {}   # (p0,p1) 좌표키 → IfcWall (문 개구용)
        for key, ifc_cls, hexc, transp, mat, predef in GEOM_MAP:
            geoms = list(_iter_geoms(geom.get(key)))
            # LOD300 경로 — userData 부재는 개별 승급, 잔여는 tessellation 폴백
            if key == "walls":
                lod300 = [g for g in geoms
                          if (g.get("userData") or {}).get("kind") == "wall"]
                for seq, g in enumerate(lod300, 1):
                    ud = g["userData"]
                    w = _wall_entity(ud, st, fid, seq)
                    if w is not None:
                        # 재질은 레이어셋(RelAssociatesMaterial)이 전담 — 이중 연결 금지
                        elems.append(w)
                        wall_registry[
                            (tuple(round(v, 2) for v in ud["p0"]),
                             tuple(round(v, 2) for v in ud["p1"]))] = w
                geoms = [g for g in geoms if g not in lod300]
            elif key == "doors":
                lod300 = [g for g in geoms
                          if (g.get("userData") or {}).get("kind") == "door"]
                for seq, g in enumerate(lod300, 1):
                    e = _opening_entity(g["userData"], st, fid, seq, wall_registry)
                    if e is not None:
                        use_material(mat, e)
                        elems.append(e)
                geoms = [g for g in geoms if g not in lod300]
            elif key in ("floors", "roof"):
                lod300 = [g for g in geoms
                          if (g.get("userData") or {}).get("kind") == "slab"]
                for g in lod300:
                    s = _slab_entity(g["userData"], st, fid, hexc)
                    if s is not None:
                        elems.append(s)
                geoms = [g for g in geoms if g not in lod300]
            elif key == "windows":
                lod300 = [g for g in geoms
                          if (g.get("userData") or {}).get("kind") == "window"]
                for seq, g in enumerate(lod300, 1):
                    e = _opening_entity(g["userData"], st, fid, seq,
                                        wall_registry, is_window=True)
                    if e is not None:
                        use_material(mat, e)
                        elems.append(e)
                geoms = [g for g in geoms if g not in lod300]
            elif key == "coverings":
                lod300 = [g for g in geoms
                          if (g.get("userData") or {}).get("kind") == "covering"]
                for g in lod300:
                    ud = g["userData"]
                    pts = _ring_xy(ud.get("outline") or [], cx, cy)
                    if len(pts) < 3:
                        continue
                    t = float(ud.get("t", 0.01))
                    solid = _extruded_solid(
                        f, pts, float(ud["top_z"]) - t - _elev(st), t)
                    _role = ud.get("role", "ceiling")
                    ent = f.create_entity(
                        "IfcCovering", GlobalId=_gid(),
                        Name=f"{fid}F {'천장마감' if _role == 'ceiling' else '테라스마감'}",
                        ObjectPlacement=_on_storey(f, st),
                        Representation=_shape_solid(
                            f, ctx, solid, surface_style(hexc, 0.0)),
                        PredefinedType="CEILING" if _role == "ceiling" else "FLOORING")
                    _associate_material(ent, _layer_set_usage(
                        ud.get("layers"),
                        "[천장]" if _role == "ceiling" else "[테라스]",
                        direction="AXIS3", offset=0.0))
                    try:
                        from shapely.geometry import Polygon as _SP3
                        _qto(f, ent, "Qto_CoveringBaseQuantities",
                             [("A", "GrossArea", _SP3(pts).area),
                              ("L", "Width", t)])
                    except Exception:
                        pass
                    elems.append(ent)
                geoms = [g for g in geoms if g not in lod300]
            elif key == "columns":
                lod300 = [g for g in geoms
                          if (g.get("userData") or {}).get("kind") == "column"]
                for seq, g in enumerate(lod300, 1):
                    e = _column_entity(g["userData"], st, fid, seq)
                    if e is not None:
                        use_material(mat, e)
                        elems.append(e)
                geoms = [g for g in geoms if g not in lod300]
            elif key == "beams":
                lod300 = [g for g in geoms
                          if (g.get("userData") or {}).get("kind") == "beam"]
                for seq, g in enumerate(lod300, 1):
                    e = _beam_entity(g["userData"], st, fid, seq)
                    if e is not None:
                        use_material(mat, e)
                        elems.append(e)
                geoms = [g for g in geoms if g not in lod300]
            facesets = [_faceset(f, g, dz=_elev(st)) for g in geoms]
            shape = _shape_tess(f, ctx, facesets, surface_style(hexc, transp))
            if shape is None:
                continue
            kwargs = dict(
                GlobalId=_gid(), Name=f"{('B1' if fid==-1 else str(fid)+'F')} {key}",
                ObjectPlacement=_on_storey(f, st), Representation=shape)
            if predef and ifc_cls in ("IfcSlab", "IfcColumn"):
                kwargs["PredefinedType"] = predef
            ent = f.create_entity(ifc_cls, **kwargs)
            if mat:
                use_material(mat, ent)
            # 계단 — tessellation Body + 치수 Pset (ExtrudedSolid 계단은 아키캐드 판정 후)
            if key == "stairs":
                for g in geoms:
                    if (g.get("userData") or {}).get("kind") == "stair":
                        _stair_pset(ent, g["userData"])
                        break
                _typed(ent, "IfcStairType", "계단(코어)", "NOTDEFINED")
            elif key == "parapets":
                _typed(ent, "IfcRailingType", "옥상 난간", "GUARDRAIL")
            elems.append(ent)
        # ── 난간동자·손스침 → IfcMember (살 간격 ≤10cm, 시행령 40조②) ──
        _rl = [g for g in _iter_geoms(geom.get("parapets"))
               if (g.get("userData") or {}).get("kind") == "railing"]
        _rseq = 0
        for g in _rl:
            _ud = g["userData"]
            for mem in railing_members(
                    _ud, post=_ud.get("post_size", 0.04),
                    clear=_ud.get("clear", 0.10)):
                fs = _faceset(f, mem["geom"], dz=_elev(st))
                if fs is None:
                    continue
                _rseq += 1
                part = mem["part"]
                m = f.create_entity(
                    "IfcMember", GlobalId=_gid(),
                    Name=f"RL {'POST' if part == 'post' else 'HANDRAIL'} - "
                         f"{fid:02d}{_rseq:03d}",
                    ObjectPlacement=_on_storey(f, st),
                    Representation=_shape_tess(
                        f, ctx, [fs], surface_style(_C_PARAPET, 0.0)),
                    PredefinedType="POST" if part == "post" else "STRINGER")
                use_material("금속(난간)", m)
                _pset(f, m, "Pset_MemberCommon",
                      {"IsExternal": True, "LoadBearing": False,
                       "Reference": part})
                elems.append(m)

        # ── 계단 부재 분해 — 챌판·디딤판·참 → IfcMember ──
        _PARTNAME = {"riser": "RISER", "tread": "TREAD", "landing": "LANDING"}
        _members = [g for g in _iter_geoms(geom.get("stairs"))
                    if (g.get("userData") or {}).get("kind") == "stair_member"]
        for g in _members:
            mu = g["userData"]
            fs = _faceset(f, g, dz=_elev(st))
            if fs is None:
                continue
            sh = _shape_tess(f, ctx, [fs], surface_style(_C_PARAPET, 0.0))
            part = mu.get("part", "tread")
            m = f.create_entity(
                "IfcMember", GlobalId=_gid(),
                Name=f"SF {_PARTNAME.get(part, part.upper())} - "
                     f"{fid:02d}{mu.get('index', 0):03d}",
                ObjectPlacement=_on_storey(f, st),
                Representation=sh)
            use_material("철근콘크리트(계단)", m)
            _pset(f, m, "Pset_MemberCommon",
                  {"IsExternal": False, "LoadBearing": True,
                   "Reference": part})
            elems.append(m)
        _rel_contained(f, st, elems)

    # ── 세대 IfcSpace (polygon, 룸) + NetFloorArea 수량 ──
    space_style = surface_style(0x78A0C8, 0.7)
    spaces_by_storey: dict[int, list] = {}
    n_units = 0
    for u in units:
        poly = u.get("polygon")
        if not poly:
            continue
        fid = int(u.get("floor") or 1)
        st = storey_by_floor.get(fid)
        if st is None:
            continue
        pts = _ring_xy(poly, cx, cy)
        if len(pts) < 3:
            continue
        sd = fdata.get(fid, {})
        bottom = _num(u.get("floor_bottom_height"),
                      _num(sd.get("floor_bottom_height"), (fid - 1) * 3.0))
        fh = _num(u.get("floor_height"), _num(sd.get("floor_height"), 3.0))
        uid = str(u.get("id", ""))
        is_core = uid.startswith("core-")
        area = (u.get("area") or {})
        net = area.get("net")
        name = "코어" if is_core else f"{uid}호"
        if not is_core:
            n_units += 1
        ent = f.create_entity(
            "IfcSpace", GlobalId=_gid(), Name=name,
            LongName=(f"{net:.1f}㎡" if isinstance(net, (int, float)) and net else None),
            ObjectPlacement=_on_storey(f, st),
            Representation=_shape_solid(
                f, ctx, _extruded_solid(f, pts, bottom - _elev(st), fh),
                space_style),
            CompositionType="ELEMENT", PredefinedType="INTERNAL")
        if not is_core and isinstance(net, (int, float)):
            _area_quantity(f, ent, net)
        spaces_by_storey.setdefault(fid, []).append(ent)

        dup = u.get("duplex_upper_polygon")
        if dup:
            dpts = _ring_xy(dup, cx, cy)
            if len(dpts) >= 3:
                up_fid = fid + 1
                up_key = up_fid if up_fid in storey_by_floor else fid
                up_st = storey_by_floor[up_key]
                ent_up = f.create_entity(
                    "IfcSpace", GlobalId=_gid(), Name=f"{uid}호 복층",
                    ObjectPlacement=_on_storey(f, up_st),
                    Representation=_shape_solid(
                        f, ctx, _extruded_solid(
                            f, dpts, bottom + fh - _elev(up_st), fh),
                        space_style),
                    CompositionType="ELEMENT", PredefinedType="INTERNAL")
                spaces_by_storey.setdefault(up_key, []).append(ent_up)

    # ── 승강기 카 — IfcTransportElement (참조 도면 1층에 1개) ──
    # 승강로(벽·IfcSpace)만 있고 승강기 자체가 없으면 설비 물량·동선 검토가 안 된다.
    _ev = (scheme_json.get("_core_layout") or {}).get("ev")
    if _ev and 1 in storey_by_floor:
        _ep = _ring_xy(_ev, cx, cy)
        if len(_ep) >= 3:
            _d1 = fdata.get(1, {})
            _ez = _num(_d1.get("floor_bottom_height"), 0.0)
            # 카는 승강로보다 작다 — 벽·레일 여유 0.2m 인셋
            try:
                from shapely.geometry import Polygon as _SP
                _car = _SP(_ep).buffer(-0.2)
                if _car.is_empty:
                    _car = _SP(_ep)
                if _car.geom_type == "MultiPolygon":
                    _car = max(_car.geoms, key=lambda g: g.area)
                _cp2 = list(_car.exterior.coords)[:-1]
            except Exception:
                _cp2 = _ep
            _lift = f.create_entity(
                "IfcTransportElement", GlobalId=_gid(), Name="승강기",
                ObjectPlacement=_on_storey(f, storey_by_floor[1]),
                Representation=_shape_solid(
                    f, ctx, _extruded_solid(
                        f, _cp2, _ez + 0.1 - _elev(storey_by_floor[1]), 2.2),
                    surface_style(_C_COLUMN, 0.0)),
                PredefinedType="ELEVATOR")
            _pset(f, _lift, "Pset_TransportElementCommon",
                  {"Reference": "P6-CO", "CapacityPeople": 6,
                   "FireExit": False})
            _rel_contained(f, storey_by_floor[1], [_lift])

    # ── 코어 실(계단실·승강기·복도) + B1 기계실 IfcSpace ──
    # 참조 도면도 세대 외에 '기계실'·'저수조'를 실로 잡는다. 코어 3실은 층마다
    # 존재하므로 거주층 전체에 stack (피난·면적 산출의 실 단위).
    _CORE_ROOM = {"stair": ("계단실", "INTERNAL"), "ev": ("승강기", "INTERNAL"),
                  "corridor": ("복도", "INTERNAL")}
    _cl = scheme_json.get("_core_layout") or {}
    _resi_fids = sorted(fid for fid in storey_by_floor
                        if fid >= 2 and not fdata.get(fid, {}).get("floor_name"))
    for key, (rname, ptype) in _CORE_ROOM.items():
        ring = _cl.get(key)
        if not ring:
            continue
        pts = _ring_xy(ring, cx, cy)
        if len(pts) < 3:
            continue
        for fid in _resi_fids:
            d = fdata.get(fid, {})
            bottom = _num(d.get("floor_bottom_height"), 0.0)
            fh = _num(d.get("floor_height"), 3.0)
            sp = f.create_entity(
                "IfcSpace", GlobalId=_gid(), Name=f"{fid}F {rname}",
                LongName=rname,
                ObjectPlacement=_on_storey(f, storey_by_floor[fid]),
                Representation=_shape_solid(
                    f, ctx, _extruded_solid(
                        f, pts, bottom - _elev(storey_by_floor[fid]), fh),
                    space_style),
                CompositionType="ELEMENT", PredefinedType=ptype)
            try:
                from shapely.geometry import Polygon as _SP
                _area_quantity(f, sp, _SP(pts).area)
            except Exception:
                pass
            spaces_by_storey.setdefault(fid, []).append(sp)

    # B1 기계실 — 참조 도면과 동일 실명
    if -1 in storey_by_floor and scheme_json.get("_basement_outline"):
        _bp = _ring_xy(scheme_json["_basement_outline"], cx, cy)
        if len(_bp) >= 3:
            _bd = fdata.get(-1, {})
            _bz = _num(_bd.get("floor_bottom_height"), -3.0)
            sp = f.create_entity(
                "IfcSpace", GlobalId=_gid(), Name="B1 기계실", LongName="기계실",
                ObjectPlacement=_on_storey(f, storey_by_floor[-1]),
                Representation=_shape_solid(
                    f, ctx, _extruded_solid(
                        f, _bp, _bz - _elev(storey_by_floor[-1]),
                        _num(_bd.get("floor_height"), 3.0)),
                    space_style),
                CompositionType="ELEMENT", PredefinedType="INTERNAL")
            _area_quantity(f, sp, _num(_bd.get("floor_area"), 0.0))
            spaces_by_storey.setdefault(-1, []).append(sp)

    # IfcSpace는 spatial이라 aggregates로 storey에 연결
    for fid, sps in spaces_by_storey.items():
        _rel_aggregates(f, storey_by_floor[fid], sps, "Storey→Spaces")

    # ── IfcGrid — 2층 외벽 중심선 = 구조 그리드 (벽식: 벽 중심선이 구조축) ──
    # 아키캐드/레빗에서 축선 스냅·일람 기준이 된다.
    try:
        _gw = []
        for fp in floor_plans:
            if (fp.get("data") or {}).get("floor_id") != 2:
                continue
            for gg in _iter_geoms((fp.get("geom") or {}).get("walls")):
                ud = gg.get("userData") or {}
                if ud.get("kind") == "wall" and ud.get("exterior"):
                    _gw.append(ud)
        if len(_gw) >= 2:
            import math as _mth

            def _axis(ud):
                p0 = (float(ud["p0"][0]) - cx, float(ud["p0"][1]) - cy)
                p1 = (float(ud["p1"][0]) - cx, float(ud["p1"][1]) - cy)
                pl = f.create_entity("IfcPolyline", Points=[
                    f.create_entity("IfcCartesianPoint", Coordinates=p0),
                    f.create_entity("IfcCartesianPoint", Coordinates=p1)])
                return pl, (p1[0] - p0[0], p1[1] - p0[1])

            _ref = None
            uax, vax = [], []
            for ud in _gw:
                pl, d = _axis(ud)
                ln = _mth.hypot(*d) or 1.0
                dn = (d[0] / ln, d[1] / ln)
                if _ref is None:
                    _ref = dn
                is_u = abs(dn[0] * _ref[0] + dn[1] * _ref[1]) > 0.7
                tag = f"X{len(uax)+1}" if is_u else f"Y{len(vax)+1}"
                ax_ = f.create_entity("IfcGridAxis", AxisTag=tag,
                                      AxisCurve=pl, SameSense=True)
                (uax if is_u else vax).append(ax_)
            if uax and vax:
                grid = f.create_entity(
                    "IfcGrid", GlobalId=_gid(), Name="구조 그리드(벽 중심선)",
                    ObjectPlacement=_placement(f, storey_by_floor.get(
                        1, storeys[0]).ObjectPlacement),
                    UAxes=uax, VAxes=vax)
                _rel_contained(f, storey_by_floor.get(1, storeys[0]), [grid])
    except Exception:
        pass

    # ── 타입 객체 방출 (IfcRelDefinesByType) ──
    _TYPE_EXTRA = {  # 필수 속성이 더 있는 타입 클래스
        "IfcDoorType": {"OperationType": "SINGLE_SWING_LEFT"},
        "IfcWindowType": {"PartitioningType": "SINGLE_PANEL"},
    }
    for (tcls, tname, tpredef), members in _type_reg.items():
        t_ent = f.create_entity(
            tcls, GlobalId=_gid(), Name=tname, PredefinedType=tpredef,
            **_TYPE_EXTRA.get(tcls, {}))
        f.create_entity(
            "IfcRelDefinesByType", GlobalId=_gid(),
            RelatedObjects=members, RelatingType=t_ent)

    # ── 재질 일괄 연결 ──
    for name, members in _mat_members.items():
        if members:
            f.create_entity(
                "IfcRelAssociatesMaterial", GlobalId=_gid(), Name=name,
                RelatedObjects=members, RelatingMaterial=_mat_cache[name])

    # ── 건물 Pset (사업개요) ──
    _building_pset(f, building, scheme_json.get("data"), n_units, style_key)

    out_path = str(out_path)
    f.write(out_path)
    return out_path


def ifc_filename(land_id, design_id=None, suffix=""):
    stamp = time.strftime("%Y%m%d")
    tag = (design_id or land_id)[:8]
    return f"sbim_{tag}_{stamp}{suffix}.ifc"
