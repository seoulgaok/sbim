"""Core.core_along · Parking.parallel — 어휘 결손 두 자리(v1.2, seoulgaok/sbim#18·#19).

`core_side`는 **변**까지만 정한다. 변 위의 자리(양끝·가운데)는 속성 창에 없어서
소장이 「코어를 남측 가운데에」라고 해도 적을 곳이 없었다 — 엔진 안의 `core_at_mid`
첫수표가 sbim에 없는 내부 키를 내는 셈. `parallel`도 마찬가지로 평행 열을 쓰느냐의
선택이 `parking_angle`(45/60/90)·deprecated `type`에는 적히지 않는다.

둘 다 None이 기본 — 새 키가 없는 기존 저장 설계안은 값이 그대로 읽힌다.
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from seoulgaok_bim_core.options import BuildOptions, Core, Parking

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


# ── Core.core_along ──────────────────────────────────────────────────


def test_core_along_default_is_none():
    assert Core().core_along is None


@pytest.mark.parametrize("along", ["start", "mid", "end"])
def test_core_along_accepted(along):
    assert Core(core_along=along).core_along == along


@pytest.mark.parametrize("along", ["center", "middle", "left", "L/2", "", 0.5])
def test_core_along_unknown_rejected(along):
    with pytest.raises(ValidationError):
        Core(core_along=along)


def test_core_along_description_names_core_side():
    """무시 조건(core_side가 c이거나 없으면)과 자동 표기를 설명이 말한다."""
    desc = Core.model_fields["core_along"].description
    assert "core_side" in desc
    assert "None=첫수표가 정한다" in desc


# ── Parking.parallel ─────────────────────────────────────────────────


def test_parallel_default_is_none():
    assert Parking().parallel is None


@pytest.mark.parametrize("parallel", [True, False])
def test_parallel_accepted(parallel):
    assert Parking(parallel=parallel).parallel is parallel


@pytest.mark.parametrize("bad", [3, [], 1.5, "maybe"])
def test_parallel_not_bool(bad):
    with pytest.raises(ValidationError):
        Parking(parallel=bad)


# ── 기존 저장 설계안은 그대로 ────────────────────────────────────────


def test_saved_design_without_new_keys_reads_unchanged():
    """새 키가 없는 저장값은 검증 후 다른 필드가 하나도 안 바뀐다 — 새 필드만 None."""
    opts = BuildOptions.model_validate(json.loads((EXAMPLES / "sbim_config.example.json").read_text()))
    design = opts.model_dump()["design"]
    assert design["core"]["core_along"] is None
    assert design["parking"]["parallel"] is None
    # 새 필드를 빼면 옛 키 집합과 같다 — 직렬화 키가 늘어난 것 외 변형 없음.
    assert set(design["core"]) == {  # 옛 필드 + core_along
        "type", "composition", "core_side", "core_rotation", "core_mirror", "core_entries", "core_along",
    }
    assert "parallel" in set(design["parking"])
