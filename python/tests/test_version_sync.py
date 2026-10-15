"""판(버전)은 하나다 — pyproject · package.json · __version__ · Cargo.toml · mix.exs · CHANGELOG 머리말.

버전을 올리면 전부 같이 올린다: python/pyproject.toml, typescript/package.json,
python/seoulgaok_bim_core/__init__.py, rust/sbim-types/Cargo.toml, elixir/sbim/mix.exs,
CHANGELOG.md 의 `## <버전> — <날짜>` 절.
"""

import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _py_version() -> str:
    with (ROOT / "python" / "pyproject.toml").open("rb") as f:
        return tomllib.load(f)["project"]["version"]


def test_python_and_typescript_versions_match():
    ts = json.loads((ROOT / "typescript" / "package.json").read_text())["version"]
    assert _py_version() == ts


def test_rust_and_elixir_versions_match():
    with (ROOT / "rust" / "sbim-types" / "Cargo.toml").open("rb") as f:
        cargo = tomllib.load(f)["package"]["version"]
    mix = (ROOT / "elixir" / "sbim" / "mix.exs").read_text()
    m = re.search(r'@version\s+"([^"]+)"', mix)
    assert m, "mix.exs 에 version: 이 없다"
    assert cargo == _py_version(), "Cargo.toml"
    assert m.group(1) == _py_version(), "mix.exs"


def test_package_dunder_version_matches():
    from seoulgaok_bim_core import __version__

    assert __version__ == _py_version()


def test_changelog_has_current_version_heading():
    text = (ROOT / "CHANGELOG.md").read_text()
    pat = rf"^## {re.escape(_py_version())}\b"
    assert re.search(pat, text, re.M), f"CHANGELOG.md 에 `## {_py_version()}` 머리말이 없다"
