"""scheme.json 의 `_column_sections` — 기둥마다의 실단면을 설계에 싣는다.

scheme에 `_column_centers`·`_column_size`만 있으면 소비처는 모든 기둥을 w×w 정사각으로
그린다 — 얇은 단면 기둥(엔진 단면 0.9×0.3 m 등)이 주차 칸을 물고 들어간 모습으로
보인다(서초 1508-29). `_column_sections`는 기둥마다 실단면을 싣고, 있음이면 소비처는
이것으로 그린다. 없음(구 scheme) = `_column_size` 정사각 폴백.

밑줄 키이므로 pydantic은 검증하지 않고 extra=allow로 통과시킨다 — 계약은 Scheme
docstring + TS SchemeSpatial(ColumnSection). center 는 [x, y], w·d·angle_deg 는 수.
"""

import json
import re
from pathlib import Path

from seoulgaok_bim_core.io import load_scheme, save_scheme
from seoulgaok_bim_core.types import Scheme

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = ROOT / "examples" / "samples"

# ColumnSection 계약 — _column_centers와 같은 좌표 프레임·같은 순서.
# 이음매 기둥(0.9×0.3)이 정사각으로 그려지면 주차 칸을 문다 — 실단면으로 그려야 한다.
COLUMN_SECTIONS = [
    {"center": [935000.1, 1742000.2], "w": 0.9, "d": 0.3, "angle_deg": 0.0},
    {"center": [935001.4, 1742003.8], "w": 0.3, "d": 0.3, "angle_deg": 45.0},
]
COLUMN_CENTERS = [[935000.1, 1742000.2], [935001.4, 1742003.8]]


def _payload(sections=None, centers=None):
    """샘플 scheme에 실단면을 얹는다 (sections=None → 이 키 없는 구 scheme)."""
    payload = json.loads((SAMPLES / "scheme.json").read_text(encoding="utf-8"))
    if sections is not None:
        payload["_column_sections"] = sections
    if centers is not None:
        payload["_column_centers"] = centers
    return payload


def test_scheme_keeps_column_sections():
    """실단면 목록이 scheme를 통과해 그대로 남는다 (extra=allow 밑줄 키)."""
    scheme = Scheme.model_validate(_payload(COLUMN_SECTIONS, COLUMN_CENTERS))
    assert scheme._column_sections == COLUMN_SECTIONS
    assert scheme.model_dump()["_column_sections"] == COLUMN_SECTIONS


def test_section_keys_and_types():
    """계약: 네 칸(center·w·d·angle_deg). center 는 [x, y] 짝, 나머지는 수."""
    scheme = Scheme.model_validate(_payload(COLUMN_SECTIONS, COLUMN_CENTERS))
    for section in scheme._column_sections:
        assert set(section) == {"center", "w", "d", "angle_deg"}
        assert isinstance(section["center"], list) and len(section["center"]) == 2
        assert all(isinstance(section["center"][i], float) for i in (0, 1))
        assert all(
            isinstance(section[k], float) for k in ("w", "d", "angle_deg")
        )


def test_order_follows_column_centers():
    """계약: _column_centers와 같은 순서 — i번째 실단면은 i번째 중심의 기둥이다."""
    dumped = Scheme.model_validate(
        _payload(COLUMN_SECTIONS, COLUMN_CENTERS)
    ).model_dump()
    assert len(dumped["_column_sections"]) == len(dumped["_column_centers"])
    assert [list(s["center"]) for s in dumped["_column_sections"]] == dumped[
        "_column_centers"
    ]


def test_save_load_round_trip(tmp_path):
    """save_scheme → load_scheme 를 오가도 실단면이 지워지지 않는다 (저장 경로)."""
    src = tmp_path / "scheme.json"
    src.write_text(
        json.dumps(_payload(COLUMN_SECTIONS, COLUMN_CENTERS), ensure_ascii=False),
        encoding="utf-8",
    )

    out = tmp_path / "out" / "scheme.json"
    save_scheme(load_scheme(src), out)

    assert json.loads(out.read_text(encoding="utf-8"))["_column_sections"] == COLUMN_SECTIONS
    assert load_scheme(out)._column_sections == COLUMN_SECTIONS


def test_absent_on_old_scheme():
    """없음(구 scheme)은 키 자체가 없다 — 소비처는 _column_size 정사각으로 폴백한다."""
    old = Scheme.model_validate(_payload(None))
    assert "_column_sections" not in old.model_dump()
    assert getattr(old, "_column_sections", None) is None

    # 실제 샘플(생성기 방출물)은 아직 이 키를 안 싣는다.
    assert "_column_sections" not in load_scheme(SAMPLES / "scheme.json").model_dump()


def test_typescript_declares_the_same_key_and_shape():
    """types.py ↔ types.ts 드리프트 방어: 키·ColumnSection 모양이 양쪽에 같다."""
    ts = (ROOT / "typescript" / "src" / "types.ts").read_text(encoding="utf-8")
    spatial = re.search(r"export interface SchemeSpatial \{([\s\S]*?)\n\}", ts)
    assert spatial, "SchemeSpatial 없음"
    assert re.search(
        r"^ {2}_column_sections\?: ColumnSection\[\];$", spatial.group(1), re.M
    ), "types.ts SchemeSpatial 에 _column_sections?: ColumnSection[] 가 없다"

    iface = re.search(r"export interface ColumnSection \{([\s\S]*?)\n\}", ts)
    assert iface, "ColumnSection interface 없음"
    fields = re.findall(r"^ {2}(\w+): [\w\[\]]+;$", iface.group(1), re.M)
    assert fields == ["center", "w", "d", "angle_deg"], fields
