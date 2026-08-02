/**
 * BufferGeometryData ↔ THREE.BufferGeometry 변환 헬퍼.
 * 프론트엔드에서 추출.
 */
import * as THREE from "three";
import type { BufferGeometryData } from "./types.js";
/** BufferGeometryData → THREE.BufferGeometry */
export declare function convertToThreeGeometry(data: BufferGeometryData): THREE.BufferGeometry;
/** BufferGeometryData → THREE.Mesh (기본 머터리얼) */
export declare function createMeshFromGeometryData(data: BufferGeometryData, material?: THREE.Material): THREE.Mesh;
//# sourceMappingURL=geometry.d.ts.map