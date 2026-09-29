/**
 * BuildOptions — 속성 창 입력 타입. **생성 파일 — 손으로 고치지 마라.**
 *
 * 정본: python/seoulgaok_bim_core/options.py (pydantic BuildOptions)
 * 생성: cd python && uv run python scripts/gen_build_options.py
 *       (schema/build_options.schema.json 을 거쳐 이 파일을 쓴다)
 *
 * 거의 모든 필드가 옵셔널이다 — 비우면 sbim 기본값(대부분 None=첫수표가 정한다)이 채운다.
 * 필수는 목록 항목 안쪽뿐이다(주차 버블 ParkingNode.kind · ParkingRow.side/stalls).
 * 지운 키(core_along·interior_aisle·far_target …)는 서버가 받아서 버리거나 옮기지만,
 * 새로 보내는 값은 이 모양으로 보낸다.
 */

/**
 * 사업성 — 도면과 무관한 값. 소비 UI는 접어 둘 수 있다.
 */
export interface Business {
  schedule?: Schedule;
  financing?: Financing;
}

/**
 * 동선 — 복도·보행로를 어떻게 낼까. 보행로 폭은 법규 보정(regulations)으로 갔다.
 */
export interface Circulation {
  /**
   * 보행통로 라우팅 — carve=최단, edge=필지 변 추종.
   * @default "carve"
   */
  corridor_mode?: "carve" | "edge";
}

export interface Concrete {
  /**
   * 외벽 두께 (m). 다세대 표준 0.20 (단열 포함).
   * @default 0.2
   */
  wall_thickness?: number;
  /**
   * 층간 슬래브 두께 (m). 실무 스펙 150 (기초는 foundation_thickness 별도).
   * @default 0.15
   */
  slab_thickness?: number;
  /**
   * 세대 **내부** 칸막이 두께 (m). 표준 0.10 (방 분할용).
   * @default 0.1
   */
  interior_wall_thickness?: number;
  /**
   * 세대 간 경계벽·공용부(복도·계단실) 경계벽 두께 (m). 실무 표준 0.20. 법정 하한은 다세대(건축허가)면 건축법 계열 경계벽 기준(철근콘크리트조 10cm 이상)이고, 주택건설기준 14조①1의 15cm는 사업계획승인(30세대 이상) 대상에만 적용된다 — 어느 쪽이든 0.20은 충족. 참조 도면(상도동 214-82) 실측도 전 층 철콘200 단일 — 외벽과 **구조체 두께가 같고** 외기 접면만 단열·마감이 덧붙어 410이 된다. 코어 벽이 층마다 달라 보이는 건 단열 유무 차이지 구조체 차이가 아니다.
   * @default 0.2
   */
  party_wall_thickness?: number;
  /**
   * 지하 외벽(옹벽) 두께 (m). 토압을 받아 지상 외벽보다 두껍다 — 참조 도면 실측 지하1층 '철근콘크리트 300' 6장.
   * @default 0.3
   */
  basement_wall_thickness?: number;
  /**
   * 난간 간살(동자) 단면 한 변 (m). 실무 φ20~50 각살 — 기본 50mm.
   * @default 0.05
   */
  railing_post_size?: number;
  /**
   * 난간 간살 사이 **안목치수** (m). 중심간 피치 = railing_post_size + 이 값. 법정: 우리 대상(도시형생활주택 30세대 미만 = 건축허가)에는 살 간격 규정이 **없다** — 건축법 시행령 40조①은 높이 1.2m만 규정하고, 안목 10cm 규정인 주택건설기준 18조②2는 같은 영 3조(적용범위)상 사업계획승인(30세대 이상) 대상에만 적용된다. 0.12는 영유아 끼임 방지 안전 관행 범위의 값이며, 30세대 이상 단지를 다루게 되면 0.10으로 낮춰야 한다.
   * @default 0.12
   */
  railing_clear?: number;
  /**
   * 옥상·노대 난간 중 **콘크리트 저벽** 높이 (m). 기본 0 = 금속 난간만(동자+상단 손스침 바)으로 법정고 1.2m를 만든다 (시행령 40조①). 저벽(방수턱 등)을 원하면 값을 준다 — 그만큼 동자 구간이 짧아진다.
   * @default 0.0
   */
  parapet_wall_height?: number;
  /**
   * 기둥 단면 한 변 (m). 실무 스펙 600 정사각 — 1층 필로티, 전이보와 접합.
   * @default 0.6
   */
  column_size?: number;
  /**
   * 기초(흙 접함) 슬래브 두께 (m). 층간 슬래브와 별도 — 두께가 다르다.
   * @default 0.6
   */
  foundation_thickness?: number;
  /**
   * 외벽 외단열 두께 (m). 참조 도면 실측 '[외벽] 철콘200 // EPS200'.
   * @default 0.2
   */
  insulation_thickness?: number;
  /**
   * 외부 마감 두께 (m). 재료마다 10~50mm — 기본 STO 10mm.
   * @default 0.01
   */
  finish_thickness?: number;
  /**
   * 외부 마감재 이름 (IFC 레이어셋 명명에 사용).
   * @default "STO"
   */
  finish_name?: string;
  /**
   * 전이보 폭 (m). 필로티 천장(2층 바닥) 600×800 — 실무 스펙.
   * @default 0.6
   */
  transfer_beam_width?: number;
  /**
   * 전이보 춤 (m). 윗층 하중을 기둥/벽으로 전달 — 기둥과 만나야 함.
   * @default 0.8
   */
  transfer_beam_depth?: number;
  /**
   * 일반 보·일조사선 꺾임부 전이보 단면 (m). 600×600 정사각.
   * @default 0.6
   */
  beam_size?: number;
  /**
   * 계단 단높이 상한 (m). 주택 계단 법정 0.18 — 실단높이 = 층고/단수.
   * @default 0.18
   */
  stair_riser_max?: number;
  /**
   * 계단 단너비(디딤판 깊이) (m).
   * @default 0.26
   */
  stair_tread?: number;
  /**
   * 계단판(waist) 두께 (m). 기본 150mm.
   * @default 0.15
   */
  stair_waist?: number;
  /**
   * 콘크리트 ㎥당 단가 (원). 다세대 표준 350만원. 공사비 = total_m3 × price_per_m3.
   * @default 3500000
   */
  price_per_m3?: number;
}

/**
 * 코어 — 무엇을(type) 어디에(core_side) 어느 방향으로(core_rotation) 어느 손잡이로
 * (core_mirror) 앉히는가.
 *
 * 치수는 입력이 아니라 매스+세대프로그램에서 derive된다(삼전 정답: 계단·EV가 16.4m
 * 분리 = 세대 배치 결과). 자리와 배향은 고르는 것이고, 값이 없으면 첫수표가 정한다.
 */
export interface Core {
  /**
   * 코어 형상 타입 (DWG→sbim 코어 라이브러리 — giga core_library.json이 진실). None=auto(매스 형상 prior). 이름은 외곽 형태(세장형·정방형·ㄱ자형)로 가르고, 외곽이 같은 것은 괄호의 계단 형식으로 갈린다. 1=세장형(꺾은계단, 2.8×6.8)·2=세장형(직선계단, 2.8×8.05)·3=세장형·편복도(직선계단, 2.8×10.15, 복도 내장, 층당 5~7세대 — 류상호 '코어 유형 추가' 2026-09; 도면 실측 2.78×9.95로 라이브러리 재추출 대기)·4=정방형(꺾은계단, 5.2×4.7)·5=정방형(직선계단, 5.2×4.7)·6=정방형(ㄱ자계단, 5.3×4.95 — ㄱ자는 외곽이 아니라 계단 모양)·7=ㄱ자형(EV측면, 4.8×5.9 — 외곽이 ㄱ자로 파인 유일한 유형). 대부분 type2(세장 타워, 회전 fit), 넓은 단독 장변접도만 type4/5. 번호는 2026-09 DWG 시트 순서로 재배열됐다(building-generator #190) — 옛 번호로 저장된 값은 migrate_core_type()으로 옮긴다.
   * @default null
   */
  type?: 1 | 2 | 3 | 4 | 5 | 6 | 7 | null;
  /**
   * 코어 자리 (EPSG 절대 방위). 정방위(n·e·s·w)=매스의 그 변 가운데, 대각(ne·nw·se·sw)=그 모서리, c=매스 안쪽(주접도 프레임 축을 따라 매스 경계에서 1.5m 이상 떨어진 자리 — 상층은 코어 양쪽에 편복도가 선다). 그 자리에 코어가 안 들면 폴백 없이 CoreTypeInfeasible. None=첫수표가 정한다.
   * @default null
   */
  core_side?: "n" | "ne" | "e" | "se" | "s" | "sw" | "w" | "nw" | "c" | null;
  /**
   * 코어 배향 — core_side로 정해진 변 기준 절대 회전각. c일 때 기준 변은 주접도 변이다. 0=코어 기준자세 그대로 변에 밀착, 90/180/270=그만큼 회전. 코어는 점대칭이 아니라(계단·EV 한쪽 편재, 복도 한 면 접합, 출입구 면이 방향별로 달라 0·90·180·270이 전부 다른 결과) 절반 지정인 구 core_axis(road/depth)로는 같은 축 위 180° 뒤집기를 표현할 수 없어 네 방위를 전부 받는다. 라이브러리 형상 가로세로와 무관한 앉은 변 기준 절대 표현이라 코어 형상이 바뀌어도 뜻이 유지된다. None=첫수표가 정한다.
   * @default null
   */
  core_rotation?: 0 | 90 | 180 | 270 | null;
  /**
   * 코어 좌우 뒤집기 — true=코어 기준자세를 거울처럼 뒤집은 모양(앉은 변에서 봐서 계단·EV의 좌우가 바뀐 반대 손잡이)으로 앉힌 뒤 core_rotation만큼 돌린다. 회전 네 방위로는 이 모양이 안 나온다 — 회전 180°는 가로·세로를 함께 뒤집어 복도 면까지 옮기지만, 거울은 복도 면을 그대로 두고 좌우만 바꾼다. 회전과 함께 코어가 변에 앉는 여덟 자세를 전부 적는다. false=기준자세 그대로. None=첫수표가 정한다.
   * @default null
   */
  core_mirror?: boolean | null;
  /**
   * 코어(복도) 보행 출입구 수 1|2. 2=코어 문 반대편에도 문 — 보행로가 도로에서 꼬이는 필지(합정동 441-31). None=자동: 둘째 문의 보행로가 첫째보다 뚜렷이 짧을 때만 2. scheme `_pedestrian_paths`로 전부 방출. (multi_road는 차량 진입 옵션 — 별개)
   * @default null
   */
  core_entries?: number | null;
}

/**
 * 이 설계에서 고르는 것. 값이 없으면 첫수표가 정한다.
 *
 * 묶음은 **대상**이다(매스·세대·코어·주차·동선·외장) — 단계로 자르면 같은 대상의
 * 속성이 두 집에 나뉘어 산다(구 GroundFloor가 주차·코어·동선·기둥을 한 서랍에 담았다).
 */
export interface Design {
  massing?: Massing;
  units?: UnitSpec;
  core?: Core;
  parking?: Parking;
  circulation?: Circulation;
  exterior?: Exterior;
  /**
   * 구조 방식 — wall=벽식(현행 다세대 표준)·rahmen=라멘(기둥·보)·steel=철골. 층고와 벽 두께·스팬 기본값이 여기서 derive된다(Standards에서 override 가능). 한 필드 클래스였던 Structure를 스칼라로 폈다.
   * @default "wall"
   */
  structure?: "wall" | "rahmen" | "steel";
  regulations?: RegulationOverrides;
}

/**
 * 구조 치수 표준 — 사업마다 고르는 값이 아니라 회사가 정해 두는 값.
 *
 * 주차 칸·차로 치수(2.5×5.0·6.0)는 주차장법 상수라 엔진이 갖는다 — 옵션이 아니다.
 */
export interface Dimensions {
  /**
   * 기둥 최대 간격 (m).
   * @default 8.0
   */
  max_span?: number;
  /**
   * 코너 캔틸레버 한계 (m).
   * @default 1.2
   */
  cantilever?: number;
  /**
   * 기둥 최소 간격 (m).
   * @default 3.0
   */
  min_col_dist?: number;
  /**
   * 엣지 분할 과밀 방지 하한 (m).
   * @default 4.2
   */
  preferred_min_span?: number;
}

/**
 * 외장 — 외벽 마감과 창 스타일. 한 필드 클래스 둘(Windows·Exterior)을 합쳤다.
 */
export interface Exterior {
  /**
   * 외장재 preset (외벽·천장/테라스 색 페어). white=화이트·라이트그레이, sandstone=사암·웜그레이, brick=벽돌브라운·라이트그레이(default), concrete=노출콘크리트·짙은회색. visualizer가 hex로 매핑.
   * @default "brick"
   */
  style?: "white" | "sandstone" | "brick" | "concrete";
  /**
   * 창 크기 의도 — 법정 채광면적(거실 바닥의 1/10)을 몇 배로 잡을지의 배율. open=넉넉(1.8배), standard=표준(1.35배), closed=최소(1.05배). 창의 위치·개수는 세대가 접한 외벽에서 컴파일러가 derive한다.
   * @default "open"
   */
  window_style?: "open" | "standard" | "closed";
}

/**
 * PF 대출(토지담보·시설자금·준공담보)과 분양 스케줄 의도.
 *
 * 이자 = 대출액 × 금리 × 기간/12. 분양수입은 계약/중도/잔금으로 월별 분배.
 *
 * **금융 조건에는 기본값이 없다(None).** 사업자·시점마다 다른 협상 결과이고,
 * 남의 조건을 조용히 물려받아 사업성을 계산하는 것이 값이 비는 것보다 위험하다.
 * 값은 설정 파일에서 주입한다 — config.py / examples/sbim_config.example.json.
 *
 *     from seoulgaok_bim_core import build_options
 *     opts = build_options()          # sbim_config.json의 financing 블록 적용
 */
export interface Financing {
  /**
   * 토지담보 LTV.
   * @default null
   */
  land_loan_ltv?: number | null;
  /**
   * 토지담보 연이자율.
   * @default null
   */
  land_loan_rate?: number | null;
  /**
   * 시설자금 LTV (직접공사비 기준).
   * @default null
   */
  fac_loan_ltv?: number | null;
  /**
   * 시설자금 연이자율.
   * @default null
   */
  fac_loan_rate?: number | null;
  /**
   * 시설자금 기성고 평균 실사용률 (이자 효율).
   * @default null
   */
  fac_efficiency?: number | null;
  /**
   * 준공담보 연이자율 (담보 확정 → 토지담보 수준).
   * @default null
   */
  post_loan_rate?: number | null;
  /**
   * 준공 후 기간 (개월). 비아파트 = 준공 후 이 기간에 균등 분양·매각.
   * @default null
   */
  post_months?: number | null;
  /**
   * 대출 취급수수료율 (토담+시설 대출액).
   * @default null
   */
  handling_fee_rate?: number | null;
  /**
   * 취급수수료 적용 여부. True=적용.
   * @default false
   */
  handling_fee_on?: boolean;
}

export interface Massing {
  /**
   * 목표 층수. None=사선·일조·FAR 한계까지 자동 stack. 사선제한으로 미달 가능.
   * @default null
   */
  target_floor_count?: number | null;
  /**
   * 1층 층고 (m). 필로티 4m+ 권장. None이면 구조방식 기본 층고(structure: 벽식 3.0/라멘 3.3)와 동일.
   * @default null
   */
  first_floor_height?: number | null;
  /**
   * 층번호 → 용도. 예: {1: 'piloti'}. 미지정 시 1층=piloti, 그 외=residential.
   */
  floor_use?: Record<string, "piloti" | "residential" | "commercial" | "rooftop_garden" | "basement_parking" | "basement_storage">;
  /**
   * 상층 매스를 반듯하게 세울 기준 방향 — road=주접도변(도로 경계선)과 나란히, sunlight=일조발생라인(정북 인접 대지경계선)과 나란히. None=첫수표가 정한다.
   * @default null
   */
  mass_axis?: "road" | "sunlight" | null;
}

/**
 * 주차 — 어떤 축으로 어디에 깔까. 대수는 결과다(법정 대수는 regulations.ratio_mode).
 *
 * 법정 수치(칸 2.5×5.0·차로 6.0·총 8대 캡·그룹 5대 등)는 옵션이 아니라 엔진 상수다
 * (주차장법 시행규칙 — 법이 정하면 상수, 설계자가 고르면 옵션).
 */
export interface Parking {
  /**
   * 주차 행 배치 축 — road=주접도 프레임(도로에 기대 깐다), inner=대지 안에 차로를 내고 그 차로 기준으로 깐다 — 까는 방식(직각·평행·경계 한 줄·회전 마당과 그 섞음)은 첫수표가 정한다. None=첫수표가 정한다. 대부분 None. legacy "auto"는 None과 같은 뜻이라 받아서 접는다. 구 "core"(코어 격자 정렬)는 제거됐다 — REF 30필지에서 엔진이 한 번도 고르지 않았고, 뜻은 매스 격자 정렬인데 이름이 구현(코어 사각형에서 방향을 빌림)을 드러냈다. 건물이 비뚤면 road/inner 안에서 기울여 깐다(#10 ④⑤). 구 interior_aisle(True/False)은 이 필드로 흡수됐다 — inner/road.
   * @default null
   * @auto None=자동
   */
  parking_axis?: "road" | "inner" | null;
  /**
   * 내부 차로(parking_axis=inner) 주차 각도. 45/60=사선(fishbone) — 차로폭은 주차장법 시행규칙 11조⑤1호 법정값(45° 3.5m·60° 4.0m), 연접(back) 없음, 막다른 차로라 일방 진입·후진 퇴출 전제. 90=직각(차로 6m). None=첫수표가 정한다(현행 90). 사선 순차 평가는 2026-09-19에 제거됐다. 외부 도로변 주차는 항상 직각(11조⑤2호 — 도로를 차로로 쓰는 형식은 직각·평행뿐)이라 inner 모드에만 의미.
   * @default null
   */
  parking_angle?: 45 | 60 | 90 | null;
  /**
   * 평행주차 열 사용 — True=평행 열을 쓴다(직각이 안 들어가는 폭에서 평행으로), False=평행 열을 쓰지 않는다. None=첫수표·엔진 규칙이 정한다.
   * @default null
   */
  parallel?: boolean | null;
  /**
   * 주접도 변 인덱스 (필지 폴리곤 기준). None=최장 접도변 자동.
   * @default null
   */
  road_edge?: number | null;
  /**
   * 다중도로 주차 — 주접도 외 잔여 접도변(넓은급→긴변, 최대 3)에 추가 주차. None=첫수표가 정한다. (구 이름 entry2 — '인접 2차 진입'에서 ≤3 도로로 일반화됐는데 이름이 2에 남아 있었다.) parking_graph 가 있으면 읽지 않는다 — 어느 도로에 몇 대인지가 그 road 노드다.
   * @default null
   * @auto None=자동
   */
  multi_road?: boolean | null;
  /**
   * 연접(직렬 2단) 백칸 허용 (제11조⑤4호). None=법정 대수 부족 시 자동.
   * @default null
   */
  tandem?: boolean | null;
  /**
   * 보행통로 출구 도로변 인덱스 (필지 폴리곤 기준). None=자동(최근접 도로변).
   * @default null
   */
  exit_road?: number | null;
  /**
   * 주차 버블 — 칸을 어느 차로에 몇 대씩 붙이는가. 목록 순서가 놓는 순서다(보행로 띠는 늘 먼저 선다). road=도로가 곧 차로, yard=대지 안 차로(곧은 차로는 면이 나란한 yard). 좌표·치수는 없다 — 칸 방향은 코어(건물) 축이고 벽을 따르는 면만 align=wall. 값이 있으면 multi_road 는 읽지 않는다. None=첫수표가 정한다.
   * @default null
   * @auto None=자동
   */
  parking_graph?: ParkingNode[] | null;
}

/**
 * 주차 버블 하나 — 칸이 어느 차로를 향하는가.
 *
 * road=도로가 곧 차로(주차장법 시행규칙 11조⑤2호 — 칸 앞 띠가 도로에 닿는다),
 * yard=대지 안 차로(11조⑤1호). 곧은 차로는 이름을 따로 두지 않는다 — 면이 나란한
 * (left·right 만 있거나 면이 하나뿐인) yard 다. REF 35필지의 곧은 차로 10조각이 전부
 * 이 꼴이었다(「곧은 차로 = 자란 마당」).
 *
 * 칸이 향하는 곳은 필드가 아니다 — 노드 소속이 곧 그것이다(road 칸은 도로, yard 칸은
 * 제 마당). 코어·보행로도 노드가 아니다 — 코어는 Core 가, 보행로는 코어 문·exit_road 가
 * 정해 칸보다 먼저 서고, 버블은 그 둘을 장애물로 받는다.
 */
export interface ParkingNode {
  /**
   * road=도로가 곧 차로(칸이 도로를 향한다) · yard=대지 안 차로(칸이 마당을 향한다). 곧은 차로는 면이 나란한 yard 다.
   */
  kind: "road" | "yard";
  /**
   * 진입 도로 (EPSG 절대 방위, core_side 와 같은 꼴). 접도 변 가운데 바깥쪽이 이 방위와 가장 나란한 변의 도로다 — 같은 방위에 도로가 둘이면 도로 앞 순서(frontage)가 앞선 쪽. None=주접도(road_edge 가 정한 변).
   * @default null
   */
  road_side?: "n" | "ne" | "e" | "se" | "s" | "sw" | "w" | "nw" | null;
  /**
   * 이 버블의 칸 수 — 좌표가 아니라 개수다(연접 뒤칸·평행칸 포함). yard 에 rows 가 있으면 그 합과 같아야 한다. None=rows 합, rows 도 없으면 법정 대수까지.
   * @default null
   */
  stalls?: number | null;
  /**
   * yard 전용 — 마당 면 목록. 적힌 순서가 세우는 순서, 한 자리에 면 하나. None=far→left→right→near 고정 순서로 면을 하나씩 더한다.
   * @default null
   */
  rows?: ParkingRow[] | null;
  /**
   * yard 전용 — 도로에 바로 닿지 않는 마당이 지나는 앞 마당의 목록 번호(0부터). 앞에 적힌 yard 만 가리킨다. None=도로에서 곧장 들어간다.
   * @default null
   */
  via?: number | null;
  /**
   * 이 버블에 연접(직렬 2단) 뒤칸 허용. None=parking.tandem 을 따른다.
   * @default null
   */
  tandem?: boolean | null;
}

/**
 * 마당의 한 면 — 칸 줄이 등을 댄 자리. 칸은 자기 마당을 향한다.
 *
 * 치수·좌표는 없다. 칸·진입 띠(직각 6m·평행 4m)는 법 상수고, 면 위 어디서부터 칸을
 * 잇는지도 엔진 규칙이다 — 좌표를 옵션에 넣으면 속성 창이 도면이 된다.
 */
export interface ParkingRow {
  /**
   * 면의 자리 — 진입 도로에서 대지 안을 볼 때. far=도로 맞은편 · left/right=옆 · near=도로 쪽(도로에 등을 대고 마당을 본다).
   */
  side: "far" | "left" | "right" | "near";
  /**
   * 이 면의 칸 수 — 연접 뒤칸·평행칸을 포함한 개수.
   */
  stalls: number;
  /**
   * 칸 줄의 방향 — wall=등 댄 필지 변을 따른다(사선 변에 붙은 칸). None=코어(건물) 축을 따른다 — 소장 도면 안쪽 칸 대부분이 이쪽이다.
   * @default null
   */
  align?: "wall" | null;
}

/**
 * 법규 보정 — 법이 정하는 값을 필지 사정으로 덮어쓴다. 평소엔 전부 비워 둔다.
 *
 * 수(설계자가 고르는 것)가 아니라 법(용도지역 룩업·조례·시행령)이 틀리거나 완화된
 * 예외 필지에서만 쓴다. 그래서 설계 묶음과 따로 모았다(2026-09-28).
 */
export interface RegulationOverrides {
  /**
   * 용적률 법정 한도 덮어쓰기 (%) — 지구단위계획·완화 등 용도지역 룩업이 틀린 예외 필지용. None=법이 정한다. (구 이름 far_target)
   * @default null
   */
  far_limit_override?: number | null;
  /**
   * 건폐율 법정 한도 덮어쓰기 (%) — 지구단위계획·완화 등 용도지역 룩업이 틀린 예외 필지용. None=법이 정한다. (구 이름 bcr_target)
   * @default null
   */
  bcr_limit_override?: number | null;
  /**
   * 방향별 후퇴거리 (m). 예: {'north': 1.5, 'side': 0.8}.
   */
  setback_overrides?: Record<string, number>;
  /**
   * 주차구획 전면선의 주도로 경계 셋백 (m). None=도로산입 derive — 주차장법 시행규칙 11조⑤2호: 직각주차 차로는 도로 포함 6m 이상, 미달분(max(0, 6−실측 도로폭))만큼 후퇴. 12m↑ 도로·폭 미상은 0. 명시(0 포함) 시 그 값 — 설계자가 도로 여건상 밀착·완화를 판단한 의도 기록 (GT 실측: 6m 미만 이면도로에서도 경계 밀착 다수). (구 자리 parking.road_setback)
   * @default null
   */
  road_setback?: number | null;
  /**
   * 보행통로 폭 (m). 기본 1.5 (시행령 41조 다세대 유효너비 하한). None=용도별 derive (다세대 1.7 등). (구 자리 circulation.pedestrian_width)
   * @default 1.5
   */
  pedestrian_width?: number | null;
  /**
   * 법정 주차대수 산정 기준 (서울시 주차장 조례). multi_family=공동주택(도시형생활주택·다세대): 30㎡↓ 0.5대, 30~60㎡ 0.8대, 60㎡↑ 1.0대, 합계 올림. non_residential=비공동주택(근생·다가구·다중): 60㎡↓ 0.5대, 60㎡↑ 0.7대, 합계 반올림. (구 자리 parking.ratio_mode)
   * @default "multi_family"
   */
  ratio_mode?: "multi_family" | "non_residential";
}

/**
 * 사업 일정 의도 — 인허가·심의 단계와 단계별 기간.
 *
 * 핵심: 착공 전 총 기간(기본설계+심의+허가+실시설계+시공사선정+착공신고)이
 * 토지담보 PF 이자 기간이 된다. 6층↑이면 건축심의·구조굴토심의로 기간이
 * 늘어 이자가 증가 — 이 비용을 사업성에 정직하게 반영하기 위한 layer.
 *
 * 원칙: 심의 토글은 None=자동유도(층수·지하 기반), 명시 시 override.
 * 단계 기간은 설계자 조정용 default(개월). 공사기간은 기하 derive.
 */
export interface Schedule {
  /**
   * 건축심의 시행 여부. None=자동(지상 6층↑ 또는 대로변 건축선후퇴 시 True, 5층 이하 False). 착공 전 기간에 arch_review_mo 가산.
   * @default null
   */
  arch_review?: boolean | null;
  /**
   * 구조·굴토심의 시행 여부. None=자동(6층↑ 기본 True). 실시설계와 병렬 수행 — 둘 중 긴 쪽이 종료 시점.
   * @default null
   */
  struct_review?: boolean | null;
  /**
   * 토목감리 적용 여부. None=자동(지하 2개층↑ True). 비용 항목.
   * @default null
   */
  civil_supervision?: boolean | null;
  /**
   * 기타조사비 (만원) — 문화재·지하철안전도 등 필지별 특수건. None=0.
   * @default null
   */
  other_survey_cost?: number | null;
  /**
   * 기본설계 기간 (개월).
   * @default 2.0
   */
  basic_design?: number;
  /**
   * 건축심의 기간 (개월). arch_review=True일 때만 가산.
   * @default 1.5
   */
  arch_review_mo?: number;
  /**
   * 건축허가 기간 (개월).
   * @default 1.0
   */
  build_permit?: number;
  /**
   * 실시설계 기간 (개월).
   * @default 1.0
   */
  exec_design?: number;
  /**
   * 구조·굴토심의 기간 (개월). 실시설계와 병렬.
   * @default 1.5
   */
  struct_review_mo?: number;
  /**
   * 시공사 선정 기간 (개월).
   * @default 1.5
   */
  constructor_select?: number;
  /**
   * 착공신고 기간 (개월).
   * @default 0.5
   */
  constr_notice?: number;
  /**
   * 공사기간 (개월). None=2+지상층+지하층×2 자동 derive.
   * @default null
   */
  construction_months?: number | null;
  /**
   * 사업 시작 연월 'YYYY-MM' (기본설계 착수 시점). 재무 숫자엔 영향 없고 현금흐름 달력 라벨용. None=상대 개월(N개월차).
   * @default null
   */
  start_year_month?: string | null;
}

/**
 * 회사 표준 — 사업마다 안 건드리는 값. 소비 UI는 접어 둘 수 있다.
 */
export interface Standards {
  concrete?: Concrete;
  dimensions?: Dimensions;
}

export interface UnitSpec {
  /**
   * 기준 층당 세대 수. None=면적 기반 자동(45㎡/세대).
   * @default null
   */
  units_per_floor?: number | null;
  /**
   * 층별 세대 수 override. 예: {1: 0, 2: 4, 3: 4, 4: 4, 5: 3}. 1층=피로티면 0. units_per_floor보다 우선.
   */
  units_by_level?: Record<string, number>;
  /**
   * 세대 전용면적 상한(㎡, 발코니 제외). 넘는 세대가 나오면 컴파일 에러 UnitAreaExceeded. 기본 60 = 소형주택 선(2026-08-28 변경, 이전 기본은 84). 단지형 다세대(도시형생활주택 전용 85㎡ 이하)로 지을 땐 84, 면적 제한 없는 용도는 None. 상한이 없으면 분할 실패가 조용히 통과한다 — 실측: 상한 없이 돌린 9,067세대 중 84 초과 722(8.0%), 최대 5,431㎡(층 전체가 1세대).
   * @default 60.0
   */
  max_net_area?: number | null;
}

/**
 * 다세대주택 파라메트릭 설계 입력 — 속성 창.
 *
 * 세 묶음이다: `design`(이 설계에서 고르는 것) · `standards`(회사 표준) ·
 * `business`(사업성). 도면 하나를 만들 때 마주하는 건 `design`뿐이다.
 *
 * 구 평면 모양(`ground_floor`·`concrete`·`schedule` …)으로 들어와도 받아서 옮긴다.
 */
export interface BuildOptions {
  /**
   * 합필 필지 PNU 리스트 (19자리). 단일 필지면 [pnu] 1개. 다중 필지는 합필(union) 전제 — 컴파일러가 geometry union 후 처리.
   */
  land_ids?: string[];
  /**
   * 대표 필지 PNU. 보고서·Studio의 '대표 주소' 출처. land_ids 중 하나여야 함. 빈 문자열이면 land_ids[0] 사용.
   * @default ""
   */
  primary_land_id?: string;
  design?: Design;
  standards?: Standards;
  business?: Business;
}
