/**
 * siteFilter.ts — 대상 필지 선별 기준의 **구조**만 정의하는 래퍼.
 *
 * 무엇을 필터링하는지(필드·URL 파라미터 조립)는 여기 있고,
 * 어떤 값으로 필터링하는지(임계값)는 이 저장소에 두지 않는다 — 사업 정보다.
 * 소비처가 자기 설정에서 SiteFilterCriteria를 만들어 넘긴다.
 *
 * Python 쌍 python/seoulgaok_bim_core/site_filter.py (SQL WHERE 조립).
 * 설정 형식은 examples/site_filter.example.json 참조.
 *
 * 컬럼은 필지 테이블 기준.
 */

/** 필지 선별 기준 — 모든 항목 선택. 빠진 항목은 조건에서 제외된다. */
export interface SiteFilterCriteria {
  /** 대지면적 하한 ㎡ (maxGarea와 함께여야 적용) */
  minGarea?: number;
  /** 대지면적 상한 ㎡ */
  maxGarea?: number;
  /** 노후도 하한 (년) */
  minAge?: number;
  /** 용도지역명 (OR) */
  zones?: readonly string[];
  /** 지형 */
  terrain?: string;
  /** 용도 부분일치 키워드 (OR) */
  useKeywords?: readonly string[];
  /** 제외할 정비구역 유형 — `lands.zone_projects`(물질화 배열)와 겹치면 뺀다.
   *  재개발·재건축은 조합이 통째로 개발할 땅이라 개별 신축 제안이 성립하지 않는다. */
  excludeZoneProjects?: readonly string[];
}

/** 필지 화면 URL 파라미터 — criteria에 있는 항목만 채운다. */
export interface SiteFilterUrlParams {
  groundSpace?: string;
  ageRange?: string;
  zone?: string;
  terrainHeight?: string;
  useEtc?: string;
  /** PostgREST 배열 겹침의 부정 — `not.ov.{...}`.
   *  구역 밖(NULL) 필지도 통과해야 하므로 PostgREST의 `not.ov`를 쓴다
   *  (NULL은 ov가 false라 not.ov가 참). */
  zoneProjects?: string;
}

/**
 * 선별 기준 → 필지 화면 URL 파라미터 프리셋.
 * 값이 없는 항목은 키 자체를 생략한다 (빈 문자열 필터를 만들지 않기 위해).
 */
export function buildSiteFilterUrlParams(
  criteria: SiteFilterCriteria,
): SiteFilterUrlParams {
  const params: SiteFilterUrlParams = {};
  if (criteria.minGarea != null && criteria.maxGarea != null) {
    params.groundSpace = `${criteria.minGarea}-${criteria.maxGarea}`;
  }
  if (criteria.minAge != null) params.ageRange = `${criteria.minAge}+`;
  if (criteria.zones?.length) params.zone = criteria.zones.join(",");
  if (criteria.terrain) params.terrainHeight = criteria.terrain;
  if (criteria.useKeywords?.length) {
    params.useEtc = criteria.useKeywords.join(",");
  }
  if (criteria.excludeZoneProjects?.length) {
    // 값에 쉼표·괄호가 들어간다(`재개발(주택정비형)`). PostgREST 배열 리터럴은
    // 쉼표가 구분자라 각 항목을 큰따옴표로 감싸야 한 항목이 둘로 쪼개지지 않는다.
    const items = criteria.excludeZoneProjects
      .map((v) => `"${v.replace(/(["\\])/g, "\\$1")}"`)
      .join(",");
    params.zoneProjects = `not.ov.{${items}}`;
  }
  return params;
}
