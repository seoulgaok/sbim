//! 생성된 타입이 저장소의 정답(fixtures/ · examples/samples/)과 같은 모양인가.
//!
//! 비교는 `serde_json::Value` 로 한다 — 키 순서는 무시되고, 숫자는 `canon` 이 전부 f64 로 맞춘다
//! (샘플이 `lot_area: 999` 처럼 number 필드에 정수 표기를 쓰는데 serde_json 은 `999 != 999.0` 이다).

use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};

use serde_json::Value;

use sbim_types::build_options::BuildOptions;
use sbim_types::migrations::core_type_old_to_new;
use sbim_types::presets::{structure_preset, STRUCTURE_PRESET};
use sbim_types::scheme::{Scheme, Surroundings};

fn root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("../..").canonicalize().unwrap()
}

fn read(path: &Path) -> Value {
    serde_json::from_str(&fs::read_to_string(path).unwrap_or_else(|e| panic!("{}: {e}", path.display())))
        .unwrap_or_else(|e| panic!("{}: {e}", path.display()))
}

/// 숫자를 전부 f64 로 — 정수 표기(999)와 실수 표기(999.0)를 같은 값으로 본다.
fn canon(v: &Value) -> Value {
    match v {
        Value::Number(n) => Value::from(n.as_f64().unwrap()),
        Value::Array(xs) => Value::Array(xs.iter().map(canon).collect()),
        Value::Object(m) => Value::Object(m.iter().map(|(k, x)| (k.clone(), canon(x))).collect()),
        other => other.clone(),
    }
}

fn assert_same(got: &Value, want: &Value, what: &str) {
    let (g, w) = (canon(got), canon(want));
    if g != w {
        // 어디서 갈리는지 — 최상위 키별로 먼저 짚는다
        if let (Value::Object(g), Value::Object(w)) = (&g, &w) {
            for k in g.keys().chain(w.keys()) {
                if g.get(k) != w.get(k) {
                    panic!("{what}: `{k}` 가 다르다\n got: {}\nwant: {}",
                           g.get(k).map(|v| v.to_string()).unwrap_or("<없음>".into()),
                           w.get(k).map(|v| v.to_string()).unwrap_or("<없음>".into()));
                }
            }
        }
        panic!("{what}: 다르다");
    }
}

fn fixture_cases() -> Vec<(String, Value)> {
    let dir = root().join("fixtures/build_options");
    let mut out: Vec<_> = fs::read_dir(&dir)
        .unwrap()
        .map(|e| e.unwrap().path())
        .filter(|p| p.extension().is_some_and(|x| x == "json"))
        .map(|p| (p.file_stem().unwrap().to_string_lossy().into_owned(), read(&p)))
        .collect();
    out.sort_by(|a, b| a.0.cmp(&b.0));
    assert!(!out.is_empty(), "{} 에 fixture 가 없다", dir.display());
    out
}

/// 1. fixtures/build_options/*.json 의 expected 를 BuildOptions 로 읽고 되써도 같다 —
///    키를 빼지도 더하지도 않는다(스키마에 없는 키가 expected 에 있으면 되쓴 쪽에 없어 갈린다).
#[test]
fn build_options_fixtures_round_trip() {
    for (name, fx) in fixture_cases() {
        let expected = &fx["expected"];
        let opts: BuildOptions = serde_json::from_value(expected.clone())
            .unwrap_or_else(|e| panic!("{name}: expected 를 BuildOptions 로 못 읽는다: {e}"));
        let back = serde_json::to_value(&opts).unwrap();
        assert_same(&back, expected, &format!("fixtures/build_options/{name}.json expected round-trip"));
        // 정규화는 멱등이다 — 되읽어도 같은 구조체
        let again: BuildOptions = serde_json::from_value(back).unwrap();
        assert_eq!(again, opts, "{name}: 되읽은 구조체가 다르다");
    }
}

/// 2. `BuildOptions::default()` == empty.json 의 expected — 기본값 전부(프리셋이 채운 max_span 8.1 포함).
#[test]
fn default_is_empty_fixture() {
    let fx = read(&root().join("fixtures/build_options/empty.json"));
    let got = serde_json::to_value(BuildOptions::default()).unwrap();
    assert_same(&got, &fx["expected"], "BuildOptions::default()");
    assert_eq!(got["standards"]["dimensions"]["max_span"], Value::from(8.1));
    // 빈 입력은 기본값이다 — pydantic `BuildOptions.model_validate({})` 와 같다
    let from_empty: BuildOptions = serde_json::from_str("{}").unwrap();
    assert_eq!(from_empty, BuildOptions::default());
}

/// 3. examples/samples/**/scheme.json 과 surroundings.json — 읽히고, 되쓰면 밑줄 키·extra 까지 같다.
///    units.json 샘플은 구 `Unit(geom/data)` 모양이라 `UnitRecord` 로는 안 맞는다 — 건너뛴다.
#[test]
fn scheme_samples_round_trip() {
    let samples = root().join("examples/samples");
    let mut paths = vec![samples.join("scheme.json")];
    for sub in ["sample-small", "sample-medium", "sample-large"] {
        paths.push(samples.join(sub).join("scheme.json"));
    }
    for path in &paths {
        let raw = read(path);
        let scheme: Scheme = serde_json::from_value(raw.clone())
            .unwrap_or_else(|e| panic!("{}: Scheme 으로 못 읽는다: {e}", path.display()));
        let back = serde_json::to_value(&scheme).unwrap();
        assert_same(&back, &raw, &path.display().to_string());
        assert!(!scheme.floor_plans.is_empty(), "{}: floor_plans 가 비었다", path.display());
        // 샘플 셋은 스키마 밖 키 `_core_candidates` 를 들고 있다 — extra 로 지나간다
        if path.parent().unwrap() != samples {
            assert!(scheme.extra.contains_key("_core_candidates"), "{}: extra 에 _core_candidates 가 없다",
                    path.display());
        }
    }
}

#[test]
fn surroundings_sample_round_trip() {
    let path = root().join("examples/samples/surroundings.json");
    let raw = read(&path);
    let items: Surroundings = serde_json::from_value(raw.clone())
        .unwrap_or_else(|e| panic!("{}: Surroundings 로 못 읽는다: {e}", path.display()));
    assert!(!items.is_empty());
    let back = serde_json::to_value(&items).unwrap();
    assert_same(&back, &raw, &path.display().to_string());
}

/// 4. 코어 번호 개번 표 == fixtures/core_type_renumber.json.
#[test]
fn core_type_renumber_matches_fixture() {
    let fx = read(&root().join("fixtures/core_type_renumber.json"));
    let table: BTreeMap<String, u8> = serde_json::from_value(fx["old_to_new"].clone()).unwrap();
    assert_eq!(table.len(), 7);
    for (old, new) in &table {
        assert_eq!(core_type_old_to_new(old.parse().unwrap()), Some(*new), "old={old}");
    }
    assert_eq!(core_type_old_to_new(0), None);
    assert_eq!(core_type_old_to_new(8), None);
}

/// 5. 구조 프리셋 == fixtures/presets.json, 이름은 design.structure 의 값과 같다.
#[test]
fn structure_presets_match_fixture() {
    let fx = read(&root().join("fixtures/presets.json"));
    let table = fx["structure_preset"].as_object().unwrap();
    assert_eq!(table.len(), STRUCTURE_PRESET.len());
    for (name, want) in table {
        let p = structure_preset(name).unwrap_or_else(|| panic!("프리셋 {name} 이 없다"));
        assert_eq!(p.wall_thickness, want["wall_thickness"].as_f64().unwrap(), "{name}");
        assert_eq!(p.max_span, want["max_span"].as_f64().unwrap(), "{name}");
        assert_eq!(p.min_col_dist, want["min_col_dist"].as_f64().unwrap(), "{name}");
        // 이름이 Structure 열거의 값이다
        let v = serde_json::json!({ "design": { "structure": name } });
        let opts: BuildOptions = serde_json::from_value(v).unwrap_or_else(|e| panic!("{name}: {e}"));
        assert_eq!(serde_json::to_value(&opts).unwrap()["design"]["structure"], Value::from(name.as_str()));
    }
    assert!(structure_preset("timber").is_none());
}
