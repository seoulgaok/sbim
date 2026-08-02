/**
 * Seoulgaok BIM core — scheme.json / units.json 데이터 계약의 **단일 진실**.
 *
 * 규율: 생성기가 새 키·userData kind를 방출하려면 여기(+python/types.py)에
 * 먼저 정의하고 sbim을 푸시한 뒤 소비처가 import한다.
 * schema/*.json은 walls/floors/roof 시절의 산물 — 현재 정본은 이 파일이다.
 *
 * 좌표계: 링·점 좌표는 EPSG:5186 절대(parcel_center 더해진 상태).
 * 메시(BufferGeometry positions)만 parcel_center 상대 — 혼동 금지.
 */
export {};
//# sourceMappingURL=types.js.map