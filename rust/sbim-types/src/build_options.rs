// 생성 파일 — 손으로 고치지 마라.
// 정본: python/seoulgaok_bim_core/options.py (pydantic)
// 생성: cd python && uv run python scripts/gen_build_options.py
//
// BuildOptions — 속성 창 입력 타입. 직렬화는 pydantic model_dump 를 거울로 삼는다 — 키를 빼지 않고
// null 도 적는다(fixtures/build_options/*.json 의 expected 가 그 모양). 빠진 키는 `Default`
// (= fixtures/build_options/empty.json 의 expected, 프리셋이 채운 정규화 기본값)로 채운다.
// 모르는 키는 serde 가 조용히 버린다 — 옛 모양(ground_floor · far_target …)을 접는 표는 migrations.rs,
// 정답은 fixtures/build_options/ 에 있다.

use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

/// 다세대주택 파라메트릭 설계 입력 — 속성 창.
///
/// 세 묶음이다: `design`(이 설계에서 고르는 것) · `standards`(회사 표준) ·
/// `business`(사업성). 도면 하나를 만들 때 마주하는 건 `design`뿐이다.
///
/// 구 평면 모양(`ground_floor`·`concrete`·`schedule` …)으로 들어와도 받아서 옮긴다.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct BuildOptions {
    /// 합필 필지 PNU 리스트 (19자리). 단일 필지면 [pnu] 1개. 다중 필지는 합필(union) 전제 — 컴파일러가 geometry union 후 처리.
    pub land_ids: Vec<String>,
    /// 대표 필지 PNU. 보고서·Studio의 '대표 주소' 출처. land_ids 중 하나여야 함. 빈 문자열이면 land_ids[0] 사용.
    ///
    /// 기본값: ""
    pub primary_land_id: String,
    pub design: Design,
    pub standards: Standards,
    pub business: Business,
}

impl Default for BuildOptions {
    fn default() -> Self {
        Self {
            land_ids: Vec::new(),
            primary_land_id: "".to_string(),
            design: Design::default(),
            standards: Standards::default(),
            business: Business::default(),
        }
    }
}

/// 욕실 마감 넷 — `UnitRoom.floor_finish·wall_finish·ceiling_finish·ceiling_h` 로 그대로 나간다.
///
/// 용도마다 모델이 따로인 이유: 언어별 방출기(emit_rust)가 한 모델에 한 기본값만 허용한다 — 모양은 셋이 같다.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct BathFinish {
    /// 바닥 마감 이름.
    ///
    /// 기본값: "바닥타일 300×300"
    pub floor: String,
    /// 벽 마감 이름.
    ///
    /// 기본값: "벽타일 300×600"
    pub wall: String,
    /// 천장 마감 이름 — 점검구 있는 판.
    ///
    /// 기본값: "SMC 천장판"
    pub ceiling: String,
    /// 천장고 (m) — 바닥 마감면에서 천장 마감면까지.
    ///
    /// 기본값: 2.2
    pub ceiling_h: f64,
}

impl Default for BathFinish {
    fn default() -> Self {
        Self {
            floor: "바닥타일 300×300".to_string(),
            wall: "벽타일 300×600".to_string(),
            ceiling: "SMC 천장판".to_string(),
            ceiling_h: 2.2,
        }
    }
}

/// 사업성 — 도면과 무관한 값. 소비 UI는 접어 둘 수 있다.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct Business {
    pub schedule: Schedule,
    pub financing: Financing,
}

impl Default for Business {
    fn default() -> Self {
        Self {
            schedule: Schedule::default(),
            financing: Financing::default(),
        }
    }
}

/// 동선 — 복도·보행로를 어떻게 낼까. 보행로 폭은 법규 보정(regulations)으로 갔다.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct Circulation {
    /// 보행통로 라우팅 — carve=최단, edge=필지 변 추종.
    ///
    /// 기본값: "carve"
    pub corridor_mode: CorridorMode,
}

impl Default for Circulation {
    fn default() -> Self {
        Self {
            corridor_mode: CorridorMode::Carve,
        }
    }
}

/// 공동현관문(`door_type` = 공동현관) 사양.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct CommonDoorSpec {
    /// 문 — 종류·구성.
    ///
    /// 기본값: "단열 자동문 (시스템 알루미늄)"
    pub frame: String,
    /// 유리 구성식.
    ///
    /// 기본값: "THK39 (5LE+12A+5CL+12A+5LE) 로이 삼중유리"
    pub glazing: String,
    /// 열관류율 (W/㎡K).
    ///
    /// 기본값: 1.42
    pub u_value: f64,
}

impl Default for CommonDoorSpec {
    fn default() -> Self {
        Self {
            frame: "단열 자동문 (시스템 알루미늄)".to_string(),
            glazing: "THK39 (5LE+12A+5CL+12A+5LE) 로이 삼중유리".to_string(),
            u_value: 1.42,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct Concrete {
    /// 외벽 두께 (m). 다세대 표준 0.20 (단열 포함).
    ///
    /// 기본값: 0.2
    pub wall_thickness: f64,
    /// 층간 슬래브 두께 (m). 실무 스펙 150 (기초는 foundation_thickness 별도).
    ///
    /// 기본값: 0.15
    pub slab_thickness: f64,
    /// 세대 **내부** 칸막이 두께 (m). 표준 0.10 (방 분할용).
    ///
    /// 기본값: 0.1
    pub interior_wall_thickness: f64,
    /// 세대 간 경계벽·공용부(복도·계단실) 경계벽 두께 (m). 실무 표준 0.20. 법정 하한은 다세대(건축허가)면 건축법 계열 경계벽 기준(철근콘크리트조 10cm 이상)이고, 주택건설기준 14조①1의 15cm는 사업계획승인(30세대 이상) 대상에만 적용된다 — 어느 쪽이든 0.20은 충족. 참조 도면(상도동 214-82) 실측도 전 층 철콘200 단일 — 외벽과 **구조체 두께가 같고** 외기 접면만 단열·마감이 덧붙어 410이 된다. 코어 벽이 층마다 달라 보이는 건 단열 유무 차이지 구조체 차이가 아니다.
    ///
    /// 기본값: 0.2
    pub party_wall_thickness: f64,
    /// 지하 외벽(옹벽) 두께 (m). 토압을 받아 지상 외벽보다 두껍다 — 참조 도면 실측 지하1층 '철근콘크리트 300' 6장.
    ///
    /// 기본값: 0.3
    pub basement_wall_thickness: f64,
    /// 난간 간살(동자) 단면 한 변 (m). 실무 φ20~50 각살 — 기본 50mm.
    ///
    /// 기본값: 0.05
    pub railing_post_size: f64,
    /// 난간 간살 사이 **안목치수** (m). 중심간 피치 = railing_post_size + 이 값. 법정: 우리 대상(도시형생활주택 30세대 미만 = 건축허가)에는 살 간격 규정이 **없다** — 건축법 시행령 40조①은 높이 1.2m만 규정하고, 안목 10cm 규정인 주택건설기준 18조②2는 같은 영 3조(적용범위)상 사업계획승인(30세대 이상) 대상에만 적용된다. 0.12는 영유아 끼임 방지 안전 관행 범위의 값이며, 30세대 이상 단지를 다루게 되면 0.10으로 낮춰야 한다.
    ///
    /// 기본값: 0.12
    pub railing_clear: f64,
    /// 옥상·노대 난간 중 **콘크리트 저벽** 높이 (m). 기본 0 = 금속 난간만(동자+상단 손스침 바)으로 법정고 1.2m를 만든다 (시행령 40조①). 저벽(방수턱 등)을 원하면 값을 준다 — 그만큼 동자 구간이 짧아진다.
    ///
    /// 기본값: 0.0
    pub parapet_wall_height: f64,
    /// 기둥 단면 한 변 (m). 실무 스펙 600 정사각 — 1층 필로티, 전이보와 접합.
    ///
    /// 기본값: 0.6
    pub column_size: f64,
    /// 기초(흙 접함) 슬래브 두께 (m). 층간 슬래브와 별도 — 두께가 다르다.
    ///
    /// 기본값: 0.6
    pub foundation_thickness: f64,
    /// 외벽 외단열 두께 (m). 참조 도면 실측 '[외벽] 철콘200 // EPS200'.
    ///
    /// 기본값: 0.2
    pub insulation_thickness: f64,
    /// 외부 마감 두께 (m). 재료마다 10~50mm — 기본 STO 10mm.
    ///
    /// 기본값: 0.01
    pub finish_thickness: f64,
    /// 외부 마감재 이름 (IFC 레이어셋 명명에 사용).
    ///
    /// 기본값: "STO"
    pub finish_name: String,
    /// 전이보 폭 (m). 필로티 천장(2층 바닥) 600×800 — 실무 스펙.
    ///
    /// 기본값: 0.6
    pub transfer_beam_width: f64,
    /// 전이보 춤 (m). 윗층 하중을 기둥/벽으로 전달 — 기둥과 만나야 함.
    ///
    /// 기본값: 0.8
    pub transfer_beam_depth: f64,
    /// 일반 보·일조사선 꺾임부 전이보 단면 (m). 600×600 정사각.
    ///
    /// 기본값: 0.6
    pub beam_size: f64,
    /// 계단 단높이 상한 (m). 주택 계단 법정 0.18 — 실단높이 = 층고/단수.
    ///
    /// 기본값: 0.18
    pub stair_riser_max: f64,
    /// 계단 단너비(디딤판 깊이) (m).
    ///
    /// 기본값: 0.26
    pub stair_tread: f64,
    /// 계단판(waist) 두께 (m). 기본 150mm.
    ///
    /// 기본값: 0.15
    pub stair_waist: f64,
    /// 콘크리트 ㎥당 단가 (원). 다세대 표준 350만원. 공사비 = total_m3 × price_per_m3.
    ///
    /// 기본값: 3500000
    pub price_per_m3: i64,
}

impl Default for Concrete {
    fn default() -> Self {
        Self {
            wall_thickness: 0.2,
            slab_thickness: 0.15,
            interior_wall_thickness: 0.1,
            party_wall_thickness: 0.2,
            basement_wall_thickness: 0.3,
            railing_post_size: 0.05,
            railing_clear: 0.12,
            parapet_wall_height: 0.0,
            column_size: 0.6,
            foundation_thickness: 0.6,
            insulation_thickness: 0.2,
            finish_thickness: 0.01,
            finish_name: "STO".to_string(),
            transfer_beam_width: 0.6,
            transfer_beam_depth: 0.8,
            beam_size: 0.6,
            stair_riser_max: 0.18,
            stair_tread: 0.26,
            stair_waist: 0.15,
            price_per_m3: 3500000,
        }
    }
}

/// 코어 — 무엇을(type) 어디에(core_side) 어느 방향으로(core_rotation) 어느 손잡이로
/// (core_mirror) 앉히는가.
///
/// 치수는 입력이 아니라 매스+세대프로그램에서 derive된다(삼전 정답: 계단·EV가 16.4m
/// 분리 = 세대 배치 결과). 자리와 배향은 고르는 것이고, 값이 없으면 첫수표가 정한다.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct Core {
    /// 코어 형상 타입 (DWG→sbim 코어 라이브러리 — giga core_library.json이 진실). None=첫수표가 정한다(매스 형상). 이름은 외곽 형태(세장형·정방형·ㄱ자형)로 가르고, 외곽이 같은 것은 괄호의 계단 형식으로 갈린다. 1=세장형(꺾은계단, 2.8×6.8)·2=세장형(직선계단, 2.8×8.05)·3=세장형·편복도(직선계단, 2.8×10.15, 복도 내장, 층당 5~7세대 — 류상호 '코어 유형 추가' 2026-09; 도면 실측 2.78×9.95로 라이브러리 재추출 대기)·4=정방형(꺾은계단, 5.2×4.7)·5=정방형(직선계단, 5.2×4.7)·6=정방형(ㄱ자계단, 5.3×4.95 — ㄱ자는 외곽이 아니라 계단 모양)·7=ㄱ자형(EV측면, 4.8×5.9 — 외곽이 ㄱ자로 파인 유일한 유형). 대부분 type2(세장 타워, 회전 fit), 넓은 단독 장변접도만 type4/5. 번호는 2026-09 DWG 시트 순서로 재배열됐다(building-generator #190) — 옛 번호로 저장된 값은 migrate_core_type()으로 옮긴다.
    ///
    /// 허용값: 1 · 2 · 3 · 4 · 5 · 6 · 7
    ///
    /// 기본값: null
    ///
    /// 비우면: auto — None=첫수표가 정한다(resolved_options 에 나온다)
    pub r#type: Option<i64>,
    /// 코어 자리 (EPSG 절대 방위). 정방위(n·e·s·w)=매스의 그 변 가운데, 대각(ne·nw·se·sw)=그 모서리, c=매스 안쪽(주접도 프레임 축을 따라 매스 경계에서 1.5m 이상 떨어진 자리 — 상층은 코어 양쪽에 편복도가 선다). 그 자리에 코어가 안 들면 폴백 없이 CoreTypeInfeasible. None=첫수표가 정한다.
    ///
    /// 기본값: null
    ///
    /// 비우면: auto — None=첫수표가 정한다(resolved_options 에 나온다)
    pub core_side: Option<CoreSide>,
    /// 코어 배향 — core_side로 정해진 변 기준 절대 회전각. c일 때 기준 변은 주접도 변이다. 0=코어 기준자세 그대로 변에 밀착, 90/180/270=그만큼 회전. 코어는 점대칭이 아니라(계단·EV 한쪽 편재, 복도 한 면 접합, 출입구 면이 방향별로 달라 0·90·180·270이 전부 다른 결과) 절반 지정인 구 core_axis(road/depth)로는 같은 축 위 180° 뒤집기를 표현할 수 없어 네 방위를 전부 받는다. 라이브러리 형상 가로세로와 무관한 앉은 변 기준 절대 표현이라 코어 형상이 바뀌어도 뜻이 유지된다. None=첫수표가 정한다.
    ///
    /// 허용값: 0 · 90 · 180 · 270
    ///
    /// 기본값: null
    ///
    /// 비우면: auto — None=첫수표가 정한다(resolved_options 에 나온다)
    pub core_rotation: Option<i64>,
    /// 코어 좌우 뒤집기 — true=코어 기준자세를 거울처럼 뒤집은 모양(앉은 변에서 봐서 계단·EV의 좌우가 바뀐 반대 손잡이)으로 앉힌 뒤 core_rotation만큼 돌린다. 회전 네 방위로는 이 모양이 안 나온다 — 회전 180°는 가로·세로를 함께 뒤집어 복도 면까지 옮기지만, 거울은 복도 면을 그대로 두고 좌우만 바꾼다. 회전과 함께 코어가 변에 앉는 여덟 자세를 전부 적는다. false=기준자세 그대로. None=첫수표가 정한다.
    ///
    /// 기본값: null
    ///
    /// 비우면: auto — None=첫수표가 정한다(resolved_options 에 나온다)
    pub core_mirror: Option<bool>,
    /// 코어(복도) 보행 출입구 수 1|2. 2=코어 문 반대편에도 문 — 보행로가 도로에서 꼬이는 필지(합정동 441-31). None=문 하나(엔진이 둘째 문을 스스로 켜지 않는다 — 2가 필요하면 옵션으로 준다). scheme `_pedestrian_paths`로 전부 방출.
    ///
    /// 기본값: null
    ///
    /// 비우면: default — None=설명에 적힌 기본 동작
    pub core_entries: Option<i64>,
}

impl Default for Core {
    fn default() -> Self {
        Self {
            r#type: None,
            core_side: None,
            core_rotation: None,
            core_mirror: None,
            core_entries: None,
        }
    }
}

/// 이 설계에서 고르는 것.
///
/// 비울 수 있는 필드는 전부 비웠을 때 누가 정하는지를 `json_schema_extra={"empty": …}`
/// 하나로 적는다 — `auto`=첫수표가 채운다(ResolvedDesign 에 나온다), `law`=법이 정한다,
/// `default`=적힌 sbim 기본값. `AUTO_FIELDS`가 auto 집합이다.
///
/// 묶음은 **대상**이다(매스·세대·코어·주차·동선·외장) — 단계로 자르면 같은 대상의
/// 속성이 두 집에 나뉘어 산다(구 GroundFloor가 주차·코어·동선·기둥을 한 서랍에 담았다).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct Design {
    pub massing: Massing,
    pub units: UnitSpec,
    pub core: Core,
    pub parking: Parking,
    pub circulation: Circulation,
    pub exterior: Exterior,
    /// 구조 방식 — wall=벽식(현행 다세대 표준)·rahmen=라멘(기둥·보)·steel=철골. 층고와 벽 두께·스팬 기본값이 여기서 derive된다(Standards에서 override 가능). 한 필드 클래스였던 Structure를 스칼라로 폈다.
    ///
    /// 기본값: "wall"
    pub structure: Structure,
    pub regulations: RegulationOverrides,
}

impl Default for Design {
    fn default() -> Self {
        Self {
            massing: Massing::default(),
            units: UnitSpec::default(),
            core: Core::default(),
            parking: Parking::default(),
            circulation: Circulation::default(),
            exterior: Exterior::default(),
            structure: Structure::Wall,
            regulations: RegulationOverrides::default(),
        }
    }
}

/// 구조 치수 표준 — 사업마다 고르는 값이 아니라 회사가 정해 두는 값.
///
/// 주차 칸·차로 치수(2.5×5.0·6.0)는 주차장법 상수라 엔진이 갖는다 — 옵션이 아니다.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct Dimensions {
    /// 기둥 최대 간격 (m). 소장 템플릿 T꺾임 8.1 수용, 2026-10-11 선장 결정.
    ///
    /// 기본값: 8.1
    pub max_span: f64,
    /// 코너 캔틸레버 한계 (m). 매스 코너에서 가장 가까운 지지(기둥·벽)까지의 거리를 축별로 재어 수직·벽따라 중 큰 쪽이 이 값 이하여야 한다. GT 1층 203장 중 193장이 3 m 이하(실측).
    ///
    /// 기본값: 3.0
    pub cantilever: f64,
    /// 기둥 최소 간격 (m).
    ///
    /// 기본값: 3.0
    pub min_col_dist: f64,
}

impl Default for Dimensions {
    fn default() -> Self {
        Self {
            max_span: 8.1,
            cantilever: 3.0,
            min_col_dist: 3.0,
        }
    }
}

/// 세대 현관문(`door_type` 없음) 사양 — 방화문 등급은 `DoorUserData.fire_door` 로 그대로 나간다.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct EntranceDoorSpec {
    /// 문 — 종류·구성.
    ///
    /// 기본값: "갑종 방화문 / 단열문 (Single, With Sill)"
    pub frame: String,
    /// 문 마감.
    ///
    /// 기본값: "ST PL 위 불소수지도장(지정색) / 문짝 단열충진"
    pub finish: String,
    /// 방화문 등급(영 제64조 ①): "60+" | "60" | "30". None = 방화문 아님.
    ///
    /// 기본값: "60+"
    pub fire_door: Option<String>,
}

impl Default for EntranceDoorSpec {
    fn default() -> Self {
        Self {
            frame: "갑종 방화문 / 단열문 (Single, With Sill)".to_string(),
            finish: "ST PL 위 불소수지도장(지정색) / 문짝 단열충진".to_string(),
            fire_door: Some("60+".to_string()),
        }
    }
}

/// 외장 — 외벽 마감과 창 스타일. 한 필드 클래스 둘(Windows·Exterior)을 합쳤다.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct Exterior {
    /// 외장재 preset (외벽·천장/테라스 색 페어). white=화이트·라이트그레이, sandstone=사암·웜그레이, brick=벽돌브라운·라이트그레이(default), concrete=노출콘크리트·짙은회색. 소비처 렌더러가 hex로 매핑.
    ///
    /// 기본값: "brick"
    pub style: ExteriorStyle,
    /// 창 크기 의도 — 법정 채광면적(거실 바닥의 1/10)을 몇 배로 잡을지의 배율. open=넉넉(1.8배), standard=표준(1.35배), closed=최소(1.05배). 창의 위치·개수는 세대가 접한 외벽에서 컴파일러가 derive한다.
    ///
    /// 기본값: "open"
    pub window_style: WindowStyle,
}

impl Default for Exterior {
    fn default() -> Self {
        Self {
            style: ExteriorStyle::Brick,
            window_style: WindowStyle::Open,
        }
    }
}

/// PF 대출(토지담보·시설자금·준공담보)과 분양 스케줄 의도.
///
/// 이자 = 대출액 × 금리 × 기간/12. 분양수입은 계약/중도/잔금으로 월별 분배.
///
/// **금융 조건에는 기본값이 없다(None).** 사업자·시점마다 다른 협상 결과이고,
/// 남의 조건을 조용히 물려받아 사업성을 계산하는 것이 값이 비는 것보다 위험하다.
/// 값은 설정 파일에서 주입한다 — config.py / examples/sbim_config.example.json.
///
///     from seoulgaok_bim_core import build_options
///     opts = build_options()          # sbim_config.json의 financing 블록 적용
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct Financing {
    /// 토지담보 LTV.
    ///
    /// 기본값: null
    pub land_loan_ltv: Option<f64>,
    /// 토지담보 연이자율.
    ///
    /// 기본값: null
    pub land_loan_rate: Option<f64>,
    /// 시설자금 LTV (직접공사비 기준).
    ///
    /// 기본값: null
    pub fac_loan_ltv: Option<f64>,
    /// 시설자금 연이자율.
    ///
    /// 기본값: null
    pub fac_loan_rate: Option<f64>,
    /// 시설자금 기성고 평균 실사용률 (이자 효율).
    ///
    /// 기본값: null
    pub fac_efficiency: Option<f64>,
    /// 준공담보 연이자율 (담보 확정 → 토지담보 수준).
    ///
    /// 기본값: null
    pub post_loan_rate: Option<f64>,
    /// 준공 후 기간 (개월). 비아파트 = 준공 후 이 기간에 균등 분양·매각.
    ///
    /// 기본값: null
    pub post_months: Option<f64>,
    /// 대출 취급수수료율 (토담+시설 대출액).
    ///
    /// 기본값: null
    pub handling_fee_rate: Option<f64>,
    /// 취급수수료 적용 여부. True=적용.
    ///
    /// 기본값: false
    pub handling_fee_on: bool,
}

impl Default for Financing {
    fn default() -> Self {
        Self {
            land_loan_ltv: None,
            land_loan_rate: None,
            fac_loan_ltv: None,
            fac_loan_rate: None,
            fac_efficiency: None,
            post_loan_rate: None,
            post_months: None,
            handling_fee_rate: None,
            handling_fee_on: false,
        }
    }
}

/// 실내 마감 표준 — 방 용도마다 하나. 엔진이 `units.rooms[]` 의 마감 넷을 여기서 채운다(building-generator #577).
///
/// 착공신고 마감재료표(건축법 시행규칙 별표 4의2)와 내역서 마감 공종(수장·타일·미장, 금액의 약 35 %)의 전제.
/// 기본값은 **초안**이다 — 류상호 BIMx 샘플(2026-07, 욕실 바닥 방통40/타일10 · 벽 방수석고보드 위 타일)과
/// 구의동 57-93 slab layers(강마루10)에서 뽑았고 소장 확인 전이다. 사업마다 고르는 값이 아니라 회사가 정해 두는 값이라
/// `standards` 에 둔다. 지금 엔진이 내는 방은 욕실·주방·거실 셋뿐이라 그 셋만 있다 — 침실·현관이 생기면 같은 꼴로 늘린다.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct Finishes {
    /// 욕실.
    pub bath: BathFinish,
    /// 주방.
    pub kitchen: KitchenFinish,
    /// 거실.
    pub living: LivingFinish,
}

impl Default for Finishes {
    fn default() -> Self {
        Self {
            bath: BathFinish::default(),
            kitchen: KitchenFinish::default(),
            living: LivingFinish::default(),
        }
    }
}

/// 세대 안 문(`door_type` = 욕실 등) 사양.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct InteriorDoorSpec {
    /// 문 — 종류·구성.
    ///
    /// 기본값: "목재 여닫이문 (ABS)"
    pub frame: String,
}

impl Default for InteriorDoorSpec {
    fn default() -> Self {
        Self {
            frame: "목재 여닫이문 (ABS)".to_string(),
        }
    }
}

/// 주방 마감 넷 — 오픈키친이라 거실과 같은 바닥·천장, 싱크 상부만 타일.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct KitchenFinish {
    /// 바닥 마감 이름.
    ///
    /// 기본값: "강마루10"
    pub floor: String,
    /// 벽 마감 이름.
    ///
    /// 기본값: "실크벽지 (싱크 상부 벽타일)"
    pub wall: String,
    /// 천장 마감 이름.
    ///
    /// 기본값: "실크벽지"
    pub ceiling: String,
    /// 천장고 (m).
    ///
    /// 기본값: 2.3
    pub ceiling_h: f64,
}

impl Default for KitchenFinish {
    fn default() -> Self {
        Self {
            floor: "강마루10".to_string(),
            wall: "실크벽지 (싱크 상부 벽타일)".to_string(),
            ceiling: "실크벽지".to_string(),
            ceiling_h: 2.3,
        }
    }
}

/// 거실 마감 넷 — 욕실·주방 외 남는 면적 전부(침실 분할 전). 천장고 2.3 은 층고 2.9·슬래브 150·바닥 구성 120 뒤의 값.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct LivingFinish {
    /// 바닥 마감 이름.
    ///
    /// 기본값: "강마루10"
    pub floor: String,
    /// 벽 마감 이름.
    ///
    /// 기본값: "실크벽지"
    pub wall: String,
    /// 천장 마감 이름.
    ///
    /// 기본값: "실크벽지"
    pub ceiling: String,
    /// 천장고 (m).
    ///
    /// 기본값: 2.3
    pub ceiling_h: f64,
}

impl Default for LivingFinish {
    fn default() -> Self {
        Self {
            floor: "강마루10".to_string(),
            wall: "실크벽지".to_string(),
            ceiling: "실크벽지".to_string(),
            ceiling_h: 2.3,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct Massing {
    /// 목표 층수. 사선제한으로 미달 가능. None=첫수표가 정한다(사선·일조·FAR 한계까지 쌓는다).
    ///
    /// 기본값: null
    ///
    /// 비우면: auto — None=첫수표가 정한다(resolved_options 에 나온다)
    pub target_floor_count: Option<i64>,
    /// 1층 층고 (m). None이면 1층이 필로티(기본)일 때 3.5 — 주차 유효높이 2.3 + 보·설비 — 그 밖의 용도는 구조방식 기본 층고(벽식 3.0/라멘 3.3/철골 3.4).
    ///
    /// 기본값: null
    ///
    /// 비우면: default — None=설명에 적힌 기본 동작
    pub first_floor_height: Option<f64>,
    /// 층번호 → 용도. 예: {1: 'piloti'}. 미지정 시 1층=piloti, 그 외=residential.
    pub floor_use: BTreeMap<String, FloorUse>,
    /// 상층 매스를 반듯하게 세울 기준 방향 — road=주접도변(도로 경계선)과 나란히, sunlight=일조발생라인(정북 인접 대지경계선)과 나란히. None=첫수표가 정한다.
    ///
    /// 기본값: null
    ///
    /// 비우면: auto — None=첫수표가 정한다(resolved_options 에 나온다)
    pub mass_axis: Option<MassAxis>,
}

impl Default for Massing {
    fn default() -> Self {
        Self {
            target_floor_count: None,
            first_floor_height: None,
            floor_use: BTreeMap::new(),
            mass_axis: None,
        }
    }
}

/// 창호 사양 표준 — 창·문 유형마다 하나. 엔진이 창·문 userData(`frame`·`glazing`·`u_value`·`finish`·`fire_door`)를 여기서
/// 채운다. 창호일람표(차하 A10 식: 타입 / 유리 / 기타)의 "프레임·유리" 열, 단열계획도·IFC `ThermalTransmittance` 의 창 U값이
/// 이 표에서 나온다 — 지금 IFC 는 1.5 를 박아 쓴다.
///
/// 기본값은 **초안** — 구의동 57-93 차하 실시설계도서 A10.10~12(2025-04: 알루미늄 로이 삼중유리 1.411~1.421, 세대현관 갑종
/// 방화문/단열문, 공동현관 단열 자동문, 실내 목재 ABS, 철재 여닫이)에서 뽑았고 소장 확인 전이다. 사업마다 고르는 값이 아니라
/// 회사가 정하는 값이라 `standards` 에 둔다(2026-10-17, 0.1.4).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct Openings {
    /// 창(전부).
    pub window: WindowSpec,
    /// 세대 현관문.
    pub entrance_door: EntranceDoorSpec,
    /// 공동현관문.
    pub common_door: CommonDoorSpec,
    /// 세대 안 문(욕실 등).
    pub interior_door: InteriorDoorSpec,
    /// 기계실·옥상 등 철재문.
    pub service_door: ServiceDoorSpec,
}

impl Default for Openings {
    fn default() -> Self {
        Self {
            window: WindowSpec::default(),
            entrance_door: EntranceDoorSpec::default(),
            common_door: CommonDoorSpec::default(),
            interior_door: InteriorDoorSpec::default(),
            service_door: ServiceDoorSpec::default(),
        }
    }
}

/// 주차 — 어떤 축으로 어디에 깔까. 대수는 결과다(법정 대수는 regulations.ratio_mode).
///
/// 법정 수치(칸 2.5×5.0·차로 6.0·총 8대 캡·그룹 5대 등)는 옵션이 아니라 엔진 상수다
/// (주차장법 시행규칙 — 법이 정하면 상수, 설계자가 고르면 옵션).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct Parking {
    /// 내부 차로 주차 각도. 45/60=사선(fishbone) — 차로폭은 주차장법 시행규칙 11조⑤1호 법정값(45° 3.5m·60° 4.0m), 연접(back) 없음, 막다른 차로라 일방 진입·후진 퇴출 전제. 90=직각(차로 6m). None=첫수표가 정한다(현행 90). 사선 순차 평가는 2026-09-19에 제거됐다. 외부 도로변 주차는 항상 직각(11조⑤2호 — 도로를 차로로 쓰는 형식은 직각·평행뿐)이라 inner 모드에만 의미.
    ///
    /// 허용값: 45 · 60 · 90
    ///
    /// 기본값: null
    ///
    /// 비우면: auto — None=첫수표가 정한다(resolved_options 에 나온다)
    pub parking_angle: Option<i64>,
    /// 평행주차 열 — None=법 폴백(직각 배치가 법정 대수에 못 미칠 때만 평행 열을 쓴다, 첫수표 행 아님). True=평행 열을 형태로 선택. False=쓰지 않음.
    ///
    /// 기본값: null
    ///
    /// 비우면: law — None=법이 정한다
    pub parallel: Option<bool>,
    /// 연접(직렬 2단) 백칸 허용 (제11조⑤4호). 법 행: 법정 대수 ≤ 8 이면 허용(11조⑤4호), None=첫수표가 정한다.
    ///
    /// 기본값: null
    ///
    /// 비우면: auto — None=첫수표가 정한다(resolved_options 에 나온다)
    pub tandem: Option<bool>,
    /// 보행통로 출구 도로변 인덱스 (필지 폴리곤 기준). None=자동(최근접 도로변).
    ///
    /// 기본값: null
    ///
    /// 비우면: law — None=법이 정한다
    pub exit_road: Option<i64>,
    /// 주차 버블 — (진입 도로 방위, road|yard|aisle) 튜플의 배열. 위상만 적는다 — 칸 수·면 자리·정렬은 대수가 결과이듯 엔진이 정한다. 배열은 명령 순서가 아니라 하나의 그림이다 — 엔진이 전체를 보고 한 번에 푼다(보행로 띠는 늘 먼저 선다). 셋 다 「도로와 이어진다」가 뜻 안에 있다 — 도로와 끊긴 마당은 yard 가 아니다. 긋는 것은 목뿐이다 — 목은 차가 지나가기만 하는 통로라 차 한 폭(2.5m)이면 되고, 6m 차로는 긋지 않는다(칸이 들어오면 그 앞 6m 박스들의 합집합이 차로가 된다 — 소장이 차로 면적을 아끼는 방식). 방위는 항상 dir8(null 없음)이며 칸이 모인 쪽이 아니라 그 차로가 도로에서 갈라져 나오는 자리다 — 필지에서 본 접도 구간의 방향으로 도로를 고른다(core_side 와 같은 규칙): 정방위(n·e·s·w)=그 변의 가운데, 대각(ne·se·sw·nw)=그 모서리 쪽 끝(주접도도 그 방위로 적는다). road=도로 자체가 차로 — 대지 안에 차로 없음, 칸은 도로에 붙은 한 줄. aisle=도로에서 대지 안으로 곧게 이어지는 목(차 한 폭~6m) — 칸은 목 양옆에 붙고, 칸 앞 6m 박스들이 차로가 된다. yard=도로에서 들어오는 목 끝에서 여러 방향으로 칸이 붙는 것 — 목 끝 둘레에서 칸 앞 박스들이 마당이 된다. 같은 도로에 둘 이상: road + 같은 방위 yard/aisle 이면 앞줄은 그 차로 자리를 비우고 깐다(목이 앞줄을 가른다). 대지 안 노드 뒤 같은 방위 대지 안 노드는 앞 노드의 차로를 지나서 든다. 한 도로에 둘 이상이면 대각으로 어느 끝인지 가른다. 버블은 선호 — 법정 대수 미달일 때만, 모자란 칸에 한해 버블 밖 도로에 덧붙인다. 예: 성북 [["n","road"],["sw","yard"]] — 북측 도로 앞 줄과 남서측 도로에서 들어가는 마당 · 연희 [["nw","yard"],["sw","yard"]] — 같은 서쪽 도로의 북쪽 끝·남쪽 끝에서 든 마당 둘 · 화곡 1033-19 의 두 대안 [["w","yard"]](서쪽 작은 마당에 칸이 세 면)과 [["w","aisle"]](같은 자리 곧은 차로 두 줄). None=첫수표가 정한다.
    ///
    /// 기본값: null
    ///
    /// 비우면: auto — None=첫수표가 정한다(resolved_options 에 나온다)
    pub parking_graph: Option<Vec<(RoadSide, ParkingKind)>>,
}

impl Default for Parking {
    fn default() -> Self {
        Self {
            parking_angle: None,
            parallel: None,
            tandem: None,
            exit_road: None,
            parking_graph: None,
        }
    }
}

/// 법규 보정 — 법이 정하는 값을 필지 사정으로 덮어쓴다. 평소엔 전부 비워 둔다.
///
/// 수(설계자가 고르는 것)가 아니라 법(용도지역 룩업·조례·시행령)이 틀리거나 완화된
/// 예외 필지에서만 쓴다. 그래서 설계 묶음과 따로 모았다(2026-09-28).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct RegulationOverrides {
    /// 용적률 법정 한도 덮어쓰기 (%) — 지구단위계획·완화 등 용도지역 룩업이 틀린 예외 필지용. None=법이 정한다. (구 이름 far_target)
    ///
    /// 기본값: null
    ///
    /// 비우면: law — None=법이 정한다
    pub far_limit_override: Option<f64>,
    /// 건폐율 법정 한도 덮어쓰기 (%) — 지구단위계획·완화 등 용도지역 룩업이 틀린 예외 필지용. None=법이 정한다. (구 이름 bcr_target)
    ///
    /// 기본값: null
    ///
    /// 비우면: law — None=법이 정한다
    pub bcr_limit_override: Option<f64>,
    /// 방향별 후퇴거리 (m). 예: {'north': 1.5, 'side': 0.8}.
    pub setback_overrides: BTreeMap<String, f64>,
    /// 주차구획 전면선의 주도로 경계 셋백 (m). None=도로산입 derive — 주차장법 시행규칙 11조⑤2호: 직각주차 차로는 도로 포함 6m 이상, 미달분(max(0, 6−실측 도로폭))만큼 후퇴. 12m↑ 도로·폭 미상은 0. 명시(0 포함) 시 그 값 — 설계자가 도로 여건상 밀착·완화를 판단한 의도 기록 (GT 실측: 6m 미만 이면도로에서도 경계 밀착 다수). (구 자리 parking.road_setback)
    ///
    /// 기본값: null
    ///
    /// 비우면: law — None=법이 정한다
    pub road_setback: Option<f64>,
    /// 보행통로 폭 (m). 기본 1.5 (시행령 41조 다세대 유효너비 하한). None=용도별 derive (다세대 1.5 등). (구 자리 circulation.pedestrian_width)
    ///
    /// 기본값: 1.5
    ///
    /// 비우면: default — None=설명에 적힌 기본 동작
    pub pedestrian_width: Option<f64>,
    /// 법정 주차대수 산정 기준 (서울시 주차장 조례). multi_family=공동주택(도시형생활주택·다세대): 30㎡↓ 0.5대, 30~60㎡ 0.8대, 60㎡↑ 1.0대, 합계 올림. non_residential=비공동주택(근생·다가구·다중): 60㎡↓ 0.5대, 60㎡↑ 0.7대, 합계 반올림. (구 자리 parking.ratio_mode)
    ///
    /// 기본값: "multi_family"
    pub ratio_mode: RatioMode,
}

impl Default for RegulationOverrides {
    fn default() -> Self {
        Self {
            far_limit_override: None,
            bcr_limit_override: None,
            setback_overrides: BTreeMap::new(),
            road_setback: None,
            pedestrian_width: Some(1.5),
            ratio_mode: RatioMode::MultiFamily,
        }
    }
}

/// 사업 일정 의도 — 인허가·심의 단계와 단계별 기간.
///
/// 핵심: 착공 전 총 기간(기본설계+심의+허가+실시설계+시공사선정+착공신고)이
/// 토지담보 PF 이자 기간이 된다. 6층↑이면 건축심의·구조굴토심의로 기간이
/// 늘어 이자가 증가 — 이 비용을 사업성에 정직하게 반영하기 위한 layer.
///
/// 원칙: 심의 토글은 None=자동유도(층수·지하 기반), 명시 시 override.
/// 단계 기간은 설계자 조정용 default(개월). 공사기간은 기하 derive.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct Schedule {
    /// 건축심의 시행 여부. None=자동(지상 6층↑ 또는 대로변 건축선후퇴 시 True, 5층 이하 False). 착공 전 기간에 arch_review_mo 가산.
    ///
    /// 기본값: null
    pub arch_review: Option<bool>,
    /// 구조·굴토심의 시행 여부. None=자동(6층↑ 기본 True). 실시설계와 병렬 수행 — 둘 중 긴 쪽이 종료 시점.
    ///
    /// 기본값: null
    pub struct_review: Option<bool>,
    /// 토목감리 적용 여부. None=자동(지하 2개층↑ True). 비용 항목.
    ///
    /// 기본값: null
    pub civil_supervision: Option<bool>,
    /// 기타조사비 (만원) — 문화재·지하철안전도 등 필지별 특수건. None=0.
    ///
    /// 기본값: null
    pub other_survey_cost: Option<f64>,
    /// 기본설계 기간 (개월).
    ///
    /// 기본값: 2.0
    pub basic_design: f64,
    /// 건축심의 기간 (개월). arch_review=True일 때만 가산.
    ///
    /// 기본값: 1.5
    pub arch_review_mo: f64,
    /// 건축허가 기간 (개월).
    ///
    /// 기본값: 1.0
    pub build_permit: f64,
    /// 실시설계 기간 (개월).
    ///
    /// 기본값: 1.0
    pub exec_design: f64,
    /// 구조·굴토심의 기간 (개월). 실시설계와 병렬.
    ///
    /// 기본값: 1.5
    pub struct_review_mo: f64,
    /// 시공사 선정 기간 (개월).
    ///
    /// 기본값: 1.5
    pub constructor_select: f64,
    /// 착공신고 기간 (개월).
    ///
    /// 기본값: 0.5
    pub constr_notice: f64,
    /// 공사기간 (개월). None=2+지상층+지하층×2 자동 derive.
    ///
    /// 기본값: null
    pub construction_months: Option<i64>,
    /// 사업 시작 연월 'YYYY-MM' (기본설계 착수 시점). 재무 숫자엔 영향 없고 현금흐름 달력 라벨용. None=상대 개월(N개월차).
    ///
    /// 기본값: null
    pub start_year_month: Option<String>,
}

impl Default for Schedule {
    fn default() -> Self {
        Self {
            arch_review: None,
            struct_review: None,
            civil_supervision: None,
            other_survey_cost: None,
            basic_design: 2.0,
            arch_review_mo: 1.5,
            build_permit: 1.0,
            exec_design: 1.0,
            struct_review_mo: 1.5,
            constructor_select: 1.5,
            constr_notice: 0.5,
            construction_months: None,
            start_year_month: None,
        }
    }
}

/// 설비·옥상 등 철재문(`door_type` = 기계실·옥상) 사양.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct ServiceDoorSpec {
    /// 문 — 종류·구성.
    ///
    /// 기본값: "철재 여닫이문"
    pub frame: String,
    /// 문 마감.
    ///
    /// 기본값: "ST PL 위 불소수지도장(지정색) / 문짝 단열충진"
    pub finish: String,
}

impl Default for ServiceDoorSpec {
    fn default() -> Self {
        Self {
            frame: "철재 여닫이문".to_string(),
            finish: "ST PL 위 불소수지도장(지정색) / 문짝 단열충진".to_string(),
        }
    }
}

/// 회사 표준 — 사업마다 안 건드리는 값. 소비 UI는 접어 둘 수 있다.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct Standards {
    pub concrete: Concrete,
    pub dimensions: Dimensions,
    pub finishes: Finishes,
    pub openings: Openings,
}

impl Default for Standards {
    fn default() -> Self {
        Self {
            concrete: Concrete::default(),
            dimensions: Dimensions::default(),
            finishes: Finishes::default(),
            openings: Openings::default(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct UnitSpec {
    /// 기준 층당 세대 수. None=첫수표가 정한다 — 층마다 (바닥−코어)/max_net_area 를 반올림한 수(최소 1): 전용 상한 안에서 가장 큰 세대(building-generator #436).
    ///
    /// 기본값: null
    ///
    /// 비우면: auto — None=첫수표가 정한다(resolved_options 에 나온다)
    pub units_per_floor: Option<i64>,
    /// 층별 세대 수 override. 예: {1: 0, 2: 4, 3: 4, 4: 4, 5: 3}. 1층=피로티면 0. units_per_floor보다 우선. 빈 층은 첫수표가 정한다.
    ///
    /// 비우면: auto — None=첫수표가 정한다(resolved_options 에 나온다)
    pub units_by_level: BTreeMap<String, i64>,
    /// 세대 전용면적 상한(㎡, 발코니 제외). 넘는 세대가 나오면 컴파일 에러 UnitAreaExceeded. 기본 60 = 소형주택 선(2026-08-28 변경, 이전 기본은 84). 단지형 다세대(도시형생활주택 전용 85㎡ 이하)로 지을 땐 84, 면적 제한 없는 용도는 None. 상한이 없으면 분할 실패가 조용히 통과한다 — 실측: 상한 없이 돌린 9,067세대 중 84 초과 722(8.0%), 최대 5,431㎡(층 전체가 1세대).
    ///
    /// 기본값: 60.0
    ///
    /// 비우면: default — None=설명에 적힌 기본 동작
    pub max_net_area: Option<f64>,
}

impl Default for UnitSpec {
    fn default() -> Self {
        Self {
            units_per_floor: None,
            units_by_level: BTreeMap::new(),
            max_net_area: Some(60.0),
        }
    }
}

/// 창 사양 — 창호일람표의 "프레임·유리" 두 열. 엔진이 `window.userData.frame·glazing·u_value` 로 그대로 옮긴다.
///
/// 용도마다 모델이 따로인 이유는 `Finishes` 와 같다(언어별 방출기가 한 모델에 한 기본값만 허용).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct WindowSpec {
    /// 프레임 — 재질·구성.
    ///
    /// 기본값: "알루미늄 시스템창 (단열바)"
    pub frame: String,
    /// 유리 구성식.
    ///
    /// 기본값: "THK39 (5LE+12A+5CL+12A+5LE) 로이 삼중유리"
    pub glazing: String,
    /// 창 열관류율 (W/㎡K) — 유리+프레임 전체.
    ///
    /// 기본값: 1.42
    pub u_value: f64,
}

impl Default for WindowSpec {
    fn default() -> Self {
        Self {
            frame: "알루미늄 시스템창 (단열바)".to_string(),
            glazing: "THK39 (5LE+12A+5CL+12A+5LE) 로이 삼중유리".to_string(),
            u_value: 1.42,
        }
    }
}

/// Core.core_side 의 값.
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

/// Circulation.corridor_mode 의 값.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum CorridorMode {
    #[serde(rename = "carve")]
    Carve,
    #[serde(rename = "edge")]
    Edge,
}

/// Exterior.style 의 값.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ExteriorStyle {
    #[serde(rename = "white")]
    White,
    #[serde(rename = "sandstone")]
    Sandstone,
    #[serde(rename = "brick")]
    Brick,
    #[serde(rename = "concrete")]
    Concrete,
}

/// Massing.floor_use 의 값.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum FloorUse {
    #[serde(rename = "piloti")]
    Piloti,
    #[serde(rename = "residential")]
    Residential,
    #[serde(rename = "commercial")]
    Commercial,
    #[serde(rename = "rooftop_garden")]
    RooftopGarden,
    #[serde(rename = "basement_parking")]
    BasementParking,
    #[serde(rename = "basement_storage")]
    BasementStorage,
}

/// Massing.mass_axis 의 값.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum MassAxis {
    #[serde(rename = "road")]
    Road,
    #[serde(rename = "sunlight")]
    Sunlight,
}

/// Parking.parking_graph 의 값.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ParkingKind {
    #[serde(rename = "road")]
    Road,
    #[serde(rename = "yard")]
    Yard,
    #[serde(rename = "aisle")]
    Aisle,
}

/// RegulationOverrides.ratio_mode 의 값.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum RatioMode {
    #[serde(rename = "multi_family")]
    MultiFamily,
    #[serde(rename = "non_residential")]
    NonResidential,
}

/// Parking.parking_graph 의 값.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum RoadSide {
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
}

/// Design.structure 의 값.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Structure {
    #[serde(rename = "wall")]
    Wall,
    #[serde(rename = "rahmen")]
    Rahmen,
    #[serde(rename = "steel")]
    Steel,
}

/// Exterior.window_style 의 값.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum WindowStyle {
    #[serde(rename = "open")]
    Open,
    #[serde(rename = "standard")]
    Standard,
    #[serde(rename = "closed")]
    Closed,
}
