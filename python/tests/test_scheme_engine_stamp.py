"""scheme.json 의 `_engine_stamp` — 이 설계안을 만든 엔진 빌드를 적는 도장.

같은 소스라도 서버(x86_64)와 로컬(arm64) 컴파일 분기가 갈릴 수 있다 — 대지가 다른
설계 결과라면 재현은 커녕 원인을 못 찾는다. 그래서 엔진이 방출한 설계에 자기 빌드를
찍는다: 어떤 커밋·플랫폼·파이썬·시각에 만들어졌는지. 소비처(서버)는 그 결과의 출처를
이 키로 추적한다.

밑줄 키이므로 pydantic은 검증하지 않고 extra=allow로 통과시킨다 — 계약은 Scheme
docstring + TS SchemeSpatial(EngineStamp). 값은 전부 문자열. 없음 = 구 scheme.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from seoulgaok_bim_core.io import load_scheme, save_scheme
from seoulgaok_bim_core.types import Scheme

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = ROOT / "examples" / "samples"

# EngineStamp 계약 — 전부 str, compiled_at 은 ISO-8601 UTC.
# x86 서버에서 방출된 설계 예(플랫폼이 다르면 같은 입력도 다른 분기로 갈린다).
ENGINE_STAMP = {
    "engine_commit": "e10b99a79b65984dcda516792cd79ab2290b075d",
    "platform": "linux-x86_64",
    "python": "3.12.7",
    "compiled_at": "2026-10-06T02:15:33Z",
}


def _payload(stamp=None):
    """샘플 scheme에 엔진 빌드 도장을 얹는다 (stamp=None → 이 키 없는 구 scheme)."""
    payload = json.loads((SAMPLES / "scheme.json").read_text(encoding="utf-8"))
    if stamp is not None:
        payload["_engine_stamp"] = stamp
    return payload


def test_scheme_keeps_engine_stamp():
    """엔진이 찍은 빌드 도장이 scheme를 통과해 그대로 남는다 (extra=allow 밑줄 키)."""
    scheme = Scheme.model_validate(_payload(ENGINE_STAMP))
    assert scheme._engine_stamp == ENGINE_STAMP
    assert scheme.model_dump()["_engine_stamp"] == ENGINE_STAMP


def test_all_stamp_fields_are_strings():
    """계약: 네 칸(engine_commit·platform·python·compiled_at) 전부 문자열."""
    scheme = Scheme.model_validate(_payload(ENGINE_STAMP))
    stamp = scheme._engine_stamp
    assert set(stamp) == {"engine_commit", "platform", "python", "compiled_at"}
    assert all(isinstance(v, str) for v in stamp.values())


def test_compiled_at_is_iso8601_utc():
    """compiled_at 은 ISO-8601 UTC 로 되읽힌다 — 시각이 아니면 추적 기준이 무너진다."""
    compiled_at = ENGINE_STAMP["compiled_at"]
    dt = datetime.fromisoformat(compiled_at.replace("Z", "+00:00"))
    assert dt.tzinfo is not None and dt.utcoffset() == timezone.utc.utcoffset(None)


def test_save_load_round_trip(tmp_path):
    """save_scheme → load_scheme 를 오가도 도장이 지워지지 않는다 (저장 경로)."""
    src = tmp_path / "scheme.json"
    src.write_text(json.dumps(_payload(ENGINE_STAMP), ensure_ascii=False), encoding="utf-8")

    out = tmp_path / "out" / "scheme.json"
    save_scheme(load_scheme(src), out)

    assert json.loads(out.read_text(encoding="utf-8"))["_engine_stamp"] == ENGINE_STAMP
    assert load_scheme(out)._engine_stamp == ENGINE_STAMP


def test_absent_on_old_scheme():
    """없음(구 scheme)은 키 자체가 없다 — 소비처는 부재를 '구 버전'으로 처리한다."""
    old = Scheme.model_validate(_payload(None))
    assert "_engine_stamp" not in old.model_dump()
    assert getattr(old, "_engine_stamp", None) is None

    # 실제 샘플(생성기 방출물)은 아직 이 키를 안 싣는다.
    assert "_engine_stamp" not in load_scheme(SAMPLES / "scheme.json").model_dump()


def test_typescript_declares_the_same_key_and_shape():
    """types.py ↔ types.ts 드리프트 방어: 키·EngineStamp 모양이 양쪽에 같다."""
    ts = (ROOT / "typescript" / "src" / "types.ts").read_text(encoding="utf-8")
    spatial = re.search(r"export interface SchemeSpatial \{([\s\S]*?)\n\}", ts)
    assert spatial, "SchemeSpatial 없음"
    assert re.search(
        r"^ {2}_engine_stamp\?: EngineStamp;$", spatial.group(1), re.M
    ), "types.ts SchemeSpatial 에 _engine_stamp?: EngineStamp 가 없다"

    iface = re.search(r"export interface EngineStamp \{([\s\S]*?)\n\}", ts)
    assert iface, "EngineStamp interface 없음"
    fields = re.findall(r"^ {2}(\w+): string;$", iface.group(1), re.M)
    assert fields == ["engine_commit", "platform", "python", "compiled_at"], fields
