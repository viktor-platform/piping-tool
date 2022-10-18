from math import isnan
from math import sqrt
from typing import List
from typing import Optional

import pandas as pd
from pandas import DataFrame
from shapely.geometry import LineString
from shapely.geometry import MultiPoint
from shapely.geometry import Point
from shapely.geometry import Polygon

from app.lib.ahn.ahn_helper_functions import fetch_ahn_z_values
from viktor.geo import Point as ViktorPoint
from viktor.geo import SoilLayout
from viktor.geo import SoilLayout2D
from viktor.geometry import Polyline as ViktorPolyline

from ..ditch.model import Ditch


def get_all_point_coordinates_on_cross(
    start_point: Point, end_point: Point, bathymetry_points: MultiPoint, spatial_resolution: float
) -> DataFrame:
    """Get the XYZ coordinates of all the points of a cross-section defined by its start and end points. The cross-
    section line is split with respect to the provided spatial resolution
    :param start_point: Starting bath_point of the cross-section
    :param end_point: Ending bath_point of the cross-section
    :param bathymetry_points: bathymetry points truncated around the cross section, as a MultiPoint object
    :param spatial_resolution: spatial resolution for which the cross-section is split into equally separated points
    """
    full_traj = LineString([start_point, end_point])
    bathymetry_convex_hull = bathymetry_points.convex_hull

    ahn_traj = full_traj.difference(bathymetry_convex_hull)
    bathy_traj = full_traj.intersection(bathymetry_convex_hull)
    if bathymetry_points.is_empty:
        pass
    if bathy_traj.is_empty:
        ahn_df = get_xyz_df(full_traj, spatial_resolution, source="ahn")
        bath_df = pd.DataFrame(columns=["x", "y", "z"])
    else:
        bath_df = get_xyz_df(bathy_traj, spatial_resolution, source="bathymetry", bathymetry_points=bathymetry_points)
        ahn_df = get_xyz_df(ahn_traj, spatial_resolution, source="ahn")

    # combine ahn df and bathymetry df
    cs_point_coords_df = pd.concat([bath_df, ahn_df])

    cs_point_coords_df["distance_from_start"] = cs_point_coords_df.apply(
        lambda row: sqrt((row["x"] - start_point.x) ** 2 + (row["y"] - start_point.y) ** 2), axis=1
    )
    cs_point_coords_df["z"].fillna(method="ffill", inplace=True)
    cs_point_coords_df = cs_point_coords_df.sort_values(by=["distance_from_start"])

    return cs_point_coords_df


def get_xyz_df(
    traj: LineString, spatial_resolution: float, source: str, bathymetry_points: Optional[MultiPoint] = None
):
    """
    Return the DataFrame with xyz coordinates of a trajectory segmented with the spatial resolution. Source for the
    z-height can be either AHN or bathymetry data
    :param traj: trajectory LineString for which xyz points will be returned
    :param spatial_resolution: spatial resolution in meter
    :param source: one of ['ahn', 'bathymetry']
    :param bathymetry_points: must be provided if the source bathymetry is selected. It is a MultiPoint collection of
    all the bathymetry data.
    :return: return xyz coordinates as a DataFrame
    """
    start_point, end_point = Point(traj.coords[0]), Point(traj.coords[-1])
    dx = start_point.x - end_point.x
    dy = start_point.y - end_point.y
    cs_length = start_point.distance(end_point)
    number_of_cs_points = int(cs_length // spatial_resolution)

    # get coordinates for all points in cross-section
    cs_points_x, cs_points_y = [], []
    for i in range(number_of_cs_points + 1):
        cs_points_x.append(start_point.x - i * dx / number_of_cs_points)
        cs_points_y.append(start_point.y - i * dy / number_of_cs_points)

    # create dataframe of all points and fetch z values from AHN data
    x_y_coords_df = pd.DataFrame(list(zip(cs_points_x, cs_points_y)), columns=["x", "y"])
    return fetch_z_values(x_y_coords_df, source, bathymetry_points)


def fetch_z_values(x_y_coords_df: DataFrame, source: str, bathymetry_points: Optional[MultiPoint] = None) -> DataFrame:
    """Fetch the z height of all the x-y points stored as a DataFrame. The height can either come from AHN data or from
    provided bathymetry points
    :param x_y_coords_df: coordinates of the points stored as a DataFrame for which the height must be calculated
    :param source: one of ['ahn', 'bathymetry']
    :param bathymetry_points: must be provided if the source bathymetry is selected. It is a MultiPoint collection of
    all the bathymetry data.
    :return: return xyz coordinates as a DataFrame
    """
    if source == "ahn":
        ahn_df = fetch_ahn_z_values(x_y_coords_df)
        ahn_df.dropna(inplace=True)
        return ahn_df

    elif source == "bathymetry" and bathymetry_points is not None and not bathymetry_points.is_empty:

        def get_z_from_closest_bathymetry_point(row, bathymetry_points: MultiPoint) -> float:
            """Helper function applied to the rows of the x_y_coords DataFrame. This function returns the z bathymetry
            value for the closest point from the bathymetry data from the iterated row"""
            min_distance = 9999
            min_z = None
            for bath_point in bathymetry_points:
                distance = bath_point.distance(Point(row["x"], row["y"]))

                # get depth of closest bath_point
                if distance < min_distance:
                    min_distance = distance
                    min_z = bath_point.z
            return min_z

        x_y_coords_df["z"] = x_y_coords_df.apply(
            lambda row: get_z_from_closest_bathymetry_point(row, bathymetry_points), axis=1
        )

        return x_y_coords_df
    else:
        raise ValueError


class SoilGeometry:
    def __init__(
        self,
        detailed_1d_soil_layout: SoilLayout,
        start_point: Point,
        end_point: Point,
        bathymetry_geopoints: MultiPoint,
        spatial_resolution: int,
        element_size: float,
        polder_level: float,
        river_level: float,
    ):

        self.all_bathymetry_points = bathymetry_geopoints
        self.spatial_resolution = spatial_resolution
        self.soil_layout = SoilLayout(list(reversed(detailed_1d_soil_layout.layers)))
        self.start_point = start_point
        self.end_point = end_point
        self.trajectory = LineString([self.start_point, self.end_point])
        self.polder_level = polder_level
        self.river_level = river_level
        self.element_size = element_size

    @property
    def soil_layout_2d(self) -> SoilLayout2D:
        """create the soil_layout2D for this geometry"""
        cover_layer_top_points = [
            ViktorPoint(row["distance_from_start"], row["z"]) for _, row in self.cross_section_data.iterrows()
        ]
        cover_layer_top_points = [point for point in cover_layer_top_points if not isnan(point.y)]
        cover_layer_top = ViktorPolyline(cover_layer_top_points)

        return SoilLayout2D.from_single_soil_layout(
            self.soil_layout, 0, self.cross_section_data["distance_from_start"].max(), cover_layer_top
        )

    @property
    def local_bathymetry_points(self) -> MultiPoint:
        """Return a subset of all the bathymetry points located inside a buffer zone around the cross-section
        trajectory"""
        BUFFER_DISTANCE = 30  # [m] TODO: should depend on the spacing of the bathymetry data.
        cross_section_buffer_polygon = self.trajectory.buffer(BUFFER_DISTANCE)
        intersected_points = self.all_bathymetry_points.intersection(cross_section_buffer_polygon)
        return intersected_points

    @property
    def cross_section_data(self):
        return get_all_point_coordinates_on_cross(
            self.start_point, self.end_point, self.local_bathymetry_points, self.spatial_resolution
        )

    def soil_layout_2d_with_ditches_removed(self, ditch_data: List[dict]) -> SoilLayout2D:
        """create the soil_layout2D for this geometry where the ditches have been removed"""
        ditches = self.intersecting_ditches(ditch_data)
        sl2d = self.soil_layout_2d
        new_cover_layer = []

        # If no ditch intersected, return the soil_layout_2d Object directly.
        if not ditches:
            return self.soil_layout_2d

        for point in sl2d.top_profile.points:
            has_ditch = False
            for ditch in ditches:
                ditch_line = ditch.cross_section

                if ditch_line.x_min < point.x < ditch_line.x_max:  # this is the region where the ditch is
                    has_ditch = True
                    ditch_y = ditch_line.intersections_with_x_location(point.x)[0].y  # first intersection, y coord
                    new_cover_layer.append(ViktorPoint(point.x, ditch_y))
            if not has_ditch:
                new_cover_layer.append(point)

        new_cover_layer = ViktorPolyline(new_cover_layer)

        return SoilLayout2D.from_single_soil_layout(self.soil_layout, 0, new_cover_layer.x_max, new_cover_layer)

    def intersecting_ditches(self, ditch_data: List[dict]) -> List[Ditch]:
        """returns a list Ditch objects for all ditches intersecting with this cross-section"""
        intersecting_ditches = []
        for ditch in ditch_data:  # dry ditches
            ditch_poly = Polygon(ditch["ditch_polygon"])
            # if len = 0, no intersection ignore this ditch
            # if len = 1, ditch only intersects partly, ignore this ditch TODO: look into partial intersections
            # if len > 2: ditch is curved and intersects twice, ignore TODO: look into double intersections
            if len(ditch_poly.intersection(self.trajectory).coords) == 2:
                left_edge = Point(ditch_poly.intersection(self.trajectory).coords[0])
                right_edge = Point(ditch_poly.intersection(self.trajectory).coords[-1])
                intersecting_ditches.append(
                    Ditch.from_intersection(left_edge, right_edge, ditch, self.start_point, self.polder_level)
                )
        return intersecting_ditches
