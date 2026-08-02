"""스모크 테스트 — 실제 샘플 JSON이 pydantic 모델로 로드되는지."""

from pathlib import Path

from seoulgaok_bim_core import Scheme, SurroundingBuilding, Unit
from seoulgaok_bim_core.io import (
    load_scheme,
    load_surroundings,
    load_units,
    save_scheme,
)

SAMPLES = Path(__file__).resolve().parents[2] / "examples" / "samples"


def test_load_scheme_sample():
    scheme = load_scheme(SAMPLES / "scheme.json")
    assert isinstance(scheme, Scheme)
    assert len(scheme.floor_plans) > 0
    assert scheme.data.lot_area > 0


def test_load_units_sample():
    units = load_units(SAMPLES / "units.json")
    assert isinstance(units, list)
    assert len(units) > 0
    assert isinstance(units[0], Unit)
    assert units[0].data.id


def test_load_surroundings_sample():
    surroundings = load_surroundings(SAMPLES / "surroundings.json")
    assert isinstance(surroundings, list)
    assert len(surroundings) > 0
    assert isinstance(surroundings[0], SurroundingBuilding)


def test_save_round_trip(tmp_path):
    scheme = load_scheme(SAMPLES / "scheme.json")
    out = tmp_path / "scheme.json"
    save_scheme(scheme, out)
    reloaded = load_scheme(out)
    assert reloaded.data.lot_area == scheme.data.lot_area
    assert len(reloaded.floor_plans) == len(scheme.floor_plans)
