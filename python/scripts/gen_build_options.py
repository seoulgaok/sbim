"""BuildOptions → schema/build_options.schema.json + typescript/src/options.ts.

정본은 pydantic `BuildOptions`(python/seoulgaok_bim_core/options.py) 하나다. 이 스크립트가
그 JSON Schema를 뽑고, 스키마에서 TS 타입을 **생성**한다 — 손으로 베끼면 갈린다(소비처
nextbase가 SbimStudio.tsx에 속성 창을 재정의해 두었다가 sbim과 어긋난 게 이 파일의 이유).

    cd python && uv run python scripts/gen_build_options.py          # 쓴다
    cd python && uv run python scripts/gen_build_options.py --check  # 어긋나면 1로 끝난다

옵션을 바꾸면 이걸 돌리고 `pnpm -r build`로 dist를 다시 굽는다. `tests/test_build_options_schema.py`가
생성물이 정본과 같은지 지킨다.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from seoulgaok_bim_core.options import BuildOptions

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schema" / "build_options.schema.json"
TS_PATH = ROOT / "typescript" / "src" / "options.ts"

HEADER = """\
/**
 * BuildOptions — 속성 창 입력 타입. **생성 파일 — 손으로 고치지 마라.**
 *
 * 정본: python/seoulgaok_bim_core/options.py (pydantic BuildOptions)
 * 생성: cd python && uv run python scripts/gen_build_options.py
 *       (schema/build_options.schema.json 을 거쳐 이 파일을 쓴다)
 *
 * 거의 모든 필드가 옵셔널이다 — 비우면 sbim 기본값(대부분 None=첫수표가 정한다)이 채운다.
 * 필수는 목록 항목 안쪽뿐이다(주차 버블 튜플의 둘째 값 road|yard).
 * 지운 키(core_along·interior_aisle·far_target …)는 서버가 받아서 버리거나 옮기지만,
 * 새로 보내는 값은 이 모양으로 보낸다.
 */
"""


def schema() -> dict:
    return BuildOptions.model_json_schema()


def _lit(v) -> str:
    return json.dumps(v, ensure_ascii=False)


def ts_type(s: dict) -> str:
    if "$ref" in s:
        return s["$ref"].rsplit("/", 1)[-1]
    if "anyOf" in s:
        parts = []
        for sub in s["anyOf"]:
            t = ts_type(sub)
            if t not in parts:
                parts.append(t)
        return " | ".join(parts)
    if "prefixItems" in s:
        return "[" + ", ".join(ts_type(sub) for sub in s["prefixItems"]) + "]"
    if "const" in s:
        return _lit(s["const"])
    if "enum" in s:
        return " | ".join(_lit(v) for v in s["enum"])
    t = s.get("type")
    if t == "null":
        return "null"
    if t == "string":
        return "string"
    if t in ("number", "integer"):
        return "number"
    if t == "boolean":
        return "boolean"
    if t == "array":
        inner = ts_type(s.get("items", {}))
        return f"({inner})[]" if "|" in inner else f"{inner}[]"
    if t == "object":
        ap = s.get("additionalProperties")
        if isinstance(ap, dict):
            return f"Record<string, {ts_type(ap)}>"
        return "Record<string, unknown>"
    return "unknown"


def _doc(notes: list[str], indent: str) -> list[str]:
    body = [ln.rstrip() for n in notes for ln in n.strip().split("\n")]
    while body and not body[-1]:
        body.pop()
    if not body:
        return []
    return ([f"{indent}/**"]
            + [f"{indent} * {ln}".rstrip().replace("*/", "*\\/") for ln in body]
            + [f"{indent} */"])


def interface(name: str, s: dict) -> list[str]:
    out = _doc([s.get("description", "")], "")
    out.append(f"export interface {name} {{")
    for prop, ps in s.get("properties", {}).items():
        notes = [ps.get("description", "")]
        if "default" in ps:
            notes.append(f"@default {_lit(ps['default'])}")
        if ps.get("auto"):
            notes.append("@auto None=자동")
        # JSON Schema 표준 `deprecated` 키 — 값이 문자열이면 그 이유를 태그에 쓴다
        # (`json_schema_extra={"deprecated": "..."}` 또는 pydantic Field(deprecated=...)).
        dep = ps.get("deprecated")
        if dep:
            notes.append(f"@deprecated {dep}" if isinstance(dep, str) else "@deprecated")
        out += _doc([n for n in notes if n], "  ")
        opt = "" if prop in s.get("required", ()) else "?"
        out.append(f"  {prop}{opt}: {ts_type(ps)};")
    out.append("}")
    return out


def render_ts(sch: dict) -> str:
    defs = dict(sch.get("$defs", {}))
    root = {k: v for k, v in sch.items() if k != "$defs"}
    blocks = [interface(n, defs[n]) for n in sorted(defs)]
    blocks.append(interface(root["title"], root))
    return HEADER + "\n" + "\n\n".join("\n".join(b) for b in blocks) + "\n"


def render_schema(sch: dict) -> str:
    return json.dumps(sch, ensure_ascii=False, indent=2) + "\n"


def main(argv: list[str]) -> int:
    sch = schema()
    want = {SCHEMA_PATH: render_schema(sch), TS_PATH: render_ts(sch)}
    if "--check" in argv:
        stale = [p for p, txt in want.items()
                 if not p.exists() or p.read_text(encoding="utf-8") != txt]
        for p in stale:
            print(f"낡음: {p.relative_to(ROOT)} — gen_build_options.py 를 다시 돌려라")
        return 1 if stale else 0
    for p, txt in want.items():
        p.write_text(txt, encoding="utf-8")
        print(f"썼다: {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
