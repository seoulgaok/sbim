"""rust/ 방출기 — gen_build_options.py 가 부른다.

`outputs(root, bundle)` 는 {경로: 내용} 을 돌려준다. bundle 키: build_options · scheme · units ·
surroundings(JSON Schema dict) · migrations(이행 표) · structure_preset · fixtures({케이스: {input, expected}}).

쓰는 것(rust/sbim-types/src/, 전부 생성 파일):
- build_options.rs — BuildOptions 와 `$defs` 전부. 모든 모델이 extra=forbid 라 `extra` 는 없다.
  **직렬화는 pydantic `model_dump` 를 거울로 삼는다** — 키를 빼지 않고 null 도 적는다
  (fixtures 의 expected 가 그 모양). 비-nullable 필드는 `T`, 빠지면 struct 단위 `#[serde(default)]`
  가 `impl Default`(= fixtures empty.expected)로 채운다 — `from_str("{}") == default()`.
- scheme.rs — Scheme · UnitRecord · SurroundingBuilding 과 겹치는 `$defs` 를 이름으로 합친 한 파일.
  types.py 모델은 extra=allow 라 `extra: BTreeMap` 으로 모르는 키를 지나보낸다. 선택 필드는
  `Option<T>` + skip_serializing_if — 샘플(examples/samples)이 선택 키를 null 이 아니라 **빼고** 적는다.
- migrations.rs — 이행 표를 `pub const` 로. 접는 로직은 없다.
- presets.rs — STRUCTURE_PRESET.

이름 없는 inline enum(core_side · floor_use …)은 필드 이름의 PascalCase 로 짓고 `ENUM_NAMES` 가 몇을
덮어쓴다 — 같은 파일 안에서 값 집합이 같으면 하나로 쓰고, 다르면 생성이 실패한다.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

GEN_NOTE = """\
// 생성 파일 — 손으로 고치지 마라.
// 정본: python/seoulgaok_bim_core/{source} (pydantic)
// 생성: cd python && uv run python scripts/gen_build_options.py
"""

# 비웠을 때 누가 정하나 — gen_build_options.EMPTY_NOTE 와 같다(순환 import 를 피하려 여기 둔다)
EMPTY_NOTE = {
    "auto": "None=첫수표가 정한다(resolved_options 에 나온다)",
    "law": "None=법이 정한다",
    "default": "None=설명에 적힌 기본 동작",
}

# inline enum 이름 — (모델, 필드[, 튜플 자리]) → Rust 이름. 없으면 PascalCase(필드).
ENUM_NAMES = {
    ("Parking", "parking_graph", 0): "RoadSide",
    ("Parking", "parking_graph", 1): "ParkingKind",
    ("Exterior", "style"): "ExteriorStyle",
    ("CompileError", "type"): "CompileErrorType",
    ("ResolvedOptions", "source"): "OptionSource",
}

RUST_KEYWORDS = {
    "as", "break", "const", "continue", "crate", "else", "enum", "extern", "false", "fn", "for",
    "if", "impl", "in", "let", "loop", "match", "mod", "move", "mut", "pub", "ref", "return",
    "self", "Self", "static", "struct", "super", "trait", "true", "type", "unsafe", "use", "where",
    "while", "async", "await", "dyn", "abstract", "become", "box", "do", "final", "macro",
    "override", "priv", "typeof", "unsized", "virtual", "yield", "try",
}


def pascal(s: str) -> str:
    return "".join(p[:1].upper() + p[1:] for p in re.split(r"[_\-\s]+", s.strip("_")) if p)


def snake(s: str) -> str:
    return re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", s).lower()


def field_ident(name: str) -> tuple[str, str | None]:
    """JSON 키 → (Rust 식별자, serde rename). `_engine_stamp`→engine_stamp, `itemSize`→item_size,
    `type`→r#type(serde 는 r# 를 떼고 보니 rename 불필요)."""
    ident = snake(name.lstrip("_"))
    rename = name if ident != name else None
    if ident in RUST_KEYWORDS:
        ident = "r#" + ident
    return ident, rename


def model_ident(name: str) -> str:
    return name.lstrip("_")


def float_lit(v) -> str:
    return repr(float(v))


def str_lit(v: str) -> str:
    return json.dumps(v, ensure_ascii=False)


def doc_lines(text: str, indent: str) -> list[str]:
    body = [ln.rstrip() for ln in text.strip("\n").split("\n")]
    while body and not body[-1]:
        body.pop()
    return [f"{indent}/// {ln}".rstrip() for ln in body]


def _nonnull(s: dict) -> tuple[list[dict], bool]:
    subs = [x for x in s["anyOf"] if x.get("type") != "null"]
    return subs, len(subs) < len(s["anyOf"])


def int_enum_values(s: dict) -> list | None:
    """정수 Literal(core.type 1~7 등)은 정수 타입 그대로 두고 허용값을 문서에 적는다."""
    if "anyOf" in s:
        for sub in _nonnull(s)[0]:
            got = int_enum_values(sub)
            if got:
                return got
        return None
    if "enum" in s and s.get("type") == "integer":
        return list(s["enum"])
    return None


class _Emitter:
    """스키마 한 묶음 → Rust 파일 하나. 타입을 그리면서 만난 inline enum 을 모아 파일 끝에 쓴다."""

    def __init__(self, defs: dict[str, dict]):
        self.defs = defs
        self.enums: dict[str, tuple[list, str]] = {}  # 이름 → (값들, 설명)
        self.untagged: dict[str, list[str]] = {}       # 이름 → 변형 줄들

    # ── 타입 ──────────────────────────────────────────────────────────────────────
    def enum_name(self, model: str, field: str, idx: int | None) -> str:
        key = (model, field) if idx is None else (model, field, idx)
        if key in ENUM_NAMES:
            return ENUM_NAMES[key]
        return pascal(field) + ("" if idx is None else f"Item{idx}")

    def register_enum(self, model: str, field: str, idx: int | None, values: list, desc: str) -> str:
        name = self.enum_name(model, field, idx)
        if name in self.enums and self.enums[name][0] != values:
            raise ValueError(f"enum 이름 충돌: {name} ({model}.{field}) — ENUM_NAMES 에 이름을 주어라")
        if name in self.defs:
            raise ValueError(f"enum 이름이 모델과 겹친다: {name} ({model}.{field})")
        self.enums.setdefault(name, (values, desc))
        return name

    def rs_type(self, s: dict, model: str, field: str, idx: int | None = None) -> str:
        if "$ref" in s:
            return model_ident(s["$ref"].rsplit("/", 1)[-1])
        if "anyOf" in s:
            subs, nullable = _nonnull(s)
            if len(subs) == 1:
                inner = self.rs_type(subs[0], model, field, idx)
            else:
                inner = self.register_untagged(model, field, subs)
            return f"Option<{inner}>" if nullable else inner
        if "prefixItems" in s:
            return "(" + ", ".join(self.rs_type(sub, model, field, i)
                                   for i, sub in enumerate(s["prefixItems"])) + ")"
        if "enum" in s:
            if s.get("type") == "integer":
                return "i64"
            return self.register_enum(model, field, idx, list(s["enum"]), f"{model}.{field}")
        if "const" in s:
            return "String"
        t = s.get("type")
        if t == "integer":
            return "i64"
        if t == "number":
            return "f64"
        if t == "boolean":
            return "bool"
        if t == "string":
            return "String"
        if t == "array":
            return f"Vec<{self.rs_type(s.get('items', {}), model, field, idx)}>"
        if t == "object":
            ap = s.get("additionalProperties")
            if isinstance(ap, dict):
                return f"BTreeMap<String, {self.rs_type(ap, model, field, idx)}>"
            return "BTreeMap<String, serde_json::Value>"
        if t is None and not s:
            return "serde_json::Value"   # pydantic `Any` — 스키마가 {} 로 나온다(UnitRecord.geom)
        raise ValueError(f"모르는 스키마: {model}.{field} {s}")

    def register_untagged(self, model: str, field: str, subs: list[dict]) -> str:
        """anyOf 에 null 아닌 가지가 둘 이상(SchemeData.pnu: integer|string) → untagged enum."""
        name = model_ident(model) + pascal(field)
        variant = {"i64": "Integer", "f64": "Number", "bool": "Bool", "String": "String"}
        lines = []
        for sub in subs:
            ty = self.rs_type(sub, model, field)
            lines.append(f"    {variant.get(ty, pascal(ty.replace('<', ' ').replace('>', ' ')))}({ty}),")
        self.untagged[name] = lines
        return name

    # ── 기본값 리터럴(options 쪽) ────────────────────────────────────────────────
    def rs_lit(self, s: dict, v, model: str, field: str, idx: int | None = None) -> str:
        if v is None:
            return "None"
        if "$ref" in s:
            return f"{model_ident(s['$ref'].rsplit('/', 1)[-1])}::default()"
        if "anyOf" in s:
            subs, nullable = _nonnull(s)
            if len(subs) != 1:
                raise ValueError(f"기본값을 못 그린다: {model}.{field}")
            inner = self.rs_lit(subs[0], v, model, field, idx)
            return f"Some({inner})" if nullable else inner
        if "prefixItems" in s:
            return "(" + ", ".join(self.rs_lit(sub, x, model, field, i)
                                   for i, (sub, x) in enumerate(zip(s["prefixItems"], v))) + ")"
        if "enum" in s:
            if s.get("type") == "integer":
                return str(int(v))
            return f"{self.enum_name(model, field, idx)}::{pascal(str(v))}"
        t = s.get("type")
        if t == "integer":
            return str(int(v))
        if t == "number":
            return float_lit(v)
        if t == "boolean":
            return "true" if v else "false"
        if t == "string":
            return f"{str_lit(v)}.to_string()"
        if t == "array":
            if not v:
                return "Vec::new()"
            return "vec![" + ", ".join(self.rs_lit(s.get("items", {}), x, model, field, idx) for x in v) + "]"
        if t == "object":
            if not v:
                return "BTreeMap::new()"
            ap = s.get("additionalProperties")
            items = ", ".join(
                f"({str_lit(k)}.to_string(), {self.rs_lit(ap, x, model, field, idx) if isinstance(ap, dict) else 'serde_json::json!(' + json.dumps(x, ensure_ascii=False) + ')'})"
                for k, x in v.items())
            return f"BTreeMap::from([{items}])"
        raise ValueError(f"기본값을 못 그린다: {model}.{field} {s}")

    # ── 구조체 ────────────────────────────────────────────────────────────────────
    def field_doc(self, ps: dict) -> list[str]:
        notes = [ps.get("description", "")]
        allowed = int_enum_values(ps)
        if allowed:
            notes.append("허용값: " + " · ".join(str(x) for x in allowed))
        if "const" in ps:
            notes.append(f"항상 {json.dumps(ps['const'], ensure_ascii=False)}")
        if "default" in ps:
            notes.append(f"기본값: {json.dumps(ps['default'], ensure_ascii=False)}")
        if ps.get("empty"):
            notes.append(f"비우면: {ps['empty']} — {EMPTY_NOTE[ps['empty']]}")
        dep = ps.get("deprecated")
        if dep:
            notes.append(f"deprecated: {dep}" if isinstance(dep, str) else "deprecated")
        out: list[str] = []
        for n in notes:
            if not n:
                continue
            if out:
                out.append("    ///")
            out += doc_lines(n, "    ")
        return out

    def struct(self, name: str, s: dict, *, options: bool, default_values: dict | None) -> list[str]:
        """options=True: 키를 빼지 않는 model_dump 거울 + struct 단위 serde(default) + impl Default.
        options=False(scheme): 선택 필드 Option+skip, extra=allow 면 flatten extra."""
        ident = model_ident(name)
        required = set(s.get("required", ()))
        allow_extra = s.get("additionalProperties", True) is not False
        out = doc_lines(s.get("description", ""), "")
        out.append("#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]")
        if options:
            out.append("#[serde(default)]")
        out.append(f"pub struct {ident} {{")
        defaults: list[str] = []
        for prop, ps in s.get("properties", {}).items():
            fid, rename = field_ident(prop)
            ty = self.rs_type(ps, name, prop)
            out += self.field_doc(ps)
            attrs = []
            if rename:
                attrs.append(f'rename = "{rename}"')
            if options:
                if default_values is None or prop not in default_values:
                    raise ValueError(f"fixtures empty.expected 에 {name}.{prop} 이 없다")
                defaults.append(f"            {fid}: {self.rs_lit(ps, default_values[prop], name, prop)},")
            elif prop not in required:
                if not ty.startswith("Option<"):
                    ty = f"Option<{ty}>"
                attrs.append('default, skip_serializing_if = "Option::is_none"')
            if attrs:
                out.append(f"    #[serde({', '.join(attrs)})]")
            out.append(f"    pub {fid}: {ty},")
        if allow_extra:
            out.append("    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).")
            out.append("    #[serde(flatten)]")
            out.append("    pub extra: BTreeMap<String, serde_json::Value>,")
            defaults.append("            extra: BTreeMap::new(),")
        out.append("}")
        if options:
            out += ["", f"impl Default for {ident} {{", "    fn default() -> Self {", "        Self {"]
            out += defaults
            out += ["        }", "    }", "}"]
        return out

    def enum_blocks(self) -> list[list[str]]:
        blocks = []
        for name in sorted(self.enums):
            values, desc = self.enums[name]
            b = [f"/// {desc} 의 값.",
                 "#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]",
                 f"pub enum {name} {{"]
            for v in values:
                b.append(f"    #[serde(rename = {str_lit(str(v))})]")
                b.append(f"    {pascal(str(v))},")
            b.append("}")
            blocks.append(b)
        for name in sorted(self.untagged):
            b = ["#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]",
                 "#[serde(untagged)]",
                 f"pub enum {name} {{"]
            b += self.untagged[name]
            b.append("}")
            blocks.append(b)
        return blocks


def _file(source: str, head: str, uses: list[str], blocks: list[list[str]]) -> str:
    body = "\n\n".join("\n".join(b) for b in blocks)
    return GEN_NOTE.format(source=source) + head + "\n" + "\n".join(uses) + "\n\n" + body + "\n"


# ── build_options.rs ──────────────────────────────────────────────────────────
def _default_values(sch: dict, expected: dict) -> dict[str, dict]:
    """모델 이름 → empty.expected 에서 그 모델이 앉은 자리의 값. 모델마다 자리는 하나다."""
    defs = sch["$defs"]
    found: dict[str, dict] = {}

    def walk(name: str, s: dict, value: dict):
        if name in found:
            if found[name] != value:
                raise ValueError(f"{name} 이 두 자리에서 다른 기본값을 가진다")
            return
        found[name] = value
        for prop, ps in s.get("properties", {}).items():
            ref = ps.get("$ref") or next((x["$ref"] for x in ps.get("anyOf", []) if "$ref" in x), None)
            if ref and isinstance(value.get(prop), dict):
                sub = ref.rsplit("/", 1)[-1]
                walk(sub, defs[sub], value[prop])

    walk(sch["title"], sch, expected)
    return found


def render_build_options(sch: dict, empty_expected: dict) -> str:
    em = _Emitter(sch["$defs"])
    values = _default_values(sch, empty_expected)
    root = {k: v for k, v in sch.items() if k != "$defs"}
    blocks = [em.struct(sch["title"], root, options=True, default_values=values[sch["title"]])]
    for name in sorted(sch["$defs"]):
        if name not in values:
            raise ValueError(f"{name} 이 BuildOptions 트리에 없다 — 기본값을 못 꺼낸다")
        blocks.append(em.struct(name, sch["$defs"][name], options=True, default_values=values[name]))
    blocks += em.enum_blocks()
    head = """\
//
// BuildOptions — 속성 창 입력 타입. 직렬화는 pydantic model_dump 를 거울로 삼는다 — 키를 빼지 않고
// null 도 적는다(fixtures/build_options/*.json 의 expected 가 그 모양). 빠진 키는 `Default`
// (= fixtures/build_options/empty.json 의 expected, 프리셋이 채운 정규화 기본값)로 채운다.
// 모르는 키는 serde 가 조용히 버린다 — 옛 모양(ground_floor · far_target …)을 접는 표는 migrations.rs,
// 정답은 fixtures/build_options/ 에 있다.
"""
    return _file("options.py", head, ["use std::collections::BTreeMap;", "",
                                      "use serde::{Deserialize, Serialize};"], blocks)


# ── scheme.rs ─────────────────────────────────────────────────────────────────
def render_scheme(scheme: dict, units: dict, surroundings: dict, site: dict) -> str:
    defs: dict[str, dict] = {}
    for sch in (scheme, units, surroundings, site):
        for name, d in sch.get("$defs", {}).items():   # SiteInfo 는 평평해 $defs 가 없다
            if name in defs and defs[name] != d:
                raise ValueError(f"$defs 가 파일마다 다르다: {name}")
            defs.setdefault(name, d)
    for r in (scheme, site):
        if r["title"] in defs:
            raise ValueError(f"$defs 에 {r['title']} 이 이미 있다")
    em = _Emitter(defs)
    root = {k: v for k, v in scheme.items() if k != "$defs"}
    firsts = [scheme["title"], units["items"]["$ref"].rsplit("/", 1)[-1],
              surroundings["items"]["$ref"].rsplit("/", 1)[-1]]
    site_root = {k: v for k, v in site.items() if k != "$defs"}
    blocks = [em.struct(scheme["title"], root, options=False, default_values=None),
              em.struct(site["title"], site_root, options=False, default_values=None)]
    for name in firsts[1:] + sorted(n for n in defs if n not in firsts):
        blocks.append(em.struct(name, defs[name], options=False, default_values=None))
    blocks.append([f"/// {units['description']}", f"pub type {units['title']} = Vec<{model_ident(firsts[1])}>;",
                   "", f"/// {surroundings['description']}",
                   f"pub type {surroundings['title']} = Vec<{model_ident(firsts[2])}>;"])
    blocks += em.enum_blocks()
    head = """\
//
// scheme.json · units.json · surroundings.json · site.json 레코드. 네 스키마의 `$defs` 를 이름으로 합쳐 한 파일에 둔다.
// 모델은 전부 extra=allow — 모르는 키는 `extra` 로 지나보낸다. 선택 필드는 없으면 빼고 적는다
// (Option + skip_serializing_if) — 샘플(examples/samples)이 그 모양이다. 명시 null 은 None 으로 읽혀
// 되쓰면 빠진다.
"""
    return _file("types.py", head, ["use std::collections::BTreeMap;", "",
                                    "use serde::{Deserialize, Serialize};"], blocks)


# ── migrations.rs ─────────────────────────────────────────────────────────────
def _str_slice(xs) -> str:
    return "&[" + ", ".join(str_lit(x) for x in xs) + "]"


def _pair_slice(pairs) -> str:
    inner = ",\n".join(f"    ({str_lit(a)}, {str_lit(b)})" for a, b in pairs)
    return "&[\n" + inner + ",\n]" if pairs else "&[]"


def render_migrations(m: dict) -> str:
    core = [(int(k), v) for k, v in m["core_type_old_to_new"].items()]
    dropped = ",\n".join(f"    ({str_lit(k)}, {_str_slice(v)})" for k, v in m["dropped"].items())
    body = f"""\
//
// 옛 저장값을 새 모양으로 옮기는 **표**(fixtures/migrations.json 과 같다). 접는 로직은 여기 없다 —
// 소비처가 이 표로 구현하고 fixtures/build_options/*.json(input → expected)을 정답으로 검사한다.
// 파이썬 구현은 options.py 의 `BuildOptions._migrate_legacy_shape` · 각 모델의 before validator.

/// 구 13블록 평평한 모양의 최상위 키 — 이 중 하나라도 있으면 옛 모양이다.
pub const LEGACY_TOP_BLOCKS: &[&str] = {_str_slice(m["legacy_top_blocks"])};

/// 구 `ground_floor` 의 키 → 새 묶음(core · parking · regulations · circulation · dimensions).
pub const GROUND_FLOOR_TO: &[(&str, &str)] = {_pair_slice(list(m["ground_floor_to"].items()))};

/// 구 `ground_floor` 에서 버리는 키.
pub const GROUND_FLOOR_DROPPED: &[&str] = {_str_slice(m["ground_floor_dropped"])};

/// 구 `parking` 의 치수 키 — 법 상수라 버린다.
pub const PARKING_DIMS_DROPPED: &[&str] = {_str_slice(m["parking_dims_dropped"])};

/// 이름만 바뀐 키(옛 → 새).
pub const RENAMED: &[(&str, &str)] = {_pair_slice(list(m["renamed"].items()))};

/// `regulations` 안에서 이름이 바뀐 키(옛 → 새).
pub const REGULATIONS_RENAMED: &[(&str, &str)] = {_pair_slice(list(m["regulations_renamed"].items()))};

/// 다른 묶음에서 `regulations` 로 옮겨 간 키 — (옛 묶음, 키).
pub const MOVED_TO_REGULATIONS: &[(&str, &str)] = {_pair_slice([tuple(p) for p in m["moved_to_regulations"]])};

/// 묶음별로 받아서 버리는 키 — (묶음, 키들).
pub const DROPPED: &[(&str, &[&str])] = &[
{dropped},
];

/// 코어 유형 번호 개번 표(2026-09, building-generator #190) — (옛, 새). 값 집합이 1~7 로 같아
/// 검증으로는 못 가리니 저장값의 `core.type` 은 읽을 때 이 표로 옮긴다.
pub const CORE_TYPE_OLD_TO_NEW: &[(u8, u8)] = &[{", ".join(f"({a}, {b})" for a, b in core)}];

/// 옛 코어 번호 → 새 번호. 표에 없는 번호는 `None`(파이썬 `migrate_core_type` 은 ValueError).
pub fn core_type_old_to_new(old: u8) -> Option<u8> {{
    CORE_TYPE_OLD_TO_NEW.iter().find(|(o, _)| *o == old).map(|(_, n)| *n)
}}
"""
    return GEN_NOTE.format(source="options.py") + body


# ── presets.rs ────────────────────────────────────────────────────────────────
def render_presets(presets: dict[str, dict]) -> str:
    names = list(presets)
    keys = list(presets[names[0]])
    for n in names:
        if list(presets[n]) != keys:
            raise ValueError(f"STRUCTURE_PRESET[{n}] 의 키가 다르다")
    fields = "\n".join(f"    pub {k}: f64," for k in keys)
    entries = ",\n".join(
        f"    ({str_lit(n)}, Preset {{ " + ", ".join(f"{k}: {float_lit(presets[n][k])}" for k in keys) + " })"
        for n in names)
    body = f"""\
//
// 구조방식(design.structure)별 프리셋 — fixtures/presets.json 과 같다. 사용자가 비운 칸만 채운다
// (파이썬 BuildOptions after validator: model_fields_set 에 없을 때).

/// 구조방식 하나가 채우는 값.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Preset {{
{fields}
}}

/// (구조방식 이름, 프리셋) — 이름은 `build_options::Structure` 의 값과 같다.
pub const STRUCTURE_PRESET: &[(&str, Preset)] = &[
{entries},
];

/// 구조방식 이름으로 프리셋을 찾는다 — 모르는 이름은 `None`.
pub fn structure_preset(name: &str) -> Option<Preset> {{
    STRUCTURE_PRESET.iter().find(|(n, _)| *n == name).map(|(_, p)| *p)
}}
"""
    return GEN_NOTE.format(source="options.py") + body


def outputs(root: Path, bundle: dict) -> dict[Path, str]:
    src = root / "rust" / "sbim-types" / "src"
    return {
        src / "build_options.rs": render_build_options(bundle["build_options"],
                                                       bundle["fixtures"]["empty"]["expected"]),
        src / "scheme.rs": render_scheme(bundle["scheme"], bundle["units"], bundle["surroundings"], bundle["site"]),
        src / "migrations.rs": render_migrations(bundle["migrations"]),
        src / "presets.rs": render_presets(bundle["structure_preset"]),
    }
