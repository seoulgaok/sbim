/**
 * @seoulgaok/bim-visualizer — entry point
 *
 * 주의: 일부 컴포넌트는 shadcn-ui (`@/components/ui/*`) 및 사용자 컴포넌트를 peer dep로
 * 요구함. 컨슈머 앱(Luis frontend, nextbase-v3)의 path alias가 호환되어야 함.
 * Phase 2에서 prop 기반 / 분리 컨테이너로 리팩토링 예정.
 */

export { default as BuildingMeshVisualizer } from "./BuildingMeshVisualizer.js";
export { default as MapFloor } from "./MapFloor.js";
export { default as VehicleSimulation } from "./VehicleSimulation.js";
export { GeoCoordinateTransformer } from "./GeoCoordinateTransformer.js";
export { useBuildingData } from "./hooks/useBuildingData.js";
