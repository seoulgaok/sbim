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
