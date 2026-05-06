'use client';
import React, { useMemo, useEffect, useState } from 'react';
import * as THREE from 'three';
//@orchestra workspace

interface MapFloorProps {
  center: [number, number]; // [경도, 위도] 형식
  level: number; // 네이버 지도 줌 레벨 (0-20)
  width: number; // 이미지 너비
  height: number; // 이미지 높이
  planeWidth: number; // 3D 평면 너비
  planeHeight: number; // 3D 평면 높이
  mapType?: 'basic' | 'satellite' | 'terrain' | 'satellite_base' | 'traffic'; // 지도 타입
  scale?: 1 | 2; // 해상도 (1: 일반, 2: 고해상도)
  opacity?: number; // 투명도 (0-1)
  brightness?: number; // 밝기 조정 (1 = 기본)
  contrast?: number; // 대비 조정 (1 = 기본)
  saturation?: number; // 채도 조정 (1 = 기본)
}

const MapFloor = ({
                    center,
                    level,
                    width,
                    height,
                    planeWidth,
                    planeHeight,
                    mapType = 'satellite',
                    scale = 2,
                    opacity = 1,
                    brightness = 1, // 기본값보다 밝게
                    contrast = 0.9, // 기본값보다 대비 높게
                    saturation = 0.9 // 기본값보다 채도 높게
                  }: MapFloorProps) => {
  const [lng, lat] = center;
  const [materialReady, setMaterialReady] = useState(false);

  // 네이버 Static Maps API 라우트 URL 구성 (서버 사이드 API 라우트 활용)
  const mapUrl = `/api/naver-map?w=${width}&h=${height}&center=${lng},${lat}&level=${level}&maptype=${mapType}&scale=${scale}&format=png`;

  // 셰이더 머티리얼 정의
  const shaderMaterial = useMemo(() => {
    // 색상 보정을 위한 커스텀 셰이더
    const vertexShader = `
      varying vec2 vUv;
      void main() {
        vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `;

    const fragmentShader = `
      uniform sampler2D map;
      uniform float brightness;
      uniform float contrast;
      uniform float saturation;
      uniform float opacity;
      varying vec2 vUv;

      void main() {
        vec4 texColor = texture2D(map, vUv);

        // 밝기 조정
        vec3 color = texColor.rgb * brightness;

        // 대비 조정
        color = (color - 0.5) * contrast + 0.5;

        // 채도 조정
        float luminance = dot(color, vec3(0.299, 0.587, 0.114));
        color = mix(vec3(luminance), color, saturation);

        gl_FragColor = vec4(color, texColor.a * opacity);
      }
    `;

    // 셰이더 머티리얼 생성
    return new THREE.ShaderMaterial({
      uniforms: {
        map: { value: null },
        brightness: { value: brightness },
        contrast: { value: contrast },
        saturation: { value: saturation },
        opacity: { value: opacity }
      },
      vertexShader: vertexShader,
      fragmentShader: fragmentShader,
      transparent: true,
      side: THREE.DoubleSide
    });
  }, [brightness, contrast, saturation, opacity]);

  // 텍스처 생성 및 관리
  useEffect(() => {
    const loader = new THREE.TextureLoader();
    loader.setCrossOrigin('');

    loader.load(
      mapUrl,
      (loadedTexture) => {
        // 텍스처 설정
        loadedTexture.wrapS = THREE.ClampToEdgeWrapping;
        loadedTexture.wrapT = THREE.ClampToEdgeWrapping;
        loadedTexture.minFilter = THREE.LinearFilter;
        loadedTexture.magFilter = THREE.LinearFilter;
        loadedTexture.needsUpdate = true;

        // 텍스처 감마 보정 및 색상 공간 설정
        // loadedTexture.encoding = THREE.sRGBEncoding;

        // 셰이더 머티리얼에 텍스처 적용
        shaderMaterial.uniforms.map.value = loadedTexture;
        setMaterialReady(true);
      },
      undefined,
      (error) => console.error('텍스처 로드 실패:', error)
    );
  }, [mapUrl, shaderMaterial]);

  // Instead of using a shader material that doesn't support shadows,
  // let's create a MeshStandardMaterial that does support shadows
  const standardMaterial = useMemo(() => {
    return new THREE.MeshStandardMaterial({
      roughness: 0.7,
      metalness: 0.0,
      side: THREE.DoubleSide,
      map: null,
    });
  }, []);

  // Update texture on the standard material
  useEffect(() => {
    if (materialReady && shaderMaterial.uniforms.map.value) {
      standardMaterial.map = shaderMaterial.uniforms.map.value;
      standardMaterial.needsUpdate = true;
    }
  }, [materialReady, shaderMaterial, standardMaterial]);

  // 지도 평면은 XZ 평면에 놓기 위해 -Math.PI/2 회전
  return (
    <>
      {/* Only use a single mesh that both displays the map and receives shadows */}
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, 0, 0]}
        receiveShadow={true}
      >
        <planeGeometry args={[planeWidth, planeHeight]} />
        {materialReady ? (
          <primitive object={standardMaterial} />
        ) : (
          <meshStandardMaterial color="#cccccc" />
        )}
      </mesh>
    </>
  );
}

export default MapFloor;
