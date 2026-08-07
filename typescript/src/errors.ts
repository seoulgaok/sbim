/**
 * CompileError — sBIM Spatial CSP 위반 데이터 모델 (TypeScript mirror).
 *
 * 단일 진실: Python `seoulgaok_bim_core/errors.py`.
 * 생성기가 compile 시 발화 → api 응답 → 프론트엔드 받아서 UI 표시.
 *
 * 부정 변증법:
 *   silent invalid 금지. 모든 도메인 명제 위반은 explicit CompileError로 표면화.
 */

// 생성기(giga)가 **실제로 방출하는** 이름이 정본이다.
//
// 구 어휘는 규제 영역별 분류였다(ZoningError·EnvelopeError·… — "어떤 법을
// 어겼나"). 생성기는 그걸 쓰지 않고 "무엇이 안 됐나" 축으로 자기 이름을 붙여
// 왔고, 교집합 0인 두 어휘가 생겨 이 타입은 죽은 계약이 됐다. nextbase는
// compile_errors를 CompileError[]로 선언하면서 실제로는 개수와 reason만 써서,
// **타입은 통과하는데 값은 계약 밖**이었다(SbimStudio.tsx:685).
//
// 죽은 계약을 살아있는 쪽에 맞춘다. 에러마다 붙일 UI 행동이 이름에서 바로
// 나온다 — 세대 수 늘리기 버튼, 주차 패널 점프, 도달 불가 세대 하이라이트.
export type CompileErrorType =
  | "UnitsInfeasible"       // units_by_level로 명시한 세대 수를 그 층에 못 넣음
  | "UnitUnreachable"       // 문에서 폭 1.2m 경로로 못 닿는 전용 면적 (도달률 < 90%)
  | "UnitAreaExceeded"      // 세대 전용면적 > units.max_net_area (기본 84㎡)
  | "ParkingSufficiency"    // 법정 주차대수 > 이 대지에 배치 가능한 stall 수
  | "FloorCountInfeasible"; // 목표 층수를 정북일조·용적률 아래 못 세움

export interface CompileError {
  type: CompileErrorType;
  reason: string;
  details: Record<string, unknown>;
  suggestion: string | null;
}
