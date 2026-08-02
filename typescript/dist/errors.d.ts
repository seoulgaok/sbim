/**
 * CompileError — sBIM Spatial CSP 위반 데이터 모델 (TypeScript mirror).
 *
 * 단일 진실: Python `seoulgaok_bim_core/errors.py`.
 * 생성기가 compile 시 발화 → api 응답 → 프론트엔드 받아서 UI 표시.
 *
 * 부정 변증법:
 *   silent invalid 금지. 모든 도메인 명제 위반은 explicit CompileError로 표면화.
 */
export type CompileErrorType = "ZoningError" | "EnvelopeError" | "AccessError" | "ParkingError" | "CirculationError" | "StructureError" | "HabitabilityError" | "GeometryError";
export interface CompileError {
    type: CompileErrorType;
    reason: string;
    details: Record<string, unknown>;
    suggestion: string | null;
}
//# sourceMappingURL=errors.d.ts.map