import React, {useMemo} from 'react';
import * as THREE from 'three';
import { useLoader } from '@react-three/fiber';
import {TextureLoader} from "three";

interface MapFloorProps {
  accessToken: string;
  center: [number, number];
  zoom: number;
  width: number;
  height: number;
  planeWidth: number;
  planeHeight: number;
}

const MapFloorMapBox = ({ accessToken, center, zoom, width, height, planeWidth, planeHeight }: MapFloorProps) => {
  const [lng, lat] = center;

  // Mapbox Static API URL 구성 (streets-v11)
  const url = `https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/${lng},${lat},${zoom}/${width}x${height}@2x?access_token=${accessToken}`;

  // useLoader로 텍스처 로드
  const texture = useMemo(() => {
    const loader = new THREE.TextureLoader();
    const tex = loader.load(url);
    tex.wrapS = tex.wrapT = THREE.ClampToEdgeWrapping;
    tex.needsUpdate = true;
    return tex;
  }, [url]);

  // 텍스처 설정
  if (texture instanceof THREE.Texture) {
    texture.wrapS = THREE.ClampToEdgeWrapping;
    texture.wrapT = THREE.ClampToEdgeWrapping;
    texture.needsUpdate = true;
  }

  // 지도 평면은 XZ 평면에 놓기 위해 -Math.PI/2 회전
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} castShadow receiveShadow>
      <planeBufferGeometry args={[planeWidth, planeHeight]} />
      <meshBasicMaterial map={texture as any} />
    </mesh>
  );
}

export default MapFloorMapBox;
