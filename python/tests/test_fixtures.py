"""fixtures/ — 소비처가 같은 정답으로 검사하는 파일이 정본(BuildOptions)과 같은가.

expected 는 `BuildOptions.model_validate(input).model_dump(mode="json")` 이다. 정본이 바뀌었는데
생성을 안 돌리면 여기서 걸린다 — cd python && uv run python scripts/gen_build_options.py
"""

import importlib.util
import json
from pathlib import Path

import pytest

from seoulgaok_bim_core import CORE_TYPE_RENUMBER_2026_09, BuildOptions

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures" / "build_options"
GEN = Path(__file__).resolve().parents[1] / "scripts" / "gen_build_options.py"

CASES = sorted(FIXTURES.glob("*.json"))


def _gen():
    spec = importlib.util.spec_from_file_location("gen_build_options", GEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_fixtures_are_fresh():
    assert _gen().main(["--check"]) == 0


def test_every_case_has_a_file():
    assert {p.stem for p in CASES} == set(_gen().FIXTURE_CASES)


@pytest.mark.parametrize("path", CASES, ids=[p.stem for p in CASES])
def test_expected_is_the_normalized_input(path):
    fx = json.loads(path.read_text(encoding="utf-8"))
    assert list(fx) == ["input", "expected"]
    got = BuildOptions.model_validate(fx["input"]).model_dump(mode="json")
    assert got == fx["expected"]
    # 키 순서 = 선언 순서 — 포트가 거울로 삼는다
    assert list(fx["expected"]) == list(BuildOptions.model_fields)
    assert list(fx["expected"]["design"]) == list(BuildOptions.model_fields["design"].annotation.model_fields)


def test_expected_round_trips():
    """expected 를 다시 넣어도 같은 expected — 정규화는 멱등이다."""
    for path in CASES:
        exp = json.loads(path.read_text(encoding="utf-8"))["expected"]
        assert BuildOptions.model_validate(exp).model_dump(mode="json") == exp, path.stem


def test_empty_carries_every_default():
    """`empty` 가 기본값 전부다 — max_span 8.0/8.1 같은 기본값 사고를 이것 하나가 잡는다."""
    exp = json.loads((FIXTURES / "empty.json").read_text(encoding="utf-8"))["expected"]
    assert exp == BuildOptions().model_dump(mode="json")
    assert exp["standards"]["dimensions"]["max_span"] == 8.1


def test_core_type_renumber_table():
    fx = json.loads((ROOT / "fixtures" / "core_type_renumber.json").read_text(encoding="utf-8"))
    assert fx == {"old_to_new": {str(k): v for k, v in CORE_TYPE_RENUMBER_2026_09.items()}}
