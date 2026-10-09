"""형상 온전성 — "타워"를 내보내기 전에 잡는다 (2026-10-08 현장 사례).

아키캐드에서 열었을 때 원점의 작은 건물에서 기둥 하나가 위아래로 끝없이 뻗은 일이
있었다. 단위 문제가 아니라 부재 하나의 높이가 터진 것이었다. 엔진 출력을 막을 수는
없지만, 그것을 IFC로 써 보내는 것은 막을 수 있다.
"""

import json
from pathlib import Path

import pytest

from seoulgaok_bim_core import check_geometry_sanity, storey_envelope
from seoulgaok_bim_core.geometry_check import raise_if_insane

SAMPLES = Path(__file__).resolve().parents[2] / "examples" / "samples"


def _mesh(z0, z1, x=1.0):
    """z0~z1을 차지하는 최소 메시 하나."""
    pos = [x, 0.0, z0, x, 1.0, z0, x, 1.0, z1, x, 0.0, z1]
    return {"data": {"attributes": {"position": {"array": pos}}}}


def _scheme(*geoms, floors=((1, 0.0, 3.0), (2, 3.0, 3.0))):
    return {
        "floor_plans": [
            {"data": {"floor_id": fid, "floor_bottom_height": z0, "floor_height": h},
             "geom": {"columns": [list(geoms)] if fid == 1 else []}}
            for fid, z0, h in floors
        ]
    }


@pytest.mark.parametrize("name", ["sample-small", "sample-medium", "sample-large"])
def test_real_samples_pass(name):
    """정상 설계는 걸리지 않는다 — 느슨한 봉투여야 쓸 수 있다."""
    scheme = json.loads((SAMPLES / name / "scheme.json").read_text())
    assert check_geometry_sanity(scheme) == []


def test_envelope_follows_storeys():
    lo, hi = storey_envelope(_scheme(_mesh(0, 3)))
    assert lo < 0 and hi > 6          # 층 표고 + 여유


def test_runaway_column_is_caught():
    """현장에서 본 그것 — 위아래로 끝없이 뻗은 기둥."""
    bad = check_geometry_sanity(_scheme(_mesh(-20000.0, 20000.0)))
    assert bad and "메시 z" in bad[0]


def test_runaway_userdata_height_is_caught():
    g = _mesh(0, 3)
    g["userData"] = {"kind": "column", "base_z": 0.0, "top_z": 19999.0}
    bad = check_geometry_sanity(_scheme(g))
    assert any("top_z" in b for b in bad)


def test_far_from_origin_is_caught():
    """메시는 상대좌표다 — EPSG 절대좌표가 섞여 들어오면 원점에서 20만m 떨어진다."""
    bad = check_geometry_sanity(_scheme(_mesh(0, 3, x=200397.0)))
    assert any("떨어짐" in b for b in bad)


def test_raise_names_the_offender():
    with pytest.raises(ValueError, match="메시 z"):
        raise_if_insane(_scheme(_mesh(-20000.0, 20000.0)))


def test_sane_scheme_does_not_raise():
    raise_if_insane(_scheme(_mesh(0.5, 2.5)))
