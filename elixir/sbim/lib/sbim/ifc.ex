defmodule Sbim.Ifc do
  @moduledoc """
  IFC 내보내기 — python/seoulgaok_bim_core/ifc.py `generate_ifc` 의 Elixir 판. scheme.json + units → IFC4 STEP.

  같은 입력·같은 GlobalId 수열이면 파이썬 판과 **같은 파일**이 나온다(FILE_NAME 줄만 다르다) —
  fixtures/ifc/*.ifc 가 정답이고 test/ifc_test.exs 가 줄 단위로 맞춘다. 그래서 개체를 만드는 **순서**까지
  파이썬을 따른다(STEP 번호 = 만든 순서). 파이썬 인자 평가 순서 때문에 순서가 갈리는 자리는 주석에 적었다.

  전략·범위·좌표 규약은 ifc.py 모듈 문서가 정본이다 — 요점만:
  - scheme 에 이미 삼각화된 메시(BufferGeometry)는 IfcTriangulatedFaceSet 으로 1:1, userData 가 있는 부재
    (벽·슬라브·기둥·보·문·창·마감)는 LOD300 개체(SweptSolid + 레이어셋 + Pset + Qto)로 승급.
  - 세대 polygon → IfcSpace + NetFloorArea. 코어 실·B1 기계실·승강기 카·구조 그리드·타입 객체·사업개요 Pset.
  - 메시는 parcel_center 상대, userData·세대 polygon 은 EPSG:5186 절대 → parcel_center 를 빼 같은 틀로.
  - **건축만.** 설비(MEP)는 엔진의 별도 모델이다.

  면적·둘레·안쪽 오프셋은 `geom:`(기본 `Sbim.Ifc.Geom.Plain`) — `Sbim.Ifc.Geom` 참고.
  """

  alias Sbim.Ifc.{GeometryCheck, Py, Step}
  alias Sbim.Ifc.Step.Ref

  # ── 뷰어(BuildingMeshVisualizer)와 동일한 색 팔레트 ──
  # 외장 preset: (외벽, 지붕) hex. sbim Exterior.style ↔ optionsMeta EXTERIOR_STYLES.
  @exterior %{
    "white" => {0xF5F5F5, 0xE0E0E0},
    "sandstone" => {0xD4C4A8, 0xB8B0A4},
    "brick" => {0x996633, 0xCCCCCC},
    "concrete" => {0x9A9A9A, 0x666666},
    # legacy alias
    "beige" => {0xD4C4A8, 0xB8B0A4}
  }
  @c_floor 0x888888
  @c_window 0x6E9BB8
  @c_parapet 0xE8E3D8
  @c_column 0x4A4A4A
  @c_parking 0xFFFFFF
  @c_door 0x8B6F47

  # role → {PredefinedType, 레이어셋 프리픽스}
  @slab_role %{
    "foundation" => {"BASESLAB", "[기초]"},
    "roof" => {"ROOF", "[지붕]"},
    "interfloor" => {"FLOOR", "[슬라브]"}
  }

  # (geom 키, IFC 클래스, 색, 투명도, 재질명, predefined) — 순서가 곧 개체 순서
  defp geom_map(wall_hex, roof_hex) do
    [
      {"walls", "IfcWall", wall_hex, 0.0, "철근콘크리트(외벽)", nil},
      {"floors", "IfcSlab", @c_floor, 0.0, "철근콘크리트(슬래브)", "FLOOR"},
      {"roof", "IfcSlab", roof_hex, 0.0, "철근콘크리트(지붕/천장)", "ROOF"},
      {"windows", "IfcWindow", @c_window, 0.55, "유리", nil},
      {"parapets", "IfcRailing", @c_parapet, 0.0, "철근콘크리트(파라펫)", nil},
      {"columns", "IfcColumn", @c_column, 0.0, "철근콘크리트(기둥)", "COLUMN"},
      {"beams", "IfcBeam", @c_column, 0.0, "철근콘크리트(보)", "BEAM"},
      {"doors", "IfcDoor", @c_door, 0.0, "목재(문)", nil},
      {"stairs", "IfcStair", @c_parapet, 0.0, "철근콘크리트(계단)", nil},
      {"coverings", "IfcCovering", 0xDCDCDC, 0.0, "마감", nil},
      {"parking_stalls", "IfcBuildingElementProxy", @c_parking, 0.4, nil, nil}
    ]
  end

  @qkind %{
    "L" => {"IfcQuantityLength", :LengthValue},
    "A" => {"IfcQuantityArea", :AreaValue},
    "V" => {"IfcQuantityVolume", :VolumeValue}
  }

  @doc """
  scheme(맵) + units(맵 목록) → IFC4 STEP 바이너리.

  옵션: `parcel_center: [x, y]`(없으면 `derive_parcel_center/1`) · `meta: %{"location", "pnu", "exterior_style",
  "skip_geometry_check"}` · `gid:`(0인자 함수, `Step.counter_gid/0` 등) · `time_stamp:` · `geom:`.
  형상이 터졌으면 `Sbim.Ifc.GeometryCheck.Error` 를 던진다(파이썬 `raise_if_insane`).
  """
  def generate_ifc(scheme, units, opts \\ []) do
    meta = Keyword.get(opts, :meta) || %{}
    unless meta["skip_geometry_check"], do: GeometryCheck.raise_if_insane!(scheme)
    [cx, cy] = Keyword.get(opts, :parcel_center) || derive_parcel_center(scheme)
    cx = cx * 1.0
    cy = cy * 1.0
    style_key = Py.str(Py.py_or(meta["exterior_style"], "brick"))
    {wall_hex, roof_hex} = Map.get(@exterior, style_key, @exterior["brick"])

    f = Step.new(Keyword.take(opts, [:gid]))
    reg = :ets.new(:sbim_ifc_reg, [:set, :private])

    try do
      c = %{
        f: f,
        reg: reg,
        cx: cx,
        cy: cy,
        wall_hex: wall_hex,
        geom: Keyword.get(opts, :geom, Sbim.Ifc.Geom.Plain)
      }

      build(c, scheme, units || [], meta, style_key, wall_hex, roof_hex)

      f
      |> Step.to_iodata(
        time_stamp: Keyword.get_lazy(opts, :time_stamp, &local_stamp/0),
        # 받는 쪽(아키캐드·레빗)은 헤더의 MVD 로 처리 방식을 고른다. 우리 파일은 벽이 SweptSolid 이고 개구부가
        # 창·문에 물려 있어 편집 가능한 모델로 넘어가야 한다 — ReferenceView 가 아니라 DesignTransferView 다.
        description: ["ViewDefinition [DesignTransferView_V1.0]"]
      )
      |> IO.iodata_to_binary()
    after
      :ets.delete(reg)
      Step.close(f)
    end
  end

  defp local_stamp do
    {{y, mo, d}, {h, mi, s}} = :calendar.local_time()

    :io_lib.format("~4..0B-~2..0B-~2..0BT~2..0B:~2..0B:~2..0B", [y, mo, d, h, mi, s])
    |> IO.iodata_to_binary()
  end

  # ═════════════════════════════════════════════════════════════════════════
  defp build(c, scheme, units, meta, style_key, wall_hex, roof_hex) do
    f = c.f

    units_assignment =
      cr(c, "IfcUnitAssignment",
        Units: [
          cr(c, "IfcSIUnit", UnitType: "LENGTHUNIT", Name: "METRE"),
          cr(c, "IfcSIUnit", UnitType: "AREAUNIT", Name: "SQUARE_METRE"),
          cr(c, "IfcSIUnit", UnitType: "VOLUMEUNIT", Name: "CUBIC_METRE")
        ]
      )

    world_axis =
      cr(c, "IfcAxis2Placement3D",
        Location: cr(c, "IfcCartesianPoint", Coordinates: [0.0, 0.0, 0.0])
      )

    ctx =
      cr(c, "IfcGeometricRepresentationContext",
        ContextType: "Model",
        CoordinateSpaceDimension: 3,
        Precision: 1.0e-5,
        WorldCoordinateSystem: world_axis
      )

    c = Map.put(c, :ctx, ctx)
    location = Py.str(Py.py_or(meta["location"], ""))
    pnu = Py.str(Py.py_or(meta["pnu"], ""))

    project =
      cr(c, "IfcProject",
        GlobalId: Step.gid(f),
        Name: Py.py_or(location, "SBIM Volume"),
        Description: "PNU #{pnu} · EPSG:5186 origin (#{Py.fmt_f(c.cx, 2)}, #{Py.fmt_f(c.cy, 2)})",
        RepresentationContexts: [ctx],
        UnitsInContext: units_assignment
      )

    # 파이썬 kwargs 평가 순서: GlobalId(_gid) → ObjectPlacement(개체 셋) → 본 개체
    g = Step.gid(f)

    site =
      cr(c, "IfcSite",
        GlobalId: g,
        Name: Py.py_or(location, "Site"),
        Description: "EPSG:5186 parcel_center (#{Py.fmt_f(c.cx, 3)}, #{Py.fmt_f(c.cy, 3)})",
        ObjectPlacement: placement(c),
        CompositionType: "ELEMENT"
      )

    g = Step.gid(f)

    building =
      cr(c, "IfcBuilding",
        GlobalId: g,
        Name: "Building",
        ObjectPlacement: placement(c, site.attrs[:ObjectPlacement]),
        CompositionType: "ELEMENT"
      )

    rel_aggregates(c, project, [site], "Project→Site")
    rel_aggregates(c, site, [building], "Site→Building")

    floor_plans = Py.py_or(scheme["floor_plans"], [])

    fdata =
      Map.new(floor_plans, fn fp -> {(fp["data"] || %{})["floor_id"], fp["data"] || %{}} end)

    c = Map.put(c, :fdata, fdata)

    # ── 난간 중복 층 판정 ── (ifc.py 같은 자리 주석: 같은 실물 난간이 두 층에 등재되면 층 천장과 base_z 가
    # 맞는 층을 정본으로, 없으면 층 번호가 낮은 쪽)
    railing_owner =
      Enum.reduce(floor_plans, %{}, fn fp, acc ->
        d = fp["data"] || %{}
        fid = d["floor_id"]

        if is_nil(fid) do
          acc
        else
          top = Py.num(d["floor_bottom_height"], (fid - 1) * 3.0) + Py.num(d["floor_height"], 3.0)

          fp
          |> Map.get("geom")
          |> Kernel.||(%{})
          |> Map.get("parapets")
          |> iter_geoms()
          |> Enum.reduce(acc, fn g, acc ->
            ud = g["userData"] || %{}

            if ud["kind"] != "railing" do
              acc
            else
              k = railing_key(ud)
              fits = abs(elem(k, 0) - top) < 0.01

              case Map.get(acc, k) do
                nil ->
                  Map.put(acc, k, {fid, fits})

                {cf, cfits} when (fits and not cfits) or (fits == cfits and fid < cf) ->
                  Map.put(acc, k, {fid, fits})

                _ ->
                  acc
              end
            end
          end)
        end
      end)

    # ── storey 생성 (지하 -1 포함, floor_id 순) ──
    {storey_by_floor, storeys_rev} =
      floor_plans
      |> Enum.sort_by(fn fp -> (fp["data"] || %{})["floor_id"] || 0 end)
      |> Enum.reduce({%{}, []}, fn fp, {m, l} ->
        d = fp["data"] || %{}
        fid = d["floor_id"]

        if is_nil(fid) do
          {m, l}
        else
          bottom = Py.num(d["floor_bottom_height"], (fid - 1) * 3.0)
          # floor_name = 옥탑층·지붕층 등 특수 층 (참조 도면 명명 규약)
          name = Py.py_or(d["floor_name"], if(fid == -1, do: "B1", else: "#{fid}F"))
          g = Step.gid(f)

          st =
            cr(c, "IfcBuildingStorey",
              GlobalId: g,
              Name: name,
              ObjectPlacement: placement(c, building.attrs[:ObjectPlacement], bottom),
              CompositionType: "ELEMENT",
              Elevation: bottom
            )

          {Map.put(m, fid, st), [st | l]}
        end
      end)

    storeys = Enum.reverse(storeys_rev)
    rel_aggregates(c, building, storeys, "Building→Storeys")

    # ── 층별 메시 → 타입별 IFC 요소 ──
    for fp <- floor_plans do
      d = fp["data"] || %{}
      fid = d["floor_id"]
      st = Map.get(storey_by_floor, fid)
      geom = fp["geom"] || %{}
      if st, do: floor_elements(c, fid, st, geom, wall_hex, roof_hex, railing_owner)
    end

    # ── 세대 IfcSpace (polygon, 룸) + NetFloorArea 수량 ──
    space_style = surface_style(c, 0x78A0C8, 0.7)

    n_units =
      Enum.reduce(units, 0, fn u, n ->
        poly = u["polygon"]
        fid = trunc(Py.py_or(u["floor"], 1))
        st = Map.get(storey_by_floor, fid)
        pts = if Py.truthy?(poly) and st, do: ring_xy(c, poly), else: []

        if length(pts) < 3 do
          n
        else
          sd = Map.get(fdata, fid, %{})

          bottom =
            Py.num(u["floor_bottom_height"], Py.num(sd["floor_bottom_height"], (fid - 1) * 3.0))

          fh = Py.num(u["floor_height"], Py.num(sd["floor_height"], 3.0))
          uid = Py.str(Map.get(u, "id", ""))
          core? = String.starts_with?(uid, "core-")
          net = (u["area"] || %{})["net"]
          name = if core?, do: "코어", else: "#{uid}호"
          g = Step.gid(c.f)
          pl = on_storey(c, st)
          rep = shape_solid(c, extruded_solid(c, pts, bottom - elev(st), fh), space_style)

          ent =
            cr(c, "IfcSpace",
              GlobalId: g,
              Name: name,
              LongName: if(is_number(net) and Py.truthy?(net), do: "#{Py.fmt_f(net, 1)}㎡"),
              ObjectPlacement: pl,
              Representation: rep,
              CompositionType: "ELEMENT",
              PredefinedType: "INTERNAL"
            )

          if not core? and is_number(net), do: area_quantity(c, ent, net)
          push(c, :spaces, fid, ent)

          dup = u["duplex_upper_polygon"]

          if Py.truthy?(dup) do
            dpts = ring_xy(c, dup)

            if length(dpts) >= 3 do
              up_fid = fid + 1
              up_key = if Map.has_key?(storey_by_floor, up_fid), do: up_fid, else: fid
              up_st = storey_by_floor[up_key]
              g = Step.gid(c.f)
              pl = on_storey(c, up_st)

              rep =
                shape_solid(
                  c,
                  extruded_solid(c, dpts, bottom + fh - elev(up_st), fh),
                  space_style
                )

              ent_up =
                cr(c, "IfcSpace",
                  GlobalId: g,
                  Name: "#{uid}호 복층",
                  ObjectPlacement: pl,
                  Representation: rep,
                  CompositionType: "ELEMENT",
                  PredefinedType: "INTERNAL"
                )

              push(c, :spaces, up_key, ent_up)
            end
          end

          if core?, do: n, else: n + 1
        end
      end)

    # ── 승강기 카 — IfcTransportElement (참조 도면 1층에 1개) ──
    # 승강로(벽·IfcSpace)만 있고 승강기 자체가 없으면 설비 물량·동선 검토가 안 된다.
    ev = (scheme["_core_layout"] || %{})["ev"]

    if Py.truthy?(ev) and Map.has_key?(storey_by_floor, 1) do
      ep = ring_xy(c, ev)

      if length(ep) >= 3 do
        ez = Py.num((fdata[1] || %{})["floor_bottom_height"], 0.0)
        # 카는 승강로보다 작다 — 벽·레일 여유 0.2m 인셋
        car =
          case c.geom.inset(ep, 0.2) do
            {:ok, r} -> r
            :empty -> ep
            :error -> ep
          end

        st1 = storey_by_floor[1]
        g = Step.gid(c.f)
        pl = on_storey(c, st1)

        rep =
          shape_solid(
            c,
            extruded_solid(c, car, ez + 0.1 - elev(st1), 2.2),
            surface_style(c, @c_column, 0.0)
          )

        lift =
          cr(c, "IfcTransportElement",
            GlobalId: g,
            Name: "승강기",
            ObjectPlacement: pl,
            Representation: rep,
            PredefinedType: "ELEVATOR"
          )

        pset(c, lift, "Pset_TransportElementCommon", [
          {"Reference", "P6-CO"},
          {"CapacityPeople", 6},
          {"FireExit", false}
        ])

        rel_contained(c, st1, [lift])
      end
    end

    # ── 코어 실(계단실·승강기·복도) + B1 기계실 IfcSpace ──
    # 참조 도면도 세대 외에 '기계실'·'저수조'를 실로 잡는다. 코어 3실은 층마다 존재하므로 거주층 전체에 stack.
    cl = scheme["_core_layout"] || %{}

    resi_fids =
      storey_by_floor
      |> Map.keys()
      |> Enum.filter(&(&1 >= 2 and not Py.truthy?((fdata[&1] || %{})["floor_name"])))
      |> Enum.sort()

    for {key, rname} <- [{"stair", "계단실"}, {"ev", "승강기"}, {"corridor", "복도"}],
        ring = cl[key],
        Py.truthy?(ring),
        pts = ring_xy(c, ring),
        length(pts) >= 3,
        fid <- resi_fids do
      d = fdata[fid] || %{}
      bottom = Py.num(d["floor_bottom_height"], 0.0)
      fh = Py.num(d["floor_height"], 3.0)
      st = storey_by_floor[fid]
      g = Step.gid(c.f)
      pl = on_storey(c, st)
      rep = shape_solid(c, extruded_solid(c, pts, bottom - elev(st), fh), space_style)

      sp =
        cr(c, "IfcSpace",
          GlobalId: g,
          Name: "#{fid}F #{rname}",
          LongName: rname,
          ObjectPlacement: pl,
          Representation: rep,
          CompositionType: "ELEMENT",
          PredefinedType: "INTERNAL"
        )

      with {:ok, a} <- c.geom.area(pts), do: area_quantity(c, sp, a)
      push(c, :spaces, fid, sp)
    end

    # B1 기계실 — 참조 도면과 동일 실명
    if Map.has_key?(storey_by_floor, -1) and Py.truthy?(scheme["_basement_outline"]) do
      bp = ring_xy(c, scheme["_basement_outline"])

      if length(bp) >= 3 do
        bd = fdata[-1] || %{}
        bz = Py.num(bd["floor_bottom_height"], -3.0)
        stb = storey_by_floor[-1]
        g = Step.gid(c.f)
        pl = on_storey(c, stb)

        rep =
          shape_solid(
            c,
            extruded_solid(c, bp, bz - elev(stb), Py.num(bd["floor_height"], 3.0)),
            space_style
          )

        sp =
          cr(c, "IfcSpace",
            GlobalId: g,
            Name: "B1 기계실",
            LongName: "기계실",
            ObjectPlacement: pl,
            Representation: rep,
            CompositionType: "ELEMENT",
            PredefinedType: "INTERNAL"
          )

        area_quantity(c, sp, Py.num(bd["floor_area"], 0.0))
        push(c, :spaces, -1, sp)
      end
    end

    # IfcSpace 는 spatial 이라 aggregates 로 storey 에 연결
    for {fid, sps} <- entries(c, :spaces),
        do: rel_aggregates(c, storey_by_floor[fid], sps, "Storey→Spaces")

    grid(c, floor_plans, storey_by_floor, storeys)

    # ── 타입 객체 방출 (IfcRelDefinesByType) ──
    for {{tcls, tname, tpredef}, members} <- entries(c, :types) do
      extra =
        case tcls do
          "IfcDoorType" ->
            # 좌/우 = 타입명 접미사(-L/-R). 문틀·문짝 상세 — 2D 뷰어가 창호 심볼을 그리는 근거. 문틀 40×110 관행.
            [
              OperationType:
                if(String.ends_with?(tname, "-R"),
                  do: "SINGLE_SWING_RIGHT",
                  else: "SINGLE_SWING_LEFT"
                ),
              HasPropertySets: [
                cr(c, "IfcDoorLiningProperties",
                  GlobalId: Step.gid(f),
                  Name: "#{tname} 문틀",
                  LiningDepth: 0.11,
                  LiningThickness: 0.04
                ),
                cr(c, "IfcDoorPanelProperties",
                  GlobalId: Step.gid(f),
                  Name: "#{tname} 문짝",
                  PanelOperation: "SWINGING",
                  PanelPosition: "MIDDLE"
                )
              ]
            ]

          "IfcWindowType" ->
            [
              PartitioningType: "SINGLE_PANEL",
              HasPropertySets: [
                cr(c, "IfcWindowLiningProperties",
                  GlobalId: Step.gid(f),
                  Name: "#{tname} 창틀",
                  LiningDepth: 0.15,
                  LiningThickness: 0.05
                ),
                cr(c, "IfcWindowPanelProperties",
                  GlobalId: Step.gid(f),
                  Name: "#{tname} 창짝",
                  OperationType: "SLIDINGHORIZONTAL",
                  PanelPosition: "MIDDLE"
                )
              ]
            ]

          _ ->
            []
        end

      t_ent = cr(c, tcls, [GlobalId: Step.gid(f), Name: tname, PredefinedType: tpredef] ++ extra)

      cr(c, "IfcRelDefinesByType",
        GlobalId: Step.gid(f),
        RelatedObjects: members,
        RelatingType: t_ent
      )
    end

    # ── 재질 일괄 연결 ──
    for {name, members} <- entries(c, :mats), members != [] do
      cr(c, "IfcRelAssociatesMaterial",
        GlobalId: Step.gid(f),
        Name: name,
        RelatedObjects: members,
        RelatingMaterial: get(c, {:mat, name})
      )
    end

    # ── 건물 Pset (사업개요) ──
    building_pset(c, building, scheme["data"], n_units, style_key)
  end

  # ── 층 하나: GEOM_MAP 순서대로 부재 → 난간동자·손스침 → 계단 부재 → RelContained ─────────────
  defp floor_elements(c, fid, st, geom, wall_hex, roof_hex, railing_owner) do
    acc = %{elems: [], walls: %{}, all_walls: []}

    acc =
      Enum.reduce(geom_map(wall_hex, roof_hex), acc, fn {key, ifc_cls, hexc, transp, mat, predef},
                                                        acc ->
        geoms = iter_geoms(geom[key])
        {acc, geoms} = lod300(c, key, geoms, st, fid, hexc, mat, acc)
        facesets = Enum.map(geoms, &faceset(c, &1, elev(st)))
        shape = shape_tess(c, facesets, surface_style(c, hexc, transp))

        if is_nil(shape) do
          acc
        else
          g = Step.gid(c.f)
          pl = on_storey(c, st)

          kw = [
            GlobalId: g,
            Name: "#{fname(fid)} #{key}",
            ObjectPlacement: pl,
            Representation: shape
          ]

          kw =
            if predef && ifc_cls in ["IfcSlab", "IfcColumn"],
              do: kw ++ [PredefinedType: predef],
              else: kw

          ent = cr(c, ifc_cls, kw)
          if mat, do: use_material(c, mat, ent)

          # 계단 — tessellation Body + 치수 Pset (ExtrudedSolid 계단은 아키캐드 판정 후)
          case key do
            "stairs" ->
              case Enum.find(geoms, &((&1["userData"] || %{})["kind"] == "stair")) do
                nil -> :ok
                g -> stair_pset(c, ent, g["userData"])
              end

              typed(c, ent, "IfcStairType", "계단(코어)", "NOTDEFINED")

            "parapets" ->
              typed(c, ent, "IfcRailingType", "옥상 난간", "GUARDRAIL")

            _ ->
              :ok
          end

          %{acc | elems: [ent | acc.elems]}
        end
      end)

    # ── 난간동자·손스침 → IfcMember (살 간격 ≤10cm, 시행령 40조②) ──
    rl =
      geom["parapets"]
      |> iter_geoms()
      |> Enum.filter(fn g ->
        ud = g["userData"] || %{}
        ud["kind"] == "railing" and elem(Map.get(railing_owner, railing_key(ud), {fid}), 0) == fid
      end)

    {elems, _} =
      for g <- rl,
          ud = g["userData"],
          mem <- railing_members(ud, Map.get(ud, "post_size", 0.04), Map.get(ud, "clear", 0.10)),
          reduce: {acc.elems, 0} do
        {elems, rseq} ->
          case faceset(c, mem.geom, elev(st)) do
            nil ->
              {elems, rseq}

            fs ->
              rseq = rseq + 1
              post? = mem.part == "post"
              g = Step.gid(c.f)
              pl = on_storey(c, st)
              rep = shape_tess(c, [fs], surface_style(c, @c_parapet, 0.0))

              m =
                cr(c, "IfcMember",
                  GlobalId: g,
                  Name:
                    "RL #{if post?, do: "POST", else: "HANDRAIL"} - #{Py.pad(fid, 2)}#{Py.pad(rseq, 3)}",
                  ObjectPlacement: pl,
                  Representation: rep,
                  PredefinedType: if(post?, do: "POST", else: "STRINGER")
                )

              use_material(c, "금속(난간)", m)

              pset(c, m, "Pset_MemberCommon", [
                {"IsExternal", true},
                {"LoadBearing", false},
                {"Reference", mem.part}
              ])

              {[m | elems], rseq}
          end
      end

    # ── 계단 부재 분해 — 챌판·디딤판·참 → IfcMember ──
    partname = %{"riser" => "RISER", "tread" => "TREAD", "landing" => "LANDING"}

    elems =
      geom["stairs"]
      |> iter_geoms()
      |> Enum.filter(&((&1["userData"] || %{})["kind"] == "stair_member"))
      |> Enum.reduce(elems, fn g, elems ->
        mu = g["userData"]

        case faceset(c, g, elev(st)) do
          nil ->
            elems

          fs ->
            sh = shape_tess(c, [fs], surface_style(c, @c_parapet, 0.0))
            part = Map.get(mu, "part", "tread")
            gid = Step.gid(c.f)
            pl = on_storey(c, st)

            m =
              cr(c, "IfcMember",
                GlobalId: gid,
                Name:
                  "SF #{Map.get(partname, part, String.upcase(part))} - #{Py.pad(fid, 2)}#{Py.pad(Map.get(mu, "index", 0), 3)}",
                ObjectPlacement: pl,
                Representation: sh
              )

            use_material(c, "철근콘크리트(계단)", m)

            pset(c, m, "Pset_MemberCommon", [
              {"IsExternal", false},
              {"LoadBearing", true},
              {"Reference", part}
            ])

            [m | elems]
        end
      end)

    rel_contained(c, st, Enum.reverse(elems))
  end

  # LOD300 경로 — userData 부재는 개별 승급, 잔여는 tessellation 폴백. {acc, 남은 geoms}
  defp lod300(c, "walls", geoms, st, fid, _hexc, _mat, acc) do
    {lod, rest} = split_kind(geoms, "wall")

    acc =
      lod
      |> Enum.with_index(1)
      |> Enum.reduce(acc, fn {g, seq}, acc ->
        ud = g["userData"]

        case wall_entity(c, ud, st, fid, seq) do
          nil ->
            acc

          w ->
            # 재질은 레이어셋(RelAssociatesMaterial)이 전담 — 이중 연결 금지.
            # 개구는 host 하나가 아니라 **겹치는 벽 전부**에 뚫어야 한다 — 외벽이 두 겹인 필지에서 바깥 벽이 안 뚫려
            # 창이 통째로 가려졌다(구의 57-93, 2026-08-24 IFC 렌더로 발견).
            %{
              acc
              | elems: [w | acc.elems],
                walls: Map.put(acc.walls, {key2(ud["p0"]), key2(ud["p1"])}, w),
                all_walls:
                  acc.all_walls ++ [{ud["p0"], ud["p1"], Py.num(Map.get(ud, "t", 0.2), 0.2), w}]
            }
        end
      end)

    {acc, rest}
  end

  defp lod300(c, key, geoms, st, fid, _hexc, mat, acc) when key in ["doors", "windows"] do
    {lod, rest} = split_kind(geoms, if(key == "doors", do: "door", else: "window"))

    acc =
      lod
      |> Enum.with_index(1)
      |> Enum.reduce(acc, fn {g, seq}, acc ->
        case opening_entity(c, g["userData"], st, fid, seq, acc, key == "windows") do
          nil ->
            acc

          e ->
            use_material(c, mat, e)
            %{acc | elems: [e | acc.elems]}
        end
      end)

    {acc, rest}
  end

  defp lod300(c, key, geoms, st, fid, hexc, _mat, acc) when key in ["floors", "roof"] do
    {lod, rest} = split_kind(geoms, "slab")

    acc =
      Enum.reduce(lod, acc, fn g, acc ->
        case slab_entity(c, g["userData"], st, fid, hexc) do
          nil -> acc
          s -> %{acc | elems: [s | acc.elems]}
        end
      end)

    {acc, rest}
  end

  defp lod300(c, "coverings", geoms, st, fid, hexc, _mat, acc) do
    {lod, rest} = split_kind(geoms, "covering")

    acc =
      Enum.reduce(lod, acc, fn g, acc ->
        ud = g["userData"]
        pts = ring_xy(c, Py.py_or(ud["outline"], []))

        if length(pts) < 3 do
          acc
        else
          t = Py.num(Map.get(ud, "t", 0.01), 0.01)
          solid = extruded_solid(c, pts, ud["top_z"] * 1.0 - t - elev(st), t)
          role = Map.get(ud, "role", "ceiling")
          ceil? = role == "ceiling"
          g = Step.gid(c.f)
          pl = on_storey(c, st)
          rep = shape_solid(c, solid, surface_style(c, hexc, 0.0))

          ent =
            cr(c, "IfcCovering",
              GlobalId: g,
              Name: "#{fid}F #{if ceil?, do: "천장마감", else: "테라스마감"}",
              ObjectPlacement: pl,
              Representation: rep,
              PredefinedType: if(ceil?, do: "CEILING", else: "FLOORING")
            )

          associate_material(
            c,
            ent,
            layer_set_usage(c, ud["layers"], if(ceil?, do: "[천장]", else: "[테라스]"), "AXIS3", 0.0)
          )

          with {:ok, a} <- c.geom.area(pts),
               do:
                 qto(c, ent, "Qto_CoveringBaseQuantities", [
                   {"A", "GrossArea", a},
                   {"L", "Width", t}
                 ])

          %{acc | elems: [ent | acc.elems]}
        end
      end)

    {acc, rest}
  end

  defp lod300(c, key, geoms, st, fid, _hexc, mat, acc) when key in ["columns", "beams"] do
    {lod, rest} = split_kind(geoms, if(key == "columns", do: "column", else: "beam"))

    acc =
      lod
      |> Enum.with_index(1)
      |> Enum.reduce(acc, fn {g, seq}, acc ->
        e =
          if key == "columns",
            do: column_entity(c, g["userData"], st, fid, seq),
            else: beam_entity(c, g["userData"], st, fid, seq)

        case e do
          nil ->
            acc

          e ->
            use_material(c, mat, e)
            %{acc | elems: [e | acc.elems]}
        end
      end)

    {acc, rest}
  end

  defp lod300(_c, _key, geoms, _st, _fid, _hexc, _mat, acc), do: {acc, geoms}

  defp split_kind(geoms, kind),
    do: Enum.split_with(geoms, &((&1["userData"] || %{})["kind"] == kind))

  # ── LOD300 부재 ───────────────────────────────────────────────────────────

  # 벽 userData → IfcWall: Axis(중심선) + Body(SweptSolid) + 레이어셋
  defp wall_entity(c, ud, st, fid, seq) do
    p0 = rel(c, ud["p0"])
    p1 = rel(c, ud["p1"])
    t = Py.num(Map.get(ud, "t", 0.2), 0.2)
    base_z = Py.num(Map.get(ud, "base_z", 0), 0)
    top_z = Py.num(Map.get(ud, "top_z", 3), 3)
    {dx, dy} = {elem(p1, 0) - elem(p0, 0), elem(p1, 1) - elem(p0, 1)}
    ln = :math.pow(dx * dx + dy * dy, 0.5)

    if ln < 1.0e-6 do
      nil
    else
      # 마이터 quad(emitter 확정, 단일 소스) 우선 — 없으면 t/2 연장 맞댐 폴백
      corners =
        if Py.truthy?(ud["quad"]) and length(ud["quad"]) >= 4 do
          Enum.map(ud["quad"], &rel(c, &1))
        else
          {ux, uy} = {dx / ln, dy / ln}
          {nx, ny, h} = {uy, -ux, t / 2.0}
          a = {elem(p0, 0) - ux * h, elem(p0, 1) - uy * h}
          b = {elem(p1, 0) + ux * h, elem(p1, 1) + uy * h}

          [
            {elem(a, 0) + nx * h, elem(a, 1) + ny * h},
            {elem(b, 0) + nx * h, elem(b, 1) + ny * h},
            {elem(b, 0) - nx * h, elem(b, 1) - ny * h},
            {elem(a, 0) - nx * h, elem(a, 1) - ny * h}
          ]
        end

      solid = extruded_solid(c, corners, base_z - elev(st), top_z - base_z)
      style = surface_style(c, c.wall_hex, 0.0)
      cr(c, "IfcStyledItem", Item: solid, Styles: [style])

      body =
        cr(c, "IfcShapeRepresentation",
          ContextOfItems: c.ctx,
          RepresentationIdentifier: "Body",
          RepresentationType: "SweptSolid",
          Items: [solid]
        )

      axis_pts = [
        cr(c, "IfcCartesianPoint", Coordinates: tl2(p0)),
        cr(c, "IfcCartesianPoint", Coordinates: tl2(p1))
      ]

      axis =
        cr(c, "IfcShapeRepresentation",
          ContextOfItems: c.ctx,
          RepresentationIdentifier: "Axis",
          RepresentationType: "Curve2D",
          Items: [cr(c, "IfcPolyline", Points: axis_pts)]
        )

      shape = cr(c, "IfcProductDefinitionShape", Representations: [axis, body])
      g = Step.gid(c.f)
      pl = on_storey(c, st)

      wall =
        cr(c, "IfcWall",
          GlobalId: g,
          Name: "#{fname(fid)} 벽-#{Py.pad(seq, 2)}",
          ObjectPlacement: pl,
          Representation: shape
        )

      # offset = 기준선(구조체 중심)→외피 (참조 도면 규약: 410 레이어셋에 +310)
      off = Py.num(Map.get(ud, "offset_out", t / 2.0), t / 2.0) * 1000.0
      ext = Py.truthy?(ud["exterior"])

      associate_material(
        c,
        wall,
        layer_set_usage(c, ud["layers"], if(ext, do: "[외벽]", else: "[내벽]"), "AXIS2", off)
      )

      t_tot = Py.num(Map.get(ud, "t_total", t), t)
      h = top_z - base_z

      pset(c, wall, "Pset_WallCommon", [
        {"IsExternal", ext},
        # 벽식 구조 — 전 벽 내력
        {"LoadBearing", true},
        {"ExtendToStructure", true},
        # EPS200 외단열 근사(W/㎡K)
        {"ThermalTransmittance", if(ext, do: 0.17)}
      ])

      qto(c, wall, "Qto_WallBaseQuantities", [
        {"L", "Length", ln},
        {"L", "Height", h},
        {"L", "Width", t_tot},
        {"A", "NetSideArea", ln * h},
        # 구조체(철콘) 물량 — 마감 제외
        {"V", "NetVolume", ln * h * t}
      ])

      typed(
        c,
        wall,
        "IfcWallType",
        if(ext, do: "[외벽] ", else: "[내벽] ") <> "#{Py.round0(t_tot * 1000)}",
        "SOLIDWALL"
      )

      wall
    end
  end

  # 슬라브 userData → IfcSlab(SweptSolid — outline 을 top_z-t 에서 t 압출)
  defp slab_entity(c, ud, st, fid, hexc) do
    outline = Py.py_or(ud["outline"], [])

    if length(outline) < 3 do
      nil
    else
      t = Py.num(Map.get(ud, "t", 0.15), 0.15)
      top_z = Py.num(Map.get(ud, "top_z", 0.0), 0.0)
      pts = ring_xy(c, outline)
      solid = extruded_solid(c, pts, top_z - t - elev(st), t)
      shape = shape_solid(c, solid, surface_style(c, hexc, 0.0))
      {predef, prefix} = Map.get(@slab_role, ud["role"], @slab_role["interfloor"])
      g = Step.gid(c.f)
      pl = on_storey(c, st)

      slab =
        cr(c, "IfcSlab",
          GlobalId: g,
          Name: "#{fname(fid)} #{String.slice(prefix, 1..-2//1)}슬라브",
          ObjectPlacement: pl,
          Representation: shape,
          PredefinedType: predef
        )

      layers = Py.py_or(ud["layers"], [%{"name" => "철근콘크리트", "t" => t}])
      associate_material(c, slab, layer_set_usage(c, layers, prefix, "AXIS3", 0.0))

      {area, per} =
        with {:ok, a} <- c.geom.area(pts), {:ok, p} <- c.geom.perimeter(pts) do
          {a, p}
        else
          _ -> {0.0, 0.0}
        end

      pset(c, slab, "Pset_SlabCommon", [
        {"IsExternal", ud["role"] in ["roof", "foundation"]},
        {"LoadBearing", true},
        {"PitchAngle", 0.0}
      ])

      qto(c, slab, "Qto_SlabBaseQuantities", [
        {"L", "Width", t},
        {"L", "Perimeter", per},
        {"A", "GrossArea", area},
        {"V", "GrossVolume", area * t}
      ])

      typed(c, slab, "IfcSlabType", "#{prefix} #{Py.round0(t * 1000)}", predef)
      slab
    end
  end

  # 기둥 userData → IfcColumn (정사각 프로파일 SweptSolid)
  defp column_entity(c, ud, st, fid, seq) do
    [ccx, ccy] = Py.py_or(ud["center"], [c.cx, c.cy])
    half = Py.num(Map.get(ud, "size", 0.6), 0.6) / 2.0
    {x, y} = {ccx * 1.0 - c.cx, ccy * 1.0 - c.cy}
    base_z = Py.num(Map.get(ud, "base_z", 0), 0)
    top_z = Py.num(Map.get(ud, "top_z", 3), 3)
    pts = [{x - half, y - half}, {x + half, y - half}, {x + half, y + half}, {x - half, y + half}]
    solid = extruded_solid(c, pts, base_z - elev(st), top_z - base_z)
    shape = shape_solid(c, solid, surface_style(c, @c_column, 0.0))
    g = Step.gid(c.f)
    pl = on_storey(c, st)

    col =
      cr(c, "IfcColumn",
        GlobalId: g,
        Name:
          "#{fid}F 기둥-#{Py.pad(seq, 2)}" <> if(Py.truthy?(ud["transfer"]), do: " (전이)", else: ""),
        ObjectPlacement: pl,
        Representation: shape,
        PredefinedType: "COLUMN"
      )

    size = Py.num(Map.get(ud, "size", 0.6), 0.6)
    hgt = top_z - base_z
    mm = Py.round0(size * 1000)

    pset(c, col, "Pset_ColumnCommon", [
      {"IsExternal", false},
      {"LoadBearing", true},
      {"Reference", "C#{mm}x#{mm}"}
    ])

    qto(c, col, "Qto_ColumnBaseQuantities", [
      {"L", "Length", hgt},
      {"A", "CrossSectionArea", size * size},
      {"A", "OuterSurfaceArea", 4 * size * hgt},
      {"V", "GrossVolume", size * size * hgt}
    ])

    typed(c, col, "IfcColumnType", "C#{mm}x#{mm}", "COLUMN")
    col
  end

  # 보 userData → IfcBeam (w×h 프로파일 — 축선 따라 하향 배치)
  defp beam_entity(c, ud, st, fid, seq) do
    p0 = rel(c, ud["p0"])
    p1 = rel(c, ud["p1"])
    w = Py.num(Map.get(ud, "w", 0.6), 0.6)
    h = Py.num(Map.get(ud, "h", 0.8), 0.8)
    top_z = Py.num(Map.get(ud, "top_z", 3.0), 3.0)
    {dx, dy} = {elem(p1, 0) - elem(p0, 0), elem(p1, 1) - elem(p0, 1)}
    ln = :math.pow(dx * dx + dy * dy, 0.5)

    if ln < 1.0e-6 do
      nil
    else
      {ux, uy} = {dx / ln, dy / ln}
      {nx, ny, hw} = {uy, -ux, w / 2.0}
      a = {elem(p0, 0) - ux * hw, elem(p0, 1) - uy * hw}
      b = {elem(p1, 0) + ux * hw, elem(p1, 1) + uy * hw}

      pts = [
        {elem(a, 0) + nx * hw, elem(a, 1) + ny * hw},
        {elem(b, 0) + nx * hw, elem(b, 1) + ny * hw},
        {elem(b, 0) - nx * hw, elem(b, 1) - ny * hw},
        {elem(a, 0) - nx * hw, elem(a, 1) - ny * hw}
      ]

      solid = extruded_solid(c, pts, top_z - h - elev(st), h)
      shape = shape_solid(c, solid, surface_style(c, @c_column, 0.0))
      transfer? = ud["role"] == "transfer"
      wh = "#{Py.round0(w * 1000)}x#{Py.round0(h * 1000)}"
      g = Step.gid(c.f)
      pl = on_storey(c, st)

      beam =
        cr(c, "IfcBeam",
          GlobalId: g,
          Name: "#{fid}F #{if transfer?, do: "전이보", else: "보"}-#{Py.pad(seq, 2)} #{wh}",
          ObjectPlacement: pl,
          Representation: shape,
          PredefinedType: "BEAM"
        )

      ref = "#{if transfer?, do: "TG", else: "G"}#{wh}"

      pset(c, beam, "Pset_BeamCommon", [
        {"IsExternal", false},
        {"LoadBearing", true},
        {"Reference", ref}
      ])

      qto(c, beam, "Qto_BeamBaseQuantities", [
        {"L", "Length", ln},
        {"A", "CrossSectionArea", w * h},
        {"A", "OuterSurfaceArea", 2 * (w + h) * ln},
        {"V", "GrossVolume", w * h * ln}
      ])

      typed(c, beam, "IfcBeamType", ref, "BEAM")
      beam
    end
  end

  # 계단 치수 Pset — 단높이/단너비/단수/계단판 두께
  defp stair_pset(c, element, ud) do
    props =
      for {nm, val, kind} <- [
            {"단높이(m)", Py.num(Map.get(ud, "riser", 0), 0), "IfcReal"},
            {"단너비(m)", Py.num(Map.get(ud, "tread", 0), 0), "IfcReal"},
            {"단수", trunc(Map.get(ud, "n_risers", 0)), "IfcInteger"},
            {"계단판두께(m)", Py.num(Map.get(ud, "waist", 0.15), 0.15), "IfcReal"},
            {"flights", trunc(Map.get(ud, "flights", 2)), "IfcInteger"}
          ],
          do: cr(c, "IfcPropertySingleValue", Name: nm, NominalValue: Step.typed(kind, val))

    ps =
      cr(c, "IfcPropertySet", GlobalId: Step.gid(c.f), Name: "Pset_SBIM_계단", HasProperties: props)

    cr(c, "IfcRelDefinesByProperties",
      GlobalId: Step.gid(c.f),
      RelatedObjects: [element],
      RelatingPropertyDefinition: ps
    )
  end

  # 문·창 userData → IfcDoor/IfcWindow + 호스트 IfcWall 에 IfcOpeningElement(RelVoids).
  # host_wall(p0,p1) 좌표키로 이 층 IfcWall 을 찾아 벽에 구멍을 뚫는다 — 없으면 문만 배치(폴백으로 정직).
  defp opening_entity(c, ud, st, fid, seq, acc, window?) do
    p0 = rel(c, ud["p0"])
    p1 = rel(c, ud["p1"])
    w = Py.num(Map.get(ud, "width", 0.9), 0.9)
    hgt = Py.num(Map.get(ud, "height", 2.1), 2.1)
    base_z = Py.num(Map.get(Map.get(c.fdata, fid, %{}), "floor_bottom_height", 0.0), 0.0)
    # 창은 창대(sill) 높이에서 시작 — 절대 z 로 방출됨
    base_z = if window?, do: Py.num(Map.get(ud, "sill", base_z + 0.9), base_z + 0.9), else: base_z
    {dx, dy} = {elem(p1, 0) - elem(p0, 0), elem(p1, 1) - elem(p0, 1)}
    ln = :math.pow(dx * dx + dy * dy, 0.5)

    if ln < 1.0e-6 do
      nil
    else
      {ux, uy} = {dx / ln, dy / ln}
      {nx, ny} = {uy, -ux}
      host = Py.py_or(ud["host_wall"], %{})

      host_wall =
        if Py.truthy?(host),
          do: Map.get(acc.walls, {key2(Map.get(host, "p0", [])), key2(Map.get(host, "p1", []))}),
          else: nil

      # 이 개구가 관통하는 벽 전부 — 중심선까지 거리 ≤ (벽두께/2 + 여유)이고 방향이 대체로 같으면 같은 자리. host 는 항상 포함.
      {mx, my} = {(elem(p0, 0) + elem(p1, 0)) / 2, (elem(p0, 1) + elem(p1, 1)) / 2}
      hosts0 = if host_wall, do: [{host_wall, Py.num(Map.get(host, "t", 0.2), 0.2)}], else: []

      hosts =
        Enum.reduce(acc.all_walls, hosts0, fn {wp0, wp1, wt, wall}, hs ->
          if Enum.any?(hs, fn {hw, _} -> hw.id == wall.id end) do
            hs
          else
            {ax, ay} = rel(c, wp0)
            {bx, by} = rel(c, wp1)
            {wdx, wdy} = {bx - ax, by - ay}
            wl = :math.pow(wdx * wdx + wdy * wdy, 0.5)

            cond do
              wl < 1.0e-6 ->
                hs

              true ->
                t_ = max(0.0, min(1.0, ((mx - ax) * wdx + (my - ay) * wdy) / (wl * wl)))
                {px_, py_} = {ax + wdx * t_, ay + wdy * t_}

                cond do
                  :math.pow(:math.pow(mx - px_, 2) + :math.pow(my - py_, 2), 0.5) >
                      wt / 2.0 + 0.35 ->
                    hs

                  # 방향이 대체로 같아야(수직 교차벽에 구멍 내지 않게) — |cos| ≥ 0.87
                  abs((wdx * ux + wdy * uy) / wl) < 0.87 ->
                    hs

                  true ->
                    hs ++ [{wall, wt}]
                end
            end
          end
        end)

      {host_wall, opening} =
        if hosts == [] do
          {host_wall, nil}
        else
          # 개구 두께는 **마감 포함 벽 두께**(wall_total) 기준 — 구조 t(0.2)로 잡으면 마감까지 두꺼운 벽(0.41)을
          # 관통하지 못해 창이 벽 속에 갇힌다(구의 57-93: 창 14/14 불가시, 2026-08-24).
          wt =
            Enum.max(
              [
                Py.num(Py.py_or(ud["wall_total"], 0.0), 0.0),
                Py.num(Py.py_or(ud["wall_t"], 0.0), 0.0)
              ] ++ Enum.map(hosts, &elem(&1, 1))
            )

          ot = wt / 2.0 + 0.15
          opts = box(p0, p1, nx, ny, ot)
          osolid = extruded_solid(c, opts, base_z - elev(st), hgt)

          oshape =
            cr(c, "IfcProductDefinitionShape",
              Representations: [
                cr(c, "IfcShapeRepresentation",
                  ContextOfItems: c.ctx,
                  RepresentationIdentifier: "Body",
                  RepresentationType: "SweptSolid",
                  Items: [osolid]
                )
              ]
            )

          g = Step.gid(c.f)
          pl = on_storey(c, st)

          opening =
            cr(c, "IfcOpeningElement",
              GlobalId: g,
              Name: "#{fid}F 개구-#{Py.pad(seq, 2)}",
              ObjectPlacement: pl,
              Representation: oshape
            )

          for {hw, _} <- hosts,
              do:
                cr(c, "IfcRelVoidsElement",
                  GlobalId: Step.gid(c.f),
                  RelatingBuildingElement: hw,
                  RelatedOpeningElement: opening
                )

          {elem(hd(hosts), 0), opening}
        end

      # 창짝·문짝 (얇은 패널)
      hw = if window?, do: 0.015, else: 0.04
      dsolid = extruded_solid(c, box(p0, p1, nx, ny, hw), base_z - elev(st), hgt)

      dshape =
        shape_solid(
          c,
          dsolid,
          if(window?, do: surface_style(c, @c_window, 0.55), else: surface_style(c, @c_door, 0.0))
        )

      unit = Py.str(Map.get(ud, "unit_id", ""))

      name =
        if window?,
          do: "#{fid}F #{Py.str(Py.py_or(ud["type"], "창"))}-#{Py.pad(seq, 2)} (#{unit})",
          else: "#{fid}F #{Py.str(Py.py_or(ud["door_type"], "세대"))}문-#{Py.pad(seq, 2)} (#{unit})"

      g = Step.gid(c.f)
      pl = on_storey(c, st)

      door =
        cr(c, if(window?, do: "IfcWindow", else: "IfcDoor"),
          GlobalId: g,
          Name: name,
          ObjectPlacement: pl,
          Representation: dshape,
          PredefinedType: if(window?, do: "WINDOW", else: "DOOR"),
          OverallHeight: hgt,
          OverallWidth: w
        )

      if host_wall,
        do:
          cr(c, "IfcRelFillsElement",
            GlobalId: Step.gid(c.f),
            RelatingOpeningElement: opening,
            RelatedBuildingElement: door
          )

      wh = "#{Py.round0(w * 1000)}x#{Py.round0(hgt * 1000)}"

      if window? do
        # 자료값(u_value, 0.1.4) — 없으면 로이 복층유리 근사 (W/㎡K)
        pset(c, door, "Pset_WindowCommon", [
          {"IsExternal", true},
          {"Reference", "W#{wh}"},
          {"ThermalTransmittance", ud["u_value"] || 1.5}
        ])

        qto(c, door, "Qto_WindowBaseQuantities", [
          {"L", "Width", w},
          {"L", "Height", hgt},
          {"A", "Area", w * hgt}
        ])

        typed(c, door, "IfcWindowType", "W#{wh}", "WINDOW")
      else
        # 피난 출구 문(옥상·기계실) · 방화문 등급(fire_door, 0.1.2) — 없으면 옛 근사
        fire = Py.truthy?(ud["fire_exit"])
        rating = ud["fire_door"] || if(fire, do: "을종")
        fd = if rating, do: "FD", else: "D"

        pset(c, door, "Pset_DoorCommon", [
          {"IsExternal", false},
          {"FireExit", fire},
          {"FireRating", rating},
          {"Reference", "#{fd}#{wh}"}
        ])

        qto(c, door, "Qto_DoorBaseQuantities", [
          {"L", "Width", w},
          {"L", "Height", hgt},
          {"A", "Area", w * hgt}
        ])

        # 실스윙 → 좌/우 타입 분화. 힌지=p0, 스윙면=swing_into 방향이고, 스윙면에서 문을 바라볼 때 힌지가 왼쪽이면
        # LEFT ⟺ cross(u, s) < 0. 이게 없으면 2D 뷰어(아키캐드 등)가 **모든 문을 왼여닫이로** 그린다.
        hand =
          case ud["swing_into"] do
            into when is_list(into) and into != [] ->
              sx = Enum.at(into, 0) * 1.0 - c.cx - (elem(p0, 0) + elem(p1, 0)) / 2.0
              sy = Enum.at(into, 1) * 1.0 - c.cy - (elem(p0, 1) + elem(p1, 1)) / 2.0
              if ux * sy - uy * sx >= 0, do: "R", else: "L"

            _ ->
              "L"
          end

        typed(c, door, "IfcDoorType", "#{fd}#{wh}-#{hand}", "DOOR")
      end

      door
    end
  end

  defp box({p0x, p0y}, {p1x, p1y}, nx, ny, o) do
    [
      {p0x + nx * o, p0y + ny * o},
      {p1x + nx * o, p1y + ny * o},
      {p1x - nx * o, p1y - ny * o},
      {p0x - nx * o, p0y - ny * o}
    ]
  end

  # ── IfcGrid — 2층 외벽 중심선 = 구조 그리드 (벽식: 벽 중심선이 구조축) ──
  # 아키캐드/레빗에서 축선 스냅·일람 기준이 된다. 파이썬은 통째로 try/except 라 실패해도 조용히 넘어간다.
  defp grid(c, floor_plans, storey_by_floor, storeys) do
    gw =
      for fp <- floor_plans,
          (fp["data"] || %{})["floor_id"] == 2,
          gg <- iter_geoms((fp["geom"] || %{})["walls"]),
          ud = gg["userData"] || %{},
          ud["kind"] == "wall" and Py.truthy?(ud["exterior"]),
          do: ud

    if length(gw) >= 2 do
      {_ref, uax, vax} =
        Enum.reduce(gw, {nil, [], []}, fn ud, {ref, uax, vax} ->
          p0 = rel(c, ud["p0"])
          p1 = rel(c, ud["p1"])

          pl =
            cr(c, "IfcPolyline",
              Points: [
                cr(c, "IfcCartesianPoint", Coordinates: tl2(p0)),
                cr(c, "IfcCartesianPoint", Coordinates: tl2(p1))
              ]
            )

          {dx, dy} = {elem(p1, 0) - elem(p0, 0), elem(p1, 1) - elem(p0, 1)}

          # math.hypot — Erlang 엔 없다. 값은 방향 판정(0.7 문턱)에만 쓰여 마지막 자리 차이는 파일에 안 나온다
          ln = Py.py_or(:math.sqrt(dx * dx + dy * dy), 1.0)
          dn = {dx / ln, dy / ln}
          ref = ref || dn
          u? = abs(elem(dn, 0) * elem(ref, 0) + elem(dn, 1) * elem(ref, 1)) > 0.7
          tag = if u?, do: "X#{length(uax) + 1}", else: "Y#{length(vax) + 1}"
          ax = cr(c, "IfcGridAxis", AxisTag: tag, AxisCurve: pl, SameSense: true)
          if u?, do: {ref, uax ++ [ax], vax}, else: {ref, uax, vax ++ [ax]}
        end)

      if uax != [] and vax != [] do
        st = Map.get(storey_by_floor, 1, hd(storeys))
        g = Step.gid(c.f)

        grid =
          cr(c, "IfcGrid",
            GlobalId: g,
            Name: "구조 그리드(벽 중심선)",
            ObjectPlacement: placement(c, st.attrs[:ObjectPlacement]),
            UAxes: uax,
            VAxes: vax
          )

        rel_contained(c, st, [grid])
      end
    end
  end

  # ── 건물 Pset (사업개요) ──
  defp building_pset(c, building, data, n_units, style_name) do
    pv = fn name, val, kind ->
      cr(c, "IfcPropertySingleValue", Name: name, NominalValue: Step.typed(kind, val))
    end

    props =
      if Py.truthy?(data) do
        for {k, label} <- [
              {"lot_area", "대지면적(㎡)"},
              {"build_area", "건축면적(㎡)"},
              {"far", "용적률(%)"},
              {"bcr", "건폐율(%)"}
            ],
            not is_nil(data[k]),
            do: pv.(label, data[k] * 1.0, "IfcReal")
      else
        []
      end

    props =
      if Py.truthy?(data) and Py.truthy?(data["pnu"]),
        do: props ++ [pv.("PNU", Py.str(data["pnu"]), "IfcLabel")],
        else: props

    props = if Py.truthy?(n_units), do: props ++ [pv.("세대수", n_units, "IfcInteger")], else: props

    props =
      if Py.truthy?(style_name), do: props ++ [pv.("외장재", style_name, "IfcLabel")], else: props

    if props != [] do
      ps =
        cr(c, "IfcPropertySet",
          GlobalId: Step.gid(c.f),
          Name: "Pset_SBIM_사업개요",
          HasProperties: props
        )

      cr(c, "IfcRelDefinesByProperties",
        GlobalId: Step.gid(c.f),
        RelatedObjects: [building],
        RelatingPropertyDefinition: ps
      )
    end
  end

  # ── 공용 조각 ─────────────────────────────────────────────────────────────

  defp cr(c, type, attrs), do: Step.create(c.f, type, attrs)

  defp fname(-1), do: "B1"
  defp fname(fid), do: "#{fid}F"

  defp rel(c, [x, y | _]), do: {x * 1.0 - c.cx, y * 1.0 - c.cy}
  defp tl2({x, y}), do: [x, y]

  defp key2(l) when is_list(l), do: Enum.map(l, &Py.round_n(&1, 2))

  defp railing_key(ud) do
    {Py.round_n(Py.num(Py.py_or(Map.get(ud, "base_z", 0), 0), 0), 3),
     Py.round_n(Py.num(Py.py_or(Map.get(ud, "top_z", 0), 0), 0), 3), ud["lines"]}
  end

  defp elev(%Ref{attrs: a}), do: Py.num(Py.py_or(a[:Elevation], 0.0), 0.0)

  defp rgb(c, hex) do
    import Bitwise

    cr(c, "IfcColourRgb",
      Red: (hex >>> 16 &&& 0xFF) / 255.0,
      Green: (hex >>> 8 &&& 0xFF) / 255.0,
      Blue: (hex &&& 0xFF) / 255.0
    )
  end

  # 표면 스타일 (색·투명도) — 색별 1회 생성 후 재사용
  defp surface_style(c, hex, transparency) do
    cache(c, {:style, hex, Py.round_n(transparency, 2)}, fn ->
      shading =
        cr(c, "IfcSurfaceStyleShading",
          SurfaceColour: rgb(c, hex),
          Transparency: transparency * 1.0
        )

      cr(c, "IfcSurfaceStyle", Side: "BOTH", Styles: [shading])
    end)
  end

  # 재질 (적산용 semantic) — 이름별 1회, 요소 모아 끝에 일괄 연결
  defp use_material(c, name, element) do
    cache(c, {:mat, name}, fn -> cr(c, "IfcMaterial", Name: name) end)
    push(c, :mats, name, element)
  end

  # 타입 객체 — 같은 사양 부재를 IfcXxxType 으로 묶는다 (아키캐드/레빗 타입 단위 일괄 편집·일람표 기반)
  defp typed(c, element, tcls, name, predef), do: push(c, :types, {tcls, name, predef}, element)

  # 레이어 리스트 → IfcMaterialLayerSetUsage (프리픽스+두께 튜플 캐시). 벽=AXIS2(중심선 기준 -t/2), 슬라브=AXIS3(상면 기준 하향).
  defp layer_set_usage(c, layers, prefix, direction, offset) do
    key = [
      prefix
      | Enum.map(layers || [], fn l ->
          {Map.get(l, "name", "?"), Py.round_n(Py.num(Map.get(l, "t", 0), 0), 4)}
        end)
    ]

    if length(key) < 2 do
      nil
    else
      ls =
        cache(c, {:layerset, key}, fn ->
          mls =
            for {nm, t} <- tl(key) do
              cr(c, "IfcMaterialLayer",
                Material: cr(c, "IfcMaterial", Name: nm),
                LayerThickness: t * 1000.0,
                Name: "#{nm}#{Py.round0(t * 1000)}"
              )
            end

          # 참조 도면 명명 관행: '[외벽] // 철콘200 // EPS200 / STO10'
          label =
            tl(key)
            |> Enum.map(fn {nm, t} -> "#{nm}#{Py.round0(t * 1000)}" end)
            |> Enum.join(" / ")

          cr(c, "IfcMaterialLayerSet", MaterialLayers: mls, LayerSetName: "#{prefix} #{label}")
        end)

      cr(c, "IfcMaterialLayerSetUsage",
        ForLayerSet: ls,
        LayerSetDirection: direction,
        DirectionSense: "POSITIVE",
        OffsetFromReferenceLine: offset * 1.0
      )
    end
  end

  defp associate_material(_c, _element, nil), do: :ok

  defp associate_material(c, element, lsu),
    do:
      cr(c, "IfcRelAssociatesMaterial",
        GlobalId: Step.gid(c.f),
        RelatedObjects: [element],
        RelatingMaterial: lsu
      )

  defp placement(c, parent \\ nil, z \\ 0.0) do
    origin = cr(c, "IfcCartesianPoint", Coordinates: [0.0, 0.0, z * 1.0])
    axis = cr(c, "IfcAxis2Placement3D", Location: origin)
    cr(c, "IfcLocalPlacement", PlacementRelTo: parent, RelativePlacement: axis)
  end

  # 요소 placement — 층 기준 z=0 (참조 IFC 정석). 지오메트리 z 는 **층 상대**로 넣는다 — 구 방식(−표고 보정 + 절대 z)은
  # 아키캐드가 보정 placement 를 무시하고 층 위에 다시 얹어 요소가 표고만큼 이중 상승했다(실측 확인).
  defp on_storey(c, st), do: placement(c, st.attrs[:ObjectPlacement])

  defp rel_aggregates(c, relating, related, name) do
    items = Enum.reject(related, &is_nil/1)

    if items != [],
      do:
        cr(c, "IfcRelAggregates",
          GlobalId: Step.gid(c.f),
          Name: name,
          RelatingObject: relating,
          RelatedObjects: items
        )
  end

  defp rel_contained(c, structure, elements) do
    items = Enum.reject(elements, &is_nil/1)

    if items != [],
      do:
        cr(c, "IfcRelContainedInSpatialStructure",
          GlobalId: Step.gid(c.f),
          RelatingStructure: structure,
          RelatedElements: items
        )
  end

  defp area_quantity(c, element, area, name \\ "NetFloorArea", qto \\ "Qto_SpaceBaseQuantities") do
    if Py.truthy?(area) and area > 0 do
      q = cr(c, "IfcQuantityArea", Name: name, AreaValue: area * 1.0)
      eq = cr(c, "IfcElementQuantity", GlobalId: Step.gid(c.f), Name: qto, Quantities: [q])

      cr(c, "IfcRelDefinesByProperties",
        GlobalId: Step.gid(c.f),
        RelatedObjects: [element],
        RelatingPropertyDefinition: eq
      )
    end
  end

  # 부재 Pset — 값 타입은 bool→IfcBoolean, int→IfcInteger, float→IfcReal, str→IfcLabel
  defp pset(c, element, name, props) do
    items =
      for {k, v} <- props, not is_nil(v) do
        kind =
          cond do
            is_boolean(v) -> "IfcBoolean"
            is_integer(v) -> "IfcInteger"
            is_float(v) -> "IfcReal"
            true -> "IfcLabel"
          end

        cr(c, "IfcPropertySingleValue", Name: k, NominalValue: Step.typed(kind, v))
      end

    if items != [] do
      ps = cr(c, "IfcPropertySet", GlobalId: Step.gid(c.f), Name: name, HasProperties: items)

      cr(c, "IfcRelDefinesByProperties",
        GlobalId: Step.gid(c.f),
        RelatedObjects: [element],
        RelatingPropertyDefinition: ps
      )
    end
  end

  # 부재 수량 — Qto_WallBaseQuantities 등. 적산 직결 — 참조 도면(ArchiCAD 출력)엔 수량 세트가 아예 없어 여기가 우위.
  defp qto(c, element, name, quants) do
    items =
      for {kind, qname, val} <- quants, not is_nil(val) and val > 0 do
        {cls, attr} = @qkind[kind]
        cr(c, cls, [{:Name, qname}, {attr, val * 1.0}])
      end

    if items != [] do
      eq = cr(c, "IfcElementQuantity", GlobalId: Step.gid(c.f), Name: name, Quantities: items)

      cr(c, "IfcRelDefinesByProperties",
        GlobalId: Step.gid(c.f),
        RelatedObjects: [element],
        RelatingPropertyDefinition: eq
      )
    end
  end

  # ── 메시 변환 ──

  @doc "geom 필드(예: [[geom]] 또는 [[]])를 평탄화해 BufferGeometry 맵만 — 목록 안의 것은 data 가 있어야 한다."
  def iter_geoms(group) do
    for sub <- group || [],
        g <-
          (cond do
             is_map(sub) -> [sub]
             is_list(sub) -> Enum.filter(sub, &(is_map(&1) and Py.truthy?(&1["data"])))
             true -> []
           end),
        do: g
  end

  # BufferGeometry → IfcTriangulatedFaceSet. dz = 층 표고(지오메트리를 층 상대 z 로 — 아키캐드 층 배정 정석). 빈 경우 nil.
  defp faceset(c, geom, dz) do
    pos = get_in(geom, ["data", "attributes", "position", "array"])
    idx = get_in(geom, ["data", "index", "array"])

    cond do
      not is_list(pos) or not is_list(idx) or length(pos) < 9 or length(idx) < 3 ->
        nil

      true ->
        coords =
          pos
          |> Enum.chunk_every(3, 3, :discard)
          |> Enum.map(fn [x, y, z] -> [x * 1.0, y * 1.0, z * 1.0 - dz] end)

        n = length(coords)

        tris =
          idx
          |> Enum.chunk_every(3, 3, :discard)
          |> Enum.filter(fn [a, b, cc] -> a < n and b < n and cc < n end)
          # IFC CoordIndex = 1-based
          |> Enum.map(fn [a, b, cc] -> [a + 1, b + 1, cc + 1] end)

        if tris == [] do
          nil
        else
          pl = cr(c, "IfcCartesianPointList3D", CoordList: coords)
          cr(c, "IfcTriangulatedFaceSet", Coordinates: pl, CoordIndex: tris, Closed: false)
        end
    end
  end

  defp shape_tess(c, facesets, style) do
    case Enum.reject(facesets, &is_nil/1) do
      [] ->
        nil

      items ->
        if style, do: Enum.each(items, &cr(c, "IfcStyledItem", Item: &1, Styles: [style]))

        rep =
          cr(c, "IfcShapeRepresentation",
            ContextOfItems: c.ctx,
            RepresentationIdentifier: "Body",
            RepresentationType: "Tessellation",
            Items: items
          )

        cr(c, "IfcProductDefinitionShape", Representations: [rep])
    end
  end

  # ── 파라메트릭 솔리드 (세대 IfcSpace·지하 공간) ──
  defp ring_xy(c, ring) do
    pts =
      Enum.reduce(ring, [], fn p, acc ->
        xy = rel(c, p)

        case acc do
          [last | _]
          when abs(elem(xy, 0) - elem(last, 0)) <= 1.0e-6 and
                 abs(elem(xy, 1) - elem(last, 1)) <= 1.0e-6 ->
            acc

          _ ->
            [xy | acc]
        end
      end)
      |> Enum.reverse()

    case pts do
      [first | _] = l when length(l) > 1 ->
        last = List.last(l)

        if abs(elem(first, 0) - elem(last, 0)) < 1.0e-6 and
             abs(elem(first, 1) - elem(last, 1)) < 1.0e-6, do: Enum.drop(l, -1), else: l

      l ->
        l
    end
  end

  defp extruded_solid(c, pts, base_z, height) do
    poly_pts = Enum.map(pts, fn {x, y} -> cr(c, "IfcCartesianPoint", Coordinates: [x, y]) end)
    polyline = cr(c, "IfcPolyline", Points: poly_pts ++ [hd(poly_pts)])
    profile = cr(c, "IfcArbitraryClosedProfileDef", ProfileType: "AREA", OuterCurve: polyline)
    origin = cr(c, "IfcCartesianPoint", Coordinates: [0.0, 0.0, base_z * 1.0])
    position = cr(c, "IfcAxis2Placement3D", Location: origin)
    direction = cr(c, "IfcDirection", DirectionRatios: [0.0, 0.0, 1.0])

    cr(c, "IfcExtrudedAreaSolid",
      SweptArea: profile,
      Position: position,
      ExtrudedDirection: direction,
      Depth: max(height, 1.0e-3)
    )
  end

  defp shape_solid(c, solid, style) do
    if style, do: cr(c, "IfcStyledItem", Item: solid, Styles: [style])

    rep =
      cr(c, "IfcShapeRepresentation",
        ContextOfItems: c.ctx,
        RepresentationIdentifier: "Body",
        RepresentationType: "SweptSolid",
        Items: [solid]
      )

    cr(c, "IfcProductDefinitionShape", Representations: [rep])
  end

  # ── 난간 부재 ──

  @doc """
  난간동자(수직 살) + 손스침 — ifc.py `railing_members`. 간살 안목 ≤0.10m(주택건설기준 18조②2), 중심간 피치 = post + clear,
  실간격은 구간 길이를 균등 분할해 상한 이하로. 반환 `[%{part: "post" | "handrail", geom: BufferGeometry 맵}]`.
  """
  def railing_members(ud, post \\ 0.04, clear \\ 0.10) do
    lines = (ud || %{})["lines"]

    if not Py.truthy?(lines) do
      []
    else
      spacing = post + clear
      z0 = Py.num(Map.get(ud, "base_z", 0.0), 0.0)
      z1 = Py.num(Map.get(ud, "top_z", z0 + 1.2), z0 + 1.2)
      h = post / 2.0

      for ln_pts <- lines,
          [[x0, y0], [x1, y1]] <- Enum.chunk_every(ln_pts, 2, 1, :discard),
          {dx, dy} = {x1 - x0, y1 - y0},
          seg = :math.pow(dx * dx + dy * dy, 0.5),
          seg >= 0.3,
          m <- railing_seg(x0, y0, x1, y1, dx, dy, seg, spacing, h, z0, z1),
          do: m
    end
  end

  defp railing_seg(x0, y0, x1, y1, dx, dy, seg, spacing, h, z0, z1) do
    {ux, uy} = {dx / seg, dy / seg}
    {nx, ny} = {uy, -ux}
    # 양끝 포함
    n_post = max(2, trunc(seg / spacing) + 1)

    posts =
      for k <- 0..(n_post - 1) do
        t = seg * k / (n_post - 1)
        {px, py} = {x0 + ux * t, y0 + uy * t}

        corners = [
          {px - ux * h - nx * h, py - uy * h - ny * h},
          {px + ux * h - nx * h, py + uy * h - ny * h},
          {px + ux * h + nx * h, py + uy * h + ny * h},
          {px - ux * h + nx * h, py - uy * h + ny * h}
        ]

        %{part: "post", geom: prism(corners, z0, z1 - 0.05)}
      end

    # 손스침 — 상단 가로재 (동자 위 5cm 띠)
    hc = [
      {x0 - nx * h, y0 - ny * h},
      {x1 - nx * h, y1 - ny * h},
      {x1 + nx * h, y1 + ny * h},
      {x0 + nx * h, y0 + ny * h}
    ]

    posts ++ [%{part: "handrail", geom: prism(hc, z1 - 0.05, z1)}]
  end

  # 수직 프리즘(옆면+상하캡) — ifc.py `_prism_geometry` 의 position·index 만(법선·uuid 는 IFC 에 안 쓰인다)
  defp prism(corners, z0, z1) do
    n = length(corners)
    cv = List.to_tuple(corners)

    {pos, idx, vi} =
      Enum.reduce(0..(n - 1), {[], [], 0}, fn i, {pos, idx, vi} ->
        {x0, y0} = elem(cv, i)
        {x1, y1} = elem(cv, rem(i + 1, n))

        {[pos, [x0, y0, z0, x1, y1, z0, x1, y1, z1, x0, y0, z1]],
         [idx, [vi, vi + 1, vi + 2, vi, vi + 2, vi + 3]], vi + 4}
      end)

    # 캡 (fan 삼각화 — 부재 프리즘은 볼록 quad 라 충분)
    {pos, idx, _} =
      Enum.reduce([{z0, true}, {z1, false}], {pos, idx, vi}, fn {z, rev}, {pos, idx, vi} ->
        ring = if rev, do: Enum.reverse(corners), else: corners
        base = vi
        pos = [pos, Enum.map(ring, fn {x, y} -> [x, y, z] end)]
        idx = [idx, for(i <- 1..(n - 2)//1, do: [base, base + i, base + i + 1])]
        {pos, idx, vi + n}
      end)

    %{
      "data" => %{
        "attributes" => %{"position" => %{"array" => List.flatten(pos)}},
        "index" => %{"array" => List.flatten(idx)}
      }
    }
  end

  # ── 대지 중심 ──

  @doc """
  scheme 에서 대지 중심(EPSG 절대)을 되찾는다 — ifc.py `derive_parcel_center`.
  벽 userData(절대 quad/p0p1) bbox 중심 − 같은 벽들의 메시 bbox 중심. 벽 userData 가 없는 구 scheme 은 밑줄 키
  절대좌표 bbox 중심으로 떨어진다(대지 밖 링이 섞이면 어긋날 수 있다 — sample-medium 에서 Y 4.33m, 2026-10-16).
  """
  def derive_parcel_center(scheme) do
    pairs =
      for fp <- (scheme || %{})["floor_plans"] || [],
          arr <- (fp["geom"] || %{})["walls"] || [],
          g <- if(is_list(arr), do: arr, else: [arr]),
          ud = (g || %{})["userData"] || %{},
          pts =
            ud["quad"] ||
              if(Map.has_key?(ud, "p0") and Map.has_key?(ud, "p1"),
                do: [ud["p0"], ud["p1"]],
                else: []
              ),
          arr_ = get_in(g || %{}, ["data", "attributes", "position", "array"]) || [],
          pts != [] and length(arr_) >= 3,
          do: {pts, arr_}

    if pairs != [] do
      ax = for {pts, _} <- pairs, p <- pts, do: Enum.at(p, 0) * 1.0
      ay = for {pts, _} <- pairs, p <- pts, do: Enum.at(p, 1) * 1.0
      mx = for {_, a} <- pairs, v <- Enum.take_every(a, 3), do: v * 1.0
      my = for {_, a} <- pairs, v <- a |> Enum.drop(1) |> Enum.take_every(3), do: v * 1.0
      mid = fn l -> (Enum.min(l) + Enum.max(l)) / 2 end
      [mid.(ax) - mid.(mx), mid.(ay) - mid.(my)]
    else
      xy =
        for {k, v} <- scheme || %{}, String.starts_with?(k, "_"), p <- abs_points(v), do: p

      if xy == [], do: raise(ArgumentError, "scheme에서 절대좌표를 찾지 못했습니다. parcel_center를 직접 넘기세요.")
      {xs, ys} = Enum.unzip(xy)
      [(Enum.min(xs) + Enum.max(xs)) / 2, (Enum.min(ys) + Enum.max(ys)) / 2]
    end
  end

  defp abs_points([x, y]) when is_number(x) and is_number(y) and abs(x) > 1000 and abs(y) > 1000,
    do: [{x * 1.0, y * 1.0}]

  defp abs_points(l) when is_list(l), do: Enum.flat_map(l, &abs_points/1)
  defp abs_points(m) when is_map(m), do: m |> Map.values() |> Enum.flat_map(&abs_points/1)
  defp abs_points(_), do: []

  # ── 등록부(파이썬 dict 캐시·삽입 순서 목록) ──

  defp get(c, key), do: :ets.lookup_element(c.reg, key, 2)

  defp cache(c, key, fun) do
    case :ets.lookup(c.reg, key) do
      [{_, v}] ->
        v

      [] ->
        v = fun.()
        :ets.insert(c.reg, {key, v})
        v
    end
  end

  defp push(c, ns, key, val) do
    case :ets.lookup(c.reg, {ns, key}) do
      [{_, vals}] ->
        :ets.insert(c.reg, {{ns, key}, [val | vals]})

      [] ->
        keys =
          case :ets.lookup(c.reg, {ns, :__keys}) do
            [{_, ks}] -> ks
            [] -> []
          end

        :ets.insert(c.reg, [{{ns, key}, [val]}, {{ns, :__keys}, [key | keys]}])
    end
  end

  defp entries(c, ns) do
    case :ets.lookup(c.reg, {ns, :__keys}) do
      [{_, ks}] ->
        for k <- Enum.reverse(ks),
            do: {k, c.reg |> :ets.lookup_element({ns, k}, 2) |> Enum.reverse()}

      [] ->
        []
    end
  end
end
