from typing import List
from typing import Optional
from typing import Tuple

from munch import Munch

from app.cpt.constants import BORE_COLOR
from app.cpt.constants import CPT_COLOR
from app.cpt.constants import CPT_MAP_ICON
from app.dyke.dyke_model import Dyke
from app.lib.constants import COLOR_MAP_GROUND_MODEL
from app.lib.constants import DRY_DITCH_COLOR
from app.lib.constants import EXISTING_EXIT_POINT_COLOR
from app.lib.constants import MAP_LEGEND_LIST
from app.lib.constants import WET_DITCH_COLOR
from app.lib.shapely_helper_functions import convert_linestring_to_geo_polyline
from app.lib.shapely_helper_functions import convert_shapely_point_to_geo_point
from app.lib.shapely_helper_functions import convert_shapely_polgon_to_geopolygon
from app.lib.shapely_helper_functions import get_value_hex_color
from app.segment.segment_model import Segment
from viktor import Color
from viktor import UserException
from viktor.api_v1 import EntityList
from viktor.geometry import GeoPoint
from viktor.geometry import GeoPolygon
from viktor.geometry import GeoPolyline
from viktor.geometry import RDWGSConverter
from viktor.views import MapEntityLink
from viktor.views import MapFeature
from viktor.views import MapLabel
from viktor.views import MapLegend
from viktor.views import MapPoint
from viktor.views import MapPolygon
from viktor.views import MapPolyline


def add_dike_trajectory_and_entry_line_to_map_features(
    map_features: List, dike_trajectory: GeoPolyline, entry_line: GeoPolyline = None
):
    """
    Add to a list of map features, the trajectory of the dike and its associated entry line
    :param map_features: List of all MapFeatures, is appended in place.
    :param dike_trajectory:
    :param entry_line:
    :return:
    """

    map_features.append(
        MapPolyline.from_geo_polyline(
            dike_trajectory,
            color=Color.green(),
            description="Dyke central axis",
        )
    )

    if entry_line:
        map_features.append(
            MapPolyline.from_geo_polyline(
                entry_line,
                color=Color.lime(),
                description="Entry line",
            )
        )


def add_ditches_to_map_features(map_features: List[MapFeature], ditch_features: dict):
    """
    Add to a list of map features, the polygons and center polyline of all the uploaded ditches
    :param map_features:
    :param ditch_features:
    :return:
    """

    for ditch in ditch_features["ditches"]:
        map_features.append(
            MapPolygon.from_geo_polygon(
                GeoPolygon(*[GeoPoint.from_rd(tuple(pt)) for pt in ditch["ditch_polygon"]]), color=Color.black()
            )
        )
        map_features.append(
            MapPolyline.from_geo_polyline(
                GeoPolyline(*[GeoPoint.from_rd(tuple(pt)) for pt in ditch["ditch_center_line"]]),
                color=WET_DITCH_COLOR,
            )
        )

    for ditch in ditch_features["dry_ditches"]:
        map_features.append(
            MapPolygon.from_geo_polygon(
                GeoPolygon(*[GeoPoint.from_rd(tuple(pt)) for pt in ditch["ditch_polygon"]]), color=Color.black()
            )
        )
        map_features.append(
            MapPolyline.from_geo_polyline(
                GeoPolyline(*[GeoPoint.from_rd(tuple(pt)) for pt in ditch["ditch_center_line"]]),
                color=DRY_DITCH_COLOR,
            )
        )


def add_dijkpalen_points_to_map_features(
    map_features: List[MapFeature], map_labels: List[MapLabel], dijkpalen: List[dict]
):
    """
    Add to a list of map features, the points of all the uploaded dijkpalen
    :param map_features:
    :param map_labels:
    :param dijkpalen: dijkpalen data parsed from the shapefile
    :return:
    """
    for point in dijkpalen:
        lat, lon = tuple(RDWGSConverter.from_rd_to_wgs((list(point["geometry"].coords)[0])))
        map_labels.append(MapLabel(lat, lon, scale=16, text=f"{point['value']}"))

        map_features.append(
            MapPoint.from_geo_point(
                convert_shapely_point_to_geo_point(point["geometry"]),
                icon="circle",
                description=f"{point['value']}",
            )
        )


def add_intersected_segment_ditches_to_map_features(map_features: List[MapFeature], segment_params: Munch):
    """
    Add to a list of map features, the polygons and center polyline of the ditches thata have been intersected with
    the buffer zone behind the dike and saved in the segment params.
    """
    if segment_params.segment_ditches:
        for ditch in segment_params.segment_ditches:
            map_features.append(
                MapPolygon.from_geo_polygon(
                    GeoPolygon(*[GeoPoint.from_rd(tuple(pt)) for pt in ditch["ditch_polygon"]]), color=Color.black()
                )
            )
            map_features.append(
                MapPolyline.from_geo_polyline(
                    GeoPolyline(*[GeoPoint.from_rd(tuple(pt)) for pt in ditch["ditch_center_line"]]),
                    color=WET_DITCH_COLOR,
                )
            )

    if segment_params.segment_dry_ditches:
        for ditch in segment_params.segment_dry_ditches:
            map_features.append(
                MapPolygon.from_geo_polygon(
                    GeoPolygon(*[GeoPoint.from_rd(tuple(pt)) for pt in ditch["ditch_polygon"]]), color=Color.black()
                )
            )
            map_features.append(
                MapPolyline.from_geo_polyline(
                    GeoPolyline(*[GeoPoint.from_rd(tuple(pt)) for pt in ditch["ditch_center_line"]]),
                    color=DRY_DITCH_COLOR,
                )
            )


def add_segment_trajectory_to_map_features(
    map_features: List[MapFeature], segment_trajectory: GeoPolyline, description: str = ""
):
    """
    Add the segment trjaectory to a list of map_features
    :param map_features:
    :param segment_trajectory:
    :return:
    """
    map_features.append(MapPolyline.from_geo_polyline(segment_trajectory, color=Color.blue(), description=description))


def add_ground_model_hull_to_map_features(
    map_features: List[MapFeature], ground_model_hull: GeoPolygon, color: Color = COLOR_MAP_GROUND_MODEL
):
    map_features.extend(
        [
            MapPolygon.from_geo_polygon(
                ground_model_hull,
                color=color,
            )
        ]
    )


def add_hinterland_polygon_to_map_features(
    map_features: List[MapFeature], segment: Segment, length_hinterland: float, buffer_length_hinterland: float
):
    """Add the polygon of the hinterland region to the map features, from which the ditches have been excluded as holes"""
    if length_hinterland is None:
        raise UserException("Visualisatie achterland faalt: Lengte achterland vanaf de kruin (m) ontbreekt")

    hinterland_hull = segment.create_hinterland_hull(length_hinterland, buffer_length_hinterland)

    # draw hinterland
    for polygon in hinterland_hull:
        polygon, holes = convert_shapely_polgon_to_geopolygon(polygon)
        holes = [MapPolygon.from_geo_polygon(hole) for hole in holes]
        map_features.append(MapPolygon(points=polygon.points, holes=holes, color=Color.black()))


def add_foreland_polygon_to_map_features(map_features: List[MapFeature], segment: Segment, length_foreland: float):
    """Add the polygon of the foreland region to the map features"""
    if length_foreland is None:
        raise UserException("Visualisatie achterland faalt: Lengte achterland vanaf de kruin (m) ontbreekt")

    foreland_hull = segment.create_foreland_hull(length_foreland, 0)

    polygon, _ = convert_shapely_polgon_to_geopolygon(foreland_hull)
    map_features.append(MapPolygon(points=polygon.points, color=Color.black()))


def add_existing_exit_point_to_map_features(
    map_features: List[MapFeature],
    map_labels: List[MapLabel],
    exit_point_entities: EntityList,
    interaction_point_list: Optional[list] = None,
):
    """Add the existing saved exit point to a MapView, including labels with exit point name"""
    for exit_point in exit_point_entities:
        lat, lon = tuple(
            RDWGSConverter.from_rd_to_wgs(
                (
                    exit_point.last_saved_summary.x_coordinate.get("value"),
                    exit_point.last_saved_summary.y_coordinate.get("value"),
                )
            )
        )
        map_point = MapPoint.from_geo_point(
            GeoPoint(lat, lon),
            color=EXISTING_EXIT_POINT_COLOR,
            icon="triangle-down",
            description=f"{exit_point.name}",
            entity_links=[MapEntityLink("To exit point entity", entity_id=exit_point.id)],
            identifier=exit_point.id,
        )
        map_features.append(map_point)
        if interaction_point_list is not None:
            interaction_point_list.append(map_point)
        map_labels.append(MapLabel(lat, lon, scale=17, text=f"{exit_point.name[13:]}"))


def add_leakage_point_to_map_features(
    map_features: List[MapFeature],
    map_labels,
    point: Tuple[float, float],
    i,
    color: Color,
    description: str,
    as_polygons: bool = True,
):
    """Add a point marker displaying t"""
    lat, lon = RDWGSConverter.from_rd_to_wgs(point)

    if as_polygons:
        x, y = point
        half_width = 25 / 2
        top_right, top_left = (x + half_width, y + half_width), (x - half_width, y + half_width)
        bottom_right, bottom_left = (x + half_width, y - half_width), (x - half_width, y - half_width)

        corners = [top_right, bottom_right, bottom_left, top_left]
        corners_mapoint = [MapPoint.from_geo_point(GeoPoint.from_rd(corner)) for corner in corners]
        map_features.append(MapPolygon(corners_mapoint, color=color, description=description))
        map_labels.append(MapLabel(lat, lon, str(i), scale=17))
    else:
        map_features.append(
            MapPoint.from_geo_point(
                GeoPoint(lat, lon),
                color=color,
                description=description,
                icon="circle-filled",
            )
        )


def add_all_leakage_points_to_map_features(
    map_features: List[MapFeature], map_labels, leakage_point_properties: List[dict], as_polygons: bool = True
) -> MapLegend:
    """Add all the leakages points to the list of map features, their color is based on their respective leakage length.
    Returns the mapleagend with a color gradient scale.
    """

    unique_leak_len = sorted(list({int(lp["ll"]) for lp in leakage_point_properties if lp["ll"] is not None}))
    color_dict = {
        ll: Color.from_hex(get_value_hex_color(ll, vmin=min(unique_leak_len), vmax=max(unique_leak_len)))
        for ll in unique_leak_len
    }
    for i, lp in enumerate(leakage_point_properties, 1):
        leakage_length = lp["ll"]

        if leakage_length is None:
            color = Color.black()
            description = "Leakage length unavailable for this voxel"
        else:
            color = Color.from_hex(get_value_hex_color(lp["ll"], vmin=min(unique_leak_len), vmax=max(unique_leak_len)))
            description = (
                f"Leakage length: {leakage_length:.2f} m \\\n \\\n"
                + f"Cover layer thickness: {lp['cover_layer_d']:.2f} m \\\n "
                + f"Cover layer permeability: {lp['cover_layer_k']:.2e} m/d \\\n"
                + f"First aquifer thickness: {lp['first_aquifer_d']:.2f} m \\\n"
                + f"First aquifer permeability: {lp['first_aquifer_k']:.2e} m/d \\\n"
            )

        add_leakage_point_to_map_features(
            map_features,
            map_labels,
            (lp["x"], lp["y"]),
            i,
            color=color,
            description=description,
            as_polygons=as_polygons,
        )

    legend = MapLegend([(color, f"{ll} m") for ll, color in color_dict.items()])
    return legend


def add_cpts_to_mapfeatures(map_features: List[MapFeature], all_cpts: EntityList, map_labels):
    for cpt in all_cpts:
        cpt_summary = cpt.last_saved_summary
        coords = (int(cpt_summary.x_coordinate["value"]), int(cpt_summary.y_coordinate["value"]))
        lat, lon = RDWGSConverter.from_rd_to_wgs(coords)
        map_features.append(
            MapPoint.from_geo_point(
                GeoPoint(lat, lon),
                color=CPT_COLOR,
                title=f"CPT: {coords}",
                entity_links=[MapEntityLink(cpt.name, cpt.id)],
                icon=CPT_MAP_ICON,
            )
        )
        map_labels.append(MapLabel(lat=lat, lon=lon, text=cpt.name, scale=16))


def add_bore_to_mapfeatures(map_features: List[MapFeature], all_bores: EntityList, map_labels):
    for bore in all_bores:
        params = bore.last_saved_params
        coords = (float(params["x_rd"]), float(params["y_rd"]))
        lat, lon = RDWGSConverter.from_rd_to_wgs(coords)
        map_features.append(
            MapPoint.from_geo_point(
                GeoPoint(lat, lon),
                color=BORE_COLOR,
                title=f"Bore: {coords}",
                entity_links=[MapEntityLink(bore.name, bore.id)],
                icon="plus",
            )
        )
        map_labels.append(MapLabel(lat=lat, lon=lon, text=params["test_id"], scale=16))


def add_2D_longitudinal_line_to_mapfeatures(map_features: List[MapFeature], dike: Dyke) -> MapLegend:
    trajectory = dike.interpolated_trajectory(for_2d_layout=True)

    buffer_polygon = trajectory.buffer(dike.params.buffer_zone_cpts_bore)
    geo_buffer_polygon, _ = convert_shapely_polgon_to_geopolygon(buffer_polygon)
    map_features.append(MapPolygon.from_geo_polygon(geo_buffer_polygon, color=Color.viktor_yellow()))

    if dike.params.soil_profile.select_base_line_for_2D_view == "uploaded_line":
        map_features.append(
            MapPolyline.from_geo_polyline(
                convert_linestring_to_geo_polyline(trajectory),
                color=Color.red(),
                description="Lijn voor 2d grondopbouw visualisatie",
            )
        )
        buffer_polygon = trajectory.buffer(dike.params.buffer_zone_cpts_bore)
        geo_buffer_polygon, _ = convert_shapely_polgon_to_geopolygon(buffer_polygon)
        MAP_LEGEND_LIST.append((Color.red(), "2D Grondopbouw lijn"))

    elif dike.params.soil_profile.select_base_line_for_2D_view == "custom_line":
        map_features.append(
            MapPolyline.from_geo_polyline(
                dike.params.soil_profile.custom_geopolyline,
                color=Color.red(),
                description="Lijn voor 2d grondopbouw visualisatie",
            )
        )
        buffer_polygon = trajectory.buffer(dike.params.buffer_zone_cpts_bore)
        geo_buffer_polygon, _ = convert_shapely_polgon_to_geopolygon(buffer_polygon)
        MAP_LEGEND_LIST.append((Color.red(), "2D Grondopbouw lijn"))

    elif dike.params.soil_profile.select_base_line_for_2D_view == "crest_line" and dike.params.soil_profile.line_offset:
        map_features.append(
            MapPolyline.from_geo_polyline(
                convert_linestring_to_geo_polyline(trajectory),
                color=Color.red(),
                description="Lijn voor 2d grondopbouw visualisatie",
            )
        )
        buffer_polygon = trajectory.buffer(dike.params.buffer_zone_cpts_bore)
        geo_buffer_polygon, _ = convert_shapely_polgon_to_geopolygon(buffer_polygon)
        MAP_LEGEND_LIST.append((Color.red(), "2D Grondopbouw lijn"))
    return MapLegend(MAP_LEGEND_LIST)
