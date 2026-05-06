/**
 * BufferGeometryData ↔ THREE.BufferGeometry 변환 헬퍼.
 * nextbase-v3에서 추출.
 */
import * as THREE from "three";
/** BufferGeometryData → THREE.BufferGeometry */
export function convertToThreeGeometry(data) {
    const geometry = new THREE.BufferGeometry();
    // position, normal
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(data.data.attributes.position.array, data.data.attributes.position.itemSize));
    geometry.setAttribute("normal", new THREE.Float32BufferAttribute(data.data.attributes.normal.array, data.data.attributes.normal.itemSize));
    // uv (있으면 사용, 없으면 bounding box 기반 자동 생성)
    if (data.data.attributes.uv) {
        geometry.setAttribute("uv", new THREE.Float32BufferAttribute(data.data.attributes.uv.array, data.data.attributes.uv.itemSize));
    }
    else {
        geometry.computeBoundingBox();
        const positions = data.data.attributes.position.array;
        const count = positions.length / 3;
        const uvs = new Float32Array(count * 2);
        if (geometry.boundingBox) {
            const { min, max } = geometry.boundingBox;
            const range = new THREE.Vector3().subVectors(max, min);
            for (let i = 0; i < count; i++) {
                const x = positions[i * 3];
                const y = positions[i * 3 + 1];
                uvs[i * 2] = (x - min.x) / range.x;
                uvs[i * 2 + 1] = (y - min.y) / range.y;
            }
            geometry.setAttribute("uv", new THREE.Float32BufferAttribute(uvs, 2));
        }
    }
    geometry.setIndex(data.data.index.array);
    geometry.computeVertexNormals();
    return geometry;
}
/** BufferGeometryData → THREE.Mesh (기본 머터리얼) */
export function createMeshFromGeometryData(data, material = new THREE.MeshStandardMaterial({ color: 0xcccccc })) {
    const geometry = convertToThreeGeometry(data);
    return new THREE.Mesh(geometry, material);
}
//# sourceMappingURL=geometry.js.map