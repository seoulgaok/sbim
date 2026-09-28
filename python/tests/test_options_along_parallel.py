"""Core.core_along(삭제) · Parking.parallel — 어휘 결손 두 자리(v1.2, seoulgaok/sbim#18·#19).

core_along 은 2026-09-28 정리에서 지웠다 — core_side 정방위가 곧 변 가운데라 겹쳤다.
저장값에 남아 있으면 받아서 버린다.

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


def test_core_along_is_gone():
    assert "core_along" not in Core.model_fields


@pytest.mark.parametrize("along", ["start", "mid", "end"])
def test_saved_core_along_is_swallowed(along):
    c = Core.model_validate({"core_side": "s", "core_along": along})
    assert c.core_side == "s"
    assert "core_along" not in c.model_dump()


def test_core_side_description_no_longer_mentions_core_along():
    assert "core_along" not in Core.model_fields["core_side"].description


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
    assert design["parking"]["parallel"] is None
    assert set(design["core"]) == {
        "type", "core_side", "core_rotation", "core_mirror", "core_entries",
    }
    assert "parallel" in set(design["parking"])
