from typing import List
from typing import Tuple
from typing import Union

from munch import Munch
from munch import unmunchify
from shapely.geometry import LineString
from shapely.geometry import MultiPoint
from shapely.geometry import Point
from shapely.geometry import Polygon

from viktor import File
from viktor import UserException
from viktor.geo import SoilLayout

from ..lib.ahn.ahn_helper_functions import get_xyz_df_from_multipoints
from ..piping_tool.PipingCalculationUtilities import calculate_leakage_length
from ..segment.param_parser_functions import get_materials_tables
from ..segment.param_parser_functions import get_representative_soil_layouts
from ..segment.param_parser_functions import get_soil_scenario
from .model import classify_tno_soil_model
from .model import get_filtered_tno_data
from .model import get_filtered_tno_data_serialized
from .model import get_leakage_length_properties


class TNOGroundModel:
    def __init__(self, params: Munch, file: Union[File, str]) -> None:
        self.params: Munch = params
        self.file = file

    @property
    def file_content(self):
        if isinstance(self.file, str):  # in case class is memoized, file content is a string
            return self.file
        return self.file.getvalue(encoding="utf-8")

    def get_soil_layouts(
        self, points: Union[MultiPoint, LineString, Point], memoize: bool = False
    ) -> Union[List[SoilLayout], SoilLayout]:
        """
        Returns a list of SoilLayout or a single SoilLayout depending on the number (or type) of provided points
        """
        if memoize:
            if isinstance(points, MultiPoint):
                points = list(points.geoms)
            elif isinstance(points, (LineString, Point)):
                points = list(points.coords)
            return [
                SoilLayout.from_dict(sl)
                for sl in get_filtered_tno_data_serialized(self.file_content, points, unmunchify(self.params))
            ]
        if isinstance(points, Point):
            return get_filtered_tno_data(self.file_content, points, self.params)[0]
        return get_filtered_tno_data(self.file_content, points, self.params)

    def get_zipped_point_coordinates_and_layout(self, multi_points: MultiPoint) -> zip:
        # Filter TNO point to optimize memory usage
        tno_soil_layout_list = get_filtered_tno_data(self.file_content, multi_points, self.params)

        df_points = get_xyz_df_from_multipoints(multi_points)
        return zip(tno_soil_layout_list, df_points["x"], df_points["y"], df_points["z"])

    def get_leakage_length_properties(
        self, segment_params: Munch, region: Polygon, for_second_aquifer: bool
    ) -> List[dict]:
        """
        Calculate for a given region, the leakage length for each voxel in that region.
        :param segment_params: Parametrization of the segment entity
        :param region: Shapely Polygon for which the leakage length is calculated per voxel.
        :param for_second_aquifer: False if the leakage properties should be calculated for the first aquifer, True for the
        second aquifer
        :return: Return location and leakage length of all voxels in region with teh following format:
        [{'x': 0, 'y': 0, 'll': 123}]
        """
        materials_tables = get_materials_tables(segment_params)

        # clip the TNO points to the region
        clipped_tno_points = region.intersection(MultiPoint(self.params.data))

        # Loop over each leakage point
        leakage_point_properties = []
        for tno_soil_layout, x, y, _ in self.get_zipped_point_coordinates_and_layout(clipped_tno_points):

            # Select which layout should be used to derived leakage length properties: tno layout or classified
            if segment_params.soil_schematization.leakage_length_map.visible_param == "from_material_table":
                layout_for_leakage_length = classify_tno_soil_model(
                    tno_soil_layout,
                    materials_tables.get("classification_table"),
                    materials_tables.get("table"),
                    minimal_aquifer_thickness=segment_params.minimal_aquifer_thickness,
                )
            else:
                layout_for_leakage_length = tno_soil_layout

            try:
                if segment_params.soil_schematization.leakage_length_map.scenario is None:
                    raise UserException("Selecteer een scenario voor de Leklengte Kaart")

                scenario = get_soil_scenario(
                    scenario_name=segment_params.soil_schematization.leakage_length_map.scenario,
                    soil_scenario_array=segment_params.input_selection.soil_schematization.soil_scen_array,
                )
                _, rep_soil_layout = get_representative_soil_layouts(segment_params, scenario=scenario)

                (
                    cover_layer_thickness,
                    k_cover_layer,
                    first_aquifer_thickness,
                    k_first_aquifer_layer,
                ) = get_leakage_length_properties(
                    layout_for_leakage_length,
                    rep_soil_layout,
                    from_representative_layout=segment_params.use_representative_layout,
                    for_second_aquifer=for_second_aquifer,
                )
                # Calculate the leakage length
                leakage_length_hinterland = calculate_leakage_length(
                    cover_layer_thickness, k_cover_layer, first_aquifer_thickness, k_first_aquifer_layer
                )
                leakage_point_properties.append(
                    {
                        "x": x,
                        "y": y,
                        "ll": leakage_length_hinterland,
                        "cover_layer_d": cover_layer_thickness,
                        "cover_layer_k": k_cover_layer,
                        "first_aquifer_d": first_aquifer_thickness,
                        "first_aquifer_k": k_first_aquifer_layer,
                    }
                )
            except AttributeError:
                leakage_point_properties.append(
                    {
                        "x": x,
                        "y": y,
                        "ll": None,
                        "cover_layer_d": None,
                        "cover_layer_k": None,
                        "first_aquifer_d": None,
                        "first_aquifer_k": None,
                    }
                )

        return leakage_point_properties

    def get_fore_and_hinterland_leakage_length_properties(
        self, segment_params: Munch, foreland: Polygon, hinterland: Polygon, for_second_aquifer: bool
    ) -> dict:
        """Get a dict with
            - all:  list of leakage points in fore and hinterland sorted based on RD coordinates
            - foreland: list of leakage points foreland sorted based on local coordinates
            - hinterland: list of leakage points hinterland sorted based on local coordinates
            :param for_second_aquifer: False if the leakage properties should be calculated for the first aquifer, True for the
        second aquifer
        """
        leakage_point_foreland_properties = self.get_leakage_length_properties(
            segment_params, region=foreland, for_second_aquifer=for_second_aquifer
        )
        leakage_point_hinterland_properties = self.get_leakage_length_properties(
            segment_params, region=hinterland, for_second_aquifer=for_second_aquifer
        )

        # add all points together and sort them so the numbering makes sense
        leakage_points = leakage_point_hinterland_properties + leakage_point_foreland_properties
        leakage_points = sorted(leakage_points, key=lambda x: x["x"])
        leakage_points = sorted(leakage_points, key=lambda x: x["y"], reverse=True)
        return {
            "all": leakage_points,
            "foreland": leakage_point_foreland_properties,
            "hinterland": leakage_point_hinterland_properties,
        }


def agglomerate_tno_layers(soil_layout: SoilLayout) -> SoilLayout:
    """Agglomerate consecutive tno layers if they share the name soil name/ soil type"""
    base_soil_layers = []
    previous_soil_type = ""
    for tno_layer in soil_layout.layers:  # Loop over all the rows of the "moTNO profile
        soil_type = tno_layer.soil.name

        # Skip this voxel to agglomerate it with the previous one if they both share the same soil type
        if soil_type == previous_soil_type:
            continue

        # Extend the bottom of the last non-agglomerated layer to the right level
        if previous_soil_type != "":
            base_soil_layers[-1].bottom_of_layer = tno_layer.top_of_layer
        base_soil_layers.append(tno_layer)
        previous_soil_type = soil_type

    # ensure that the bottom of the layout is passed when last layer is aggregated with previous ones
    base_soil_layers[-1].bottom_of_layer = soil_layout.layers[-1].bottom_of_layer
    return SoilLayout(base_soil_layers)


def get_tno_soil_layout_at_distance(
    distance_from_start: int, trajectory: LineString, tno_ground_model: TNOGroundModel
) -> SoilLayout:
    """Returns tno soil layout at location equal or larger than distance_from_start
    :params distance_from_start: Distance from the first point of the trajectory for which the soil layout is
     returned
    """
    return tno_ground_model.get_soil_layouts(trajectory.interpolate(distance_from_start))


def get_longitudinal_soil_layout(trajectory: LineString, tno_ground_model: TNOGroundModel) -> List[SoilLayout]:
    if not tno_ground_model:
        raise ValueError("longitudinal_soil_layout can not be accessed if no TNOGroundModel is provided")
    return tno_ground_model.get_soil_layouts(trajectory, memoize=True)


def get_min_max_permeabilities_from_soil_layout(
    longitudinal_soil_layout: List[SoilLayout],
) -> Tuple[float, float, float, float]:
    """Returns a list with the minimum and maximum values of the vertical and horizontal permeability from a soillayout"""

    min_perm_v = min(
        [
            min([layer.properties.vertical_permeability for layer in soil_layout.layers])
            for soil_layout in longitudinal_soil_layout
        ]
    )

    max_perm_v = max(
        [
            max([layer.properties.vertical_permeability for layer in soil_layout.layers])
            for soil_layout in longitudinal_soil_layout
        ]
    )

    min_perm_h = min(
        [
            min([layer.properties.horizontal_permeability for layer in soil_layout.layers])
            for soil_layout in longitudinal_soil_layout
        ]
    )

    max_perm_h = max(
        [
            max([layer.properties.horizontal_permeability for layer in soil_layout.layers])
            for soil_layout in longitudinal_soil_layout
        ]
    )

    return min_perm_v, max_perm_v, min_perm_h, max_perm_h
