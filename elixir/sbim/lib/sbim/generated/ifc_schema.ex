# 생성 파일 — 손으로 고치지 마라.
# 정본: ifcopenshell 0.9.0.post1 IFC4 스키마 · 대상 타입 fixtures/ifc/types.txt
# 생성: cd python && uv run python scripts/gen_ifc_schema.py

defmodule Sbim.Ifc.Schema do
  @moduledoc """
  IFC4 속성 표 — 타입마다 STEP 이름과 속성(자리 순서·종류). `Sbim.Ifc.Step` 이 이것으로 줄을 쓴다.
  ifc.py 가 만드는 타입만 담는다 — 새 타입을 쓰면 fixtures 를 다시 뜨고 이 표를 다시 생성한다.
  """

  @entities %{
    "IfcArbitraryClosedProfileDef" => {"IFCARBITRARYCLOSEDPROFILEDEF", [{:ProfileType, :enum}, {:ProfileName, :string}, {:OuterCurve, :ref}]},
    "IfcAxis2Placement3D" => {"IFCAXIS2PLACEMENT3D", [{:Location, :ref}, {:Axis, :ref}, {:RefDirection, :ref}]},
    "IfcBeam" => {"IFCBEAM", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ObjectType, :string}, {:ObjectPlacement, :ref}, {:Representation, :ref}, {:Tag, :string}, {:PredefinedType, :enum}]},
    "IfcBeamType" => {"IFCBEAMTYPE", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ApplicableOccurrence, :string}, {:HasPropertySets, {:list, :ref}}, {:RepresentationMaps, {:list, :ref}}, {:Tag, :string}, {:ElementType, :string}, {:PredefinedType, :enum}]},
    "IfcBuilding" => {"IFCBUILDING", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ObjectType, :string}, {:ObjectPlacement, :ref}, {:Representation, :ref}, {:LongName, :string}, {:CompositionType, :enum}, {:ElevationOfRefHeight, :real}, {:ElevationOfTerrain, :real}, {:BuildingAddress, :ref}]},
    "IfcBuildingElementProxy" => {"IFCBUILDINGELEMENTPROXY", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ObjectType, :string}, {:ObjectPlacement, :ref}, {:Representation, :ref}, {:Tag, :string}, {:PredefinedType, :enum}]},
    "IfcBuildingStorey" => {"IFCBUILDINGSTOREY", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ObjectType, :string}, {:ObjectPlacement, :ref}, {:Representation, :ref}, {:LongName, :string}, {:CompositionType, :enum}, {:Elevation, :real}]},
    "IfcCartesianPoint" => {"IFCCARTESIANPOINT", [{:Coordinates, {:list, :real}}]},
    "IfcCartesianPointList3D" => {"IFCCARTESIANPOINTLIST3D", [{:CoordList, {:list, {:list, :real}}}]},
    "IfcColourRgb" => {"IFCCOLOURRGB", [{:Name, :string}, {:Red, :real}, {:Green, :real}, {:Blue, :real}]},
    "IfcColumn" => {"IFCCOLUMN", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ObjectType, :string}, {:ObjectPlacement, :ref}, {:Representation, :ref}, {:Tag, :string}, {:PredefinedType, :enum}]},
    "IfcColumnType" => {"IFCCOLUMNTYPE", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ApplicableOccurrence, :string}, {:HasPropertySets, {:list, :ref}}, {:RepresentationMaps, {:list, :ref}}, {:Tag, :string}, {:ElementType, :string}, {:PredefinedType, :enum}]},
    "IfcCovering" => {"IFCCOVERING", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ObjectType, :string}, {:ObjectPlacement, :ref}, {:Representation, :ref}, {:Tag, :string}, {:PredefinedType, :enum}]},
    "IfcDirection" => {"IFCDIRECTION", [{:DirectionRatios, {:list, :real}}]},
    "IfcDoor" => {"IFCDOOR", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ObjectType, :string}, {:ObjectPlacement, :ref}, {:Representation, :ref}, {:Tag, :string}, {:OverallHeight, :real}, {:OverallWidth, :real}, {:PredefinedType, :enum}, {:OperationType, :enum}, {:UserDefinedOperationType, :string}]},
    "IfcDoorLiningProperties" => {"IFCDOORLININGPROPERTIES", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:LiningDepth, :real}, {:LiningThickness, :real}, {:ThresholdDepth, :real}, {:ThresholdThickness, :real}, {:TransomThickness, :real}, {:TransomOffset, :real}, {:LiningOffset, :real}, {:ThresholdOffset, :real}, {:CasingThickness, :real}, {:CasingDepth, :real}, {:ShapeAspectStyle, :ref}, {:LiningToPanelOffsetX, :real}, {:LiningToPanelOffsetY, :real}]},
    "IfcDoorPanelProperties" => {"IFCDOORPANELPROPERTIES", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:PanelDepth, :real}, {:PanelOperation, :enum}, {:PanelWidth, :real}, {:PanelPosition, :enum}, {:ShapeAspectStyle, :ref}]},
    "IfcDoorType" => {"IFCDOORTYPE", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ApplicableOccurrence, :string}, {:HasPropertySets, {:list, :ref}}, {:RepresentationMaps, {:list, :ref}}, {:Tag, :string}, {:ElementType, :string}, {:PredefinedType, :enum}, {:OperationType, :enum}, {:ParameterTakesPrecedence, :bool}, {:UserDefinedOperationType, :string}]},
    "IfcElementQuantity" => {"IFCELEMENTQUANTITY", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:MethodOfMeasurement, :string}, {:Quantities, {:list, :ref}}]},
    "IfcExtrudedAreaSolid" => {"IFCEXTRUDEDAREASOLID", [{:SweptArea, :ref}, {:Position, :ref}, {:ExtrudedDirection, :ref}, {:Depth, :real}]},
    "IfcGeometricRepresentationContext" => {"IFCGEOMETRICREPRESENTATIONCONTEXT", [{:ContextIdentifier, :string}, {:ContextType, :string}, {:CoordinateSpaceDimension, :integer}, {:Precision, :real}, {:WorldCoordinateSystem, :select}, {:TrueNorth, :ref}]},
    "IfcGrid" => {"IFCGRID", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ObjectType, :string}, {:ObjectPlacement, :ref}, {:Representation, :ref}, {:UAxes, {:list, :ref}}, {:VAxes, {:list, :ref}}, {:WAxes, {:list, :ref}}, {:PredefinedType, :enum}]},
    "IfcGridAxis" => {"IFCGRIDAXIS", [{:AxisTag, :string}, {:AxisCurve, :ref}, {:SameSense, :bool}]},
    "IfcLocalPlacement" => {"IFCLOCALPLACEMENT", [{:PlacementRelTo, :ref}, {:RelativePlacement, :select}]},
    "IfcMaterial" => {"IFCMATERIAL", [{:Name, :string}, {:Description, :string}, {:Category, :string}]},
    "IfcMaterialLayer" => {"IFCMATERIALLAYER", [{:Material, :ref}, {:LayerThickness, :real}, {:IsVentilated, :logical}, {:Name, :string}, {:Description, :string}, {:Category, :string}, {:Priority, :integer}]},
    "IfcMaterialLayerSet" => {"IFCMATERIALLAYERSET", [{:MaterialLayers, {:list, :ref}}, {:LayerSetName, :string}, {:Description, :string}]},
    "IfcMaterialLayerSetUsage" => {"IFCMATERIALLAYERSETUSAGE", [{:ForLayerSet, :ref}, {:LayerSetDirection, :enum}, {:DirectionSense, :enum}, {:OffsetFromReferenceLine, :real}, {:ReferenceExtent, :real}]},
    "IfcMember" => {"IFCMEMBER", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ObjectType, :string}, {:ObjectPlacement, :ref}, {:Representation, :ref}, {:Tag, :string}, {:PredefinedType, :enum}]},
    "IfcOpeningElement" => {"IFCOPENINGELEMENT", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ObjectType, :string}, {:ObjectPlacement, :ref}, {:Representation, :ref}, {:Tag, :string}, {:PredefinedType, :enum}]},
    "IfcPolyline" => {"IFCPOLYLINE", [{:Points, {:list, :ref}}]},
    "IfcProductDefinitionShape" => {"IFCPRODUCTDEFINITIONSHAPE", [{:Name, :string}, {:Description, :string}, {:Representations, {:list, :ref}}]},
    "IfcProject" => {"IFCPROJECT", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ObjectType, :string}, {:LongName, :string}, {:Phase, :string}, {:RepresentationContexts, {:list, :ref}}, {:UnitsInContext, :ref}]},
    "IfcPropertySet" => {"IFCPROPERTYSET", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:HasProperties, {:list, :ref}}]},
    "IfcPropertySingleValue" => {"IFCPROPERTYSINGLEVALUE", [{:Name, :string}, {:Description, :string}, {:NominalValue, :select}, {:Unit, :select}]},
    "IfcQuantityArea" => {"IFCQUANTITYAREA", [{:Name, :string}, {:Description, :string}, {:Unit, :ref}, {:AreaValue, :real}, {:Formula, :string}]},
    "IfcQuantityLength" => {"IFCQUANTITYLENGTH", [{:Name, :string}, {:Description, :string}, {:Unit, :ref}, {:LengthValue, :real}, {:Formula, :string}]},
    "IfcQuantityVolume" => {"IFCQUANTITYVOLUME", [{:Name, :string}, {:Description, :string}, {:Unit, :ref}, {:VolumeValue, :real}, {:Formula, :string}]},
    "IfcRailing" => {"IFCRAILING", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ObjectType, :string}, {:ObjectPlacement, :ref}, {:Representation, :ref}, {:Tag, :string}, {:PredefinedType, :enum}]},
    "IfcRailingType" => {"IFCRAILINGTYPE", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ApplicableOccurrence, :string}, {:HasPropertySets, {:list, :ref}}, {:RepresentationMaps, {:list, :ref}}, {:Tag, :string}, {:ElementType, :string}, {:PredefinedType, :enum}]},
    "IfcRelAggregates" => {"IFCRELAGGREGATES", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:RelatingObject, :ref}, {:RelatedObjects, {:list, :ref}}]},
    "IfcRelAssociatesMaterial" => {"IFCRELASSOCIATESMATERIAL", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:RelatedObjects, {:list, :select}}, {:RelatingMaterial, :select}]},
    "IfcRelContainedInSpatialStructure" => {"IFCRELCONTAINEDINSPATIALSTRUCTURE", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:RelatedElements, {:list, :ref}}, {:RelatingStructure, :ref}]},
    "IfcRelDefinesByProperties" => {"IFCRELDEFINESBYPROPERTIES", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:RelatedObjects, {:list, :ref}}, {:RelatingPropertyDefinition, :select}]},
    "IfcRelDefinesByType" => {"IFCRELDEFINESBYTYPE", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:RelatedObjects, {:list, :ref}}, {:RelatingType, :ref}]},
    "IfcRelFillsElement" => {"IFCRELFILLSELEMENT", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:RelatingOpeningElement, :ref}, {:RelatedBuildingElement, :ref}]},
    "IfcRelVoidsElement" => {"IFCRELVOIDSELEMENT", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:RelatingBuildingElement, :ref}, {:RelatedOpeningElement, :ref}]},
    "IfcSIUnit" => {"IFCSIUNIT", [{:Dimensions, :derived}, {:UnitType, :enum}, {:Prefix, :enum}, {:Name, :enum}]},
    "IfcShapeRepresentation" => {"IFCSHAPEREPRESENTATION", [{:ContextOfItems, :ref}, {:RepresentationIdentifier, :string}, {:RepresentationType, :string}, {:Items, {:list, :ref}}]},
    "IfcSite" => {"IFCSITE", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ObjectType, :string}, {:ObjectPlacement, :ref}, {:Representation, :ref}, {:LongName, :string}, {:CompositionType, :enum}, {:RefLatitude, {:list, :integer}}, {:RefLongitude, {:list, :integer}}, {:RefElevation, :real}, {:LandTitleNumber, :string}, {:SiteAddress, :ref}]},
    "IfcSlab" => {"IFCSLAB", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ObjectType, :string}, {:ObjectPlacement, :ref}, {:Representation, :ref}, {:Tag, :string}, {:PredefinedType, :enum}]},
    "IfcSlabType" => {"IFCSLABTYPE", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ApplicableOccurrence, :string}, {:HasPropertySets, {:list, :ref}}, {:RepresentationMaps, {:list, :ref}}, {:Tag, :string}, {:ElementType, :string}, {:PredefinedType, :enum}]},
    "IfcSpace" => {"IFCSPACE", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ObjectType, :string}, {:ObjectPlacement, :ref}, {:Representation, :ref}, {:LongName, :string}, {:CompositionType, :enum}, {:PredefinedType, :enum}, {:ElevationWithFlooring, :real}]},
    "IfcStair" => {"IFCSTAIR", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ObjectType, :string}, {:ObjectPlacement, :ref}, {:Representation, :ref}, {:Tag, :string}, {:PredefinedType, :enum}]},
    "IfcStairType" => {"IFCSTAIRTYPE", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ApplicableOccurrence, :string}, {:HasPropertySets, {:list, :ref}}, {:RepresentationMaps, {:list, :ref}}, {:Tag, :string}, {:ElementType, :string}, {:PredefinedType, :enum}]},
    "IfcStyledItem" => {"IFCSTYLEDITEM", [{:Item, :ref}, {:Styles, {:list, :select}}, {:Name, :string}]},
    "IfcSurfaceStyle" => {"IFCSURFACESTYLE", [{:Name, :string}, {:Side, :enum}, {:Styles, {:list, :select}}]},
    "IfcSurfaceStyleShading" => {"IFCSURFACESTYLESHADING", [{:SurfaceColour, :ref}, {:Transparency, :real}]},
    "IfcTransportElement" => {"IFCTRANSPORTELEMENT", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ObjectType, :string}, {:ObjectPlacement, :ref}, {:Representation, :ref}, {:Tag, :string}, {:PredefinedType, :enum}]},
    "IfcTriangulatedFaceSet" => {"IFCTRIANGULATEDFACESET", [{:Coordinates, :ref}, {:Normals, {:list, {:list, :real}}}, {:Closed, :bool}, {:CoordIndex, {:list, {:list, :integer}}}, {:PnIndex, {:list, :integer}}]},
    "IfcUnitAssignment" => {"IFCUNITASSIGNMENT", [{:Units, {:list, :select}}]},
    "IfcWall" => {"IFCWALL", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ObjectType, :string}, {:ObjectPlacement, :ref}, {:Representation, :ref}, {:Tag, :string}, {:PredefinedType, :enum}]},
    "IfcWallType" => {"IFCWALLTYPE", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ApplicableOccurrence, :string}, {:HasPropertySets, {:list, :ref}}, {:RepresentationMaps, {:list, :ref}}, {:Tag, :string}, {:ElementType, :string}, {:PredefinedType, :enum}]},
    "IfcWindow" => {"IFCWINDOW", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ObjectType, :string}, {:ObjectPlacement, :ref}, {:Representation, :ref}, {:Tag, :string}, {:OverallHeight, :real}, {:OverallWidth, :real}, {:PredefinedType, :enum}, {:PartitioningType, :enum}, {:UserDefinedPartitioningType, :string}]},
    "IfcWindowLiningProperties" => {"IFCWINDOWLININGPROPERTIES", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:LiningDepth, :real}, {:LiningThickness, :real}, {:TransomThickness, :real}, {:MullionThickness, :real}, {:FirstTransomOffset, :real}, {:SecondTransomOffset, :real}, {:FirstMullionOffset, :real}, {:SecondMullionOffset, :real}, {:ShapeAspectStyle, :ref}, {:LiningOffset, :real}, {:LiningToPanelOffsetX, :real}, {:LiningToPanelOffsetY, :real}]},
    "IfcWindowPanelProperties" => {"IFCWINDOWPANELPROPERTIES", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:OperationType, :enum}, {:PanelPosition, :enum}, {:FrameDepth, :real}, {:FrameThickness, :real}, {:ShapeAspectStyle, :ref}]},
    "IfcWindowType" => {"IFCWINDOWTYPE", [{:GlobalId, :string}, {:OwnerHistory, :ref}, {:Name, :string}, {:Description, :string}, {:ApplicableOccurrence, :string}, {:HasPropertySets, {:list, :ref}}, {:RepresentationMaps, {:list, :ref}}, {:Tag, :string}, {:ElementType, :string}, {:PredefinedType, :enum}, {:PartitioningType, :enum}, {:ParameterTakesPrecedence, :bool}, {:UserDefinedPartitioningType, :string}]}
  }

  @types %{
    "IfcBoolean" => {"IFCBOOLEAN", :bool},
    "IfcInteger" => {"IFCINTEGER", :integer},
    "IfcLabel" => {"IFCLABEL", :string},
    "IfcReal" => {"IFCREAL", :real}
  }

  @doc "개체 타입 → {STEP 이름, [{속성, 종류}]}"
  def entity!(name), do: Map.fetch!(@entities, name)

  @doc "값 타입(IfcLabel 등) → {STEP 이름, 종류}"
  def type!(name), do: Map.fetch!(@types, name)
end
