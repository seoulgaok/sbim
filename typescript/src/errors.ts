/**
 * CompileError — sBIM Spatial CSP 위반 데이터 모델 (TypeScript mirror).
 *
 * 단일 진실: Python `seoulgaok_bim_core/errors.py`.
 * giga가 compile 시 발화 → api 응답 → nextbase 받아서 UI 표시.
 *
 * 부정 변증법:
 *   silent invalid 금지. 모든 도메인 명제 위반은 explicit CompileError로 표면화.
 */

export type CompileErrorType =
  | "ZoningError"        // 용적률·건폐율 한도 초과
  | "EnvelopeError"      // 정북사선·가각전제
  | "AccessError"        // 4m 도로 미달 (건축법 44조)
  | "ParkingError"       // 법정 주차 > 가능 stall
  | "CirculationError"   // 코어 진입 동선 / 4각 충돌
  | "StructureError"     // 기둥 stall 침범
  | "HabitabilityError"  // 도시형생활주택 net 14㎡ 미달
  | "GeometryError";     // polygon degenerate / self-intersect

export interface CompileError {
  type: CompileErrorType;
  reason: string;
  details: Record<string, unknown>;
  suggestion: string | null;
}
