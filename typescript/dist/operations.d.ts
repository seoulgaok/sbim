/**
 * Scheme 편집 연산. Python 측 operations.py와 동일한 시그니처를 유지해야 함.
 *
 * 모든 함수는 새 Scheme을 반환 (immutable). 원본 변경 X.
 */
import type { FloorPlan, Scheme } from "./types.js";
export declare function getFloor(scheme: Scheme, floorId: number): FloorPlan | undefined;
export declare function removeFloor(scheme: Scheme, floorId: number): Scheme;
//# sourceMappingURL=operations.d.ts.map