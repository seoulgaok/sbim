"""scheme.json 의 `_compile_errors` — 엔진이 스스로 이 설계안을 거절한 사유.

컴파일 거절은 결과를 버리는 사유가 아니라 **저장된 설계에 남아야 하는 경고**다
(설계는 저장되지만 화면에서는 경고와 함께 보여야 한다). 밑줄 키이므로 pydantic은
검증하지 않고 extra=allow로 통과시킨다 — 계약은 Scheme docstring + TS SchemeSpatial.

값 모양은 생성기가 오늘 실제로 방출하는 것(building-generator pipeline.py·units.py 의
compile_errors.append 사이트: type · reason · details · suggestion)과 같고, 그 정의가
errors.py CompileError 이다.
"""

import json
import re
from pathlib import Path
from typing import get_args

from seoulgaok_bim_core.errors import CompileError, CompileErrorType
from seoulgaok_bim_core.io import load_scheme, save_scheme
from seoulgaok_bim_core.types import Scheme

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = ROOT / "examples" / "samples"

# 생성기 방출형 그대로 — type / reason / details / suggestion 네 칸.
# 군자동 352-9: UnitUnreachable ×2 를 신고하고도 경고 없이 「깨끗한 설계」로 저장된 사례.
ENGINE_ERRORS = [
    {
        "type": "UnitUnreachable",
        "reason": (
            "5층 502호의 전용 면적 중 문에서 폭 1.2m 경로로 도달 가능한 비율이 61%뿐입니다"
            "(기준 90%). 사람이 쓸 수 없는 평면이라 이 기획안은 만들 수 없습니다."
        ),
        "details": {"unit": "502", "reach": 0.61},
        "suggestion": "층 세대 수를 낮추거나 코어 위치·매스를 조정하세요.",
    },
    {
        "type": "ParkingSufficiency",
        "reason": (
            "법정 주차 12대가 필요하지만 이 대지에는 10대만 둘 수 있어 2대가 모자랍니다. "
            "주차 기준을 충족하지 못해 이 기획안은 만들 수 없습니다."
        ),
        "details": {"required": 12, "actual": 10, "shortfall": 2},
        "suggestion": "세대 수를 줄이거나(현재 10세대), 기계식 주차 또는 층수 조정을 검토하세요.",
    },
]


def _payload(errors=None):
    """샘플 scheme에 엔진 방출값을 얹는다 (errors=None → 이 키 없는 구 scheme)."""
    payload = json.loads((SAMPLES / "scheme.json").read_text(encoding="utf-8"))
    if errors is not None:
        payload["_compile_errors"] = errors
    return payload


def test_scheme_keeps_engine_rejections():
    """엔진이 낸 거절 사유가 scheme를 통과해 그대로 남는다 (extra=allow 밑줄 키)."""
    scheme = Scheme.model_validate(_payload(ENGINE_ERRORS))
    assert scheme._compile_errors == ENGINE_ERRORS
    assert scheme.model_dump()["_compile_errors"] == ENGINE_ERRORS


def test_items_satisfy_compile_error_contract():
    """방출값이 errors.py 정본으로 그대로 검증된다 — 새 필드가 새 어휘를 만들지 않는다."""
    scheme = Scheme.model_validate(_payload(ENGINE_ERRORS))
    parsed = [CompileError.model_validate(e) for e in scheme._compile_errors]
    assert [p.type for p in parsed] == ["UnitUnreachable", "ParkingSufficiency"]
    assert parsed[0].details["unit"] == "502"
    assert parsed[1].details["shortfall"] == 2


def test_save_load_round_trip(tmp_path):
    """save_scheme → load_scheme 를 오가도 경고가 지워지지 않는다 (nextbase 저장 경로)."""
    src = tmp_path / "scheme.json"
    src.write_text(json.dumps(_payload(ENGINE_ERRORS), ensure_ascii=False), encoding="utf-8")

    out = tmp_path / "out" / "scheme.json"
    save_scheme(load_scheme(src), out)

    assert json.loads(out.read_text(encoding="utf-8"))["_compile_errors"] == ENGINE_ERRORS
    assert load_scheme(out)._compile_errors == ENGINE_ERRORS


def test_absent_and_empty_are_distinguishable():
    """없음(구 scheme)은 키 자체가 없고, [] 는 엔진이 보고할 게 없었다는 정직한 값. 둘 다 컴파일 통과."""
    old = Scheme.model_validate(_payload(None))
    assert "_compile_errors" not in old.model_dump()
    assert getattr(old, "_compile_errors", None) is None

    clean = Scheme.model_validate(_payload([]))
    assert clean._compile_errors == []
    assert clean.model_dump()["_compile_errors"] == []

    # 실제 샘플(생성기 방출물)은 아직 이 키를 안 싣는다 — 소비처는 부재를 '구 버전'으로 본다.
    assert "_compile_errors" not in load_scheme(SAMPLES / "scheme.json").model_dump()


def test_typescript_declares_the_same_key_and_vocabulary():
    """types.py ↔ types.ts 드리프트 방어: 키 선언과 CompileError 어휘가 양쪽에 같다."""
    ts = (ROOT / "typescript" / "src" / "types.ts").read_text(encoding="utf-8")
    spatial = re.search(r"export interface SchemeSpatial \{([\s\S]*?)\n\}", ts)
    assert spatial, "SchemeSpatial 없음"
    assert re.search(
        r"^ {2}_compile_errors\?: CompileError\[\];$", spatial.group(1), re.M
    ), "types.ts SchemeSpatial 에 _compile_errors?: CompileError[] 가 없다"

    errs_ts = (ROOT / "typescript" / "src" / "errors.ts").read_text(encoding="utf-8")
    body = re.search(r"export type CompileErrorType =([\s\S]*?);", errs_ts).group(1)
    assert set(re.findall(r'"([^"]+)"', body)) == set(get_args(CompileErrorType))
