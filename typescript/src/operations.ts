/**
 * Scheme 편집 연산. Python 측 operations.py와 동일한 시그니처를 유지해야 함.
 *
 * 모든 함수는 새 Scheme을 반환 (immutable). 원본 변경 X.
 */

import type { FloorPlan, Scheme } from "./types.js";

export function getFloor(scheme: Scheme, floorId: number): FloorPlan | undefined {
  return scheme.floor_plans.find((fp) => fp.data.floor_id === floorId);
}

export function removeFloor(scheme: Scheme, floorId: number): Scheme {
  return {
    ...scheme,
    floor_plans: scheme.floor_plans.filter((fp) => fp.data.floor_id !== floorId),
  };
}

// TODO: Python 측과 함께 추가 예정 (LoD 200 룰)
// - moveCore(scheme, direction)
// - setFloorType(scheme, floorId, type)
// - setUnitCount(scheme, floorId, count)
// - addWindow(scheme, floorId, wallId, offset)
// - layoutParking(scheme, mode)
