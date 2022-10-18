from copy import deepcopy
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import numpy as np
from munch import Munch
from munch import munchify
from numpy import nan
from pandas import DataFrame
from plotly import graph_objects as go
from shapely.geometry import LineString
from shapely.geometry import MultiPoint
from shapely.geometry import MultiPolygon
from shapely.geometry import Point
from shapely.geometry import Polygon
from shapely.ops import nearest_points
from shapely.ops import unary_union

from app.lib.shapely_helper_functions import check_if_point_in_polygons
from app.lib.shapely_helper_functions import extend_line
from app.lib.shapely_helper_functions import extend_linestring
from app.lib.shapely_helper_functions import find_direction
from app.lib.shapely_helper_functions import find_perpendicular_direction
from app.lib.shapely_helper_functions import get_objects_in_polygon
from app.lib.shapely_helper_functions import get_unit_vector
from app.lib.shapely_helper_functions import get_unity_check_color
from app.lib.shapely_helper_functions import rotate_90_deg
from viktor.api_v1 import Entity
from viktor.api_v1 import EntityList
from viktor.core import UserException
from viktor.core import progress_message
from viktor.geometry import GeoPoint
from viktor.geometry import RDWGSConverter
from viktor.views import MapEntityLink
from viktor.views import MapFeature
from viktor.views import MapLabel
from viktor.views import MapPoint

from ..ditch.model import Ditch
from ..ditch.model import DitchHeffError
from ..ditch.model import DitchIntersectionLines
from ..ditch.model import DitchLargeBError
from ..ditch.utils import DitchPolygonIntersectionError
from ..ditch.utils import get_ditch_points_data
from ..dyke.dyke_model import LINE_SCALE
from ..dyke.dyke_model import Dyke
from ..exit_point.model import ExitPointProperties
from ..ground_model.model import build_combined_rep_and_exit_point_layout
from ..ground_model.tno_model import TNOGroundModel
from ..ground_model.tno_model import get_longitudinal_soil_layout
from ..ground_model.tno_model import get_min_max_permeabilities_from_soil_layout
from ..lib.ahn.ahn_helper_functions import get_xyz_df_from_multipoints
from ..lib.plotly_2d_profile_helper_functions import get_visualisation_along_trajectory
from ..lib.regis.regis_helper import get_longitudinal_regis_soil_layouts
from ..piping_tool.constants import PipingDataFrameColumns
from .constants import DEFAULT_PIPING_ERROR_RESULTS
from .constants import SPATIAL_RESOLUTION_SEGMENT_CHAINAGE
from .param_parser_functions import Scenario
from .param_parser_functions import get_piping_hydro_parameters
from .param_parser_functions import get_representative_soil_layouts
from .param_parser_functions import get_soil_scenario

TOL = 0.5  # meter tolerance to generate points along ditches lines


class Segment:
    def __init__(self, params: Munch, trajectory: LineString, dyke: Dyke, entry_line: Union[LineString, None]):
        self._params = params
        self.trajectory = trajectory  # coordinate system: RD
        self._dyke = dyke
        self._rotation_matrices = self._get_rotation_matrices
        self._entry_line = entry_line

    @property
    def interpolated_trajectory(self) -> LineString:
        """Returns the segmented trajectory, that is to say a LineString cut into portions of equal length based on
        the chainage resolution.
        This trajectory differs from the base trajectory of the segment that is uploaded but the two are very similar.
        This is not so much of a problem as long as the chainage resolution is small
        enough (25m in practice), which is acceptable.
        """
        base_trajectory = self.trajectory
        chainage_step = SPATIAL_RESOLUTION_SEGMENT_CHAINAGE
        nb_points = int(base_trajectory.length / chainage_step)

        # The last point of the base trajectory is added because it is not interpolated
        interpolated_trajectory = LineString(
            [base_trajectory.interpolate(n * chainage_step) for n in range(nb_points)] + [base_trajectory.coords[-1]]
        )
        return interpolated_trajectory

    def create_hinterland_hull(self, length: float, buffer_length_hinterland: float) -> list:
        """Return a shapely Polygon encapsulating the hinterland where length is the hinterland length, this polygon
        can potentially have interiors (i.e. holes)"""
        # TODO: consider memoizing this function?
        # note: vector switches direction if length is negative
        vector = length * self.perpendicular_unit_vector
        buffer_vector = buffer_length_hinterland * self.perpendicular_unit_vector

        # create the hinterland polygon
        hinterland = Polygon(
            [
                *(Point(np.array(point) + buffer_vector) for point in self.trajectory.coords),
                *(Point(np.array(point) + vector) for point in reversed(self.trajectory.coords)),
            ]
        )

        # remove the ditches if needed
        list_polygon = []
        if self._params.segment_ditches and self._params.segment_dry_ditches:
            for ditch in self._params.segment_ditches + self._params.segment_dry_ditches:
                poly_coord = ditch.ditch_polygon
                list_polygon.append(Polygon(poly_coord))
            ditch_polygons = MultiPolygon(list_polygon)
        else:
            ditch_polygons = MultiPolygon([])

        hinterland = hinterland.difference(ditch_polygons)

        if hinterland.geom_type == "MultiPolygon":
            hinterland_hull = list(hinterland.geoms)
        else:
            hinterland_hull = [hinterland]

        return hinterland_hull

    def create_foreland_hull(self, length: float, buffer_length_hinterland: float) -> Polygon:
        """create a geopolygon encapsulating the foreland"""
        # note: vector switches direction if length is negative
        vector = length * self.perpendicular_unit_vector * -1
        buffer_vector = buffer_length_hinterland * self.perpendicular_unit_vector

        # create the foreland polygon
        foreland = Polygon(
            [
                *(Point(np.array(point) + buffer_vector) for point in self.trajectory.coords),
                *(Point(np.array(point) + vector) for point in reversed(self.trajectory.coords)),
            ]
        )
        return foreland

    def create_ditches_hull(self, length: float) -> Polygon:
        """create geopolygon encapsulating the ditches buffer zone
        where length is the hinterland length"""
        # note: vector switches direction if length is negative
        vector = length * self.perpendicular_unit_vector

        # create the hinterland polygon
        hinterland = Polygon(
            [
                *(Point(point) for point in self.trajectory.coords),
                *(Point(np.array(point) + vector) for point in reversed(self.trajectory.coords)),
            ]
        )
        return hinterland

    @property
    def perpendicular_unit_vector(self) -> np.array:
        """get the unit vector perpendicular to the midpoint of the segment ** expressed  in RD ***
        in direction of hinterland"""
        middle_index = int(len(self.trajectory.coords) / 2)
        direction = find_perpendicular_direction(
            self.trajectory, middle_index, clockwise=not self._dyke.direction_to_river
        )  # not river = hinterland
        return get_unit_vector(self._origin_local_system_expressed_in_rd, direction)

    @property
    def parallel_unit_vector(self) -> np.array:
        """get the unit vector parallel to the midpoint of the segement ** expressed  in RD ***
        rotated clockwise from the perpendicular vector for right hand coordinate system"""
        midpoint = self._origin_local_system_expressed_in_rd
        direction = rotate_90_deg(midpoint, midpoint + self.perpendicular_unit_vector)
        return get_unit_vector(midpoint, direction)

    @property
    def _get_rotation_matrices(self) -> dict:
        """get the rotation matrix to transform between RD and the local coordinate system"""
        sin = self.parallel_unit_vector[0]
        cos = self.parallel_unit_vector[1]
        # because norm unit vector is 1 therefore it is on the unit circle

        return {"rd_to_local": np.array(((cos, -sin), (sin, cos))), "local_to_rd": np.array(((cos, sin), (-sin, cos)))}

    def transform_rd_to_local_coordinates(self, point_in_rd: np.array) -> np.array:
        """transform 2D point from RD to local coordinates, where the local system is defined by
        - origin at the midpoint of the segment
        - x parallel to the segment at the midpoint,
        - y perpendicular to the segment at the midpoint"""
        coords = self._rotation_matrices["rd_to_local"] @ (point_in_rd - self._origin_local_system_expressed_in_rd)
        return coords @ np.array([[0, -1], [1, 0]])

    def transform_local_coordinates_to_rd(self, point: np.array) -> np.array:
        """transform 2D point in local coordinates to RD"""
        coords = (self._rotation_matrices["local_to_rd"] @ point) @ np.array([[0, 1], [-1, 0]])
        return coords + self._origin_local_system_expressed_in_rd

    def fill_polygon_with_grid(self, polygon_hinterland: Polygon, delta_x: float, delta_y: float) -> MultiPoint:
        """Returns a multipoint containing the grid inside polygon to fill with a step of
        delta_x along the dyke and delta_y perpendicular to it"""
        polygon_to_fill = Polygon(polygon_hinterland.exterior)
        points_local_cs = [
            self.transform_rd_to_local_coordinates(np.array(point)) for point in polygon_to_fill.exterior.coords
        ]

        # find bounding box in local coordinate system
        x_min = min(p[0] for p in points_local_cs)
        x_max = max(p[0] for p in points_local_cs)
        y_min = min(p[1] for p in points_local_cs)
        y_max = max(p[1] for p in points_local_cs)

        # fill bounding box with points inside the hinterland polygon and outside the ditch
        exit_points = []
        for x in np.arange(x_min, x_max, delta_x):
            for y in np.arange(y_min, y_max, delta_y):
                pt = Point(self.transform_local_coordinates_to_rd(np.array([x, y])))
                if pt.within(
                    polygon_hinterland.buffer(0.1)
                ):  # this condition ALSO checks whether a point is inside a ditch or not
                    exit_points.append(pt)

        return polygon_to_fill.buffer(0.1).intersection(MultiPoint(exit_points))

    def get_exit_points_from_ditches(self) -> MultiPoint:
        if self._params.is_ditch_points:
            delta_ditch = self._params.delta_ditch
            exit_points = []

            for segment_ditch in self.all_ditches:
                ditch_line = LineString(segment_ditch.ditch_center_line)
                distances = np.arange(TOL, ditch_line.length - TOL, delta_ditch)
                points = [
                    ditch_line.interpolate(ditch_line.length - TOL)
                    if np.isclose(distance, ditch_line.length)
                    else ditch_line.interpolate(distance)
                    for distance in distances
                ]
                points = [(point.x, point.y) for point in points]
                exit_points.extend(points)
            return MultiPoint(exit_points)
        return MultiPoint([])

    def get_exit_points_from_grid_option_1(self) -> MultiPoint:
        """Return as a MultiPoint all the exit points generated from a grid. This grid generation ('option_1') is the
        first one implemented and has shown poor results. This generated has been kept here just in case."""
        if self._params.is_hinterland_grid:

            # transform hull to local coordinate system
            hinterland_polygon = self.create_hinterland_hull(
                self._params.exit_point_creation.exit_point_tab.length_hinterland,
                self._params.exit_point_creation.exit_point_tab.buffer_length_hinterland,
            )

            grid_points = []
            for polygon in hinterland_polygon:
                hinterland_grid = self.fill_polygon_with_grid(
                    polygon, self._params.hinterland_delta_x, self._params.hinterland_delta_y
                )
                for point in hinterland_grid.geoms:
                    grid_points.append(point)

            hinterland_grid = MultiPoint(grid_points)

            return hinterland_grid
        return MultiPoint([])

    def get_exit_points_from_manual_selection(self) -> MultiPoint:
        """Return as a MulitPoint all the exit points manually assigned on a MapView"""
        if self._params.manual_exit_point is None or not self._params.is_manual_exit_point:
            return MultiPoint([])
        exit_points = [Point(point.rd) for point in self._params.manual_exit_point.points]
        return MultiPoint(exit_points)

    def get_regular_grid_points_hinterland(
        self, resolution_x: float, resolution_y: float
    ) -> Union[MultiPoint, List[Point]]:
        """
        Return as a MultiPoint all the exit points generated from a grid. Points are generated more or less
        homogeneously in the hinterland region.
        :param resolution_x: resolution of the grid points in the direction parallel to the dike
        :param resolution_y: resolution of the grid points in the direction perpendicular to the dike
        :return:
        """

        # Get Hinterland start linestring

        _, _, direction = find_direction(
            self.trajectory, 0, clockwise=not self._dyke.direction_to_river
        )  # not river = hinterland
        side = "right" if direction > 0 else "left"
        hinterland_start_line = self.trajectory.parallel_offset(
            distance=self._params.exit_point_creation.exit_point_tab.buffer_length_hinterland, side=side
        )
        hinterland_end_line = self.trajectory.parallel_offset(
            distance=self._params.exit_point_creation.exit_point_tab.length_hinterland, side=side
        )

        # Partition of the hinterland start and end line
        distances = np.arange(0, hinterland_start_line.length, resolution_x)
        points_start_line = [hinterland_start_line.interpolate(distance) for distance in distances]
        multipoint_start_line = unary_union(points_start_line)
        points_end_line = [hinterland_end_line.interpolate(distance) for distance in distances]
        multipoint_end_line = unary_union(points_end_line)

        list_points = []
        for point_start, point_end in zip(multipoint_start_line, multipoint_end_line):
            perp_linestring = LineString([point_start, point_end])
            distances = np.arange(0, perp_linestring.length, resolution_y)
            points_on_line = [perp_linestring.interpolate(distance) for distance in distances]
            list_points.extend(points_on_line)

        return MultiPoint(list_points)

    def get_exit_points_from_grid_option_2(self) -> MultiPoint:
        if self._params.is_hinterland_grid:
            return self.get_regular_grid_points_hinterland(
                self._params.hinterland_delta_x, self._params.hinterland_delta_y
            )
        return MultiPoint([])

    def get_perpendicular_grid_points_hinterland(self, resolution_x: float, resolution_y: float) -> MultiPoint:
        """
        Return as a MultiPoint all the exit points generated from a grid. Points are generated on lines that are
        perpendicular to the segment's trajectory.
        :param resolution_x: resolution of the grid points in the direction parallel to the dike
        :param resolution_y: resolution of the grid points in the direction perpendicular to the dike
        :return:
        """
        LINE_OVER_EXTENSION = 500

        # Get Hinterland start linestring
        _, _, direction = find_direction(
            self.trajectory, 0, clockwise=not self._dyke.direction_to_river
        )  # not river = hinterland
        side = "right" if direction > 0 else "left"
        hinterland_start_line = self.trajectory.parallel_offset(
            distance=self._params.exit_point_creation.exit_point_tab.buffer_length_hinterland, side=side
        )
        hinterland_end_line = self.trajectory.parallel_offset(
            distance=self._params.exit_point_creation.exit_point_tab.length_hinterland, side=side
        )  # This line might be a bit short and must be extended on both sides to allow successful intersection

        hinterland_end_line = extend_line(
            line=hinterland_end_line,
            offset=20,
            side="start",
        )
        hinterland_end_line = extend_line(
            line=hinterland_end_line,
            offset=20,
            side="end",
        )

        # Partition of the hinterland start
        distances_start = np.arange(0, hinterland_start_line.length, resolution_x)
        points_start_line = [hinterland_start_line.interpolate(distance) for distance in distances_start]
        multipoint_start_line = unary_union(points_start_line)

        # Intersect the hinterland end line with perpendicular lines to the segment trajectory
        list_points = []
        for point_start in multipoint_start_line:

            projected_point_on_dike_trajectory = nearest_points(self.trajectory, point_start)[0]

            intersection_line = extend_linestring(
                LineString([projected_point_on_dike_trajectory, point_start]),
                LINE_OVER_EXTENSION,
            )

            projected_point_to_hinterland_endline = hinterland_end_line.intersection(intersection_line)
            if isinstance(projected_point_to_hinterland_endline, MultiPoint):  # error catching
                projected_point_to_hinterland_endline = projected_point_to_hinterland_endline[0]

            perp_linestring = LineString([point_start, projected_point_to_hinterland_endline])
            distances = np.arange(0, perp_linestring.length, resolution_y)
            points_on_line = [perp_linestring.interpolate(distance) for distance in distances]
            list_points.extend(points_on_line)
        return MultiPoint(list_points)

    def get_exit_points_from_grid_option_3(self) -> MultiPoint:
        if self._params.is_hinterland_grid:
            return self.get_perpendicular_grid_points_hinterland(
                self._params.hinterland_delta_x, self._params.hinterland_delta_y
            )
        return MultiPoint([])

    def find_lowest_point_hinterland(self) -> Tuple[float, float, float]:
        """Return the xyz coordinates of the lowest point in the hinterland from the AHN data"""
        all_grid_points = self.get_regular_grid_points_hinterland(
            self._params.exit_point_creation.exit_point_tab.resolution_lowest_point,
            self._params.exit_point_creation.exit_point_tab.resolution_lowest_point,
        )
        df_points = get_xyz_df_from_multipoints(all_grid_points)
        row_min_z = df_points.loc[df_points["z"].idxmin()]

        return row_min_z["x"], row_min_z["y"], row_min_z["z"]

    def get_all_draft_exit_point_locations(self) -> MultiPoint:
        """
        :return: Return all the draft exit points (both manually and automatically generated) as a single MultiPoint object.
        generated draft exit points are ordered according to the local coordinate system to facilitate proper naming
        """
        sorting_list = []

        if self._params.option_grid_hinterland == "option_1":
            exit_point_grids = self.get_exit_points_from_grid_option_1().geoms
        elif self._params.option_grid_hinterland == "option_2":
            exit_point_grids = self.get_exit_points_from_grid_option_2()
        elif self._params.option_grid_hinterland == "option_3":
            exit_point_grids = self.get_exit_points_from_grid_option_3()
        else:
            raise ValueError
        for point in exit_point_grids:
            x = point.x
            y = point.y
            x_local = round(self.transform_rd_to_local_coordinates(np.array([point.x, point.y]))[0], 1)
            y_local = round(self.transform_rd_to_local_coordinates(np.array([point.x, point.y]))[1], 1)
            sorting_list.append([x, y, x_local, y_local])

        # Sort draft exit points based on y_local (hence i[3])
        sorting_list = sorted(sorting_list, key=lambda i: i[3])

        points_list = [(Point(element[0], element[1])) for element in sorting_list]
        points_list.extend(self.get_exit_points_from_manual_selection().geoms)
        points_list.extend(self.get_exit_points_from_ditches().geoms)
        if self._params.is_lowest_point:
            x, y, _ = self.find_lowest_point_hinterland()
            points_list.extend([Point(x, y)])

        return MultiPoint(points_list)

    @property
    def _origin_local_system_expressed_in_rd(self) -> np.array:
        """coordinates of the origin of the local coordinate system in RD, at the midpoint of the segment"""
        middle_index = int(len(self.trajectory.coords) / 2)
        origin = np.array(self.trajectory.coords[middle_index])  # origin local coordinate system in RD
        return origin

    @property
    def all_ditches(self):
        if not self._params.segment_ditches and not self._params.segment_dry_ditches:
            raise UserException(
                "Geen sloten geselecteerd, gebruik de 'snij sloten' knop " "in Input Selectie> Selecteer Sloten"
            )

        all_ditches = []
        if self._params.segment_ditches is not None:
            all_ditches.extend(self._params.segment_dry_ditches)
        if self._params.segment_ditches is not None:
            all_ditches.extend(self._params.segment_ditches)
        return all_ditches

    @property
    def get_ditches_as_multipolygons(self) -> Tuple[MultiPolygon, MultiPolygon]:
        """Return Multipolygons containing the ditches if the Toggle 'params.select_with_buffer_zone' is switched on, or empty MultiPolygons otherwise."""
        if self._params.select_with_buffer_zone:
            if self._params.segment_ditches is None or self._params.segment_dry_ditches is None:
                raise UserException("Sloten dienen te worden gedefinieerd")

            segment_ditches_pol = MultiPolygon([Polygon(pol["ditch_polygon"]) for pol in self._params.segment_ditches])
            segment_dry_ditches_pol = MultiPolygon(
                [Polygon(pol["ditch_polygon"]) for pol in self._params.segment_dry_ditches]
            )
        else:
            segment_ditches_pol = MultiPolygon([])
            segment_dry_ditches_pol = MultiPolygon([])
        return segment_ditches_pol, segment_dry_ditches_pol

    def get_segment_2D_longitudinal_profile(
        self,
        tno_ground_model: TNOGroundModel,
        chainage_step: float,
        cpt_folder: Optional[Entity] = None,
        bore_folder: Optional[Entity] = None,
    ) -> go.Figure:
        """Get the 2D longitudinal figure of the segment trajectory"""
        buffer_polygon = self.interpolated_trajectory.buffer(self._dyke.params.buffer_zone_cpts_bore)
        if cpt_folder:
            cpt_entity_list = cpt_folder.children(entity_type_names=["CPT"])
            cpt_entity_list = get_objects_in_polygon(cpt_entity_list, buffer_polygon)
            cpt_params = dict(
                cpt_entity_list=cpt_entity_list,
                scale_measurement_cpt_qc=5 * LINE_SCALE,
                scale_measurement_cpt_rf=5 * LINE_SCALE,
                scale_measurement_cpt_u2=100 * LINE_SCALE,
            )
        else:
            cpt_params = None
        if bore_folder:
            bore_entity_list = bore_folder.children(entity_type_names=["Bore"])
            bore_entity_list = get_objects_in_polygon(bore_entity_list, buffer_polygon)
        else:
            bore_entity_list = None
        long_profile = get_longitudinal_soil_layout(self.interpolated_trajectory, tno_ground_model)
        min_perm_v, max_perm_v, min_perm_h, max_perm_h = get_min_max_permeabilities_from_soil_layout(long_profile)

        min_max_permeabilities = dict(
            min_perm_v=min_perm_v, max_perm_v=max_perm_v, min_perm_h=min_perm_h, max_perm_h=max_perm_h
        )
        regis_soil_layouts = get_longitudinal_regis_soil_layouts(
            buffer_polygon, self.interpolated_trajectory, self._params.input_selection.materials.bottom_level_query
        )

        return get_visualisation_along_trajectory(
            trajectory=self.interpolated_trajectory,
            longitudinal_soil_layout=long_profile,
            min_max_permeabilities=min_max_permeabilities,
            materials_table=self._params.input_selection.materials.table,
            chainage_step=chainage_step,
            classification_table=self._params.input_selection.materials.classification_table,
            vertical_line_location=self._params.input_selection.soil_schematization.distance_from_start,
            cpt_params=cpt_params,
            bore_entity_list=bore_entity_list,
            regis_layouts=regis_soil_layouts,
        )

    def get_ditch(self, coordinates: Tuple[float, float]) -> Optional[Ditch]:
        # Get ditch if Exit point is in a ditch
        segment_ditches_pol, segment_dry_ditches_pol = self.get_ditches_as_multipolygons
        point = Point(coordinates)
        check_bool, type_ditch = check_if_point_in_polygons(segment_ditches_pol, segment_dry_ditches_pol, point)
        if check_bool is True:
            if type_ditch == "wet":
                ditch_points, talu_slope = get_ditch_points_data(
                    self._params.segment_ditches, point, self._params.polder_level
                )
                ditch_param = {
                    "ditch_points": ditch_points,
                    "talu_slope": talu_slope,
                    "is_wet": True,
                }
            else:
                ditch_points, talu_slope = get_ditch_points_data(
                    self._params.segment_dry_ditches, point, self._params.polder_level
                )
                ditch_param = {
                    "ditch_points": ditch_points,
                    "talu_slope": talu_slope,
                    "is_wet": False,
                }

            if ditch_param.get("ditch_points") and ditch_param.get("is_wet") is not None:
                ditch = Ditch(
                    *ditch_param.get("ditch_points"),
                    is_wet=ditch_param.get("is_wet"),
                    talu_slope=ditch_param.get("talu_slope"),
                )
            else:
                ditch = None
        else:
            ditch = None
        return ditch

    def get_all_scenarios(
        self, leakage_length_array: List[Munch], geohyromodel: str, scenario_name: Optional[str] = None
    ) -> List:
        """
        Append the leakaage length to the scenario from the soil schematization and return the complete parametrization
        of the scenarios.
        :param leakage_length_array: DynamicArray containing the leakage lengths, structure is:
        [{"leakage_length_foreland_aquifer_1": float,
          "leakage_length_foreland_aquifer_2": float,
          "leakage_length_hinterland_aquifer_1": float,
          "leakage_length_hinterland_aquifer_2": float,
        }]
        :param geohyromodel: one of ['1', '2', '3']. Describe the level of detail for the geohydrological model.
        :param scenario_name: Optional, provide the index of a scenario if only this scenario should be returned.
        :return: list of Scenario objects

        """
        # If only a single scenario based on its index must be returned
        if scenario_name is not None:
            soil_scenario = get_soil_scenario(
                scenario_name, self._params.input_selection.soil_schematization.soil_scen_array
            )
            leakage_lengths = None

            # If model 2 selected, then fetch the corresponding leakage length row of the DynamicArray
            if geohyromodel == "2":
                for row in leakage_length_array:
                    if row.scenario == scenario_name:
                        leakage_lengths = row
                        break
                if leakage_lengths is None:
                    raise UserException("Selected scenario has no leakage lengths.")  # TODO TRANSLATE
            elif geohyromodel in ["0", "1"]:
                pass
            else:
                raise NotImplementedError
            try:
                return [Scenario(soil_scenario, geohyromodel, leakage_lengths)]
            except IndexError:
                raise UserException("Missing leakage length for at least one scenario")  # TODO TRANSLATE

        # if all scenarios should be returned in a list
        scenarios_soil = self._params.input_selection.soil_schematization.soil_scen_array
        if geohyromodel in ["0", "1"]:
            return [Scenario(scenario_soil, geohyromodel) for scenario_soil in scenarios_soil]
        elif geohyromodel == "2":
            compiled_scenarios = []
            for scenario in scenarios_soil:
                for leakage_length_row in leakage_length_array:
                    if leakage_length_row.scenario == scenario.name_of_scenario:
                        compiled_scenarios.append(Scenario(scenario, geohyromodel, leakage_length_row))
            return compiled_scenarios
        else:
            raise NotImplementedError

    def get_serialized_piping_results(self, exit_point_list: Union[EntityList, List[Entity]]) -> List[dict]:
        """
        Return all the piping results (Uplift, heave, Sellmeijer) for every aquifer of every exit point for every
        scenarios in a serialized format easily convertible into a DataFrame
        :param exit_point_list: List of ExitPoint entities to iterate
        :return:
        """
        scenario_index = (
            None
            if self._params.calculations.soil_profile.results_settings.composite_result_switch
            else self._params.calculations.soil_profile.results_settings.scenario_selection
        )
        scenarios = self.get_all_scenarios(
            self._params.soil_schematization.geohydrology.level2.leakage_length_array,
            geohyromodel=self._params.geohydrology_method,
            scenario_name=scenario_index,
        )
        result_list = []
        for j, scenario in enumerate(scenarios, 0):
            piping_hydro_parameters = munchify(get_piping_hydro_parameters(self._params))
            for i, exit_point in enumerate(exit_point_list, 1):
                progress_message(
                    f"{scenario.name_of_scenario} \n\n{exit_point.name}\n\n{i + j * len(exit_point_list)}/{len(exit_point_list) * len(scenarios)}"
                )

                exit_point_params = exit_point.last_saved_params
                coordinates = (
                    exit_point_params.exit_point_data.x_coordinate,
                    exit_point_params.exit_point_data.y_coordinate,
                )

                _, rep_soil_layout = get_representative_soil_layouts(self._params, scenario)
                soil_layout_piping = build_combined_rep_and_exit_point_layout(
                    exit_point_params.get("classified_soil_layout"), rep_soil_layout
                )
                try:
                    res_list = ExitPointProperties(
                        soil_layout_piping=soil_layout_piping.serialize(),
                        coordinates=coordinates,
                        dyke=self._dyke,
                        ditch=self.get_ditch(coordinates),
                        leakage_lengths=scenario.leakage_lengths,
                    ).get_exit_point_summary_piping_results(piping_hydro_parameters)
                    for piping_calculation in res_list:
                        piping_calculation[PipingDataFrameColumns.EXIT_POINT.value] = exit_point
                        piping_calculation["scenario"] = scenario
                        piping_calculation["scenario_name"] = scenario.name_of_scenario
                        result_list.append(piping_calculation)
                except (DitchHeffError, DitchLargeBError, DitchIntersectionLines, DitchPolygonIntersectionError):
                    piping_calculation = deepcopy(
                        DEFAULT_PIPING_ERROR_RESULTS
                    )  # deepcopy necessary here otherwise piping_calculation is getting overwritten
                    piping_calculation[PipingDataFrameColumns.EXIT_POINT.value] = exit_point
                    piping_calculation["scenario"] = scenario
                    piping_calculation["scenario_name"] = scenario.name_of_scenario
                    result_list.append(piping_calculation)

        return result_list

    def get_map_features_for_uncombined_piping_results(
        self,
        serialized_piping_res: List[dict],
        scenario_name: str,
        calculation_type: Optional[str] = None,
    ) -> Tuple[List[MapFeature], List[MapLabel]]:
        """
        Build the map features and labels for the uncombined piping calculations
        :param serialized_piping_res: Full piping results for all scenarios, all exit point and all aquifer
        :param scenario_name: name of the scenario for which the piping result nust be filtered
        :param calculation_type: one of ["uplift", "heave", "sellmeijer"]
        """
        map_features, map_labels = [], []

        # Filter the results for the selected scenario
        df_res = DataFrame.from_records(
            serialized_piping_res, columns=[col.value for col in PipingDataFrameColumns] + ["scenario_name"]
        )
        sorted_df = df_res[df_res["scenario_name"] == scenario_name]
        # Build the markers for the MapView
        description = ""
        uc_list = []
        for _, row in sorted_df.iterrows():  # iterrows() is code smell
            exit_point = row[PipingDataFrameColumns.EXIT_POINT.value]
            if row["aquifer"] == 1:
                description = f"## {exit_point.name} \n\n " + self.get_description_uncombined_results(
                    row, aquifer=1, calculation_type=calculation_type
                )
                uc_list = self.get_uc_list_uncombined_results(row, calculation_type=calculation_type)
            else:
                map_features.pop()
                map_labels.pop()
                description += self.get_description_uncombined_results(
                    row, aquifer=2, calculation_type=calculation_type
                )
                uc_list.extend(self.get_uc_list_uncombined_results(row, calculation_type=calculation_type))

            coordinates = (
                exit_point.last_saved_params.exit_point_data.x_coordinate,
                exit_point.last_saved_params.exit_point_data.y_coordinate,
            )
            map_features.append(
                MapPoint.from_geo_point(
                    GeoPoint.from_rd(coordinates),
                    color=get_unity_check_color(uc_list),
                    description=description,
                    entity_links=[MapEntityLink("Na Uitredepunt", entity_id=exit_point.id)],
                )
            )
            lat, lon = RDWGSConverter.from_rd_to_wgs(coordinates)
            map_labels.append(MapLabel(lat, lon, scale=17, text=f"{exit_point.name[13:]}"))

        return (
            map_features,
            map_labels,
        )

    @staticmethod
    def get_uc_list_uncombined_results(row, calculation_type: Optional[str] = None) -> List[float]:
        if calculation_type is None:
            uc_list = [row["uc_opbarsten"], row["uc_heave"], row["uc_sellmeijer"]]
        elif calculation_type == "uplift":
            uc_list = [row["uc_opbarsten"]]
        elif calculation_type == "heave":
            uc_list = [row["uc_heave"]]
        elif calculation_type == "sellmeijer":
            uc_list = [row["uc_sellmeijer"]]
        else:
            raise ValueError
        return uc_list

    @staticmethod
    def get_description_uncombined_results(row, aquifer: int, calculation_type: Optional[str] = None) -> str:
        if calculation_type is None:
            description = f"### Aquifer {aquifer}  \n\n Opbarsten: {cut_off_float(row['uc_opbarsten'])} \\\n Heave: {cut_off_float(row['uc_heave'])} \\\n Sellmeijer {cut_off_float(row['uc_sellmeijer'])} \n\n"
        elif calculation_type == "uplift":
            description = f"### Aquifer {aquifer}  \n\n Opbarsten: {cut_off_float(row['uc_opbarsten'])} \n\n"
        elif calculation_type == "heave":
            description = f"### Aquifer {aquifer}  \n\n Heave: {cut_off_float(row['uc_heave'])} \n\n"
        elif calculation_type == "sellmeijer":
            description = f"### Aquifer {aquifer}  \n\n Sellmeijer {cut_off_float(row['uc_sellmeijer'])} \n\n"
        else:
            raise ValueError
        return description

    def get_map_features_for_combined_piping_results(
        self, serialized_piping_res: List[dict], calculation_type: Optional[str] = None
    ) -> Tuple[List[MapFeature], List[MapLabel]]:
        """Build the map features and labels for the combined piping calculations
        :param serialized_piping_res: Full piping results for all scenarios, all exit point and all aquifer
        """
        # Filter the results for the selected scenario
        df_res = DataFrame.from_records(
            serialized_piping_res, columns=[col.value for col in PipingDataFrameColumns] + ["scenario_name"]
        )
        df_res = df_res.replace("nan", nan)

        # Add exit point name to dataframe
        def add_exit_point_name(row):
            return row.name

        df_res["exit_point_name"] = df_res[PipingDataFrameColumns.EXIT_POINT.value].apply(add_exit_point_name)
        unique_exit_point_entities = df_res.drop_duplicates(subset=["exit_point_name"])[
            PipingDataFrameColumns.EXIT_POINT.value
        ].to_list()
        exit_point_mapping = {exit_point.name: exit_point for exit_point in unique_exit_point_entities}
        sorted_df = df_res.sort_values(by=["exit_point_name"])

        # Separate first and second aquifer in different dataframes
        aq_1_df = sorted_df[sorted_df["aquifer"] == 1].sort_values(by=["scenario_name"])
        aq_2_df = sorted_df[sorted_df["aquifer"] == 2].sort_values(by=["scenario_name"])
        aq_1_df["w_sellmeijer"] = aq_1_df.apply(
            lambda x: (x["scenario"].weight_of_scenario * x["uc_sellmeijer"]), axis=1
        )
        aq_1_df["w_uplift"] = aq_1_df.apply(lambda x: (x["scenario"].weight_of_scenario * x["uc_opbarsten"]), axis=1)
        aq_1_df["w_heave"] = aq_1_df.apply(lambda x: (x["scenario"].weight_of_scenario * x["uc_heave"]), axis=1)

        if calculation_type is None:
            final_aq_1 = (
                aq_1_df.groupby("exit_point_name")["w_sellmeijer", "w_uplift", "w_heave"]
                .sum()
                .replace(0.0, nan)
                .to_dict("index")
            )
        else:
            final_aq_1 = (
                (aq_1_df.groupby("exit_point_name")["w_" + calculation_type].sum().replace(0.0, nan))
                .to_frame()
                .to_dict("index")
            )  # groupby returns a series when only one argument is provided

        if len(aq_2_df) > 0:
            aq_2_df["w_sellmeijer"] = aq_2_df.apply(
                lambda x: (x["scenario"].weight_of_scenario * x["uc_sellmeijer"]), axis=1
            )
            aq_2_df["w_uplift"] = aq_2_df.apply(
                lambda x: (x["scenario"].weight_of_scenario * x["uc_opbarsten"]), axis=1
            )
            aq_2_df["w_heave"] = aq_2_df.apply(lambda x: (x["scenario"].weight_of_scenario * x["uc_heave"]), axis=1)
            if calculation_type is None:
                final_aq_2 = (
                    aq_2_df.groupby("exit_point_name")["w_sellmeijer", "w_uplift", "w_heave"].sum().to_dict("index")
                )
            else:
                final_aq_2 = (
                    (aq_2_df.groupby("exit_point_name")["w_" + calculation_type].sum().replace(0.0, nan))
                    .to_frame()
                    .to_dict("index")
                )
            return make_marker_double_aquifer(final_aq_1, final_aq_2, exit_point_mapping, calculation_type)

        return make_marker_single_aquifer(final_aq_1, exit_point_mapping, calculation_type)


def make_marker_double_aquifer(
    final_aq_1: DataFrame, final_aq_2: DataFrame, exit_point_mapping: dict, calculation_type: Optional[str] = None
) -> Tuple[List[MapFeature], List[MapLabel]]:
    map_features, map_labels = [], []
    for key, aq_1, aq_2 in common_entries(final_aq_1, final_aq_2):
        exit_point = exit_point_mapping[key]
        coordinates = (
            exit_point.last_saved_params.exit_point_data.x_coordinate,
            exit_point.last_saved_params.exit_point_data.y_coordinate,
        )
        uc_list = list(aq_1.values()) + list(aq_2.values())

        map_features.append(
            MapPoint.from_geo_point(
                GeoPoint.from_rd(coordinates),
                color=get_unity_check_color(uc_list),
                description=get_marker_description_double_aquifer(exit_point, aq_1, aq_2, calculation_type),
                entity_links=[MapEntityLink("Na Uitredepunt", entity_id=exit_point.id)],
            )
        )
        lat, lon = RDWGSConverter.from_rd_to_wgs(coordinates)
        map_labels.append(MapLabel(lat, lon, scale=17, text=f"{exit_point.name[13:]}"))
    return (
        map_features,
        map_labels,
    )


def get_marker_description_double_aquifer(
    exit_point: Entity, aq_1: DataFrame, aq_2: DataFrame, calculation_type: Optional[str]
) -> str:
    if calculation_type is None:
        description = f"## {exit_point.name} \n\n ### Aquifer 1 \n\n Opbarsten: {cut_off_float(aq_1['w_uplift'])} \\\n  Heave: {cut_off_float(aq_1['w_heave'])} \\\n Sellmeijer {cut_off_float(aq_1['w_sellmeijer'])} \n\n"
        description += f"### Aquifer 2 \n\n Opbarsten: {cut_off_float(aq_2['w_uplift'])} \\\n  Heave: {cut_off_float(aq_2['w_heave'])} \\\n Sellmeijer {cut_off_float(aq_2['w_sellmeijer'])}"
    elif calculation_type == "uplift":
        description = f"## {exit_point.name} \n\n ### Aquifer 1 \n\n Opbarsten: {cut_off_float(aq_1['w_uplift'])} \n\n"
        description += f"### Aquifer 2 \n\n Opbarsten: {cut_off_float(aq_2['w_uplift'])}"
    elif calculation_type == "heave":
        description = f"## {exit_point.name} \n\n ### Aquifer 1 \n\n Heave: {cut_off_float(aq_1['w_heave'])} \n\n"
        description += f"### Aquifer 2 \n\n Heave: {cut_off_float(aq_2['w_heave'])}"
    elif calculation_type == "sellmeijer":
        description = (
            f"## {exit_point.name} \n\n ### Aquifer 1 \n\n Sellmeijer {cut_off_float(aq_1['w_sellmeijer'])} \n\n"
        )
        description += f"### Aquifer 2 \n\n Sellmeijer {cut_off_float(aq_2['w_sellmeijer'])}"
    else:
        raise ValueError
    return description


def make_marker_single_aquifer(
    final_aq_1: DataFrame, exit_point_mapping: dict, calculation_type: Optional[str] = None
) -> Tuple[List[MapFeature], List[MapLabel]]:
    map_features, map_labels = [], []
    for key, aq_1 in common_entries(final_aq_1):
        exit_point = exit_point_mapping[key]
        coordinates = (
            exit_point.last_saved_params.exit_point_data.x_coordinate,
            exit_point.last_saved_params.exit_point_data.y_coordinate,
        )
        uc_list = list(aq_1.values())

        map_features.append(
            MapPoint.from_geo_point(
                GeoPoint.from_rd(coordinates),
                color=get_unity_check_color(uc_list),
                description=get_marker_description_single_aquifer(exit_point, aq_1, calculation_type),
                entity_links=[MapEntityLink("Na Uitredepunt", entity_id=exit_point.id)],
            )
        )
        lat, lon = RDWGSConverter.from_rd_to_wgs(coordinates)
        map_labels.append(MapLabel(lat, lon, scale=17, text=f"{exit_point.name[13:]}"))
    return (
        map_features,
        map_labels,
    )


def get_marker_description_single_aquifer(exit_point: Entity, aq_1: DataFrame, calculation_type: Optional[str]) -> str:
    if calculation_type is None:
        description = f"## {exit_point.name} \n\n ### Aquifer 1 \n\n Opbarsten: {cut_off_float(aq_1['w_uplift'])} \\\n  Heave: {cut_off_float(aq_1['w_heave'])} \\\n Sellmeijer {cut_off_float(aq_1['w_sellmeijer'])} \n\n"
    elif calculation_type == "uplift":
        description = f"## {exit_point.name} \n\n ### Aquifer 1 \n\n Opbarsten: {cut_off_float(aq_1['w_uplift'])}"

    elif calculation_type == "heave":
        description = f"## {exit_point.name} \n\n ### Aquifer 1 \n\n Heave: {cut_off_float(aq_1['w_heave'])}"

    elif calculation_type == "sellmeijer":
        description = (
            f"## {exit_point.name} \n\n ### Aquifer 1 \n\n Sellmeijer {cut_off_float(aq_1['w_sellmeijer'])} \n\n"
        )

    else:
        raise ValueError
    return description


def common_entries(*dcts):
    """Make it easy to zip multiple dictionaries"""
    if not dcts:
        return
    for i in set(dcts[0]).intersection(*dcts[1:]):
        yield (i,) + tuple(d[i] for d in dcts)


def cut_off_float(value: Union[float, str]):
    if isinstance(value, float):
        return round(value, 2)
    elif isinstance(value, str):
        return value
    raise TypeError
