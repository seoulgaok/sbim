"use client";
//@orchestra workspace

import React, {useRef, useState, useMemo, useEffect} from 'react';
import {Canvas} from '@react-three/fiber';
import {
  CameraControls,
  Environment,
  Grid,
  Html,
  ContactShadows,
  Edges,
  Line,
  Lightformer,
  Sky
} from '@react-three/drei';
import * as THREE from 'three';
import type {GeoJSON} from 'geojson';
import MapFloor from './MapFloor.js';
import {motion, AnimatePresence} from 'framer-motion';
import {
  Scheme,
  SchemeData,
  FloorPlan,
  FloorData,
  BufferGeometryData,
  UnitData,
  convertToThreeGeometry,
  createMeshFromGeometryData,
} from '@seoulgaok/bim-core';
import VehicleSimulation from "./VehicleSimulation.js";
import {GeoCoordinateTransformer} from "./GeoCoordinateTransformer.js";

// UI peer-deps — consuming app must provide shadcn-ui-compatible paths.
// TODO: Phase 2에서 prop-based 또는 별도 컨테이너로 분리.
import {Card, CardContent, CardHeader, CardTitle} from '@/components/ui/card';
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow} from '@/components/ui/table';
import {ScrollArea} from '@/components/ui/scroll-area';
import {Button} from '@/components/ui/button';
import {Building2, ChevronDown, ChevronUp, Plus, Minus} from "lucide-react";
import InquiryDialog, {InquiryScenario} from "@/components/Feedback";

// UnitList component with DeFi-style box layout (no scroll wheel)
const UnitList = ({ unitsData, selectedUnit, onUnitSelect }) => {
  const [expandedFloor, setExpandedFloor] = useState<number | null>(null);

  // Extract all units and organize by floor
  const unitsByFloor = useMemo(() => {
    if (!unitsData || unitsData.length === 0) return {};

    const grouped = unitsData.reduce((acc, unit) => {
      const floorId = unit.data?.floor_id || 1;
      if (!acc[floorId]) {
        acc[floorId] = [];
      }

      acc[floorId].push({
        floorId: floorId,
        unitId: unit.data?.id,
        data: {
          id: unit.data?.id || `unknown-${Math.random()}`,
          name: unit.data?.name || `Unit`,
          price: unit.data?.price || 0,
          floor_id: floorId,
          floor_height: unit.data?.floor_height || 3.0,
          floor_bottom_height: unit.data?.floor_bottom_height || floorId * 3.0,
          area_net: unit.data?.area_net || 0,
          area_common: unit.data?.area_common || 0,
          land_portion: unit.data?.land_portion || 0,
          area_service: unit.data?.area_service || 0,
          area_contract: unit.data?.area_contract || 0
        }
      });
      return acc;
    }, {});

    // Sort units by name within each floor
    Object.keys(grouped).forEach(floorId => {
      grouped[Number(floorId)].sort((a, b) => {
        return a.data.name.localeCompare(b.data.name, undefined, { numeric: true });
      });
    });

    return grouped;
  }, [unitsData]);

  // Get floor IDs in descending order (top floor first)
  const floorIds = useMemo(() => {
    return Object.keys(unitsByFloor)
      .map(id => Number(id))
      .sort((a, b) => b - a);
  }, [unitsByFloor]);

  // Format helpers
  const formatPrice = (price) => {
    return (price / 100000000).toFixed(1) + "억원";
  };

  const toKoreanPyeong = (squareMeters) => {
    return (squareMeters / 3.3058).toFixed(1);
  };

  return (
    <div className="h-full flex flex-col bg-[#f8f7f5] overflow-hidden">
      {/* Header - DeFi style */}
      <div className="p-4 bg-white border-b-2 border-gray-900 flex-shrink-0">
        <h3 className="text-xl font-bold text-gray-900 tracking-tight">유닛 목록</h3>
        <p className="text-sm text-gray-600 mt-1">층을 선택하여 유닛을 확인하세요</p>
      </div>

      {/* Floor Grid - DeFi style boxes with scrollbar */}
      <div className="flex-1 p-4 space-y-3 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-gray-100">
        {floorIds.length > 0 ? (
          floorIds.map(floorId => {
            const unitsOnFloor = unitsByFloor[floorId] || [];
            const isExpanded = expandedFloor === floorId;

            return (
              <div key={floorId} className="bg-white border-2 border-gray-200 hover:border-gray-900 transition-colors">
                {/* Floor Header - Clickable */}
                <div
                  className="p-4 cursor-pointer flex items-center justify-between"
                  onClick={() => setExpandedFloor(isExpanded ? null : floorId)}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gray-900 text-white flex items-center justify-center font-bold text-lg">
                      {floorId}
                    </div>
                    <div>
                      <h4 className="font-bold text-gray-900">{floorId}층</h4>
                      <p className="text-sm text-gray-600">{unitsOnFloor.length}개 유닛</p>
                    </div>
                  </div>
                  {isExpanded ?
                    <ChevronUp size={20} className="text-gray-600" /> :
                    <ChevronDown size={20} className="text-gray-600" />
                  }
                </div>

                {/* Expanded Units */}
                {isExpanded && (
                  <div className="border-t-2 border-gray-200 p-4 bg-gray-50">
                    <div className="grid grid-cols-1 gap-3">
                      {unitsOnFloor.map(unit => (
                        <div
                          key={unit.unitId}
                          className={`p-4 bg-white border-2 cursor-pointer transition-colors ${
                            selectedUnit === unit.unitId
                              ? 'border-gray-900 shadow-md'
                              : 'border-gray-200 hover:border-gray-400'
                          }`}
                          onClick={() => onUnitSelect(unit.unitId)}
                        >
                          <div className="flex justify-between items-start mb-2">
                            <h5 className="font-bold text-gray-900">{unit.data.name}</h5>
                            <span className="text-lg font-bold text-gray-900">
                              {formatPrice(unit.data.price)}
                            </span>
                          </div>
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            <div className="p-2 bg-gray-50 border border-gray-200">
                              <span className="text-gray-600 block text-xs">전용면적</span>
                              <span className="font-medium text-gray-900">
                                {toKoreanPyeong(unit.data.area_net)}평
                              </span>
                            </div>
                            <div className="p-2 bg-gray-50 border border-gray-200">
                              <span className="text-gray-600 block text-xs">계약면적</span>
                              <span className="font-medium text-gray-900">
                                {toKoreanPyeong(unit.data.area_contract)}평
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div className="flex items-center justify-center h-40 bg-white border-2 border-gray-200">
            <div className="text-center text-gray-500">
              <Building2 className="h-10 w-10 mx-auto mb-2 opacity-20" />
              <p>등록된 유닛이 없습니다</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Calculate center of a GeoJSON object
function calculateCenter(landGeojson: GeoJSON): [number, number] {
  let minLng = Infinity, maxLng = -Infinity;
  let minLat = Infinity, maxLat = -Infinity;

  const processCoords = (coords: number[][]) => {
    coords.forEach(([lng, lat]) => {
      minLng = Math.min(minLng, lng);
      maxLng = Math.max(maxLng, lng);
      minLat = Math.min(minLat, lat);
      maxLat = Math.max(maxLat, lat);
    });
  };

  if ('type' in landGeojson) {
    if (landGeojson.type === 'Feature' && 'geometry' in landGeojson) {
      const geometry = landGeojson.geometry;
      if (geometry.type === 'Polygon') {
        processCoords(geometry.coordinates[0]);
      } else if (geometry.type === 'MultiPolygon') {
        geometry.coordinates.forEach(poly => processCoords(poly[0]));
      }
    } else if (landGeojson.type === 'Polygon' && 'coordinates' in landGeojson) {
      processCoords(landGeojson.coordinates[0]);
    } else if (landGeojson.type === 'MultiPolygon' && 'coordinates' in landGeojson) {
      landGeojson.coordinates.forEach(poly => processCoords(poly[0]));
    }
  }

  if (minLng === Infinity) {
    return [127.0, 37.5]; // Default Seoul coordinates
  }

  return [(minLng + maxLng) / 2, (minLat + maxLat) / 2];
}

interface ParcelProps {
  landGeojson: GeoJSON;
  transformer: GeoCoordinateTransformer;
  height?: number;
}

const Parcel: React.FC<ParcelProps> = ({
                                         landGeojson,
                                         transformer,
                                         height = 0.5
                                       }) => {
  const polygons = useMemo(() => {
    const extractedPolygons: number[][][] = [];

    if ('type' in landGeojson) {
      if (landGeojson.type === 'Feature' && 'geometry' in landGeojson) {
        const geometry = landGeojson.geometry;
        if (geometry.type === 'Polygon') {
          extractedPolygons.push(geometry.coordinates[0]);
        } else if (geometry.type === 'MultiPolygon') {
          geometry.coordinates.forEach(poly => extractedPolygons.push(poly[0]));
        }
      } else if (landGeojson.type === 'Polygon' && 'coordinates' in landGeojson) {
        extractedPolygons.push(landGeojson.coordinates[0]);
      } else if (landGeojson.type === 'MultiPolygon' && 'coordinates' in landGeojson) {
        landGeojson.coordinates.forEach(poly => extractedPolygons.push(poly[0]));
      }
    }

    return extractedPolygons;
  }, [landGeojson]);

  return (
    <group>
      {polygons.map((coords, idx) => {
        const points2D = coords.map(coord => {
          const [lng, lat] = coord;
          const [x, y] = transformer.latLngToLocal(lat, lng);
          return new THREE.Vector2(x, y);
        });

        if (points2D.length > 0 && !points2D[0].equals(points2D[points2D.length - 1])) {
          points2D.push(points2D[0].clone());
        }

        const outlinePoints = points2D.map(p => new THREE.Vector3(p.x, p.y, 0));
        const shape = new THREE.Shape(points2D);

        return (
          <group key={idx} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.1, 0]}>
            <Line points={outlinePoints} color="#008000" dashed={true}/>
            <mesh>
              <shapeGeometry args={[shape]}/>
              <meshBasicMaterial
                color="#008000"
                transparent
                opacity={0.2}
                side={THREE.DoubleSide}
              />
            </mesh>
          </group>
        );
      })}
    </group>
  );
};

function computeScaleFactor(tileSize: number, zoom: number, latitude: number, earthRadius = 6371000) {
  const latitudeRad = latitude * Math.PI / 180;
  const totalPixels = tileSize * Math.pow(2, zoom);
  const denominator = 2 * Math.PI * earthRadius * Math.cos(latitudeRad);
  return totalPixels / denominator;
}

// Modified FloorGroup component to support unit selection and use new scheme types
// This component renders a single floor with walls, floors, and units
const FloorGroup = ({
                      floorPlan,
                      hoveredUnit,
                      selectedUnit,
                      setHoveredUnit,
                      transformer,
                      unitsOnThisFloor,
                      onUnitSelect
                    }) => {
  // Reusable materials
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
        clearcoatRoughness: 0
      }),
    []
  );

  const floorMaterial = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: 0x888888,
        side: THREE.DoubleSide,
        roughness: 0.7,
        metalness: 0.1
      }),
    []
  );

  const roofMaterial = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: 0x996633, // Brown color for roof
        side: THREE.DoubleSide,
        roughness: 0.8,
        metalness: 0.2
      }),
    []
  );

  const baseUnitMaterial = useMemo(
    () =>
      new THREE.MeshPhysicalMaterial({
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0,
        roughness: 0.5,
        metalness: 0.2
      }),
    []
  );

  // Unit colors array
  const unitColors = [0x00ff00];

  // Base unit materials array
  const unitMaterials = useMemo(() => {
    return unitColors.map(color => {
      const mat = baseUnitMaterial.clone();
      mat.color.set(color);
      return mat;
    });
  }, [baseUnitMaterial]);

  // Hover materials
  const hoverMaterials = useMemo(() => {
    return unitMaterials.map(mat => {
      const hoverMat = mat.clone();
      const color = new THREE.Color(mat.color);
      color.offsetHSL(0, 0, 0.15);
      hoverMat.color = color;
      hoverMat.opacity = 0.8;
      return hoverMat;
    });
  }, [unitMaterials]);

  const scaleFactor = transformer.scale * 1;
  // Convert BufferGeometryData array to THREE.js mesh components
  const renderGeometryGroup = (geometryDataArray, material, groupName) => {
    if (!geometryDataArray || !Array.isArray(geometryDataArray)) {
      return null;
    }

    return geometryDataArray.map((geometryArray, groupIndex) => (
      <group key={`${groupName}-${groupIndex}`}>
        {geometryArray.map((geomData, index) => {
          // Use the utility function from scheme.ts to convert buffer geometry
          const geometry = convertToThreeGeometry(geomData);

          return (
            <mesh
              key={`${groupName}-${groupIndex}-${index}`}
              geometry={geometry}
              material={material}
              castShadow={true}
              receiveShadow={true}
            >
              <Edges
                threshold={15}
                color="#333333"
                scale={1.001}
              />
            </mesh>
          );
        })}
      </group>
    ));
  };

  // Render actual unit geometries from the units data
  const renderUnitVisualizations = (unitsOnThisFloor, floorId) => {
    if (!unitsOnThisFloor || !Array.isArray(unitsOnThisFloor) || unitsOnThisFloor.length === 0) {
      return null;
    }

    return unitsOnThisFloor.map((unit: any, index: number) => {
      const unitId = unit.data?.id || index;
      const uniqueUnitId = `${unitId}`;
      const isHovered = hoveredUnit === uniqueUnitId;
      const isSelected = selectedUnit === uniqueUnitId;

      // Create material based on hover/selected state
      const baseMaterial = new THREE.MeshStandardMaterial({
        color: isSelected ? 0x00B5A1 : unitColors[index % unitColors.length],
        transparent: true,
        opacity: isSelected ? 0.9 : 0.1
      });

      // If the unit has boundary geometry, use it
      if (unit.geom && unit.geom.boundary && Array.isArray(unit.geom.boundary)) {
        return unit.geom.boundary.map((geomData: any, geomIndex: number) => {
          try {
            // Convert buffer geometry data to THREE geometry
            const geometry = convertToThreeGeometry(geomData);

            return (
              <mesh
                key={`${uniqueUnitId}-boundary-${geomIndex}`}
                geometry={geometry}
                material={baseMaterial}
                onPointerOver={e => {
                  e.stopPropagation();
                  setHoveredUnit(uniqueUnitId);
                }}
                onPointerOut={e => {
                  e.stopPropagation();
                  setHoveredUnit(null);
                }}
                onClick={e => {
                  e.stopPropagation();
                  onUnitSelect(uniqueUnitId);
                }}
              >
                {(isHovered || isSelected) && (
                  <Edges
                    threshold={15}
                    color={isSelected ? "#00B5A1" : "black"}
                    scale={1.002}
                  />
                )}
              </mesh>
            );
          } catch (error) {
            console.error("Error creating unit visualization:", error);
            return null;
          }
        });
      }

      // Fallback to a simple box if no geometry data is available
      return (
        <mesh
          key={uniqueUnitId}
          scale={[1.01, 1.01, 1.01]}
          position={[0, 0, (index * 0.5) + 0.5]} // Stack units for visualization
          onPointerOver={e => {
            e.stopPropagation();
            setHoveredUnit(uniqueUnitId);
          }}
          onPointerOut={e => {
            e.stopPropagation();
            setHoveredUnit(null);
          }}
          onClick={e => {
            e.stopPropagation();
            onUnitSelect(uniqueUnitId);
          }}
        >
          <boxGeometry args={[2, 2, 0.1]}/>
          <primitive object={baseMaterial}/>
          {(isHovered || isSelected) && (
            <Edges
              threshold={15}
              color={isSelected ? "#00B5A1" : "black"}
              scale={1.002}
            />
          )}
        </mesh>
      );
    });
  };

  return (
    <group
      rotation={[-Math.PI / 2, 0, 0]}
      scale={[scaleFactor, scaleFactor, scaleFactor]}
    >
      {/* Walls rendering using the new scheme structure */}
      {renderGeometryGroup(floorPlan.geom.walls, wallMaterial, 'wall')}

      {/* Floors rendering using the new scheme structure */}
      {renderGeometryGroup(floorPlan.geom.floors, floorMaterial, 'floor')}

      {/* roof rendering using the new scheme structure */}
      {floorPlan.geom.roof && renderGeometryGroup(floorPlan.geom.roof, roofMaterial, 'roof')}

      {/* Units visualization from actual unit data */}
      {renderUnitVisualizations(unitsOnThisFloor, floorPlan.data.floor_id)}
    </group>
  );
};

// Updated BuildingScene component to use new scheme types
const BuildingScene = ({
                         schemeData,
                         unitsData,
                         surroundingsData,
                         landGeojson,
                         initialLatitude,
                         initialLongitude,
                         controlsRef,
                         hoveredUnit,
                         setHoveredUnit,
                         selectedFloor,
                         selectedUnit,
                         onUnitSelect
                       }) => {
  const center = useMemo(() => calculateCenter(landGeojson), [landGeojson]);
  const zoomLevel = 17;
  const tileSize = 1024;

  const scaleFactor = computeScaleFactor(tileSize, zoomLevel, center[1]);
  const transformer = useMemo(() =>
      new GeoCoordinateTransformer(center[1], center[0], scaleFactor),
    [center, scaleFactor]);

  const mapFloorProps = {
    center: [initialLongitude, initialLatitude] as [number, number],
    level: 18,
    width: tileSize,
    height: tileSize,
    planeWidth: tileSize,
    planeHeight: tileSize,
    // mapType: 'basic' as const,
  };

  // Initial camera position setup
  React.useEffect(() => {
    if (controlsRef.current) {
      setTimeout(() => {
        controlsRef.current.setLookAt(200, 200, 200, 0, 10, 0, true);
      }, 2000);
    }
  }, [controlsRef]);

  // Filter floor plans based on selected floor
  const visibleFloorPlans = selectedFloor
    ? schemeData.floor_plans.filter((fp: any) => fp.data.floor_id === selectedFloor)
    : schemeData.floor_plans;

  // Component to render surrounding buildings
  const SurroundingBuildings = ({surroundingsData, transformer}) => {
    if (!surroundingsData || !Array.isArray(surroundingsData)) {
      return null;
    }

    const scaleFactor = transformer.scale * 1;

    const surroundingMaterial = useMemo(() => {
      return new THREE.MeshStandardMaterial({
        color: 0xeeeeee,      // Light, desaturated color
        side: THREE.DoubleSide,
        roughness: 0.9,
        metalness: 0.0,
        transparent: true,
        opacity: 0.8          // 60% transparent
      });
    }, []);

    return (
      <group rotation={[-Math.PI / 2, 0, 0]} scale={[scaleFactor, scaleFactor, scaleFactor]}>
        {surroundingsData.map((building: any, index: number) => {
          if (!building.geom || !building.data) return null;
          // const height = building.data.height || 10;
          const position = [0, 0, 0];
          return (
            <group key={`surrounding-${index}`}>
              {building.geom.boundary && building.geom.boundary.map((geomData: any, geomIndex: number) => {
                const geometry = convertToThreeGeometry(geomData);

                return (
                  <mesh
                    key={`surrounding-${index}-${geomIndex}`}
                    geometry={geometry}
                    material={surroundingMaterial}
                    position={[position[0], position[1], position[2]]}
                    castShadow={true}
                    receiveShadow={true}
                  >
                  </mesh>
                );
              })}
            </group>
          );
        })}
      </group>
    );
  };

  return (
    <>
      <MapFloor {...mapFloorProps} />
      <Parcel landGeojson={landGeojson} transformer={transformer} />

      {/* Render surrounding buildings */}
      <SurroundingBuildings
        surroundingsData={surroundingsData}
        transformer={transformer}
      />

      {visibleFloorPlans.map(floorPlan => {
        // Find units that belong to this floor
        const unitsOnThisFloor = unitsData.filter((unit: any) =>
          unit.data && unit.data.floor_id === floorPlan.data.floor_id
        );

        return (
          <FloorGroup
            key={`floor-${floorPlan.data.floor_id}`}
            floorPlan={floorPlan}
            hoveredUnit={hoveredUnit}
            selectedUnit={selectedUnit}
            setHoveredUnit={setHoveredUnit}
            transformer={transformer}
            unitsOnThisFloor={unitsOnThisFloor}
            onUnitSelect={onUnitSelect}
          />
        );
      })}
      <Sky
        distance={450000}
        sunPosition={[100, 100, 100]}
        inclination={0.6}
        azimuth={0.25}
        turbidity={10}
        rayleigh={0.5}
      />

      {/* Main directional light (sun) */}
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

      {/* Back/Fill light */}
      <directionalLight
        position={[-100, 80, -100]}
        intensity={0.3}
        color="#CCDFFF"
      />

      {/* Ambient light */}
      <ambientLight intensity={0.4} color="#E6F0FF"/>

      {/* Enhanced contact shadows */}
      <ContactShadows
        position={[0, 0.01, 0]}
        opacity={0.4}
        scale={200}
        blur={3}
        far={300}
        resolution={1024}
        color="#000000"
        rotation={[0, 0, 0]}
      />
    </>
  );
};

// Enhanced UnitDetailPanel component with the request button
const UnitDetailPanel: React.FC<{
  unitData: UnitData | null;
  floorId: number;
  onClose: () => void;
}> = ({unitData, floorId, onClose}) => {
  if (!unitData) return null;

  // Helper function to convert m² to pyeong
  const toKoreanPyeong = (squareMeters: number): number => {
    return squareMeters / 3.3058;
  };

  return (
    <motion.div
      initial={{opacity: 0, y: 20, scale: 0.95}}
      animate={{opacity: 1, y: 0, scale: 1}}
      exit={{opacity: 0, y: 20, scale: 0.95}}
      transition={{duration: 0.2}}
      className="fixed bottom-6 right-6 mx-auto bg-white rounded-lg shadow-xl w-80 max-w-full z-50 border-2 border-primary overflow-hidden"
    >
      <div className="bg-gradient-to-r from-primary to-primary/80 text-white p-3 relative">
        <h3 className="text-lg font-bold m-0">
          {unitData.name}
        </h3>
        <button
          onClick={onClose}
          className="absolute top-3 right-3 bg-transparent border-none text-white text-base cursor-pointer"
        >
          ✕
        </button>
      </div>
      <div className="p-3">
        <div className="mb-3 p-2 bg-gray-50 rounded-md text-center">
          <span className="text-2xl font-bold text-primary">
            {(unitData.price / 100000000).toFixed(1)}억원
          </span>
        </div>
        <div className="text-sm leading-relaxed">
          <div className="flex justify-between py-2 border-b border-gray-100">
            <span className="font-medium text-gray-600">전용면적</span>
            <span className="font-bold">
              {(unitData.area_net).toFixed(2)}㎡ ({toKoreanPyeong(unitData.area_net).toFixed(1)}평)
            </span>
          </div>
          <div className="flex justify-between py-2 border-b border-gray-100">
            <span className="font-medium text-gray-600">공용면적</span>
            <span>{(unitData.area_common).toFixed(2)}㎡</span>
          </div>
          <div className="flex justify-between py-2 border-b border-gray-100">
            <span className="font-medium text-gray-600">계약면적</span>
            <span>
              {(unitData.area_contract).toFixed(2)}㎡ ({toKoreanPyeong(unitData.area_contract).toFixed(1)}평)
            </span>
          </div>
          <div className="flex justify-between py-2">
            <span className="font-medium text-gray-600">대지지분</span>
            <span>{(unitData.land_portion).toFixed(2)}㎡</span>
          </div>
        </div>
        <div className="mt-3 p-2 bg-gray-50 rounded-md text-xs text-gray-600">
          <div className="flex justify-between">
            <span>㎡당 가격</span>
            <span>{Math.round(unitData.price / (unitData.area_net)).toLocaleString()}원/㎡</span>
          </div>
          <div className="flex justify-between mt-1">
            <span>평당 가격</span>
            <span>{Math.round(unitData.price / toKoreanPyeong(unitData.area_net)).toLocaleString()}원/평</span>
          </div>
        </div>
      </div>
      <div className="px-3 pb-3 pt-1">
        <InquiryDialog scenario={InquiryScenario.FEEDBACK}>
        <Button className="w-full h-10 bg-primary hover:bg-primary/90 text-white">
            소개서 요청하기
          </Button>
        </InquiryDialog>
      </div>
    </motion.div>
  );
};

// Main BuildingMeshVisualizer component with three separate data sources
interface BuildingMeshVisualizerProps {
  schemeData: any; // Building structure (walls, floors)
  unitsData: any; // Unit information
  surroundingsData: any | null; // Surrounding buildings
  landGeojson: GeoJSON;
  initialLatitude?: number;
  initialLongitude?: number;
}

const BuildingMeshVisualizer: React.FC<BuildingMeshVisualizerProps> = ({
                                                                         schemeData,
                                                                         unitsData,
                                                                         surroundingsData,
                                                                         landGeojson,
                                                                         initialLatitude = 37.5326,
                                                                         initialLongitude = 126.9679
                                                                       }) => {
  const controlsRef = useRef(null);
  const [showInstructions, setShowInstructions] = useState(true);
  const [hoveredUnit, setHoveredUnit] = useState<string | null>(null);
  const [selectedUnit, setSelectedUnit] = useState<string | null>(null);
  const [selectedFloor, setSelectedFloor] = useState<number | null>(null);
  const [selectedUnitData, setSelectedUnitData] = useState<UnitData | null>(null);
  const [selectedFloorId, setSelectedFloorId] = useState<number>(0);
  const [showUnitList, setShowUnitList] = useState(false);

  // Auto-hide instructions
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setShowInstructions(false);
    }, 5000);
    return () => clearTimeout(timer);
  }, []);

  // Find unit data based on the selected unit ID
  const findUnitData = (unitId: string | null): { unitData: UnitData | null, floorId: number } => {
    if (!unitId) return {unitData: null, floorId: 0};

    // Find the actual unit in unitsData
    const foundUnit = unitsData.find((unit: any) =>
      String(unit.data?.id) === String(unitId)
    );
    if (foundUnit && foundUnit.data) {
      const floorId = foundUnit.data.floor_id
      return {
        unitData: {
          id: foundUnit.data.id || unitId,
          name: foundUnit.data.name || '이름 없음',
          price: foundUnit.data.price || 0,
          floor_id: floorId,
          floor_height: foundUnit.data.floor_height || 3.0,
          floor_bottom_height: foundUnit.data.floor_bottom_height || floorId * 3.0,
          area_net: foundUnit.data.area_net || 60,
          area_common: foundUnit.data.area_common || 20,
          land_portion: foundUnit.data.land_portion || 10,
          area_service: foundUnit.data.area_service || 5,
          area_contract: foundUnit.data.area_contract || 85
        },
        floorId
      };
    }


    return {unitData: null, floorId: 0};
  };

  // Handle unit selection
  const handleUnitSelect = (unitId: string) => {
    if (selectedUnit === unitId) {
      // Deselect if clicking the same unit
      setSelectedUnit(null);
      setSelectedFloor(null);
      setSelectedUnitData(null);
      setSelectedFloorId(0);
    } else {
      setSelectedUnit(unitId);

      // Extract floor ID and unit data
      const {unitData, floorId} = findUnitData(unitId);
      setSelectedUnitData(unitData);
      setSelectedFloorId(floorId);

      // Set selected floor to focus on that floor
      setSelectedFloor(floorId);
    }
  };

  // Close unit detail panel
  const handleCloseUnitDetail = () => {
    setSelectedUnit(null);
    setSelectedUnitData(null);
  };

  // Zoom controls
  const handleZoomIn = () => {
    if (controlsRef.current) {
      (controlsRef.current as any).dolly(-50, true);
    }
  };

  const handleZoomOut = () => {
    if (controlsRef.current) {
      (controlsRef.current as any).dolly(50, true);
    }
  };

  return (
    <div className="w-full h-full relative">
      {/* 3D 뷰어 - Full Width */}
      <div className="w-full h-full">
        <AnimatePresence>
          {showInstructions && (
            <motion.div
              className="absolute top-4 left-1/2 transform -translate-x-1/2 z-10 bg-black/75 text-white rounded-lg p-4"
              initial={{opacity: 0, y: -20}}
              animate={{opacity: 1, y: 0}}
              exit={{opacity: 0, y: -20}}
              transition={{duration: 0.3}}
            >
              <p className="text-sm text-center">
                🏠 <strong>건물 3D 모델을 확인해보세요!</strong> 마우스로 회전하고, 확대/축소할 수 있습니다.
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Zoom Controls */}
        <div className="absolute top-6 left-6 z-10 flex flex-col gap-2">
          <button
            onClick={handleZoomOut}
            className="w-10 h-10 bg-white border-2 border-gray-900 flex items-center justify-center hover:bg-gray-100 transition-colors"
            aria-label="확대"
          >
            <Plus className="h-5 w-5 text-gray-900" />
          </button>
          <button
            onClick={handleZoomIn}
            className="w-10 h-10 bg-white border-2 border-gray-900 flex items-center justify-center hover:bg-gray-100 transition-colors"
            aria-label="축소"
          >
            <Minus className="h-5 w-5 text-gray-900" />
          </button>
        </div>

        {/* Unit List Toggle Button */}
        <button
          onClick={() => setShowUnitList(!showUnitList)}
          className="absolute top-6 right-6 z-10 px-4 py-2 bg-white border-2 border-gray-900 flex items-center gap-2 hover:bg-gray-100 transition-colors"
        >
          <Building2 className="h-4 w-4 text-gray-900" />
          <span className="text-sm font-medium text-gray-900">
            {showUnitList ? '유닛 목록 닫기' : '유닛 목록'}
          </span>
        </button>

        {/* Unit Detail Panel */}
        <AnimatePresence>
          {selectedUnitData && (
            <UnitDetailPanel
              unitData={selectedUnitData}
              floorId={selectedFloorId}
              onClose={handleCloseUnitDetail}
            />
          )}
        </AnimatePresence>

        {/* 3D Canvas */}
        <Canvas
          camera={{position: [0, 1000, 0], fov: 45, far: 20000}}
          gl={{
            antialias: true,
            logarithmicDepthBuffer: true,
            shadowMapEnabled: true
          }}
          shadows={{
            type: THREE.PCFSoftShadowMap,
            enabled: true
          }}
        >
          <BuildingScene
            schemeData={schemeData}
            unitsData={unitsData}
            surroundingsData={surroundingsData}
            landGeojson={landGeojson}
            initialLatitude={initialLatitude}
            initialLongitude={initialLongitude}
            controlsRef={controlsRef}
            hoveredUnit={hoveredUnit}
            setHoveredUnit={setHoveredUnit}
            selectedFloor={selectedFloor}
            selectedUnit={selectedUnit}
            onUnitSelect={handleUnitSelect}
          />
          <CameraControls
            ref={controlsRef}
            minPolarAngle={0}
            maxPolarAngle={Math.PI / 1.6}
            smoothTime={0.3}
            minDistance={5}
            maxDistance={800}
            azimuthRotateSpeed={0.7}
            polarRotateSpeed={0.7}
            dampingFactor={0.05}
            mouseButtons={{
              left: 1,
              middle: 0,
              right: 2,
              wheel: 0
            }}
          />
        </Canvas>
      </div>

      {/* Floating Unit List Panel */}
      <AnimatePresence>
        {showUnitList && (
          <motion.div
            className="absolute top-16 right-6 w-[360px] h-[calc(100%-6rem)] max-h-[500px] bg-white border-2 border-gray-900 shadow-xl z-20 flex flex-col"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.2 }}
          >
            <UnitList
              unitsData={unitsData}
              selectedUnit={selectedUnit}
              onUnitSelect={handleUnitSelect}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default BuildingMeshVisualizer;
