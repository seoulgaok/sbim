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
/**
 * 선별 기준 → 필지 화면 URL 파라미터 프리셋.
 * 값이 없는 항목은 키 자체를 생략한다 (빈 문자열 필터를 만들지 않기 위해).
 */
export function buildSiteFilterUrlParams(criteria) {
    const params = {};
    if (criteria.minGarea != null && criteria.maxGarea != null) {
        params.groundSpace = `${criteria.minGarea}-${criteria.maxGarea}`;
    }
    if (criteria.minAge != null)
        params.ageRange = `${criteria.minAge}+`;
    if (criteria.zones?.length)
        params.zone = criteria.zones.join(",");
    if (criteria.terrain)
        params.terrainHeight = criteria.terrain;
    if (criteria.useKeywords?.length) {
        params.useEtc = criteria.useKeywords.join(",");
    }
    return params;
}
//# sourceMappingURL=siteFilter.js.map