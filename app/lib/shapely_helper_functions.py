from io import BytesIO
from math import hypot
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union

import numpy as np
import pandas as pd
import shapefile as pyshp
from matplotlib import cm
from matplotlib.colors import Normalize
from matplotlib.colors import rgb2hex
from munch import Munch
from numpy import isinf
from numpy import isnan
from pandas import DataFrame
from shapely.geometry import LineString
from shapely.geometry import MultiPolygon
from shapely.geometry import Point
from shapely.geometry import Polygon
from shapely.ops import nearest_points
from shapely.ops import transform

# ------
# POINTS
# ------
from app.lib.constants import WaterDirection
from viktor import Color
from viktor import UserException
from viktor.api_v1 import Entity
from viktor.api_v1 import EntityList
from viktor.geo import SoilLayout
from viktor.geometry import GeoPoint
from viktor.geometry import GeoPolygon
from viktor.geometry import GeoPolyline
from viktor.geometry import Polygon as ViktorPolygon

TOL = 0.5  # meter tolerance to generate points along ditches lines


def convert_geo_point_to_shapeply_point(geo_point: GeoPoint) -> Point:
    return Point(geo_point.rd)


def convert_shapely_point_to_geo_point(point: Point) -> GeoPoint:
    return GeoPoint.from_rd(*list(point.coords))


# ---------
# POLYLINES
# ---------


def convert_geo_polyline_to_linestring(geo_polyline: GeoPolyline, offset: int = 0, side: str = "left") -> LineString:
    """Convert a SDK GeoPolyline object into a shapely LineString, if necessary including an offset"""
    list_points = [pt.rd for pt in geo_polyline.points]
    if offset < 0:
        return reverse_shapely_geoms(LineString(list_points).parallel_offset(offset, side, join_style=2))
    return LineString(list_points).parallel_offset(offset, side, join_style=2)


def reverse_shapely_geoms(geom):
    def _reverse(x, y, z=None):
        if z:
            return x[::-1], y[::-1], z[::-1]
        return x[::-1], y[::-1]

    return transform(_reverse, geom)


def convert_linestring_to_geo_polyline(linestring: LineString) -> GeoPolyline:
    """Convert a shapely LineString into a shapely a SDK GeoPolyline"""
    linestring_points = list(linestring.coords)
    return GeoPolyline(*[GeoPoint.from_rd(pt) for pt in linestring_points])


def convert_shapely_linestring_to_shapefile(params: Munch, polygon: GeoPolygon, name: str) -> Dict[str, BytesIO]:
    """Convert a shapely LineString to shapefiles for download"""
    selected_trajectory = find_intersection_with_polygon_on_map(params.dyke_geo_coordinates, polygon)
    shp, shx, dbf = BytesIO(), BytesIO(), BytesIO()
    w = pyshp.Writer(shp=shp, shx=shx, dbf=dbf)
    pointlist = [[point[0], point[1]] for point in selected_trajectory.coords]
    w.field("trajectory of segment", "C")
    w.line([pointlist])
    w.record("linestring1")
    w.close()

    shapefiles = {f"{name}_trajectory.shp": shp, f"{name}_trajectory.shx": shx, f"{name}_trajectory.dbf": dbf}

    return shapefiles


def extend_linestring(linestring: LineString, dist_end: int) -> LineString:
    """Extend a (straight) shapely LineString over a given distance"""
    start, end = Point(linestring.coords[0]), Point(linestring.coords[-1])
    dx = end.x - start.x
    dy = end.y - start.y
    linelen = hypot(dx, dy)

    new_end = Point(end.x + dx / linelen * dist_end, end.y + dy / linelen * dist_end)
    linepoints = list(linestring.coords)
    linepoints.append(new_end)

    return LineString(linepoints)


def create_perpendicular_vector_at_chainage(
    trajectory_points: List, point_index: int, line_length: Union[float, int]
) -> np.array:
    """Create perpendicular vector at specified chainage along the trajectory"""
    segment_linestring = LineString(trajectory_points)
    perpendicular_unit_vector = get_unit_vector(
        trajectory_points[point_index], find_perpendicular_direction(segment_linestring, point_index)
    )
    perpendicular_line = line_length * perpendicular_unit_vector
    return perpendicular_line


def create_line_by_point_and_vector(point: Point, vector: np.array) -> LineString:
    """Create line with two points at +vector and -vector of the specified location"""
    return LineString(
        [
            (Point(np.array(point) - vector)),
            (Point(np.array(point) + vector)),
        ]
    )


# ---------
# POLYGONS:
# --------
def convert_geopolygon_to_shapely_polgon(geopolygon: GeoPolygon) -> Polygon:
    return Polygon([points.rd for points in geopolygon.points])


def convert_shapely_polgon_to_geopolygon(polygon: Polygon) -> Tuple[GeoPolygon, List[GeoPolygon]]:
    list_holes = []
    for interior in polygon.interiors:
        list_holes.append(GeoPolygon(*[GeoPoint.from_rd(point) for point in interior.coords]))
    return GeoPolygon(*[GeoPoint.from_rd(point) for point in polygon.exterior.coords]), list_holes


def convert_viktor_polygon_to_shapely(polygon: ViktorPolygon) -> Polygon:
    return Polygon([Point(p.x, p.y) for p in polygon.points])


def find_intersection_with_polygon_on_map(trajectory: GeoPolyline, polygon: GeoPolygon) -> LineString:
    """From the Geopolygon defining the section and the GeoPolyline of the dyke trajectory, this function returns
    the Geopolyline of the section along the dyke trajectory"""
    trajectory = convert_geo_polyline_to_linestring(trajectory)
    selected_region = convert_geopolygon_to_shapely_polgon(polygon)
    return selected_region.intersection(trajectory)


def create_polygon_from_linestring_offset(
    trajectory_points: list, start_chainage: float, end_chainage: float, buffer_distance: float = 30
) -> Polygon:
    """Creates an elongated polygon around the linestring by the defined BUFFER_DISTANCE constant"""
    segment_points = []
    trajectory_chainage = []
    distance_along_dyke = 0
    prev_point = trajectory_points[0]

    for point in trajectory_points[1:]:
        distance_along_dyke += prev_point.distance(point)
        if (round(distance_along_dyke, 0) >= start_chainage) and (round(distance_along_dyke, 0) <= end_chainage):
            segment_points.append(point)
        trajectory_chainage.append(distance_along_dyke)
        prev_point = point

    middle_point = int(len(segment_points) / 2)
    if len(segment_points) < 2:
        raise UserException("De afstand tussen start en eind kilometrering is te klein.")
    perpendicular_vector = create_perpendicular_vector_at_chainage(segment_points, middle_point, buffer_distance)

    return Polygon(
        [
            *(Point(np.array(point) - perpendicular_vector) for point in segment_points),
            *(Point(np.array(point) + perpendicular_vector) for point in reversed(segment_points)),
        ]
    )


# --------------------------------------
# Vectors and Coordinate transformations
# --------------------------------------


def get_all_exit_point_entities_within_polygon(
    exit_point_entities: Union[EntityList, List[Entity]], polygon_coord: GeoPolygon
) -> List[Entity]:
    """Return a list of entities for which the exit points are located within a drawn polygon"""
    polygon = Polygon([point.rd for point in polygon_coord.points])
    filtered_exit_point_entities = []
    for exit_point in exit_point_entities:
        exit_point_coord = (
            exit_point.last_saved_summary.x_coordinate.get("value"),
            exit_point.last_saved_summary.y_coordinate.get("value"),
        )
        if polygon.contains(Point(*exit_point_coord)):
            filtered_exit_point_entities.append(exit_point)
    return filtered_exit_point_entities


def find_perpendicular_direction(trajectory: LineString, i: int = 0, clockwise: bool = True) -> Tuple[float, float]:
    """Given a line string, find a point P such that (P, point[i]) is perpendicular to the linestring at point[i]
    in the clockwise or counterclockwise direction"""
    return rotate_90_deg(*find_direction(trajectory, i, clockwise))


def find_direction(trajectory: LineString, i: int = 0, clockwise: bool = True) -> Tuple[Point, Point, WaterDirection]:
    """Given a line string, find a point P such that (P, point[i]) is perpendicular to the linestring at point[i]
    in the clockwise or counterclockwise direction"""
    start_point = trajectory.coords[i]

    try:
        if clockwise:
            direction = WaterDirection.CLOCKWISE
        else:
            direction = WaterDirection.COUNTER_CLOCKWISE
        end_point = trajectory.coords[i + 1]

        return start_point, end_point, direction

    except IndexError:  # this is the last point on the list
        if clockwise:  # we need to switch it around
            direction = WaterDirection.COUNTER_CLOCKWISE
        else:
            direction = WaterDirection.CLOCKWISE
        start_point = np.array(trajectory.coords[i - 1])
        end_point = np.array(trajectory.coords[i])
        return start_point, end_point, direction


def rotate_90_deg(
    start_point: np.array,
    end_point: np.array,
    direction: WaterDirection = WaterDirection.CLOCKWISE,
) -> np.array:
    """find the coordinates of the end_point
    - rotated 90 degrees around the start point,
    - in the given direction (clockwise or counterclockwise)
    """
    vector = np.subtract(end_point, start_point)

    if direction == WaterDirection.COUNTER_CLOCKWISE:
        rot = np.array([[0, 1], [-1, 0]])
        return start_point + vector @ rot
    else:
        rot = np.array([[0, -1], [1, 0]])
        return start_point + vector @ rot


def get_unit_vector(a: np.array, b: np.array) -> np.array:
    """get the unit vector point in the direction point A -> point B"""
    vector = np.subtract(b, a)
    unit_v = vector / np.linalg.norm(vector)
    if not 0.99 < np.linalg.norm(unit_v) < 1.01:
        raise UserException(
            "Error in de app: fout in de berekening van het lokale coordinatenstelsel: "
            f"Eenheid vector heeft geen lengte 1, maar {np.norm.linalg(unit_v)}"
        )
    return unit_v


def show_df(df: DataFrame):
    """For development purposes only, this allows full visualization of large pandas DataFrame"""
    with pd.option_context("display.max_rows", None, "display.max_columns", None):  # more options can be specified also
        print(df)


def convert_rgb_string_to_tuple(rgb: str) -> Tuple[int, int, int]:
    """Convert the string '0,1,2' into a tuple (0, 1, 2)"""
    try:
        return tuple([int(p) for p in rgb.split(",")])  # pylint: disable=consider-using-generator
    except Exception:
        raise UserException(f"Verkeerde rgb kleur format {rgb} in de materiaaltabel")


def calc_minimum_distance(
    geom_1: Union[Point, LineString, Polygon], geom_2: Union[Point, LineString, Polygon]
) -> float:
    """Calculate the minimum distance between two shapely geometric objects"""
    return geom_1.distance(geom_2)


def intersect_soil_layout_table_with_z(soil_layout: SoilLayout, ahn_ground_level: float) -> SoilLayout:
    """
    Intersect the soil layout table with ground level.

    Parameters
    ----------
    soil_layout
        List of dictionaries, example:
            [ {'name': 'Zand grof', 'top_of_layer': -5},
              {'name': 'Zand grof', 'top_of_layer': -8},
              ...
            ]
    ahn_ground_level
        Value of ahn
    Returns
    -------
    soil_layout_table
    """
    # if no AHN data has been found, don't intersect soil layout.
    if isnan(ahn_ground_level):
        return soil_layout

    soil_layout_serialized = soil_layout.serialize()
    index_to_remove = 0
    for layer, next_layer in zip(soil_layout_serialized["layers"], soil_layout_serialized["layers"][1:]):
        if ahn_ground_level >= layer["top_of_layer"]:
            # If the first layer has a lower z, this is extended until the ahn value
            layer["top_of_layer"] = ahn_ground_level
            break

        if next_layer["top_of_layer"] < ahn_ground_level <= layer["top_of_layer"]:
            layer["top_of_layer"] = ahn_ground_level
            break
        index_to_remove += 1
    return SoilLayout.from_dict({"layers": soil_layout_serialized["layers"][index_to_remove:]})


def get_unity_check_color(unity_checks: List[float]) -> Color:
    """Return a green color if at least one unity check is above 1 and red otherwise"""
    for uc in unity_checks:
        if isinstance(uc, str):
            return Color.from_hex("#FFC300")
        elif isnan(uc):
            return Color.from_hex("#FFC300")

    map_uc = [uc > 1 for uc in unity_checks]

    # If uc is Inf, turn the market to orange. An infinite uc results from wrong (among other) geohydrological inputs
    if any((isinf(uc) for uc in unity_checks)):
        return Color.from_hex("#FFC300")
    if any(map_uc):
        return Color.green()
    return Color.red()


def check_if_point_in_polygons(
    segment_ditches_pol: MultiPolygon, segment_dry_ditches_pol: MultiPolygon, point: Point
) -> Tuple[bool, str]:
    """
    Check if exit point is contained in one of the ditch polygons
    """
    for ditch_polygon in segment_ditches_pol:
        if ditch_polygon.contains(point):
            return True, "wet"
    for ditch_polygon in segment_dry_ditches_pol:
        if ditch_polygon.contains(point):
            return True, "dry"
    return False, ""


def generate_perpendicular_line_to_trajectory_from_point(
    trajectory: LineString, point: Point, buffer: float = 0.0
) -> LineString:
    """
    Get the perpendicular line to the trajectory passing for a point.
    """
    point1 = trajectory.interpolate(trajectory.project(point))
    point2 = trajectory.interpolate(trajectory.project(point) + TOL)
    n = [-(point2.y - point1.y), (point2.x - point1.x)]  # perpendicular vector

    distance = LineString([point1, point]).length + buffer
    perp_line = LineString(
        [
            (point1.x - n[0] * distance, point1.y - n[1] * distance),
            (point1.x + n[0] * distance, point1.y + n[1] * distance),
        ]
    )
    return perp_line


def get_value_hex_color(value: float, vmin: float, vmax: float) -> str:
    """Get the hex color of a value within 2 given bounds vmin and vmax. This is useful to make color gradient scales"""
    cmap = cm.viridis
    norm = Normalize(vmin=vmin, vmax=vmax)
    rgb = cmap(norm(value))
    color = rgb2hex(rgb)
    return color


def get_objects_in_polygon(list_objects: List, polygon: Polygon) -> List:
    """
    Return only cpts or bore within the polygon boundaries.
    """
    filtered_list_objects = []
    for obj in list_objects:
        params = obj.last_saved_params
        coords = [float(params["x_rd"]), float(params["y_rd"])]

        if polygon.contains(Point(coords)):
            filtered_list_objects.append(obj)
    return filtered_list_objects


def get_point_from_trajectory(trajectory_points: List, chainage: Union[float, int]) -> Point:
    """Get point at specific chainage along trajectory"""
    distance_along_dyke = 0
    prev_point = trajectory_points[0]
    for point in trajectory_points:
        distance_along_dyke += prev_point.distance(point)
        if round(distance_along_dyke, 0) >= chainage:
            return point
        prev_point = point
    return None


def get_exit_point_projection_on_entry_line(
    exit_point: Point, dyke_trajectory: LineString, entry_line: LineString, extension: int = 0
) -> Point:
    """Take the exit point and search for the closest point on the dike trajectory. That line extends to the
    entry line and their intersection point is returned.
    :param exit_point: starting point of  the cross-section line
    :param dyke_trajectory: trajectory of the dike as a Linestring.
    :param entry_line: trajectory of the entry line of the dike as a LineString.
    :param extension: distance from the entry line for which the cross section line must be extended. Is set to 0
    by default, which means that the point on the entry line is returned exactly.
    """
    LINE_OVER_EXTENSION = 500
    exit_point_projection_on_dike_trajectory = nearest_points(dyke_trajectory, exit_point)[0]
    intersection_line = extend_linestring(
        LineString([exit_point, exit_point_projection_on_dike_trajectory]), LINE_OVER_EXTENSION
    )
    projected_exit_point = entry_line.intersection(intersection_line)
    if extension == 0:
        return projected_exit_point
    return intersection_line.interpolate(exit_point.distance(projected_exit_point) + extension)


def extend_line(line: LineString, offset: float, side: str) -> LineString:
    """Extend a LineString with an offset, either from the start or the end of the line
    copied and adapted from shapely_tools.py written by Dirk Eilander (dirk.eilander@deltares.nl)
    """
    coords = line.coords
    if side == "start":
        p_new = shift_point(coords[0], coords[1], -1.0 * offset)
        line = LineString([p_new] + coords[:])
    elif side == "end":
        p_new = shift_point(coords[-1], coords[-2], -1.0 * offset)
        line = LineString(coords[:] + [p_new])

    return line


def shift_point(c1: Tuple[float, float], c2: Tuple[float, float], offset: float) -> Point:
    """
    shift points with offset in orientation of line c1->c2
    copied and adapted from shapely_tools.py written by Dirk Eilander (dirk.eilander@deltares.nl)
    """
    x1, y1 = c1
    x2, y2 = c2

    if ((x1 - x2) == 0) and ((y1 - y2) == 0):  # zero length line
        x_new, y_new = x1, y1
    else:
        rel_length = np.minimum(offset / np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2), 1)
        x_new = x1 + (x2 - x1) * rel_length
        y_new = y1 + (y2 - y1) * rel_length
    return Point(x_new, y_new)
