"""rust/sbim-types — 생성물이 정본과 같은지는 test_fixtures 의 `--check` 가 지킨다. 여기서는 방출기
자체를 본다: 결정적인가, 스키마의 모델이 전부 나왔나, 크레이트 판이 pyproject 와 같은가.

cargo 는 여기서 돌리지 않는다 — CI 의 rust job(`cargo test --locked`)이 한다.
"""

import importlib.util
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
CRATE = ROOT / "rust" / "sbim-types"


def _gen():
    spec = importlib.util.spec_from_file_location("gen_build_options", SCRIPTS / "gen_build_options.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _rust_outputs():
    gen = _gen()
    spec = importlib.util.spec_from_file_location("emit_rust", SCRIPTS / "emit_rust.py")
    emit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(emit)
    b = gen.bundle()
    return b, emit.outputs(ROOT, b), emit.outputs(ROOT, b)


def test_outputs_are_deterministic_and_land_in_src():
    _, a, b = _rust_outputs()
    assert a == b
    assert {p.name for p in a} == {"build_options.rs", "scheme.rs", "migrations.rs", "presets.rs"}
    assert all(p.parent == CRATE / "src" for p in a)
    for p, txt in a.items():
        assert txt.startswith("// 생성 파일 — 손으로 고치지 마라."), p.name


def test_every_model_is_a_struct():
    b, out, _ = _rust_outputs()
    bo = out[CRATE / "src" / "build_options.rs"]
    for name in ["BuildOptions", *b["build_options"]["$defs"]]:
        assert f"pub struct {name} {{" in bo, name
        assert f"impl Default for {name} {{" in bo, name
    sc = out[CRATE / "src" / "scheme.rs"]
    names = {"Scheme"}
    for key in ("scheme", "units", "surroundings"):
        names |= set(b[key]["$defs"])
    for name in names:
        assert f"pub struct {name.lstrip('_')} {{" in sc, name
    # 옵션 모델은 전부 extra=forbid — flatten extra 가 없다
    assert "flatten" not in bo
    assert "pub extra: BTreeMap<String, serde_json::Value>" in sc


def test_crate_version_matches_pyproject():
    with (ROOT / "python" / "pyproject.toml").open("rb") as f:
        py = tomllib.load(f)["project"]["version"]
    with (CRATE / "Cargo.toml").open("rb") as f:
        rs = tomllib.load(f)["package"]["version"]
    assert rs == py


def test_core_type_table_is_the_fixture():
    b, out, _ = _rust_outputs()
    mig = out[CRATE / "src" / "migrations.rs"]
    pairs = re.search(r"CORE_TYPE_OLD_TO_NEW: &\[\(u8, u8\)\] = &\[(.*?)\];", mig).group(1)
    got = dict(re.findall(r"\((\d+), (\d+)\)", pairs))
    assert got == {k: str(v) for k, v in b["migrations"]["core_type_old_to_new"].items()}
