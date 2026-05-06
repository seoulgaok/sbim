// src/components/BuildingVisualizer/CoordinateTransformer.ts
import * as THREE from 'three';

/**
 * 지리 좌표(위경도)를 3D 씬의 로컬 좌표로 변환하는 클래스
 */
export class GeoCoordinateTransformer {
  private originLat: number;
  private originLng: number;
  private scale: number;

  /**
   * 좌표 변환기 생성
   * @param originLat 원점의 위도(latitude)
   * @param originLng 원점의 경도(longitude)
   * @param scale 축척 계수 (기본값: 1.0)
   */
  constructor(originLat: number, originLng: number, scale: number = 1.0) {
    this.originLat = originLat;
    this.originLng = originLng;
    this.scale = scale;
  }

  /**
   * 지구 좌표계의 위경도를 로컬 좌표로 변환
   * @param lat 변환할 위도
   * @param lng 변환할 경도
   * @returns 로컬 좌표계의 [x,z] 좌표값
   */
  latLngToLocal(lat: number, lng: number): [number, number] {
    // 지구 반경 (미터)
    const earthRadius = 6371000;

    // 라디안 변환
    const latRad = lat * Math.PI / 180;
    const lngRad = lng * Math.PI / 180;
    const originLatRad = this.originLat * Math.PI / 180;
    const originLngRad = this.originLng * Math.PI / 180;

    // Haversine 공식을 사용한 거리 계산
    const dLat = latRad - originLatRad;
    const dLng = lngRad - originLngRad;

    // x 좌표 (경도 차이, 동-서 방향)
    // 위도에 따라 경도 1도의 실제 거리가 달라지므로 cosine 보정
    const x = earthRadius * Math.cos(originLatRad) * dLng;

    // z 좌표 (위도 차이, 남-북 방향)
    const z = earthRadius * dLat;

    // 축척 적용 및 반환
    return [x * this.scale, z * this.scale];
  }

  /**
   * 3D 맵에서 사용하기 위한 위경도 좌표 경계 계산
   * @param radius 미터 단위 반경
   * @returns 경계 좌표 [minLng, minLat, maxLng, maxLat]
   */
  calculateBounds(radius: number): [number, number, number, number] {
    // 지구 반경 (미터)
    const earthRadius = 6371000;

    // 위도 1도의 대략적인 거리(미터)
    const latMetersPerDegree = 111000;

    // 주어진 위도에서 경도 1도의 대략적인 거리(미터)
    const lngMetersPerDegree = earthRadius * Math.cos(this.originLat * Math.PI / 180) * (Math.PI / 180);

    // 반경을 위경도 차이로 변환
    const latDiff = radius / latMetersPerDegree;
    const lngDiff = radius / lngMetersPerDegree;

    return [
      this.originLng - lngDiff,  // minLng
      this.originLat - latDiff,  // minLat
      this.originLng + lngDiff,  // maxLng
      this.originLat + latDiff   // maxLat
    ];
  }

  /**
   * 맵 플로어와 정확히 맞는 도로를 계산하기 위한 메서드
   * @param mapWidth 맵의 너비 (픽셀)
   * @param mapHeight 맵의 높이 (픽셀)
   * @param zoom 줌 레벨
   * @returns 맵에 맞는 변환 스케일 계수
   */
  getMapAlignedScale(mapWidth: number, mapHeight: number, zoom: number): number {
    // 타일 크기 (픽셀)
    const TILE_SIZE = 256;

    // 줌 레벨에 따른 지구 둘레 대비 타일 크기 계산
    const zoomScale = Math.pow(2, zoom);

    // 적절한 스케일 계수 계산
    const scale = (mapWidth / TILE_SIZE) / zoomScale;

    return scale;
  }

  /**
   * 지도 이미지와 도로 네트워크를 맞추기 위한 변환 행렬 생성
   * @param mapFloorWidth 맵 플로어의 너비
   * @param mapZoom 맵 줌 레벨
   * @returns THREE.js 변환 행렬
   */
  createAlignmentMatrix(mapFloorWidth: number, mapZoom: number): THREE.Matrix4 {
    const matrix = new THREE.Matrix4();

    // 도로 네트워크를 지도 크기에 맞게 조정
    const alignmentScale = this.getMapAlignedScale(mapFloorWidth, mapFloorWidth, mapZoom);

    // 회전 및 스케일 변환 적용
    matrix.makeRotationX(-Math.PI / 2); // 맵플로어와 같은 회전
    matrix.scale(new THREE.Vector3(alignmentScale, alignmentScale, alignmentScale));

    return matrix;
  }
}
