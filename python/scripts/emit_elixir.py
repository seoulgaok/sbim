"""elixir/ 방출기 — gen_build_options.py 가 부른다.

`outputs(root, bundle)` 는 {경로: 내용} 을 돌려준다 — elixir/sbim/lib/sbim/generated/ 의 넷:
options.ex(BuildOptions 와 그 `$defs`) · scheme.ex(Scheme·UnitRecord·SurroundingBuilding 과
세 스키마의 `$defs` 를 이름으로 합친 것) · migrations.ex(이행 표) · presets.ex(STRUCTURE_PRESET).

- 모델 하나 = 모듈 하나(`Sbim.Options.<Model>`·`Sbim.Scheme.<Model>`). defstruct 순서 = 스키마
  `properties` 순서(= pydantic 선언 순서). 모듈은 참조 순서로 쓴다 — 중첩 기본값
  `%Sbim.Options.Design{}` 는 Design 이 같은 파일에서 먼저 컴파일돼 있어야 한다.
- 옵션 기본값은 스키마 `default` 가 아니라 fixtures `empty.expected`(after-validator 가 채운
  정규화 값)에서 꺼낸다 — 손 포트의 max_span 8.0/8.1 사고가 이 생성의 이유다. scheme 쪽은 nil.
- 값은 JSON 그대로다 — 문자열 Literal 은 문자열, dict 는 문자열 키 map, tuple 은 리스트.
- from_map/to_map 의 본체는 손으로 쓴 elixir/sbim/lib/sbim/codec.ex 다. 생성 모듈은
  `__shape__/0` 로 필드 모양(어디서 재귀하나·extra 허용·nil 생략)만 준다.
- 이행 **로직**은 만들지 않는다 — migrations.ex 는 표를 돌려주는 함수뿐이다.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

GEN_DIR = ("elixir", "sbim", "lib", "sbim", "generated")
OPTIONS_NS = "Sbim.Options"
SCHEME_NS = "Sbim.Scheme"
WIDTH = 96


# ── 리터럴 ───────────────────────────────────────────────────────────────────────────

def ex_float(f: float) -> str:
    """Elixir 는 `1e-05` 를 못 읽는다 — `1.0e-5` 꼴로."""
    s = repr(f)
    if "e" in s:
        m, e = s.split("e")
        if "." not in m:
            m += ".0"
        return f"{m}e{int(e)}"
    return s


def ex_str(s: str) -> str:
    # JSON 이스케이프는 Elixir 문자열이 그대로 읽는다 — 보간 `#{` 만 막는다
    return json.dumps(s, ensure_ascii=False).replace("#{", "\\#{")


def ex_lit(v) -> str:
    if v is None:
        return "nil"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return ex_float(v)
    if isinstance(v, str):
        return ex_str(v)
    if isinstance(v, list):
        return "[" + ", ".join(ex_lit(x) for x in v) + "]"
    if isinstance(v, dict):
        if not v:
            return "%{}"
        return "%{" + ", ".join(f"{ex_lit(k)} => {ex_lit(x)}" for k, x in v.items()) + "}"
    raise TypeError(f"Elixir 리터럴로 못 적는 값: {v!r}")


def ex_pretty(v, ind: str) -> str:
    """여러 줄 리터럴 — 표(migrations·presets)용."""
    inner = ind + "  "
    if isinstance(v, dict) and v:
        items = [f"{inner}{ex_lit(k)} => {ex_pretty(x, inner)}" for k, x in v.items()]
        return "%{\n" + ",\n".join(items) + f"\n{ind}}}"
    if isinstance(v, list) and v and any(isinstance(x, (dict, list)) for x in v):
        items = [f"{inner}{ex_pretty(x, inner)}" for x in v]
        return "[\n" + ",\n".join(items) + f"\n{ind}]"
    return ex_lit(v)


_IDENT = re.compile(r"[a-z_][a-zA-Z0-9_]*[?!]?")


def ex_key(name: str) -> str:
    """키워드 키 — 식별자가 아니면 따옴표 원자."""
    return f"{name}:" if _IDENT.fullmatch(name) else f"{ex_str(name)}:"


def ex_atom(name: str) -> str:
    return f":{name}" if _IDENT.fullmatch(name) else f":{ex_str(name)}"


# ── 스키마 걷기 ──────────────────────────────────────────────────────────────────────

def ref_name(s: dict) -> str:
    return s["$ref"].rsplit("/", 1)[-1]


def refs_of(s) -> set[str]:
    out: set[str] = set()
    if isinstance(s, dict):
        if "$ref" in s:
            out.add(ref_name(s))
        for v in s.values():
            out |= refs_of(v)
    elif isinstance(s, list):
        for v in s:
            out |= refs_of(v)
    return out


def topo(defs: dict[str, dict]) -> list[str]:
    """참조되는 모델이 먼저 — 이름순 안정 정렬이라 결정적이다."""
    order: list[str] = []
    seen: set[str] = set()

    def visit(n: str) -> None:
        if n in seen:
            return
        seen.add(n)
        for d in sorted(refs_of(defs[n])):
            if d in defs:
                visit(d)
        order.append(n)

    for n in sorted(defs):
        visit(n)
    return order


def _lit_type(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return "String.t()"   # 타입스펙에 문자열 리터럴은 없다 — 값은 필드 주석에
    if v is None:
        return "nil"
    return "term()"


def _uniq(parts: list[str]) -> list[str]:
    out: list[str] = []
    for p in parts:
        if p not in out:
            out.append(p)
    return out


def ex_type(s: dict, mod_of) -> str:
    if "$ref" in s:
        return f"{mod_of(ref_name(s))}.t()"
    if "anyOf" in s:
        return " | ".join(_uniq([ex_type(x, mod_of) for x in s["anyOf"]]))
    if "prefixItems" in s:
        return "[" + " | ".join(_uniq([ex_type(x, mod_of) for x in s["prefixItems"]])) + "]"
    if "const" in s:
        return _lit_type(s["const"])
    if "enum" in s:
        return " | ".join(_uniq([_lit_type(v) for v in s["enum"]]))
    t = s.get("type")
    if t == "null":
        return "nil"
    if t == "string":
        return "String.t()"
    if t == "integer":
        return "integer()"
    if t == "number":
        return "number()"
    if t == "boolean":
        return "boolean()"
    if t == "array":
        return f"[{ex_type(s.get('items', {}), mod_of)}]"
    if t == "object":
        ap = s.get("additionalProperties")
        if isinstance(ap, dict):
            return f"%{{optional(String.t()) => {ex_type(ap, mod_of)}}}"
        return "map()"
    return "term()"


def shape(s: dict, mod_of) -> str:
    """codec 이 재귀할 자리만 적는다 — 모델이 없는 가지는 `:value`(값 그대로)."""
    def one(subs: list[str]) -> str:
        nested = _uniq([x for x in subs if x != ":value"])
        if not nested:
            return ":value"
        if len(nested) == 1:
            return nested[0]
        raise ValueError(f"한 자리에 모델 가지가 둘 — codec 이 못 가른다: {s}")

    if "$ref" in s:
        return f"{{:model, {mod_of(ref_name(s))}}}"
    if "anyOf" in s:
        return one([shape(x, mod_of) for x in s["anyOf"]])
    if s.get("type") == "array":
        if "prefixItems" in s:
            inner = one([shape(x, mod_of) for x in s["prefixItems"]])
        else:
            inner = shape(s.get("items", {}), mod_of)
        return ":value" if inner == ":value" else f"{{:list, {inner}}}"
    if s.get("type") == "object" and isinstance(s.get("additionalProperties"), dict):
        inner = shape(s["additionalProperties"], mod_of)
        return ":value" if inner == ":value" else f"{{:map, {inner}}}"
    return ":value"


def enum_values(s: dict) -> list | None:
    """필드 주석에 적을 문자열 Literal 값 — 타입스펙엔 못 적는다."""
    if "enum" in s and all(isinstance(v, str) for v in s["enum"]):
        return s["enum"]
    for sub in s.get("anyOf", []):
        vals = enum_values(sub)
        if vals:
            return vals
    return None


# ── 문서 ─────────────────────────────────────────────────────────────────────────────

def _dw(s: str) -> int:
    """표시 폭 — 한글은 두 칸이라 textwrap 의 글자 수로 접으면 줄이 두 배로 길다."""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def wrap(text: str, width: int) -> list[str]:
    out: list[str] = []
    for para in text.strip().split("\n"):
        words = para.split()
        if not words:
            out.append("")
            continue
        line: list[str] = []
        cur = 0
        for w in words:
            ww = _dw(w)
            if line and cur + 1 + ww > width:
                out.append(" ".join(line))
                line, cur = [w], ww
            else:
                cur += ww + (1 if line else 0)
                line.append(w)
        out.append(" ".join(line))
    while out and not out[-1]:
        out.pop()
    return out


def moduledoc(text: str, ind: str) -> list[str]:
    if not text.strip():
        return []
    if '"""' in text:
        raise ValueError("description 에 \"\"\" 가 있다 — heredoc 으로 못 적는다")
    body = wrap(text, WIDTH - len(ind))
    return [f'{ind}@moduledoc ~S"""'] + [f"{ind}{ln}".rstrip() for ln in body] + [f'{ind}"""']


def comment(lines: list[str], ind: str) -> list[str]:
    return [f"{ind}# {ln}".rstrip() for ln in lines]


def field_notes(ps: dict) -> list[str]:
    notes = wrap(ps.get("description", ""), WIDTH - 6)
    tags = []
    vals = enum_values(ps)
    if vals:
        tags.append("값: " + " | ".join(ex_str(v) for v in vals))
    if ps.get("empty"):
        tags.append(f"empty: {ps['empty']}")
    dep = ps.get("deprecated")
    if dep:
        tags.append(f"deprecated: {dep}" if isinstance(dep, str) else "deprecated")
    if tags:
        notes.append(" · ".join(tags))
    return notes


# ── 모델 모듈 ────────────────────────────────────────────────────────────────────────

def render_model(mod: str, s: dict, mod_of, *, defaults: dict | None, omit_nil: bool) -> str:
    """defaults 가 None 이면(scheme) 전부 nil, 아니면(options) 그 dict 에서 필드값을 꺼낸다."""
    props: dict = s.get("properties", {})
    required: list[str] = list(s.get("required", []))
    extra = s.get("additionalProperties", True) is not False

    out = [f"defmodule {mod} do"]
    out += moduledoc(s.get("description", ""), "  ")
    if out[-1] != f"defmodule {mod} do":
        out.append("")

    # @type t
    out.append("  @type t :: %__MODULE__{")
    specs = [f"          {ex_key(p)} {ex_type(ps, mod_of)}" for p, ps in props.items()]
    if extra:
        specs.append("          extra: %{optional(String.t()) => term()}")
    out.append(",\n".join(specs))
    out.append("        }")
    out.append("")

    # defstruct — 순서 = properties 순서
    out.append("  defstruct [")
    entries: list[str] = []
    for p, ps in props.items():
        lines = comment(field_notes(ps), "    ")
        if defaults is None:
            d = "nil"
        else:
            v = defaults[p]
            refd = ref_name(ps) if "$ref" in ps else next(
                (ref_name(x) for x in ps.get("anyOf", []) if "$ref" in x), None)
            d = f"%{mod_of(refd)}{{}}" if refd and isinstance(v, dict) else ex_lit(v)
        lines.append(f"    {ex_key(p)} {d}")
        entries.append("\n".join(lines))
    if extra:
        entries.append("    # 스키마에 없는 키 — from_map 이 여기 담고 to_map 이 도로 펼친다\n    extra: %{}")
    out.append(",\n".join(entries))
    out.append("  ]")
    out.append("")

    unknown = ("스키마에 없는 키는 `extra` 에 담는다" if extra
               else "스키마에 없는 키는 `{:error, {:unknown_keys, 경로, 키들}}` 다")
    out += [
        f'  @doc "문자열 키 map → struct(중첩 재귀). {unknown}."',
        "  @spec from_map(map()) :: {:ok, t()} | {:error, term()}",
        "  def from_map(map), do: Sbim.Codec.decode(__MODULE__, map)",
        "",
        "  @spec from_map!(map()) :: t()",
        "  def from_map!(map), do: Sbim.Codec.decode!(__MODULE__, map)",
        "",
    ]
    nil_note = ("nil 인 선택 필드는 뺀다(없음 ≠ null)" if omit_nil else "nil 은 null 로 낸다")
    out += [
        f'  @doc "struct → 문자열 키 map(중첩 재귀). {nil_note}{"; extra 는 펼친다" if extra else ""}."',
        "  @spec to_map(t()) :: map()",
        "  def to_map(%__MODULE__{} = s), do: Sbim.Codec.encode(s)",
        "",
        "  @doc false",
        "  def __shape__ do",
        "    %{",
        "      fields: [",
    ]
    out.append(",\n".join(
        f"        {{{ex_str(p)}, {ex_atom(p)}, {shape(ps, mod_of)}}}" for p, ps in props.items()))
    out += [
        "      ],",
        f"      required: {ex_lit(required)},",
        f"      extra?: {ex_lit(extra)},",
        f"      omit_nil?: {ex_lit(omit_nil)}",
        "    }",
        "  end",
        "end",
    ]
    return "\n".join(out) + "\n"


def model_paths(root: dict, defs: dict) -> dict[str, list[str]]:
    """`$defs` 모델 → 루트에서의 경로(기본값을 empty.expected 에서 꺼내는 자리). 한 모델이
    두 자리에 쓰이면 기본값이 하나가 아니라 거부한다."""
    paths: dict[str, list[str]] = {}

    def walk(s: dict, path: list[str]) -> None:
        for p, ps in s.get("properties", {}).items():
            n = ref_name(ps) if "$ref" in ps else next(
                (ref_name(x) for x in ps.get("anyOf", []) if "$ref" in x), None)
            if n is None:
                continue
            if n in paths:
                raise ValueError(f"{n} 가 두 자리({paths[n]}·{path + [p]})에서 쓰인다")
            paths[n] = path + [p]
            walk(defs[n], path + [p])

    walk(root, [])
    missing = set(defs) - set(paths)
    if missing:
        raise ValueError(f"루트에서 닿지 않는 모델 — 기본값을 못 꺼낸다: {sorted(missing)}")
    return paths


def _dig(d: dict, path: list[str]) -> dict:
    for k in path:
        d = d[k]
    return d


def render_options(schema: dict, empty_expected: dict) -> str:
    defs = schema["$defs"]
    root = {k: v for k, v in schema.items() if k != "$defs"}
    paths = model_paths(root, defs)

    def mod_of(name: str) -> str:
        return f"{OPTIONS_NS}.{name}"

    blocks = [render_model(mod_of(n), defs[n], mod_of,
                           defaults=_dig(empty_expected, paths[n]), omit_nil=False)
              for n in topo(defs)]
    blocks.append(render_model(mod_of(root["title"]), root, mod_of,
                               defaults=empty_expected, omit_nil=False))
    head = header("python/seoulgaok_bim_core/options.py (pydantic BuildOptions)") + (
        "#\n"
        "# 기본값은 fixtures/build_options/empty.json 의 expected(after-validator 가 채운 정규화\n"
        "# 기본값)다 — `%Sbim.Options.BuildOptions{} |> to_map()` 이 그 expected 와 같다.\n"
        "# 이행 로직은 없다 — 파이썬은 지운 키를 받아서 버리지만 여기 from_map 은 스키마에 없는 키를\n"
        "# 거부한다. 옛 저장값은 Sbim.Migrations 의 표를 먼저 적용한 뒤 from_map 에 넣는다.\n"
    )
    return head + "\n" + "\n".join(blocks)


def _merged_defs(schemas: dict[str, dict]) -> dict[str, dict]:
    """세 스키마의 `$defs` 를 이름으로 합친다 — 같은 이름은 같은 모델이어야 한다."""
    merged: dict[str, dict] = {}
    for label, sch in schemas.items():
        for n, d in sch.get("$defs", {}).items():
            if n in merged and merged[n] != d:
                raise ValueError(f"$defs {n} 가 {label} 에서 다르다 — 이름으로 못 합친다")
            merged.setdefault(n, d)
    return merged


def render_scheme(scheme: dict, units: dict, surroundings: dict, site: dict) -> str:
    defs = _merged_defs({"scheme": scheme, "units": units, "surroundings": surroundings, "site": site})
    for r in (scheme, site):
        root = {k: v for k, v in r.items() if k != "$defs"}
        defs[root["title"]] = root

    names: dict[str, str] = {}
    for n in defs:
        public = n.lstrip("_")   # 모듈 이름은 밑줄로 못 시작한다
        if public in names.values():
            raise ValueError(f"모델 이름이 겹친다: {n} → {public}")
        names[n] = public

    def mod_of(name: str) -> str:
        return f"{SCHEME_NS}.{names[name]}"

    blocks = [render_model(mod_of(n), defs[n], mod_of, defaults=None, omit_nil=True)
              for n in topo(defs)]
    head = header("python/seoulgaok_bim_core/types.py (pydantic Scheme·UnitRecord·SurroundingBuilding)") + (
        "#\n"
        "# 네 스키마(schema/scheme·units·surroundings·site.schema.json)의 `$defs` 를 이름으로 합쳤다.\n"
        "# 기본값은 전부 nil 이고 to_map 은 nil 인 선택 필드를 뺀다 — 밑줄 키의 「없음 ≠ null」.\n"
        "# 값은 Jason 이 준 그대로(정수·실수를 강제하지 않는다). units.json 은 아직 구\n"
        "# `Unit(geom/data)` 모양이라 UnitRecord 로 안 읽힌다.\n"
    )
    return head + "\n" + "\n".join(blocks)


# ── 표 ───────────────────────────────────────────────────────────────────────────────

MIGRATION_DOCS = {
    "legacy_top_blocks": "구 13블록 평면 모양의 최상위 키 — 하나라도 있으면 구 모양이다.",
    "ground_floor_to": "구 `ground_floor.<키>` → 새 묶음(core·parking·regulations·circulation·dimensions).",
    "ground_floor_dropped": "구 `ground_floor` 에서 지운 키 — 옮길 자리가 없다.",
    "parking_dims_dropped": "주차 칸·차로 치수 — 주차장법 상수라 받아서 버린다.",
    "renamed": "구 이름 → 새 이름(뜻은 같다).",
    "regulations_renamed": "구 regulations 이름 → 새 이름(`far_target` → `far_limit_override`).",
    "moved_to_regulations": "옛 자리 → `design.regulations` 로 옮긴 필드 — [묶음, 필드] 쌍.",
    "dropped": "묶음별 지운 키 — 받아서 버린다.",
    "core_type_old_to_new": "코어 유형 번호 개번 표(2026-09) — 옛 번호 → 새 번호. 값 집합이 1~7 로 같아 검증에 안 걸린다.",
}


def render_migrations(mig: dict) -> str:
    out = [header("python/seoulgaok_bim_core/options.py (_LEGACY_TOP·_GF_TO·… · fixtures/migrations.json 과 같다)"),
           "defmodule Sbim.Migrations do",
           '  @moduledoc ~S"""',
           "  옛 저장값을 새 모양으로 옮기는 표 — fixtures/migrations.json 과 같다. 표만 있고 적용 로직은",
           "  없다(파이썬은 `BuildOptions._migrate_legacy_shape`·각 모델의 before validator). 표로 못 적는",
           "  규칙(주차 버블 구 노드 접기 등)은 fixtures/build_options/ 케이스가 정답을 준다.",
           '  """',
           ""]
    for key, val in mig.items():
        if key == "core_type_old_to_new":
            table = {int(k): v for k, v in val.items()}
            out += [f'  @doc "{MIGRATION_DOCS[key]}"',
                    f"  def {key}, do: {ex_pretty(table, '  ')}",
                    "",
                    '  @doc "옛 번호 하나 → 새 번호. nil(auto)은 그대로, 표에 없는 번호는 KeyError."',
                    f"  def {key}(nil), do: nil",
                    f"  def {key}(old) when is_integer(old), do: Map.fetch!({key}(), old)",
                    ""]
        else:
            out += [f'  @doc "{MIGRATION_DOCS.get(key, key)}"',
                    f"  def {key}, do: {ex_pretty(val, '  ')}",
                    ""]
    out[-1] = "end"
    return "\n".join(out) + "\n"


def render_presets(preset: dict) -> str:
    out = [header("python/seoulgaok_bim_core/options.py (STRUCTURE_PRESET · fixtures/presets.json 과 같다)"),
           "defmodule Sbim.Presets do",
           '  @moduledoc ~S"""',
           "  구조방식 → 벽 두께·스팬·기둥 간격 기본값. BuildOptions 의 after-validator 가 명시하지 않은",
           "  `standards.concrete.wall_thickness`·`standards.dimensions.max_span`·`min_col_dist` 를 이 표로",
           "  채운다 — 생성된 defstruct 기본값에는 기본 구조(`design.structure`)의 몫이 이미 들어 있다.",
           '  """',
           "",
           '  @doc "구조방식 전부 — {구조: %{wall_thickness, max_span, min_col_dist}}."',
           f"  def structure_preset, do: {ex_pretty(preset, '  ')}",
           "",
           '  @doc "구조방식 하나 — 모르는 이름은 nil."']
    for name, vals in preset.items():
        out.append(f"  def structure_preset({ex_str(name)}), do: {ex_lit(vals)}")
    out += ["  def structure_preset(_), do: nil", "end"]
    return "\n".join(out) + "\n"


def header(source: str) -> str:
    return ("# 생성 파일 — 손으로 고치지 마라.\n"
            f"# 정본: {source}\n"
            "# 생성: cd python && uv run python scripts/gen_build_options.py\n")


def outputs(root: Path, bundle: dict) -> dict[Path, str]:
    gen = root.joinpath(*GEN_DIR)
    return {
        gen / "options.ex": render_options(bundle["build_options"],
                                           bundle["fixtures"]["empty"]["expected"]),
        gen / "scheme.ex": render_scheme(bundle["scheme"], bundle["units"], bundle["surroundings"], bundle["site"]),
        gen / "migrations.ex": render_migrations(bundle["migrations"]),
        gen / "presets.ex": render_presets(bundle["structure_preset"]),
    }
