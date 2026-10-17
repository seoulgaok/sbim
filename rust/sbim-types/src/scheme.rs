// 생성 파일 — 손으로 고치지 마라.
// 정본: python/seoulgaok_bim_core/types.py (pydantic)
// 생성: cd python && uv run python scripts/gen_build_options.py
//
// scheme.json · units.json · surroundings.json · site.json 레코드. 네 스키마의 `$defs` 를 이름으로 합쳐 한 파일에 둔다.
// 모델은 전부 extra=allow — 모르는 키는 `extra` 로 지나보낸다. 선택 필드는 없으면 빼고 적는다
// (Option + skip_serializing_if) — 샘플(examples/samples)이 그 모양이다. 명시 null 은 None 으로 읽혀
// 되쓰면 빠진다.

use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

/// scheme.json — data·floor_plans·unit_ids + 밑줄 키(SchemeSpatial).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Scheme {
    /// 기본값: null
    #[serde(rename = "_core_layout", default, skip_serializing_if = "Option::is_none")]
    pub core_layout: Option<CoreLayout>,
    /// 기본값: null
    #[serde(rename = "_parking_stalls", default, skip_serializing_if = "Option::is_none")]
    pub parking_stalls: Option<Vec<Vec<(f64, f64)>>>,
    /// 기본값: null
    #[serde(rename = "_column_centers", default, skip_serializing_if = "Option::is_none")]
    pub column_centers: Option<Vec<(f64, f64)>>,
    /// 기본값: null
    #[serde(rename = "_basement_outline", default, skip_serializing_if = "Option::is_none")]
    pub basement_outline: Option<Vec<(f64, f64)>>,
    /// 층별 footprint ring — 복도(=층외곽−세대−코어) 유도 기준
    ///
    /// 기본값: null
    #[serde(rename = "_floor_outlines", default, skip_serializing_if = "Option::is_none")]
    pub floor_outlines: Option<BTreeMap<String, Vec<(f64, f64)>>>,
    /// 보행 출입로 (도로→코어) — 보행 경로 산출. 1F 전용
    ///
    /// 기본값: null
    #[serde(rename = "_pedestrian_path", default, skip_serializing_if = "Option::is_none")]
    pub pedestrian_path: Option<Vec<(f64, f64)>>,
    /// 보행 출입로 전부 — 코어 문 2개(#35)면 2개. [0] === _pedestrian_path (호환)
    ///
    /// 기본값: null
    #[serde(rename = "_pedestrian_paths", default, skip_serializing_if = "Option::is_none")]
    pub pedestrian_paths: Option<Vec<Vec<(f64, f64)>>>,
    /// DH 공용 홀 — {level: ring[]}. 코어 복도 띠를 양옆으로 늘인 팔·EV 로비(연희 75-9 GT T자 홀 — 코어로 갈라진 2조각이라 링 목록). 세대에서 차감된 공용, 접면 연결계 = 코어 복도 ∪ 홀
    ///
    /// 기본값: null
    #[serde(rename = "_halls", default, skip_serializing_if = "Option::is_none")]
    pub halls: Option<BTreeMap<String, Vec<Vec<(f64, f64)>>>>,
    /// 옥탑(계단탑) 외곽 — 옥탑층·지붕층 평면이 공유
    ///
    /// 기본값: null
    #[serde(rename = "_penthouse_outline", default, skip_serializing_if = "Option::is_none")]
    pub penthouse_outline: Option<Vec<(f64, f64)>>,
    /// 전층 교집합 — 코어 탐색공간
    ///
    /// 기본값: null
    #[serde(rename = "_common_footprint", default, skip_serializing_if = "Option::is_none")]
    pub common_footprint: Option<Vec<(f64, f64)>>,
    /// 준법 위반·경고 메모
    ///
    /// 기본값: null
    #[serde(rename = "_validation", default, skip_serializing_if = "Option::is_none")]
    pub validation: Option<Vec<String>>,
    /// 기둥 단면 한 변 (m) — Concrete.column_size 확정값. 도면 재구성이 scheme만 보고도 같은 크기를 그리도록 방출(폴백 이원화 방지).
    ///
    /// 기본값: null
    #[serde(rename = "_column_size", default, skip_serializing_if = "Option::is_none")]
    pub column_size: Option<f64>,
    /// 기둥 실단면 목록 — _column_centers와 같은 좌표 프레임·같은 순서. 있음이면 소비처는 정사각 대신 이것으로 그린다(얇은 단면 기둥을 정사각으로 그리면 주차 칸을 문다). 없음 = _column_size 정사각 폴백 (구 scheme).
    ///
    /// 기본값: null
    #[serde(rename = "_column_sections", default, skip_serializing_if = "Option::is_none")]
    pub column_sections: Option<Vec<ColumnSection>>,
    /// 정북일조 기준선 (EPSG:5186 절대, 변마다 [p1,p2]) — 3D 뷰어 천공면. 북향 변마다 별도 엣지(상업 인접 면제·도로 인접은 중심선 offset), 매스 깎기(apply_north_setback)와 동일 기준. 면제면 [].
    ///
    /// 기본값: null
    #[serde(rename = "_north_ref_edges", default, skip_serializing_if = "Option::is_none")]
    pub north_ref_edges: Option<Vec<((f64, f64), (f64, f64))>>,
    /// 정북일조 기산면 보정 (m) — 영 119조①5호 나목: 높이는 본 대지와 북측 인접대지의 평균 수평면 기준. z0 − 본 대지 지표면 = 고저차의 1/2. 천공면 그리기: 유효높이 h' = z − 이 값 (경사지에서 프로파일이 수직으로 이동). 미방출·null이면 0(평지 가정).
    ///
    /// 기본값: null
    #[serde(rename = "_north_datum_offset", default, skip_serializing_if = "Option::is_none")]
    pub north_datum_offset: Option<f64>,
    /// 법규 체크리스트 33항목 판정 실값 (giga legal_checklist.yaml SSOT, #16). 합격/불합격이 아니라 적용여부 + 산출값이다 — 엔진은 규제를 생성 단계에서 지켜버리므로(사선은 매스를 깎고, 미충족은 compile_errors) 완성 설계에 '미달' 항목이 존재할 수 없다. law-graph가 결정 노드에서 근거 조문으로 엣지를 이을 때 이 실값을 쓴다. 구 scheme엔 없다 — 소비처는 부재를 "구 버전"으로 처리할 것.
    ///
    /// 기본값: null
    #[serde(rename = "_legal_checks", default, skip_serializing_if = "Option::is_none")]
    pub legal_checks: Option<Vec<LegalCheck>>,
    /// 엔진이 이 설계안을 스스로 거절한 사유 (errors.py CompileError — type·reason·details·suggestion). 없음 또는 [] = 컴파일 통과. 하나 이상이면 설계는 저장됐지만 경고와 함께 보여야 한다.
    ///
    /// 기본값: null
    #[serde(rename = "_compile_errors", default, skip_serializing_if = "Option::is_none")]
    pub compile_errors: Option<Vec<CompileError>>,
    /// 이 설계안을 만든 엔진 빌드 도장 (EngineStamp) — 서버 결과를 추적·재현한다. 전부 문자열. 구 scheme엔 없다 — 소비처는 부재를 "구 버전"으로 처리할 것.
    ///
    /// 기본값: null
    #[serde(rename = "_engine_stamp", default, skip_serializing_if = "Option::is_none")]
    pub engine_stamp: Option<EngineStamp>,
    /// 설비 (제안 2026-10-16, #549 — 엔진 미방출). 계통별 평면도(위생·냉난방·환기·가스·전기)의 재료. 처음엔 기기(kind: "device") 자리만이어도 도면이 된다. 좌표 EPSG 절대.
    ///
    /// 기본값: null
    #[serde(rename = "_mep", default, skip_serializing_if = "Option::is_none")]
    pub mep: Option<Vec<MepItem>>,
    pub data: SchemeData,
    pub floor_plans: Vec<FloorPlan>,
    pub unit_ids: Vec<String>,
    /// 엔진이 실제로 쓴 속성 창 값 + 출처. 구 scheme엔 없다.
    ///
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub resolved_options: Option<ResolvedOptions>,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

/// 설계안 폴더의 `site.json` — 필지·도로·외곽선. 키 이름·좌표(EPSG:5186 절대)는 엔진 building_info 와 같다.
///
/// scheme.json 에 없어 에디터가 대지 경계·도로·정북 한계선을 못 그리던 것을 채운다. TS `SiteInfo` 와 같은 모양.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SiteInfo {
    /// 기본값: []
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub parcel_polygon: Option<Vec<(f64, f64)>>,
    /// 기본값: [0, 0]
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub parcel_center: Option<(f64, f64)>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub road_polygon: Option<Vec<Vec<(f64, f64)>>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub road_polygon_wide: Option<Vec<Vec<(f64, f64)>>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub road_centerlines: Option<Vec<Vec<(f64, f64)>>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub road_centerline_widths: Option<Vec<f64>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub effective_parcel_outline: Option<Vec<(f64, f64)>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub buildable_outline: Option<Vec<(f64, f64)>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub footprint_outline: Option<Vec<(f64, f64)>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub north_datum_offset: Option<f64>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub parcel_polygon_z: Option<Vec<f64>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub road_centerline_z: Option<Vec<Vec<f64>>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub elevation_src: Option<String>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub raw_parcel_area: Option<f64>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub effective_parcel_area: Option<f64>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub road_widening_area: Option<f64>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub corner_cut_area: Option<f64>,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

/// units.json 레코드 — 생성기 units 직렬화 계약.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct UnitRecord {
    pub id: String,
    pub floor: i64,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub floor_height: Option<f64>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub floor_bottom_height: Option<f64>,
    /// 기본값: 0
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub price: Option<f64>,
    /// 기본값: {"net": null, "common": null, "land_portion": null, "contract": null, "veranda": null, "veranda_eq": null, "balcony": null, "balcony_depth": null, "service": null, "actual_use": null, "duplex_upper": null}
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub area: Option<UnitAreaBreakdown>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub geom: Option<serde_json::Value>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub polygon: Option<Vec<(f64, f64)>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub duplex_upper_polygon: Option<Vec<(f64, f64)>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub balcony_polygons: Option<Vec<Vec<(f64, f64)>>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub polygons_by_floor: Option<BTreeMap<String, Vec<(f64, f64)>>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub rooms: Option<Vec<UnitRoom>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub fixtures: Option<Vec<UnitFixture>>,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SurroundingBuilding {
    pub geom: SurroundingGeometry,
    pub data: SurroundingData,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BufferAttributeData {
    #[serde(rename = "itemSize")]
    pub item_size: i64,
    pub r#type: String,
    pub array: Vec<f64>,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BufferGeometryData {
    pub metadata: BufferGeometryMetadata,
    pub uuid: String,
    /// 항상 "BufferGeometry"
    pub r#type: String,
    pub data: BufferGeometryInner,
    /// 기본값: null
    #[serde(rename = "userData", default, skip_serializing_if = "Option::is_none")]
    pub user_data: Option<BTreeMap<String, serde_json::Value>>,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

/// 기둥 실단면 하나 — _column_centers의 같은 자리 기둥을 정사각이 아니라 이 단면으로 그린다.
/// w는 빔 축 방향, d는 그 가로, angle_deg는 w 축의 각(도).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ColumnSection {
    /// 기둥 중심 (EPSG:5186 절대) — _column_centers와 같은 프레임·같은 순서
    pub center: (f64, f64),
    /// 단면 치수 (m) — 빔 축 방향
    pub w: f64,
    /// 단면 치수 (m) — 빔 축의 가로
    pub d: f64,
    /// w 축의 각 (도)
    pub angle_deg: f64,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

/// sBIM 도메인 명제 위반 — invalid design 발화.
///
/// type: 위반 종류. 프론트엔드 TypeScript에서 discriminated union.
/// reason: 사람이 읽는 짧은 설명.
/// details: 위반 수치 / polygon 정보 (디버깅·LLM용).
/// suggestion: BuildOptions 조정 힌트 (사용자/LLM이 따라 재컴파일).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CompileError {
    pub r#type: CompileErrorType,
    pub reason: String,
    /// 기본값: {}
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub details: Option<BTreeMap<String, serde_json::Value>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub suggestion: Option<String>,
}

/// 코어 내부 분할 — 링은 EPSG 절대.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CoreLayout {
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub ev: Option<Vec<(f64, f64)>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub stair: Option<Vec<(f64, f64)>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub corridor: Option<Vec<(f64, f64)>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub ev_front: Option<Vec<(f64, f64)>>,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

/// 이 설계안을 만든 엔진 빌드 도장 — 서버 결과를 추적·재현한다. 전부 문자열.
/// 같은 소스라도 CPU 아키텍처가 다르면 컴파일 분기가 갈릴 수 있어 platform 을 남긴다.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EngineStamp {
    /// 엔진 저장소 커밋 SHA — 이 도면을 만든 빌드
    pub engine_commit: String,
    /// 엔진이 돈 플랫폼 — "linux-x86_64" · "darwin-arm64" 등
    pub platform: String,
    /// 엔진 파이썬 버전 문자열
    pub python: String,
    /// 컴파일 시각 — ISO-8601 UTC
    pub compiled_at: String,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FloorData {
    pub floor_id: i64,
    pub floor_area: f64,
    pub floor_height: f64,
    pub floor_bottom_height: f64,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub floor_name: Option<String>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub parking_count: Option<i64>,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FloorGeometry {
    pub walls: Vec<Vec<BufferGeometryData>>,
    pub floors: Vec<Vec<BufferGeometryData>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub roof: Option<Vec<Vec<BufferGeometryData>>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub windows: Option<Vec<Vec<BufferGeometryData>>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub parapets: Option<Vec<Vec<BufferGeometryData>>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub columns: Option<Vec<Vec<BufferGeometryData>>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub parking_stalls: Option<Vec<Vec<BufferGeometryData>>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub doors: Option<Vec<Vec<BufferGeometryData>>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub beams: Option<Vec<Vec<BufferGeometryData>>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub stairs: Option<Vec<Vec<BufferGeometryData>>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub coverings: Option<Vec<Vec<BufferGeometryData>>>,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FloorPlan {
    pub data: FloorData,
    pub geom: FloorGeometry,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

/// 법규 체크리스트 한 항목의 판정 실값 — key는 giga legal_checklist.yaml 의 key(변경 금지,
/// 그래프 노드 id).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LegalCheck {
    pub key: String,
    pub group: String,
    pub item: String,
    /// '적용' | '해당없음' | '검토' | '참고' 또는 실값 포함('적용 (확폭 12㎡)')
    pub status: String,
    /// 적용 내용 — 산출값 채워진 문장
    pub apply: String,
    /// 근거 조문
    pub law: String,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub note: Option<String>,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

/// 설비 항목 하나 (제안 2026-10-16, #549 — 엔진 미방출). 배관·덕트는 path, 기기는 origin.
///
/// system: water|drain|heating|vent|gas|elec · kind: pipe|duct|device · 좌표 EPSG 절대.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MepItem {
    pub system: String,
    pub kind: String,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub floor_id: Option<i64>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub origin: Option<(f64, f64)>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path: Option<Vec<(f64, f64)>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub size: Option<f64>,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

/// `BuildOptions.design`과 같은 중첩 모양 — 첫수표가 채우는 필드(`empty: "auto"`)만.
/// 잎 집합은 `options.AUTO_FIELDS`와 같다(tests/test_auto_fields.py가 지킨다).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ResolvedDesign {
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub massing: Option<ResolvedMassing>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub units: Option<ResolvedUnits>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub core: Option<ResolvedCore>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub parking: Option<ResolvedParking>,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

/// 엔진이 실제로 쓴 속성 창 값 + 필드별 출처 — 엔진이 방출, 소비처가 표시.
///
/// 사용자가 비운(None) 칸을 첫수표가 채우면 그 값이 여기 적힌다. 소비처는 전문가 칸의
/// 자동값을 흐리게 「자동 (s · 90° · 2형)」으로 보여 주고, 누르면 그 값으로 고정한다.
/// source 키는 "<묶음>.<필드>"(예: "core.core_side"), 값은 user(사용자가 준 값) |
/// prior(첫수표가 채운 값). design 에 없는 필드는 source 에도 없다.
///
/// 계약: 첫수표가 채우는 필드(`AUTO_FIELDS` — 층수·층별 세대 수 포함)는 전부 design 에
/// 나온다. source=="prior" 인 값은 결코 null 이 아니다 — 단 "units.units_per_floor" 는
/// 모든 층의 세대 수가 같을 때만 채우고, 다르면 null 이며 source 에도 없다. design 을
/// (null 잎을 버리고) 요청의 design 에 합쳐 되먹이면 같은 결과(세대·전용면적·주차 대수·
/// compile_errors)가 재현된다. 소비처는 source 를 되보내지 않는다(BuildOptions 는
/// extra="forbid"). 비우면 법이 정하는 필드(`law` — exit_road·한도 덮어쓰기·road_setback)와
/// 적힌 기본값이 정하는 필드(`default`)는 여기 없다 — 비워 두는 것이 재현되는 선택이다.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ResolvedOptions {
    pub design: ResolvedDesign,
    /// 기본값: {}
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub source: Option<BTreeMap<String, OptionSource>>,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SchemeData {
    pub lot_area: f64,
    pub build_area: f64,
    pub far: f64,
    pub bcr: f64,
    pub pnu: SchemeDataPnu,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SurroundingData {
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub address: Option<String>,
    pub height: f64,
    pub floor: i64,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SurroundingGeometry {
    pub boundary: Vec<BufferGeometryData>,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct UnitAreaBreakdown {
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub net: Option<f64>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub common: Option<f64>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub land_portion: Option<f64>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub contract: Option<f64>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub veranda: Option<f64>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub veranda_eq: Option<f64>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub balcony: Option<f64>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub balcony_depth: Option<f64>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub service: Option<f64>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub actual_use: Option<f64>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub duplex_upper: Option<f64>,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

/// 세대 안 가구·기구 (제안 2026-10-16, #549 — 엔진 미방출).
///
/// 소비처는 kind 별 2D 기호·3D 상자만 그린다 — 종류 이름과 자리·치수면 된다.
/// kind 어휘(BIMx 샘플): 싱크·쿡탑·인덕션·후드·냉장고·세탁기·상부장·하부장·아일랜드식탁·
/// 세면대·대변기·샤워부스·젠다이·신발장·침대·소파·의자·식탁.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct UnitFixture {
    pub kind: String,
    /// 기본값: [0, 0]
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub origin: Option<(f64, f64)>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub angle_deg: Option<f64>,
    /// 기본값: 0
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub w: Option<f64>,
    /// 기본값: 0
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub d: Option<f64>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub h: Option<f64>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub room_index: Option<i64>,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

/// 방 최소 의미론 — 벽·문 기하는 geom userData가 따로 옴.
///
/// 엔진은 욕실·주방과, 그 외 남는 면적을 거실 하나로 낸다(#549, 2026-10-16). 침실·현관·발코니·다용도실·복도 는 제안.
/// 마감 넷(바닥·벽·천장 이름, 천장고)은 착공신고 마감재료표(건축법 시행규칙 별표 4의2)·내역서 마감 공종의 전제 —
/// 엔진이 회사 표준(용도별)에서 채운다, building-generator #577. 2026-10-17 벽·천장 마감 추가(0.1.2).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct UnitRoom {
    /// 기본값: ""
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub r#use: Option<String>,
    /// 기본값: []
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub polygon: Option<Vec<(f64, f64)>>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub floor_finish: Option<String>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub wall_finish: Option<String>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub ceiling_finish: Option<String>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub ceiling_h: Option<f64>,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BufferAttributes {
    pub position: BufferAttributeData,
    pub normal: BufferAttributeData,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub uv: Option<BufferAttributeData>,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BufferGeometryInner {
    pub attributes: BufferAttributes,
    pub index: BufferIndex,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BufferGeometryMetadata {
    pub version: f64,
    pub r#type: String,
    pub generator: String,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BufferIndex {
    pub r#type: String,
    pub array: Vec<i64>,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ResolvedCore {
    /// 허용값: 1 · 2 · 3 · 4 · 5 · 6 · 7
    ///
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub r#type: Option<i64>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub core_side: Option<CoreSide>,
    /// 허용값: 0 · 90 · 180 · 270
    ///
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub core_rotation: Option<i64>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub core_mirror: Option<bool>,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ResolvedMassing {
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub mass_axis: Option<MassAxis>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub target_floor_count: Option<i64>,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ResolvedParking {
    /// 허용값: 45 · 60 · 90
    ///
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub parking_angle: Option<i64>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub tandem: Option<bool>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub parking_graph: Option<Vec<(String, String)>>,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ResolvedUnits {
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub units_per_floor: Option<i64>,
    /// 기본값: null
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub units_by_level: Option<BTreeMap<String, i64>>,
    /// 스키마에 없는 키 — 거부하지 않고 지나보낸다(extra=allow).
    #[serde(flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

/// units.json — 생성기 세대 레코드(UnitRecord) 배열.
pub type Units = Vec<UnitRecord>;

/// surroundings.json — 주변 건물(SurroundingBuilding) 배열. 일조·시각화용.
pub type Surroundings = Vec<SurroundingBuilding>;

/// CompileError.type 의 값.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum CompileErrorType {
    #[serde(rename = "UnitsInfeasible")]
    UnitsInfeasible,
    #[serde(rename = "UnitUnreachable")]
    UnitUnreachable,
    #[serde(rename = "UnitAreaExceeded")]
    UnitAreaExceeded,
    #[serde(rename = "ParkingSufficiency")]
    ParkingSufficiency,
    #[serde(rename = "FloorCountInfeasible")]
    FloorCountInfeasible,
    #[serde(rename = "CoreTypeInfeasible")]
    CoreTypeInfeasible,
}

/// _ResolvedCore.core_side 의 값.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum CoreSide {
    #[serde(rename = "n")]
    N,
    #[serde(rename = "ne")]
    Ne,
    #[serde(rename = "e")]
    E,
    #[serde(rename = "se")]
    Se,
    #[serde(rename = "s")]
    S,
    #[serde(rename = "sw")]
    Sw,
    #[serde(rename = "w")]
    W,
    #[serde(rename = "nw")]
    Nw,
    #[serde(rename = "c")]
    C,
}

/// _ResolvedMassing.mass_axis 의 값.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum MassAxis {
    #[serde(rename = "road")]
    Road,
    #[serde(rename = "sunlight")]
    Sunlight,
}

/// ResolvedOptions.source 의 값.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum OptionSource {
    #[serde(rename = "user")]
    User,
    #[serde(rename = "prior")]
    Prior,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(untagged)]
pub enum SchemeDataPnu {
    Integer(i64),
    String(String),
}
