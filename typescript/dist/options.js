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
export {};
//# sourceMappingURL=options.js.map