/**
 * BimCanvas — sbim 데이터(Scheme/Unit/SurroundingBuilding) 기반 R3F 3D 뷰어.
 *
 * nextbase-v3의 BuildingMeshVisualizer에서 UI 패널·차량·문의 다이얼로그·지도
 * underlay를 제거한 슬림 + 시각 풀 버전.
 *
 * 의존성: react, three, @react-three/fiber, @react-three/drei, @seoulgaok/bim-core
 * shadcn / Next.js / lucide / framer-motion 의존 없음.
 */

"use client";

import {
  CameraControls,
  ContactShadows,
  Edges,
  Environment,
  Sky,
} from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import {
  type BufferGeometryData,
  type FloorPlan,
  type Scheme,
  type SurroundingBuilding,
  type Unit,
  convertToThreeGeometry,
} from "@seoulgaok/bim-core";
import { useMemo, useRef, useState } from "react";
import * as THREE from "three";

export interface BimCanvasProps {
  schemeData: Scheme;
  unitsData?: Unit[] | null;
  surroundingsData?: SurroundingBuilding[] | null;
  /** 화면에 띄울 층만 필터 (null/undefined면 전체) */
  selectedFloor?: number | null;
  /** 클래스 (size 등) */
  className?: string;
}

export function BimCanvas({
  schemeData,
  unitsData,
  surroundingsData,
  selectedFloor,
  className,
}: BimCanvasProps): React.JSX.Element {
  const controlsRef = useRef<CameraControls>(null);

  return (
    <div className={className} style={{ width: "100%", height: "100%" }}>
      <Canvas shadows camera={{ position: [80, 80, 80], fov: 45 }}>
        <BuildingScene
          schemeData={schemeData}
          unitsData={unitsData ?? []}
          surroundingsData={surroundingsData ?? []}
          selectedFloor={selectedFloor ?? null}
          controlsRef={controlsRef}
        />
        <CameraControls ref={controlsRef} makeDefault />
        <Environment preset="city" />
      </Canvas>
    </div>
  );
}

/* ============================================================
 * BuildingScene — 환경 + 빌딩 + 주변 건물
 * ============================================================ */

function BuildingScene({
  schemeData,
  unitsData,
  surroundingsData,
  selectedFloor,
  controlsRef,
}: {
  schemeData: Scheme;
  unitsData: Unit[];
  surroundingsData: SurroundingBuilding[];
  selectedFloor: number | null;
  controlsRef: React.RefObject<CameraControls | null>;
}) {
  // 첫 등장 시 시점 부드럽게 이동
  React.useEffect(() => {
    const id = setTimeout(() => {
      controlsRef.current?.setLookAt(80, 80, 80, 0, 5, 0, true);
    }, 600);
    return () => clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const visibleFloorPlans = useMemo(() => {
    if (selectedFloor == null) return schemeData.floor_plans;
    return schemeData.floor_plans.filter(
      (fp) => fp.data.floor_id === selectedFloor,
    );
  }, [schemeData.floor_plans, selectedFloor]);

  return (
    <>
      <SurroundingBuildingsMesh data={surroundingsData} />

      {visibleFloorPlans.map((floorPlan) => {
        const unitsOnThisFloor = unitsData.filter(
          (u) => u.data?.floor_id === floorPlan.data.floor_id,
        );
        return (
          <FloorGroup
            key={`floor-${floorPlan.data.floor_id}`}
            floorPlan={floorPlan}
            unitsOnThisFloor={unitsOnThisFloor}
          />
        );
      })}

      {/* 환경광·태양·역광·접지 그림자 */}
      <Sky
        distance={450000}
        sunPosition={[100, 100, 100]}
        inclination={0.6}
        azimuth={0.25}
        turbidity={10}
        rayleigh={0.5}
      />
      <directionalLight
        position={[500, 500, 0]}
        intensity={1.2}
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
        shadow-camera-far={1000}
        shadow-camera-left={-500}
        shadow-camera-right={500}
        shadow-camera-top={500}
        shadow-camera-bottom={-500}
        shadow-bias={-0.0001}
        color="#FDF4DC"
      />
      <directionalLight
        position={[-100, 80, -100]}
        intensity={0.3}
        color="#CCDFFF"
      />
      <ambientLight intensity={0.4} color="#E6F0FF" />
      <ContactShadows
        position={[0, 0.01, 0]}
        opacity={0.4}
        scale={200}
        blur={3}
        far={300}
        resolution={1024}
        color="#000000"
      />
    </>
  );
}

/* ============================================================
 * SurroundingBuildingsMesh — 주변 건물
 * ============================================================ */

function SurroundingBuildingsMesh({
  data,
}: {
  data: SurroundingBuilding[];
}) {
  const material = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: 0xeeeeee,
        side: THREE.DoubleSide,
        roughness: 0.9,
        metalness: 0,
        transparent: true,
        opacity: 0.8,
      }),
    [],
  );

  if (!data || data.length === 0) return null;

  return (
    <group rotation={[-Math.PI / 2, 0, 0]}>
      {data.map((building, i) => (
        <group key={`surrounding-${i}`}>
          {building.geom?.boundary?.map((g, gi) => {
            const geometry = convertToThreeGeometry(g);
            return (
              <mesh
                key={`surrounding-${i}-${gi}`}
                geometry={geometry}
                material={material}
                castShadow
                receiveShadow
              />
            );
          })}
        </group>
      ))}
    </group>
  );
}

/* ============================================================
 * FloorGroup — 한 층의 walls / floors / roof
 * ============================================================ */

function FloorGroup({
  floorPlan,
  unitsOnThisFloor,
}: {
  floorPlan: FloorPlan;
  unitsOnThisFloor: Unit[];
}) {
  const wallMaterial = useMemo(
    () =>
      new THREE.MeshPhysicalMaterial({
        color: 0xffffff,
        side: THREE.DoubleSide,
        roughness: 0,
        metalness: 0,
        transparent: true,
        opacity: 1,
        clearcoat: 0,
        clearcoatRoughness: 0,
      }),
    [],
  );

  const floorMaterial = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: 0x888888,
        side: THREE.DoubleSide,
        roughness: 0.7,
        metalness: 0.1,
      }),
    [],
  );

  const roofMaterial = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: 0x996633,
        side: THREE.DoubleSide,
        roughness: 0.8,
        metalness: 0.2,
      }),
    [],
  );

  const unitMaterial = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: 0x00ff00,
        transparent: true,
        opacity: 0.1,
      }),
    [],
  );

  return (
    <group rotation={[-Math.PI / 2, 0, 0]}>
      <GeometryGroup
        groups={floorPlan.geom.walls}
        material={wallMaterial}
        groupName="wall"
      />
      <GeometryGroup
        groups={floorPlan.geom.floors}
        material={floorMaterial}
        groupName="floor"
      />
      {floorPlan.geom.roof && (
        <GeometryGroup
          groups={floorPlan.geom.roof}
          material={roofMaterial}
          groupName="roof"
        />
      )}

      {unitsOnThisFloor.map((unit, i) => {
        const id = unit.data?.id ?? `unit-${i}`;
        if (!unit.geom?.boundary) return null;
        return (
          <group key={`unit-${id}`}>
            {unit.geom.boundary.map((g, gi) => {
              const geometry = convertToThreeGeometry(g);
              return (
                <mesh
                  key={`unit-${id}-${gi}`}
                  geometry={geometry}
                  material={unitMaterial}
                />
              );
            })}
          </group>
        );
      })}
    </group>
  );
}

function GeometryGroup({
  groups,
  material,
  groupName,
}: {
  groups: BufferGeometryData[][];
  material: THREE.Material;
  groupName: string;
}) {
  if (!groups || !Array.isArray(groups)) return null;

  return (
    <>
      {groups.map((arr, gi) => (
        <group key={`${groupName}-${gi}`}>
          {arr.map((g, i) => {
            const geometry = convertToThreeGeometry(g);
            return (
              <mesh
                key={`${groupName}-${gi}-${i}`}
                geometry={geometry}
                material={material}
                castShadow
                receiveShadow
              >
                <Edges threshold={15} color="#333333" scale={1.001} />
              </mesh>
            );
          })}
        </group>
      ))}
    </>
  );
}

// react fwd reference for useEffect (avoid circular import in some bundlers)
import * as React from "react";
