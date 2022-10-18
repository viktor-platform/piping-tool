from io import BytesIO
from typing import Tuple

import rasterio
from munch import Munch
from plotly import graph_objects as go
from shapely.geometry import LineString
from shapely.geometry import MultiPoint

from app.ground_model.tno_model import TNOGroundModel
from app.ground_model.tno_model import get_longitudinal_soil_layout
from app.ground_model.tno_model import get_min_max_permeabilities_from_soil_layout
from app.lib.helper_read_files import shape_file_to_geo_poly_line
from app.lib.plotly_2d_profile_helper_functions import get_visualisation_along_trajectory
from app.lib.regis.regis_helper import get_longitudinal_regis_soil_layouts
from app.lib.shapely_helper_functions import convert_geo_polyline_to_linestring
from app.lib.shapely_helper_functions import find_perpendicular_direction
from app.lib.shapely_helper_functions import get_objects_in_polygon
from viktor import UserException
from viktor.geometry import GeoPolyline

LINE_SCALE = 0.2


class Dyke:
    def __init__(self, params: Munch, tno_groundmodel: TNOGroundModel = None) -> None:
        self.params: Munch = params
        self.tno_ground_model = tno_groundmodel

    def interpolated_trajectory(self, for_2d_layout: bool = False) -> LineString:
        """Returns the segmented trajectory, that is to say a LineString cut into portions of equal length based on
        the chainage resolution.
        This trajectory differs from the base trajectory of the dike that is uploaded (or manually modified) for the
        dike, but the two are very similar. This is not so much of a problem as long as the chainage resolution is small
        enough (25m in practice), which is acceptable.
        """
        base_trajectory = self.get_base_trajectory(for_2d_layout=for_2d_layout)
        nb_points = int(base_trajectory.length / self.params.chainage_step)

        # The last point of the base trajectory is added because it is not interpolated
        interpolated_trajectory = LineString(
            [base_trajectory.interpolate(n * self.params.chainage_step) for n in range(nb_points)]
            + [base_trajectory.coords[-1]]
        )
        return interpolated_trajectory

    @property
    def entry_line(self) -> LineString:
        return convert_geo_polyline_to_linestring(shape_file_to_geo_poly_line(self.params.entry_line.file))

    @property
    def bathymetry_points(self) -> MultiPoint:
        """Open the raster file uploaded in the application at the dike entity level and return a MultiPoint for all the
        point having real bathymetry data."""
        file = self.params.geometry.data_selection.bathymetry_file

        if file is None:
            return MultiPoint([])
        list_points = []
        with rasterio.open(BytesIO(file.file.getvalue_binary())) as src:
            band = src.read()[0]
            bounds = src.bounds

            nb_lines, nb_columns = src.shape
            horizontal_spacing = (bounds.right - bounds.left) / nb_columns
            vertical_spacing = (bounds.top - bounds.bottom) / nb_lines

            for i in range(nb_lines):
                for j in range(nb_columns):
                    pixel = band[i, j]
                    # Points without real bathymetry data are set to 1000000 by default, they are filtered below
                    if pixel < 100:
                        list_points.append(
                            (bounds.left + horizontal_spacing * j, bounds.top - i * vertical_spacing, pixel)
                        )
        return MultiPoint(list_points)

    def get_base_trajectory(self, for_2d_layout: bool = None) -> LineString:
        """Extract the base trajectory from the params. Also creates the trajectory used for 2D soil layout
        visualisation based on (default) the crest-line or any other user-entered line. Possibly with offset
        :param for_2d_layout:
        """
        offset = self.params.soil_profile.line_offset if for_2d_layout else 0
        if self.params.soil_profile.select_base_line_for_2D_view == "crest_line" or not for_2d_layout:
            line = self.params.dyke_geo_coordinates
        elif self.params.soil_profile.select_base_line_for_2D_view == "uploaded_line":
            try:
                line = shape_file_to_geo_poly_line(self.params.line_for_2d_soil_layout.file)
            except AttributeError:
                raise UserException("Upload een geldige lijn optie")
        elif self.params.soil_profile.select_base_line_for_2D_view == "custom_line":
            line = self.params.soil_profile.custom_geopolyline
            offset = 0
        else:
            raise UserException(
                "No baseline has been found for the trajectory of the view 2D Grondopbouw"
            )  # TODO TRANSLATE

        if self.params.geometry.dyke.reverse_direction_chainage:
            trajectory = convert_geo_polyline_to_linestring(GeoPolyline(*reversed(line.points)), offset)
        else:
            trajectory = convert_geo_polyline_to_linestring(line, offset)

        return trajectory

    def perpendicular_to_river(self, i: int = 0) -> Tuple[float, float]:
        """Find a point p such that the line (p, Linestring[i])
        - is perpendicular to the dyke trajectory at point i,
        - points towards the riverbed based on user input"""
        return find_perpendicular_direction(
            self.interpolated_trajectory(for_2d_layout=True), i, clockwise=self.direction_to_river
        )

    @property
    def ground_model_entity_id(self):
        return self.params.geometry.data_selection.ground_model

    @property
    def direction_to_river(self):
        return self.params.geometry.dyke.clockwise_direction_to_water

    @property
    def geopolyline_trajectory(self):
        return self.params.dyke_geo_coordinates

    def get_visualisation_along_trajectory(self) -> go.Figure:
        """
        Get a 2d lithological profile.
        """
        interpolated_trajectory = self.interpolated_trajectory(for_2d_layout=True)
        segment_array = self.params.segment_generation.segment_array
        buffer_polygon = interpolated_trajectory.buffer(self.params.buffer_zone_cpts_bore)
        if self.params.cpt_folder:
            try:
                cpt_entity_list = self.params.cpt_folder.children(entity_type_names=["CPT"])
                cpt_entity_list = get_objects_in_polygon(cpt_entity_list, buffer_polygon)
                cpt_params = dict(
                    cpt_entity_list=cpt_entity_list,
                    scale_measurement_cpt_qc=self.params.scale_measurement_cpt_qc * LINE_SCALE,
                    scale_measurement_cpt_rf=self.params.scale_measurement_cpt_rf * LINE_SCALE,
                    scale_measurement_cpt_u2=self.params.scale_measurement_cpt_u2 * LINE_SCALE,
                )
            except:
                raise UserException("Te veel CPTs")
        else:
            cpt_params = None
        if self.params.bore_folder:
            try:
                bore_entity_list = self.params.bore_folder.children(entity_type_names=["Bore"])
                bore_entity_list = get_objects_in_polygon(bore_entity_list, buffer_polygon)
            except:
                raise UserException("Te veel boringen")
        else:
            bore_entity_list = None
        classification_table = self.params.models.materials.classification_table
        materials_table = self.params.models.materials.table

        longitudinal_soil_layouts = get_longitudinal_soil_layout(
            interpolated_trajectory, tno_ground_model=self.tno_ground_model
        )
        min_perm_v, max_perm_v, min_perm_h, max_perm_h = get_min_max_permeabilities_from_soil_layout(
            longitudinal_soil_layouts
        )
        regis_soil_layouts = get_longitudinal_regis_soil_layouts(
            buffer_polygon, interpolated_trajectory, self.params.soil_profile.bottom_level_query
        )

        min_max_permeabilities = dict(
            min_perm_v=min_perm_v, max_perm_v=max_perm_v, min_perm_h=min_perm_h, max_perm_h=max_perm_h
        )
        return get_visualisation_along_trajectory(
            interpolated_trajectory,
            longitudinal_soil_layouts,
            classification_table,
            materials_table,
            self.params.chainage_step,
            min_max_permeabilities,
            segment_array,
            cpt_params=cpt_params,
            bore_entity_list=bore_entity_list,
            regis_layouts=regis_soil_layouts,
        )
