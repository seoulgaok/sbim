// src/components/BuildingVisualizer/VehicleSimulation.tsx
"use client";

import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { GeoJSON } from 'geojson';

// Vehicle model - a simple car shape using THREE.js primitives
const Vehicle = ({ position, rotation, color = '#ff3333', scale = 5 }) => {
  // Use a smaller scale for the vehicle to match the map
  const vehicleScale = scale * 7;

  return (
    <group position={position} rotation={rotation} scale={[vehicleScale, vehicleScale, vehicleScale]}>
      {/* Car body */}
      <mesh castShadow>
        <boxGeometry args={[2, 0.5, 1]} />
        <meshStandardMaterial color={color} metalness={0.1} roughness={0.8} />
      </mesh>
      {/* Car roof */}
      <mesh position={[0, 0.35, 0]} castShadow>
        <boxGeometry args={[1.2, 0.2, 0.8]} />
        <meshStandardMaterial color={color} metalness={0.1} roughness={0.6} />
      </mesh>
      {/* Wheels - made bigger and darker for better visibility */}
      <mesh position={[0.6, -0.25, 0.5]} castShadow>
        <cylinderGeometry args={[0.3, 0.3, 0.2, 12]} />
        <meshStandardMaterial color="#111111" />
      </mesh>
      <mesh position={[-0.6, -0.25, 0.5]} castShadow>
        <cylinderGeometry args={[0.3, 0.3, 0.2, 12]} />
        <meshStandardMaterial color="#111111" />
      </mesh>
      <mesh position={[0.6, -0.25, -0.5]} castShadow>
        <cylinderGeometry args={[0.3, 0.3, 0.2, 12]} />
        <meshStandardMaterial color="#111111" />
      </mesh>
      <mesh position={[-0.6, -0.25, -0.5]} castShadow>
        <cylinderGeometry args={[0.3, 0.3, 0.2, 12]} />
        <meshStandardMaterial color="#111111" />
      </mesh>
    </group>
  );
};

interface RoadData {
  id: number;
  path: THREE.Vector2[];
}

interface VehicleState {
  id: number;
  position: THREE.Vector3;
  rotation: THREE.Euler;
  roadIndex: number;
  pathIndex: number;
  speed: number;
  color: string;
  direction: number; // 1 for forward, -1 for backward
}

interface VehicleSimulationProps {
  centerLat: number;
  centerLng: number;
  radius?: number; // in meters
  vehicleCount?: number;
  transformer: any; // Coordinate transformer from parent component
  enabled?: boolean; // Whether the simulation is enabled
  scale?: number; // Additional scale factor for roads and vehicles
}

const fetchRoadsFromOverpass = async (lat: number, lng: number, radius: number): Promise<RoadData[]> => {
  // Define Overpass query to get roads within radius
  const query = `
    [out:json];
    (
      way["highway"~"^(motorway|trunk|primary|secondary|tertiary|residential|unclassified)$"]
      (around:${radius},${lat},${lng});
    );
    out body;
    >;
    out skel qt;
  `;

  try {
    console.log(`Sending Overpass query for roads within ${radius}m of ${lat},${lng}`);

    // Use our proxy API route to avoid CORS issues
    const response = await fetch('/api/overpass', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      throw new Error(`Error fetching road data: ${response.status} - ${response.statusText}`);
    }

    const data = await response.json();
    console.log(`Received response with ${data.elements?.length || 0} elements`);

    // Process the data to extract roads
    const nodes = new Map();
    let nodeCount = 0;
    let wayCount = 0;

    data.elements?.forEach(element => {
      if (element.type === 'node') {
        nodes.set(element.id, { lat: element.lat, lon: element.lon });
        nodeCount++;
      }
    });

    console.log(`Processed ${nodeCount} nodes`);

    const roads: RoadData[] = [];
    data.elements?.forEach(element => {
      if (element.type === 'way' && element.tags && element.tags.highway) {
        wayCount++;
        const path: THREE.Vector2[] = [];

        element.nodes.forEach(nodeId => {
          const node = nodes.get(nodeId);
          if (node) {
            path.push(new THREE.Vector2(node.lon, node.lat));
          }
        });

        if (path.length > 1) {
          roads.push({
            id: element.id,
            path,
          });
        }
      }
    });

    console.log(`Processed ${wayCount} ways, created ${roads.length} valid road paths`);
    return roads;
  } catch (error) {
    console.error('Failed to fetch road data:', error);
    return [];
  }
};

// Utility functions
const getRandomColor = () => {
  // Softer, more muted colors for subtlety
  const colors = [
    '#a8a8a8', // soft gray
    '#b0c4de', // light steel blue
    '#c3b091', // khaki
    '#d3d3d3', // light gray
    '#bc8f8f', // rosy brown
    '#8fbc8f', // dark sea green
    '#a9a9a9', // dim gray
    '#deb887', // burlywood
  ];
  return colors[Math.floor(Math.random() * colors.length)];
};


// Calculate the correct angle between two points on the road
const calculateAngle = (p1: THREE.Vector2, p2: THREE.Vector2): number => {
  return Math.atan2(p2.y - p1.y, p2.x - p1.x);
};

const VehicleSimulation: React.FC<VehicleSimulationProps> = ({
                                                               centerLat,
                                                               centerLng,
                                                               radius = 100, // Reduced radius for a more localized area
                                                               vehicleCount = 10, // Fewer vehicles for better visibility
                                                               transformer,
                                                               enabled = true,
                                                               scale = 1 // Increased scale factor for better visibility
                                                             }) => {
  // If simulation is disabled, don't render anything
  if (!enabled) return null;
  const [roads, setRoads] = useState<RoadData[]>([]);
  const [vehicles, setVehicles] = useState<VehicleState[]>([]);
  const [loading, setLoading] = useState(true);
  const frameCount = useRef(0);

  // Fetch road data on component mount
  useEffect(() => {
    if (!enabled) return;

    const fetchRoads = async () => {
      setLoading(true);
      try {
        console.log(`Fetching roads within ${radius}m of ${centerLat},${centerLng}`);
        const roadData = await fetchRoadsFromOverpass(centerLat, centerLng, radius);
        console.log(`Fetched ${roadData.length} roads`);

        // Filter roads to only include those with at least 2 points
        const validRoads = roadData.filter(road => road.path.length >= 2);
        console.log(`Found ${validRoads.length} valid roads for vehicle simulation`);

        setRoads(validRoads);

        // Initialize vehicles even if no roads were found (will create dummy vehicles)
        initializeVehicles(validRoads);
      } catch (error) {
        console.error('Error in road fetch:', error);
        // Initialize vehicles with empty road data in case of error
        initializeVehicles([]);
      } finally {
        setLoading(false);
      }
    };

    fetchRoads();
  }, [centerLat, centerLng, radius, enabled]);

  // Initialize vehicles on roads
  const initializeVehicles = (roadData: RoadData[]) => {
    const newVehicles: VehicleState[] = [];

    // If no road data, create some dummy vehicles for testing
    if (roadData.length === 0) {
      console.log('No road data found, creating dummy vehicles');
      for (let i = 0; i < vehicleCount; i++) {
        // Create vehicles in a circle around the center point
        const angle = (i / vehicleCount) * Math.PI * 2;
        const distance = 20 + Math.random() * 30;
        const x = Math.cos(angle) * distance * scale;
        const z = Math.sin(angle) * distance * scale;

        newVehicles.push({
          id: i,
          position: new THREE.Vector3(x, 5.0, z), // Higher y for better visibility
          rotation: new THREE.Euler(0, angle, 0),
          roadIndex: -1, // Indicates not on a road
          pathIndex: 0,
          speed: 0.2 + Math.random() * 0.2, // Slower speed for more control
          color: getRandomColor(),
          direction: 1 // Start moving forward
        });
      }
      setVehicles(newVehicles);
      return;
    }

    // Filter out any roads with less than 2 points
    const validRoads = roadData.filter(road => road.path.length >= 2);
    if (validRoads.length === 0) {
      console.log('No valid roads found, creating dummy vehicles');
      initializeVehicles([]);
      return;
    }

    console.log(`Initializing ${vehicleCount} vehicles on ${roadData.length} roads`);

    // Distribute vehicles evenly among roads
    const vehiclesPerRoad = Math.max(1, Math.ceil(vehicleCount / roadData.length));
    let vehicleId = 0;

    for (let roadIndex = 0; roadIndex < roadData.length && vehicleId < vehicleCount; roadIndex++) {
      const road = roadData[roadIndex];

      if (!road || road.path.length < 2) {
        console.log(`Skipping invalid road at index ${roadIndex}`);
        continue;
      }

      for (let v = 0; v < vehiclesPerRoad && vehicleId < vehicleCount; v++) {
        // Place vehicle at a random position on the road
        const pathIndex = Math.floor(Math.random() * (road.path.length - 1));
        const point = road.path[pathIndex];
        const nextPoint = road.path[pathIndex + 1];

        // Convert to local coordinates and apply scale
        const [x, z] = transformer.latLngToLocal(point.y, point.x);
        const [nextX, nextZ] = transformer.latLngToLocal(nextPoint.y, nextPoint.x);

        // Calculate initial rotation - direction from current point to next point
        // Note: We're using a corrected angle calculation for the transformed coordinate system
        const direction = new THREE.Vector2(nextX - x, nextZ - z).normalize();
        const angle = Math.atan2(direction.y, direction.x);

        // Initially all vehicles travel forward for consistency
        const travelDirection = 1;
        // Account for the flipped z-axis in the scale [1,1,-1]
        const finalAngle = angle;

        newVehicles.push({
          id: vehicleId++,
          position: new THREE.Vector3(x * scale, 5.0 * scale, z * scale), // Higher y for better visibility
          rotation: new THREE.Euler(0, finalAngle, 0),
          roadIndex,
          pathIndex,
          speed: 0.2 + Math.random() * 0.2, // Lower, more realistic speed
          color: getRandomColor(),
          direction: travelDirection
        });
      }
    }

    setVehicles(newVehicles);
  };

  // Helper to ensure a vehicle stays precisely on its assigned road
  const snapVehicleToRoad = (vehicle: VehicleState, roads: RoadData[]): THREE.Vector3 => {
    if (vehicle.roadIndex === -1 || !roads[vehicle.roadIndex]) return vehicle.position;

    const road = roads[vehicle.roadIndex];
    const pathIndex = Math.max(0, Math.min(vehicle.pathIndex, road.path.length - 1));
    const point = road.path[pathIndex];
    const [x, z] = transformer.latLngToLocal(point.y, point.x);

    return new THREE.Vector3(x * scale, vehicle.position.y, z * scale);
  };

  // Animation loop
  useFrame(() => {
    if (!enabled) return;
    frameCount.current += 1;
    if (frameCount.current % 2 !== 0) return;

    setVehicles(prevVehicles => {
      return prevVehicles.map(vehicle => {
        // Handle dummy vehicles (no roads)
        if (vehicle.roadIndex === -1) {
          // Move in a circle pattern
          const angle = Math.atan2(vehicle.position.z, vehicle.position.x);
          const newAngle = angle + 0.01;
          const radius = Math.sqrt(vehicle.position.x ** 2 + vehicle.position.z ** 2);

          return {
            ...vehicle,
            position: new THREE.Vector3(
              Math.cos(newAngle) * radius,
              vehicle.position.y,
              Math.sin(newAngle) * radius
            ),
            rotation: new THREE.Euler(0, newAngle + Math.PI / 2, 0),
          };
        }

        // Get the road the vehicle is on
        const road = roads[vehicle.roadIndex];
        if (!road || road.path.length < 2) return vehicle;

        // Get current path index and determine next point based on direction
        let pathIndex = vehicle.pathIndex;
        let nextPathIndex;

        if (vehicle.direction === 1) {
          // Moving forward
          nextPathIndex = pathIndex + 1;
          // If at the end of the road, reverse direction
          if (nextPathIndex >= road.path.length) {
            return {
              ...vehicle,
              direction: -1,
              pathIndex: road.path.length - 2 // Second-to-last point
            };
          }
        } else {
          // Moving backward
          nextPathIndex = pathIndex - 1;
          // If at the start of the road, reverse direction
          if (nextPathIndex < 0) {
            return {
              ...vehicle,
              direction: 1,
              pathIndex: 1 // Second point
            };
          }
        }

        // Get the current and next points on the road
        const currentPoint = road.path[pathIndex];
        const nextPoint = road.path[nextPathIndex];

        // Convert to local coordinates and apply scale
        const [x1, z1] = transformer.latLngToLocal(currentPoint.y, currentPoint.x);
        const [x2, z2] = transformer.latLngToLocal(nextPoint.y, nextPoint.x);

        const scaledX1 = x1 * scale;
        const scaledZ1 = z1 * scale;
        const scaledX2 = x2 * scale;
        const scaledZ2 = z2 * scale;

        // Calculate direction vector and angle
        // Account for the [-1] scale in z-axis when calculating direction
        const dirVector = new THREE.Vector2(
          scaledX2 - scaledX1,
          -(scaledZ2 - scaledZ1) // Negate z component due to scale [1,1,-1]
        ).normalize();

        // Calculate proper angle for the vehicle to face the direction of travel
        // For the Three.js coordinate system with our scale adjustments
        const angle = Math.atan2(dirVector.y, dirVector.x);

        // Calculate distance to next point
        const currentPos = new THREE.Vector2(vehicle.position.x, vehicle.position.z);
        const nextPos = new THREE.Vector2(scaledX2, scaledZ2);
        const distance = currentPos.distanceTo(nextPos);

        // If we've reached the next point (or close enough), update the path index
        if (distance < vehicle.speed) {
          // Snap exactly to the next point for precision
          return {
            ...vehicle,
            position: new THREE.Vector3(scaledX2, vehicle.position.y, scaledZ2),
            pathIndex: nextPathIndex,
            rotation: new THREE.Euler(0, angle, 0)
          };
        }

        // Move towards the next point with adjusted z for flipped axis
        const newX = vehicle.position.x + dirVector.x * vehicle.speed;
        // For z, we need to handle the flipped axis when applying the direction
        const newZ = vehicle.position.z - dirVector.y * vehicle.speed; // Note the minus sign

        // Create the new position
        const newPosition = new THREE.Vector3(newX, vehicle.position.y, newZ);

        // Check if the new position is too far from the road segment
        // Calculate distance from the line segment
        const p = new THREE.Vector2(newPosition.x, newPosition.z);
        const a = new THREE.Vector2(scaledX1, scaledZ1);
        const b = new THREE.Vector2(scaledX2, scaledZ2);

        // Vector from a to b
        const ab = new THREE.Vector2().subVectors(b, a);
        // Vector from a to p
        const ap = new THREE.Vector2().subVectors(p, a);

        // Project ap onto ab to find the closest point on the line
        const projection = ap.dot(ab) / ab.lengthSq();

        // If projection is outside [0,1], the closest point is one of the endpoints
        let closestPoint;
        if (projection < 0) {
          closestPoint = a;
        } else if (projection > 1) {
          closestPoint = b;
        } else {
          closestPoint = new THREE.Vector2().addVectors(a, ab.multiplyScalar(projection));
        }

        // Get distance from p to the closest point
        const distance_p = p.distanceTo(closestPoint);

        // If distance is too large, snap back to the road
        const MAX_ALLOWED_DISTANCE = scale * 0.5; // Half a scale unit
        if (distance_p > MAX_ALLOWED_DISTANCE) {
          // Snap vehicle back to the closest point on the road
          return {
            ...vehicle,
            position: new THREE.Vector3(closestPoint.x, vehicle.position.y, closestPoint.y),
            rotation: new THREE.Euler(0, angle, 0)
          };
        }

        return {
          ...vehicle,
          position: newPosition,
          rotation: new THREE.Euler(0, angle, 0)
        };
      });
    });
  });

  // Render roads and vehicles
  return (
    <group rotation={[0, 0, 0]} scale={[1, 1, -1]}>
      {/* Debug road lines */}
      {/*{roads.map(road => {*/}
      {/*  // Create a properly formatted Float32Array for the road path*/}
      {/*  const points = road.path.flatMap(point => {*/}
      {/*    // Apply the transformer with an additional scale factor*/}
      {/*    const [x, z] = transformer.latLngToLocal(point.y, point.x);*/}
      {/*    return [x * scale, 0.2, z * scale]; // Scale down and position slightly above ground*/}
      {/*  });*/}

      {/*  // Create the Float32Array with the correct size*/}
      {/*  const positionArray = new Float32Array(points);*/}

      {/*  return (*/}
      {/*    <line key={`road-${road.id}`}>*/}
      {/*      <bufferGeometry attach="geometry">*/}
      {/*        <bufferAttribute*/}
      {/*          attach="attributes-position"*/}
      {/*          count={positionArray.length / 3}*/}
      {/*          array={positionArray}*/}
      {/*          itemSize={3}*/}
      {/*        />*/}
      {/*      </bufferGeometry>*/}
      {/*      <lineBasicMaterial attach="material" color="#444444" linewidth={1} />*/}
      {/*    </line>*/}
      {/*  );*/}
      {/*})}*/}

      {/* Vehicles */}
      {vehicles.map(vehicle => (
        <Vehicle
          key={`vehicle-${vehicle.id}`}
          position={vehicle.position}
          rotation={vehicle.rotation}
          color={vehicle.color}
          scale={scale}
        />
      ))}

      {loading && (
        <mesh position={[0, 10, 0]}>
          <sphereGeometry args={[1, 16, 16]} />
          <meshStandardMaterial color="red" />
        </mesh>
      )}
    </group>
  );
};

export default VehicleSimulation;
