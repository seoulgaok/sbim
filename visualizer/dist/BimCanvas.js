/**
 * BimCanvas — sbim 데이터(Scheme/Unit/SurroundingBuilding) 기반 R3F 3D 뷰어.
 *
 * 프론트엔드의 BuildingMeshVisualizer에서 UI 패널·차량·문의 다이얼로그·지도
 * underlay를 제거한 슬림 + 시각 풀 버전.
 *
 * 의존성: react, three, @react-three/fiber, @react-three/drei, @seoulgaok/bim-core
 * shadcn / Next.js / lucide / framer-motion 의존 없음.
 */
"use client";
import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { CameraControls, ContactShadows, Edges, Environment, Sky, } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { convertToThreeGeometry, } from "@seoulgaok/bim-core";
import { useMemo, useRef } from "react";
import * as THREE from "three";
export function BimCanvas({ schemeData, unitsData, surroundingsData, selectedFloor, className, }) {
    const controlsRef = useRef(null);
    return (_jsx("div", { className: className, style: { width: "100%", height: "100%" }, children: _jsxs(Canvas, { shadows: true, camera: { position: [80, 80, 80], fov: 45 }, 
            // preserveDrawingBuffer: 캔버스 픽셀을 스왑 후에도 유지 — 스크린샷·
            // toDataURL 캡처가 검은 화면으로 나오는 것을 막는다 (약간의 메모리 비용)
            gl: { preserveDrawingBuffer: true }, children: [_jsx(BuildingScene, { schemeData: schemeData, unitsData: unitsData ?? [], surroundingsData: surroundingsData ?? [], selectedFloor: selectedFloor ?? null, controlsRef: controlsRef }), _jsx(CameraControls, { ref: controlsRef, makeDefault: true }), _jsx(Environment, { preset: "city" })] }) }));
}
/* ============================================================
 * BuildingScene — 환경 + 빌딩 + 주변 건물
 * ============================================================ */
function BuildingScene({ schemeData, unitsData, surroundingsData, selectedFloor, controlsRef, }) {
    const buildingRef = useRef(null);
    // 첫 등장 시 건물이 화면에 담기도록 시점 이동.
    // 고정 좌표(80,80,80)를 쓰면 소형 필지는 점처럼, 대형은 잘려 보인다.
    // Sky·바닥 plane은 박스에 넣으면 안 되므로 건물 그룹만 잰다.
    React.useEffect(() => {
        const id = setTimeout(() => {
            const g = buildingRef.current;
            if (!g)
                return;
            const box = new THREE.Box3().setFromObject(g);
            if (box.isEmpty())
                return;
            const size = box.getSize(new THREE.Vector3());
            const radius = Math.max(size.x, size.y, size.z);
            if (!Number.isFinite(radius) || radius <= 0)
                return;
            const c = box.getCenter(new THREE.Vector3());
            const d = radius * 1.25 + 6; // 여백
            void controlsRef.current?.setLookAt(c.x + d, c.y + d * 0.7, c.z + d, c.x, c.y, c.z, true);
        }, 600);
        return () => clearTimeout(id);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [schemeData]);
    const visibleFloorPlans = useMemo(() => {
        if (selectedFloor == null)
            return schemeData.floor_plans;
        return schemeData.floor_plans.filter((fp) => fp.data.floor_id === selectedFloor);
    }, [schemeData.floor_plans, selectedFloor]);
    return (_jsxs(_Fragment, { children: [_jsxs("group", { ref: buildingRef, children: [_jsx(SurroundingBuildingsMesh, { data: surroundingsData }), visibleFloorPlans.map((floorPlan) => {
                        const unitsOnThisFloor = unitsData.filter((u) => u.data?.floor_id === floorPlan.data.floor_id);
                        return (_jsx(FloorGroup, { floorPlan: floorPlan, unitsOnThisFloor: unitsOnThisFloor, cutaway: selectedFloor != null }, `floor-${floorPlan.data.floor_id}`));
                    })] }), _jsx(Sky, { distance: 450000, sunPosition: [100, 100, 100], inclination: 0.6, azimuth: 0.25, turbidity: 10, rayleigh: 0.5 }), _jsx("directionalLight", { position: [500, 500, 0], intensity: 1.2, castShadow: true, "shadow-mapSize-width": 2048, "shadow-mapSize-height": 2048, "shadow-camera-far": 1000, "shadow-camera-left": -500, "shadow-camera-right": 500, "shadow-camera-top": 500, "shadow-camera-bottom": -500, "shadow-bias": -0.0001, color: "#FDF4DC" }), _jsx("directionalLight", { position: [-100, 80, -100], intensity: 0.3, color: "#CCDFFF" }), _jsx("ambientLight", { intensity: 0.4, color: "#E6F0FF" }), _jsx(ContactShadows, { position: [0, 0.01, 0], opacity: 0.4, scale: 200, blur: 3, far: 300, resolution: 1024, color: "#000000" })] }));
}
/* ============================================================
 * SurroundingBuildingsMesh — 주변 건물
 * ============================================================ */
function SurroundingBuildingsMesh({ data, }) {
    const material = useMemo(() => new THREE.MeshStandardMaterial({
        color: 0xeeeeee,
        side: THREE.DoubleSide,
        roughness: 0.9,
        metalness: 0,
        transparent: true,
        opacity: 0.8,
    }), []);
    if (!data || data.length === 0)
        return null;
    return (_jsx("group", { rotation: [-Math.PI / 2, 0, 0], children: data.map((building, i) => (_jsx("group", { children: building.geom?.boundary?.map((g, gi) => {
                const geometry = convertToThreeGeometry(g);
                return (_jsx("mesh", { geometry: geometry, material: material, castShadow: true, receiveShadow: true }, `surrounding-${i}-${gi}`));
            }) }, `surrounding-${i}`))) }));
}
/* ============================================================
 * FloorGroup — 한 층의 walls / floors / roof
 * ============================================================ */
function FloorGroup({ floorPlan, unitsOnThisFloor, cutaway = false, }) {
    const wallMaterial = useMemo(() => new THREE.MeshPhysicalMaterial({
        color: 0xffffff,
        side: THREE.DoubleSide,
        roughness: 0,
        metalness: 0,
        transparent: true,
        opacity: 1,
        clearcoat: 0,
        clearcoatRoughness: 0,
    }), []);
    const floorMaterial = useMemo(() => new THREE.MeshStandardMaterial({
        color: 0x888888,
        side: THREE.DoubleSide,
        roughness: 0.7,
        metalness: 0.1,
    }), []);
    const roofMaterial = useMemo(() => new THREE.MeshStandardMaterial({
        color: 0x996633,
        side: THREE.DoubleSide,
        roughness: 0.8,
        metalness: 0.2,
    }), []);
    // 전체 보기에서는 매스를 가리지 않도록 거의 투명, 단일 층에서는 세대 구획이
    // 읽히도록 진하게. 0.1은 층 하나만 볼 때 사실상 보이지 않는다.
    const unitMaterial = useMemo(() => new THREE.MeshStandardMaterial({
        color: cutaway ? 0x4da6ff : 0x00ff00,
        transparent: true,
        opacity: cutaway ? 0.35 : 0.1,
        side: THREE.DoubleSide,
    }), [cutaway]);
    return (_jsxs("group", { rotation: [-Math.PI / 2, 0, 0], children: [_jsx(GeometryGroup, { groups: floorPlan.geom.walls, material: wallMaterial, groupName: "wall" }), _jsx(GeometryGroup, { groups: floorPlan.geom.floors, material: floorMaterial, groupName: "floor" }), floorPlan.geom.roof && !cutaway && (_jsx(GeometryGroup, { groups: floorPlan.geom.roof, material: roofMaterial, groupName: "roof" })), unitsOnThisFloor.map((unit, i) => {
                const id = unit.data?.id ?? `unit-${i}`;
                if (!unit.geom?.boundary)
                    return null;
                return (_jsx("group", { children: unit.geom.boundary.map((g, gi) => {
                        const geometry = convertToThreeGeometry(g);
                        return (_jsx("mesh", { geometry: geometry, material: unitMaterial }, `unit-${id}-${gi}`));
                    }) }, `unit-${id}`));
            })] }));
}
function GeometryGroup({ groups, material, groupName, }) {
    if (!groups || !Array.isArray(groups))
        return null;
    return (_jsx(_Fragment, { children: groups.map((arr, gi) => (_jsx("group", { children: arr.map((g, i) => {
                const geometry = convertToThreeGeometry(g);
                return (_jsx("mesh", { geometry: geometry, material: material, castShadow: true, receiveShadow: true, children: _jsx(Edges, { threshold: 15, color: "#333333", scale: 1.001 }) }, `${groupName}-${gi}-${i}`));
            }) }, `${groupName}-${gi}`))) }));
}
// react fwd reference for useEffect (avoid circular import in some bundlers)
import * as React from "react";
//# sourceMappingURL=BimCanvas.js.map