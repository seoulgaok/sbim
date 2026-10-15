/**
 * Seoulgaok BIM core — scheme.json / units.json 데이터 계약의 TS 판.
 *
 * 정본은 python/seoulgaok_bim_core/types.py(pydantic)다. 이 파일은 손으로 맞춘
 * TS 판이고, python/tests/test_types_parity.py 가 두 쪽의 필드 집합이 같은지
 * 지킨다. schema/scheme.schema.json·units.schema.json 은 pydantic 에서 생성된다.
 *
 * 규율: 생성기가 새 키·userData kind를 방출하려면 types.py 에 먼저 정의하고
 * 여기를 맞춘 뒤 sbim을 푸시하고, 소비처가 import한다.
 *
 * 좌표계: 링·점 좌표는 EPSG:5186 절대(parcel_center 더해진 상태).
 * 메시(BufferGeometry positions)만 parcel_center 상대 — 혼동 금지.
 */
export {};
//# sourceMappingURL=types.js.map