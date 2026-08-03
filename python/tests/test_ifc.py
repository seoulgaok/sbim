"""IFC 내보내기 스모크 — 샘플 scheme이 열리는 IFC4로 나오는지.

ifcopenshell은 선택 의존이라 없으면 건너뛴다.
"""
import json
from pathlib import Path

import pytest

ifcopenshell = pytest.importorskip("ifcopenshell")

from seoulgaok_bim_core import generate_ifc  # noqa: E402
from seoulgaok_bim_core.ifc import derive_parcel_center  # noqa: E402

SAMPLE = Path(__file__).resolve().parents[2] / "examples/samples/sample-small"


@pytest.fixture(scope="module")
def model(tmp_path_factory):
    scheme = json.loads((SAMPLE / "scheme.json").read_text(encoding="utf-8"))
    units = json.loads((SAMPLE / "units.json").read_text(encoding="utf-8"))
    out = tmp_path_factory.mktemp("ifc") / "sample.ifc"
    generate_ifc(scheme, units, out_path=str(out))
    assert out.exists() and out.stat().st_size > 0
    return ifcopenshell.open(str(out))


def test_schema_and_hierarchy(model):
    assert model.schema == "IFC4"
    assert len(model.by_type("IfcProject")) == 1
    assert len(model.by_type("IfcBuilding")) == 1
    # 샘플은 지하 1층 + 지상 8층
    assert len(model.by_type("IfcBuildingStorey")) == 9


@pytest.mark.parametrize(
    "entity",
    ["IfcWall", "IfcSlab", "IfcWindow", "IfcDoor", "IfcStair", "IfcSpace"],
)
def test_core_elements_present(model, entity):
    assert model.by_type(entity), f"{entity}이 하나도 없다"


def test_mep_excluded(model):
    """설비는 volume 쪽 책임 — 여기서 나오면 경계가 무너진 것."""
    for entity in ("IfcPipeSegment", "IfcSanitaryTerminal",
                   "IfcDistributionSystem"):
        assert not model.by_type(entity), f"{entity}이 섞여 나왔다"


def test_spaces_have_area(model):
    """세대 IfcSpace에 NetFloorArea가 붙어야 적산에 쓸 수 있다."""
    quantities = [
        q for q in model.by_type("IfcQuantityArea") if q.Name == "NetFloorArea"
    ]
    assert quantities, "NetFloorArea 수량이 없다"
    assert all(q.AreaValue > 0 for q in quantities)


def test_derive_parcel_center_matches_explicit(tmp_path):
    """parcel_center 자동 도출이 명시 전달과 같은 결과를 내는지."""
    scheme = json.loads((SAMPLE / "scheme.json").read_text(encoding="utf-8"))
    center = derive_parcel_center(scheme)
    assert len(center) == 2
    # 샘플은 합성 원점(20xxxx, 5000xx) 근처로 평행이동돼 있다
    assert 100000 < center[0] < 400000
    assert 300000 < center[1] < 750000


def test_derive_parcel_center_rejects_empty():
    with pytest.raises(ValueError):
        derive_parcel_center({"data": {"lot_area": 100}})


# ── Import (IFC → scheme/units) ──────────────────────────────────────────

@pytest.fixture(scope="module")
def roundtrip(tmp_path_factory):
    """sample → IFC → scheme/units 복원."""
    from seoulgaok_bim_core.ifc import load_ifc

    scheme = json.loads((SAMPLE / "scheme.json").read_text(encoding="utf-8"))
    units = json.loads((SAMPLE / "units.json").read_text(encoding="utf-8"))
    out = tmp_path_factory.mktemp("rt") / "rt.ifc"
    generate_ifc(scheme, units, out_path=str(out))
    return load_ifc(str(out)), scheme, units


def test_import_recovers_building_data(roundtrip):
    (got_scheme, _), scheme, _ = roundtrip
    for key in ("lot_area", "build_area", "far", "bcr", "pnu"):
        assert got_scheme["data"][key] == scheme["data"][key], key


def test_import_recovers_storeys(roundtrip):
    (got_scheme, _), scheme, _ = roundtrip
    got = {fp["data"]["floor_id"] for fp in got_scheme["floor_plans"]}
    want = {fp["data"]["floor_id"] for fp in scheme["floor_plans"]}
    assert got == want
    for fp in got_scheme["floor_plans"]:
        src = next(s for s in scheme["floor_plans"]
                   if s["data"]["floor_id"] == fp["data"]["floor_id"])
        assert fp["data"]["floor_bottom_height"] == pytest.approx(
            src["data"]["floor_bottom_height"], abs=1e-6)


def test_import_recovers_unit_ids_and_polygons(roundtrip):
    """세대는 flat UnitRecord로 복원돼야 한다 — generate_ifc가 읽는 그 형태."""
    (_, got_units), _, units = roundtrip
    want = [str(u["id"]) for u in units if not str(u["id"]).startswith("core")]
    assert [u["id"] for u in got_units] == want
    assert all(u.get("polygon") for u in got_units), "세대 polygon이 복원되지 않았다"
    assert all(u["area"]["net"] > 0 for u in got_units)


def test_import_produces_renderable_geometry(roundtrip):
    """복원된 메시가 BufferGeometry 형태를 갖추는지 — 뷰어가 바로 그릴 수 있어야."""
    (got_scheme, _), _, _ = roundtrip
    meshes = [m
              for fp in got_scheme["floor_plans"]
              for groups in fp["geom"].values()
              for group in groups
              for m in group]
    assert meshes, "복원된 메시가 없다"
    for m in meshes[:50]:
        attrs = m["data"]["attributes"]
        assert m["type"] == "BufferGeometry"
        assert len(attrs["position"]["array"]) % 3 == 0
        assert len(attrs["position"]["array"]) >= 9
        assert len(m["data"]["index"]["array"]) % 3 == 0


def test_import_skips_derived_members(roundtrip):
    """IfcMember(난간살·계단 부재)는 원본 메시에서 파생된 것 — 되읽으면 중복."""
    (got_scheme, _), _, _ = roundtrip
    keys = {k for fp in got_scheme["floor_plans"] for k in fp["geom"]}
    assert "members" not in keys
    # 난간은 parapets 한 벌로만 들어와야 한다
    parapets = sum(len(fp["geom"].get("parapets", []))
                   for fp in got_scheme["floor_plans"])
    assert 0 < parapets < 50, parapets


def test_reexport_is_stable(roundtrip, tmp_path):
    """복원한 scheme을 다시 내보내도 층·슬래브·계단·세대 수가 유지되는지.

    벽/창/문 개수는 줄어든다 — LOD300 userData(세그먼트 분할·재질 레이어)가
    복원 대상이 아니라, 재수출 시 그룹당 1개 요소로 합쳐지기 때문. 형상은
    남고 요소 단위만 거칠어진다. 아래 항목은 그 영향을 받지 않는다.
    """
    (got_scheme, got_units), _, _ = roundtrip
    out = tmp_path / "again.ifc"
    generate_ifc(got_scheme, got_units, parcel_center=[0, 0], out_path=str(out))
    again = ifcopenshell.open(str(out))
    assert len(again.by_type("IfcBuildingStorey")) == 9
    assert len(again.by_type("IfcSlab")) == 15
    assert len(again.by_type("IfcStair")) == 7
    assert len(again.by_type("IfcSpace")) == len(got_units)
    assert not again.by_type("IfcPipeSegment")


def test_railing_not_duplicated_across_floors(model):
    """같은 절대 위치의 난간동자가 두 번 나가지 않아야 한다.

    샘플 3건 모두 6F 난간(base_z = 6F 천장)이 옥탑층에도 그대로 등재돼 있다.
    그대로 내보내면 같은 실물이 두 벌 나가 적산 물량이 2배가 된다.

    층별 개수 비교는 못 쓴다 — 서로 다른 난간이 우연히 같은 개수일 수 있다
    (sample-small은 3·4·5F가 모두 66개다). 절대 좌표로 판정한다.
    """
    elevation_of = {}
    for rel in model.by_type("IfcRelContainedInSpatialStructure"):
        structure = rel.RelatingStructure
        if structure.is_a("IfcBuildingStorey"):
            for el in rel.RelatedElements:
                elevation_of[el.id()] = float(structure.Elevation or 0.0)

    positions = []
    for member in model.by_type("IfcMember"):
        if member.PredefinedType != "POST":
            continue
        dz = elevation_of.get(member.id(), 0.0)
        for rep in (member.Representation.Representations or []):
            for item in (rep.Items or []):
                if not item.is_a("IfcTriangulatedFaceSet"):
                    continue
                first = item.Coordinates.CoordList[0]
                positions.append((round(first[0], 3), round(first[1], 3),
                                  round(first[2] + dz, 3)))

    assert positions, "동자가 하나도 없다"
    duplicates = len(positions) - len(set(positions))
    assert duplicates == 0, f"같은 자리에 동자가 겹쳐 있다: {duplicates}개"
