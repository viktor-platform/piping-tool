from typing import List
from typing import Tuple

import pandas as pd
import requests.exceptions
from numpy import isnan
from shapely.geometry import LineString
from shapely.geometry import Point
from shapely.geometry import Polygon

from app.lib.ahn.ahn_helper_functions import fetch_ahn_z_values
from app.lib.shapely_helper_functions import generate_perpendicular_line_to_trajectory_from_point
from viktor import UserException


def get_ditch_points_data(
    segment_ditches: List[dict],
    point: Point,
    water_level: float,
) -> Tuple[List[dict], float]:
    """
    Get ditch points with respect to the local (cross-section) coordinate's system and the talu slope.
    """

    for ditch in segment_ditches:
        pol = Polygon(ditch["ditch_polygon"])
        line = LineString(ditch["ditch_center_line"])
        if pol.contains(point):
            loop = True
            buffer = 20
            # If the buffer is too large for the `S-shaped` ditches, then the perpendicular line to the ditch
            # trajectory can intersect the ditch polygon several times, and 'perp_line.intersection(pol)' becomes
            # a MultiLineString object and raises a NotImplementedError. If such is the case, the buffer is
            # incrementally decreased until there is a single intersection.
            # Carefull, if the buffer is too small, the algorithm might get infinitely stuck!
            while loop:
                if buffer < 0:
                    raise DitchPolygonIntersectionError
                try:
                    perp_line = generate_perpendicular_line_to_trajectory_from_point(line, point, buffer=buffer)
                    # Get RD coords of first and last ditch points
                    coords = list(perp_line.intersection(pol).coords)
                    loop = False
                except NotImplementedError:
                    buffer -= 5
            df_coords = pd.DataFrame({"x": [c[0] for c in coords], "y": [c[1] for c in coords],})[
                ::-1
            ].reset_index(drop=True)
            df_coords = get_not_nan_closest_points_to_ditch(df_coords, perp_line, point)
            # Transform coords into the local coordinate system: x=0 is the first ditch point
            if df_coords.empty:
                raise AHNEmptyDfError
            point0 = Point(df_coords.loc[0, "x"], df_coords.loc[0, "y"])
            df_coords["x_local"] = [
                ((x - point0.x) ** 2 + (y - point0.y) ** 2) ** 0.5 for x, y in zip(df_coords["x"], df_coords["y"])
            ]
            inclination = ditch["talu_slope"]
            water_depth = ditch["water_depth"]
            maintenance_depth = ditch["maintenance_depth"]
            z_bottom = water_level - water_depth - maintenance_depth
            x_1 = df_coords.loc[0, "x_local"] + inclination * water_depth
            x_2 = df_coords.loc[1, "x_local"] - inclination * water_depth

            if x_1 >= df_coords.loc[1, "x_local"]:
                x_1 = df_coords.loc[1, "x_local"] / 2

            # There are some cases in which the points at the bottom are inverted
            # (i.e. very narrow ditch  or very deep)
            # In these cases the second point is se to coincide with the first
            x_2 = max(x_2, x_1)
            ditch_points = [
                {"x": df_coords.loc[0, "x_local"], "z": df_coords.loc[0, "z"]},
                {"x": x_1, "z": z_bottom},
                {"x": x_2, "z": z_bottom},
                {"x": df_coords.loc[1, "x_local"], "z": df_coords.loc[1, "z"]},
            ]
            return ditch_points, inclination
    raise UserException("Punt hoort niet bij een van de sloten")


def get_not_nan_closest_points_to_ditch(
    df_coords_rd: pd.DataFrame, perp_line: LineString, point: Point
) -> pd.DataFrame:
    """
    If one of the requested points has NaN as z-coordinate, the point is shifted of 0.5 meter (tolerance ahn)
    """
    try:
        df_coords_rd = fetch_ahn_z_values(df_coords_rd, skip_clustering=True)
    except requests.exceptions.HTTPError:
        raise UserException("AHN unavailable, try again later")  # TODO TRANSLATE
    counter = 0
    while any(df_coords_rd["z"].isna()):
        coords = []
        counter += 1
        if counter > 20:
            raise ConnectionError
        for x, y, z, i in zip(df_coords_rd["x"], df_coords_rd["y"], df_coords_rd["z"], df_coords_rd.index):
            if i == 0:
                tol = -0.5
            else:
                tol = 0.5
            if isnan(z):
                point = perp_line.interpolate(perp_line.project(point) + tol)
                coords.append([point.x, point.y])
            else:
                coords.append([x, y])

        df_coords_rd = pd.DataFrame(
            {
                "x": [c[0] for c in coords],
                "y": [c[1] for c in coords],
            }
        )
        df_coords_rd = fetch_ahn_z_values(df_coords_rd, skip_clustering=True)
    return df_coords_rd


# Temporary custom errors raised during generation of Exit Point in ditches. Because of how messy ditch data can be,
# some edge-cases are hard to handle. Just leave them for now.


class AHNEmptyDfError(Exception):
    """Custom error when the returned Dataframe is empty? Need to investigate why, so for just raise an error and skip
    the exit point"""


class DitchPolygonIntersectionError(Exception):
    """Could not find the width of the ditch polygon"""
