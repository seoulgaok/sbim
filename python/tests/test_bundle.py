"""설계안 묶음(.sbim) — 묶고 풀기, 빠짐·손상 거부, 정답(fixtures/bundle/) 읽기."""
import io
import zipfile
from pathlib import Path

import pytest

from seoulgaok_bim_core import BundleError, pack_bundle, read_bundle

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "examples/samples/sample-small"


def _files(*names):
    return {n: (SRC / n).read_bytes() for n in names}


def test_round_trip_keeps_bytes_and_stamp():
    files = _files("scheme.json", "units.json")
    b = read_bundle(pack_bundle(files, land_ids=["1"], design_id="d"))
    assert b.raw == files                       # 엔진이 올린 바이트 그대로
    assert b.manifest.land_ids == ["1"] and b.manifest.design_id == "d"
    assert set(b.manifest.files) == set(files)
    assert b.site is None
    assert len(b.units) > 0


def test_required_and_unknown_entries():
    with pytest.raises(BundleError):
        pack_bundle(_files("scheme.json"), land_ids=[])
    with pytest.raises(BundleError):
        pack_bundle({**_files("scheme.json", "units.json"), "surroundings.json": b"[]"}, land_ids=[])


def test_tampered_entry_is_rejected():
    data = pack_bundle(_files("scheme.json", "units.json"), land_ids=[])
    src = zipfile.ZipFile(io.BytesIO(data))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        for n in src.namelist():
            z.writestr(n, b"[]" if n == "units.json" else src.read(n))
    with pytest.raises(BundleError, match="sha256"):
        read_bundle(out.getvalue())


def test_fixture_reads():
    b = read_bundle(ROOT / "fixtures/bundle/sample-small.sbim")
    assert b.manifest.created_at == "2026-01-01T00:00:00Z"
    assert set(b.manifest.files) == {"scheme.json", "units.json", "site.json"}
    assert b.site is not None and b.site.raw_parcel_area == 400.0
