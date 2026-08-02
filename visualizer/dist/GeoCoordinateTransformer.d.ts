import * as THREE from 'three';
/**
 * 지리 좌표(위경도)를 3D 씬의 로컬 좌표로 변환하는 클래스
 */
export declare class GeoCoordinateTransformer {
    private originLat;
    private originLng;
    private scale;
    /**
     * 좌표 변환기 생성
     * @param originLat 원점의 위도(latitude)
     * @param originLng 원점의 경도(longitude)
     * @param scale 축척 계수 (기본값: 1.0)
     */
    constructor(originLat: number, originLng: number, scale?: number);
    /**
     * 지구 좌표계의 위경도를 로컬 좌표로 변환
     * @param lat 변환할 위도
     * @param lng 변환할 경도
     * @returns 로컬 좌표계의 [x,z] 좌표값
     */
    latLngToLocal(lat: number, lng: number): [number, number];
    /**
     * 3D 맵에서 사용하기 위한 위경도 좌표 경계 계산
     * @param radius 미터 단위 반경
     * @returns 경계 좌표 [minLng, minLat, maxLng, maxLat]
     */
    calculateBounds(radius: number): [number, number, number, number];
    /**
     * 맵 플로어와 정확히 맞는 도로를 계산하기 위한 메서드
     * @param mapWidth 맵의 너비 (픽셀)
     * @param mapHeight 맵의 높이 (픽셀)
     * @param zoom 줌 레벨
     * @returns 맵에 맞는 변환 스케일 계수
     */
    getMapAlignedScale(mapWidth: number, mapHeight: number, zoom: number): number;
    /**
     * 지도 이미지와 도로 네트워크를 맞추기 위한 변환 행렬 생성
     * @param mapFloorWidth 맵 플로어의 너비
     * @param mapZoom 맵 줌 레벨
     * @returns THREE.js 변환 행렬
     */
    createAlignmentMatrix(mapFloorWidth: number, mapZoom: number): THREE.Matrix4;
}
//# sourceMappingURL=GeoCoordinateTransformer.d.ts.map