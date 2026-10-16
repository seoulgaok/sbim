"""IFC4 속성 표 생성 — elixir/sbim/lib/sbim/generated/ifc_schema.ex.

    cd python && uv run python scripts/gen_ifc_schema.py [--check]

STEP 은 속성을 이름이 아니라 **자리**로 쓴다(`create_entity(**kw)` 가 숨기는 것). 그래서 Elixir
판은 타입마다 속성 순서·종류를 알아야 한다. 정본은 ifcopenshell 의 IFC4 스키마이고, 표는
ifc.py 가 실제로 만드는 타입(fixtures/ifc/types.txt — gen_ifc_fixtures.py 가 남긴다)만 담는다.

종류: :real · :integer · :bool · :logical · :string · :enum · :ref(개체) · :select · {:list, 종류} ·
:derived(STEP `*`).
"""
from pathlib import Path

import sys

import ifcopenshell
import ifcopenshell.ifcopenshell_wrapper as W

ROOT = Path(__file__).resolve().parents[2]
TYPES = ROOT / "fixtures/ifc/types.txt"
OUT = ROOT / "elixir/sbim/lib/sbim/generated/ifc_schema.ex"
S = W.schema_by_name("IFC4")
SIMPLE = {"real": ":real", "number": ":real", "integer": ":integer", "boolean": ":bool",
          "logical": ":logical", "string": ":string", "binary": ":string"}


def kind(t) -> str:
    n = type(t).__name__
    if n == "simple_type":
        return SIMPLE[t.declared_type()]
    if n == "aggregation_type":
        return "{:list, %s}" % kind(t.type_of_element())
    if n == "named_type":
        return kind(t.declared_type())
    if n == "type_declaration":
        return kind(t.declared_type())
    if n == "enumeration_type":
        return ":enum"
    if n == "entity":
        return ":ref"
    if n == "select_type":
        return ":select"
    raise TypeError(f"{n} {t}")


def main():
    names = [l.strip() for l in TYPES.read_text().splitlines() if l.strip()]
    ents, decls = [], []
    for nm in names:
        d = S.declaration_by_name(nm)
        if type(d).__name__ == "entity":
            attrs = []
            for a, der in zip(d.all_attributes(), d.derived()):
                attrs.append(f"{{:{a.name()}, {':derived' if der else kind(a.type_of_attribute())}}}")
            ents.append(f'    "{nm}" => {{"{nm.upper()}", [{", ".join(attrs)}]}}')
        else:
            decls.append(f'    "{nm}" => {{"{nm.upper()}", {kind(d)}}}')
    text = f'''# 생성 파일 — 손으로 고치지 마라.
# 정본: ifcopenshell {ifcopenshell.version} IFC4 스키마 · 대상 타입 fixtures/ifc/types.txt
# 생성: cd python && uv run python scripts/gen_ifc_schema.py

defmodule Sbim.Ifc.Schema do
  @moduledoc """
  IFC4 속성 표 — 타입마다 STEP 이름과 속성(자리 순서·종류). `Sbim.Ifc.Step` 이 이것으로 줄을 쓴다.
  ifc.py 가 만드는 타입만 담는다 — 새 타입을 쓰면 fixtures 를 다시 뜨고 이 표를 다시 생성한다.
  """

  @entities %{{
{(","+chr(10)).join(ents)}
  }}

  @types %{{
{(","+chr(10)).join(decls)}
  }}

  @doc "개체 타입 → {{STEP 이름, [{{속성, 종류}}]}}"
  def entity!(name), do: Map.fetch!(@entities, name)

  @doc "값 타입(IfcLabel 등) → {{STEP 이름, 종류}}"
  def type!(name), do: Map.fetch!(@types, name)
end
'''
    if "--check" in sys.argv:
        if OUT.read_text(encoding="utf-8") != text:
            print(f"{OUT.relative_to(ROOT)} 가 낡음 — uv run python scripts/gen_ifc_schema.py", file=sys.stderr)
            sys.exit(1)
        return
    OUT.write_text(text, encoding="utf-8")
    print(f"{len(ents)} entities · {len(decls)} types → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
