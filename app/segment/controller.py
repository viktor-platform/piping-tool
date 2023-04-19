from copy import deepcopy
from io import BytesIO
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import geopandas as gpd
from munch import Munch
from munch import munchify
from munch import unmunchify
from numpy import mean
from shapely.geometry import LineString
from shapely.geometry import MultiLineString
from shapely.geometry import Point
from shapely.geometry import Polygon

from app.lib.constants import DRY_DITCH_COLOR
from app.lib.constants import EXISTING_EXIT_POINT_COLOR
from app.lib.constants import FUTURE_EXIT_POINT_COLOR
from app.lib.constants import LEGEND_LIST_EXIT_POINT_CREATION
from app.lib.constants import LOWEST_POINT_COLOR
from app.lib.constants import WET_DITCH_COLOR
from app.lib.shapely_helper_functions import check_if_point_in_polygons
from app.lib.shapely_helper_functions import convert_linestring_to_geo_polyline
from app.lib.shapely_helper_functions import get_all_exit_point_entities_within_polygon
from app.lib.shapely_helper_functions import intersect_soil_layout_table_with_z
from viktor import Color
from viktor import File
from viktor import UserException
from viktor import ViktorController
from viktor.core import progress_message
from viktor.geometry import GeoPoint
from viktor.result import DownloadResult
from viktor.result import SetParamsResult
from viktor.views import DataGroup
from viktor.views import DataItem
from viktor.views import InteractionEvent
from viktor.views import MapAndDataResult
from viktor.views import MapAndDataView
from viktor.views import MapFeature
from viktor.views import MapLabel
from viktor.views import MapLegend
from viktor.views import MapPoint
from viktor.views import MapPolygon
from viktor.views import MapResult
from viktor.views import MapView
from viktor.views import PlotlyResult
from viktor.views import PlotlyView

from ..cpt.constants import CLASSIFICATION_PARAMS
from ..cpt.model import CPT
from ..cpt.soil_layout_conversion_functions import Classification
from ..ditch.utils import AHNEmptyDfError
from ..ditch.utils import DitchPolygonIntersectionError
from ..ditch.utils import get_ditch_points_data
from ..ground_model.model import check_validity_of_classification_table
from ..ground_model.model import classify_tno_soil_model
from ..ground_model.model import convert_input_table_to_soil_layout
from ..ground_model.model import convert_soil_layout_to_input_table
from ..ground_model.model import get_aquifer_effective_properties
from ..ground_model.model import get_soil_layer_from_soil_type
from ..ground_model.tno_model import get_tno_soil_layout_at_distance
from ..lib.helper_read_files import entry_line_to_params
from ..lib.map_view_helper_functions import add_all_leakage_points_to_map_features
from ..lib.map_view_helper_functions import add_cpts_to_mapfeatures
from ..lib.map_view_helper_functions import add_dike_trajectory_and_entry_line_to_map_features
from ..lib.map_view_helper_functions import add_ditches_to_map_features
from ..lib.map_view_helper_functions import add_existing_exit_point_to_map_features
from ..lib.map_view_helper_functions import add_foreland_polygon_to_map_features
from ..lib.map_view_helper_functions import add_ground_model_hull_to_map_features
from ..lib.map_view_helper_functions import add_hinterland_polygon_to_map_features
from ..lib.map_view_helper_functions import add_intersected_segment_ditches_to_map_features
from ..lib.map_view_helper_functions import add_segment_trajectory_to_map_features
from ..lib.shapely_helper_functions import convert_shapely_polgon_to_geopolygon
from ..lib.shapely_helper_functions import create_polygon_from_linestring_offset
from ..segment.parametrization import SegmentParametrization
from ..segment.segmentAPI import SegmentAPI
from .constants import PIPING_LEGEND
from .constants import SPATIAL_RESOLUTION_SEGMENT_CHAINAGE
from .output_excel_builder import PipingExcelBuilder
from .param_parser_functions import Scenario
from .param_parser_functions import get_materials_tables
from .param_parser_functions import get_representative_soil_layouts
from .param_parser_functions import get_selected_exit_point_params
from .param_parser_functions import get_soil_scenario
from .segment_model import Segment
from .segment_visualization_functions import visualize_exit_point_soil_layouts
from .segment_visualization_functions import visualize_leakage_point_layouts
from .segment_visualization_functions import visualize_representative_layouts


class Controller(ViktorController):  # pylint: disable=too-many-public-methods
    """
    Controller to show embankment designs
    """

    label = "Dijkvak"
    children = ["ExitPoint"]
    show_children_as = "Table"
    parametrization = SegmentParametrization

    def __init__(self, *args, api: SegmentAPI = None, **kwargs):
        """Intializes controller class.

        :api: API to be used for querying. Default is none. This is done for mocking purposes.
        """
        self._api = api
        super().__init__(*args, **kwargs, perform_string_to_number_conversion=False)

    def get_api(self, entity_id):
        """Lazy loaded API entity."""
        self._api = self._api or SegmentAPI(entity_id)

        return self._api

    ####################################################################################################################
    #                                                   STEP 1                                                         #
    ####################################################################################################################

    @MapView("Inputoverzicht", duration_guess=2)
    def map_ditch_selection(self, params: Munch, entity_id: int, **kwargs):
        """
        MapView of the first step to visualise the selected input data of the segment: dike crest line, entry line
        and ditches.
        """
        map_features, map_labels = [], []
        this_segment = self.get_segment(entity_id, params)
        dyke = self.get_api(entity_id).get_dyke()
        tno_ground_model = self.get_api(entity_id).get_tno_ground_model()

        if params.input_selection.general.show_cpts:
            add_cpts_to_mapfeatures(map_features, self.get_api(entity_id).all_cpts, map_labels)

        if params.input_selection.general.show_ground_model:
            add_ground_model_hull_to_map_features(map_features, ground_model_hull=tno_ground_model.params.convex_hull)

        if params.input_selection.general.show_entry_exit_lines:
            add_dike_trajectory_and_entry_line_to_map_features(
                map_features,
                dike_trajectory=convert_linestring_to_geo_polyline(dyke.interpolated_trajectory()),
                entry_line=entry_line_to_params(dyke.params.entry_line),
            )
        if params.segment_polygon:
            add_segment_trajectory_to_map_features(
                map_features, convert_linestring_to_geo_polyline(this_segment.trajectory)
            )

        if params.input_selection.general.show_selected_ditches:
            add_intersected_segment_ditches_to_map_features(map_features, segment_params=params)
        else:
            ditch_features = self.get_api(entity_id).get_ditches()
            if ditch_features:
                add_ditches_to_map_features(map_features, ditch_features)

        if params.select_with_buffer_zone:
            buffer_pol = this_segment.create_ditches_hull(params.buffer_zone)
            polygon, holes = convert_shapely_polgon_to_geopolygon(buffer_pol)
            map_features.append(
                MapPolygon.from_geo_polygon(polygon, holes=holes, color=Color.black()),
            )

        legend = MapLegend(
            [(WET_DITCH_COLOR, "Natte sloot"), (DRY_DITCH_COLOR, "Droge sloot"), (Color.blue(), "Segment")]
        )

        return MapResult(map_features, map_labels, legend=legend)

    @PlotlyView("2D bodemopbouw", duration_guess=5)
    def visualize_ground_model_along_segment(self, params: Munch, entity_id: int, **kwargs) -> PlotlyResult:
        """Visualise 2D soil layout along the trajectory of the segment."""
        api = self.get_api(entity_id)
        segment = self.get_segment(entity_id, params)
        tno_ground_model = api.get_tno_ground_model()
        cpt_folder = api.get_cpt_folder_from_parent()
        bore_folder = api.get_borehole_folder_from_parent()
        fig = segment.get_segment_2D_longitudinal_profile(
            tno_ground_model,
            cpt_folder=cpt_folder,
            bore_folder=bore_folder,
            chainage_step=SPATIAL_RESOLUTION_SEGMENT_CHAINAGE,
        )
        return PlotlyResult(fig.to_dict())

    @PlotlyView("Dijkvak", duration_guess=4)
    def visualize_representative_layout(self, params: Munch, entity_id: int, **kwargs):
        """Visualise the representative layouts (Dijkvaken) for the selected scenario"""
        if params.input_selection.soil_schematization.scenario_to_visualise is None:
            raise UserException("Selecteer een scenario in 'Ondergrondschematisatie'.")
        scenario = get_soil_scenario(
            scenario_name=params.input_selection.soil_schematization.scenario_to_visualise,
            soil_scenario_array=params.input_selection.soil_schematization.soil_scen_array,
        )

        detailed_1d_soil_layout, rep_soil_layout = get_representative_soil_layouts(params, scenario)
        return PlotlyResult(
            visualize_representative_layouts(
                detailed_soil_layout=detailed_1d_soil_layout,
                simplified_soil_layout=rep_soil_layout,
                segment_params=params,
            )
        )

    def adjust_segment_polygon_by_chainage(self, params: Munch, entity_id: int, **kwargs) -> SetParamsResult:
        """
        Creates a new segment polygon based on the start and end chainage values
        """
        dyke = self.get_api(entity_id).get_dyke()
        trajectory_points = [Point(coord) for coord in dyke.interpolated_trajectory().coords]
        segment_geopolygon = convert_shapely_polgon_to_geopolygon(
            create_polygon_from_linestring_offset(trajectory_points, params.start_chainage, params.end_chainage)
        )[0]
        return SetParamsResult({"segment_polygon": segment_geopolygon})

    def fetch_table_from_dike(self, params: Munch, entity_id: int, **kwargs) -> SetParamsResult:
        """
        Fetch the default material and classification tables from the parent dike entity and set it the params
         of the segment.
        """
        dike_params = self.get_api(entity_id).get_dyke().params
        return SetParamsResult(
            {
                "input_selection": {
                    "materials": {
                        "table": dike_params.models.materials.table,
                        "classification_table": dike_params.models.materials.classification_table,
                    }
                }
            }
        )

    def fetch_soil_layout_at_location(self, params: Munch, entity_id: int, **kwargs) -> SetParamsResult:
        """
        Fetch the classified SoilLayout at a distance along the segment trajectory set by the user, and fill the soil
        layout table accordingly.
        """
        api = self.get_api(entity_id)
        segment = self.get_segment(entity_id, params)
        tno_ground_model = api.get_tno_ground_model()
        if not params.input_selection.soil_schematization.distance_from_start:
            raise UserException("Vul de meetpunt locatie")

        classified_layout = classify_tno_soil_model(
            get_tno_soil_layout_at_distance(
                params.input_selection.soil_schematization.distance_from_start,
                segment.interpolated_trajectory,
                tno_ground_model,
            ),
            params.input_selection.materials.classification_table,
            params.input_selection.materials.table,
            minimal_aquifer_thickness=params.minimal_aquifer_thickness,
        )
        bottom_soil_layout = classified_layout.layers[-1].bottom_of_layer

        soil_scen_array_content = unmunchify(params.input_selection.soil_schematization.soil_scen_array)
        soil_scen_array_content.insert(
            0,
            {
                "name_of_scenario": f"Scenario {len(params.input_selection.soil_schematization.soil_scen_array) + 1}",
                "bottom_of_soil_layout": bottom_soil_layout,
                "soil_layout_table": convert_soil_layout_to_input_table(classified_layout),
            },
        )

        return SetParamsResult(
            {"input_selection": {"soil_schematization": {"soil_scen_array": soil_scen_array_content}}}
        )

    def calculate_effective_aquifer_properties(self, params: Munch, entity_id: int, **kwargs) -> SetParamsResult:
        """Calculate the effective properties (permeability and d70) of the aquifers based on the user soil layout
        table from the parametrization, and fill the appropriate NumberFields with these properties"""
        if len(params.input_selection.soil_schematization.soil_scen_array) > 3:
            raise UserException("Niet meer dan 3 scenarios zijn toegestaan")

        aquifer_prop_array_content = []
        for row in params.input_selection.soil_schematization.soil_scen_array:
            detailed_1d_soil_layout = convert_input_table_to_soil_layout(
                bottom_of_soil_layout_user=row.bottom_of_soil_layout,
                soil_layers_from_table_input=row.soil_layout_table,
                material_table=params.input_selection.materials.table,
            )
            aquifers_prop = get_aquifer_effective_properties(detailed_1d_soil_layout)
            aquifer_prop_array_content.append(
                {
                    # First keep the relevant infor
                    "name_of_scenario": row.name_of_scenario,
                    "weight_of_scenario": row.weight_of_scenario,
                    "bottom_of_soil_layout": row.bottom_of_soil_layout,
                    "soil_layout_table": row.soil_layout_table,
                    # Add aquifer properties to DynamicArray
                    "first_aquifer_permeability": aquifers_prop.get("first_aquifer").get("permeability"),
                    "first_aquifer_d70": aquifers_prop.get("first_aquifer").get("d70"),
                    "second_aquifer_activate": aquifers_prop.get("second_aquifer").get("is_second_aquifer"),
                    "second_aquifer_permeability": aquifers_prop.get("second_aquifer").get("permeability"),
                    "second_aquifer_d70": aquifers_prop.get("second_aquifer").get("d70"),
                }
            )

        return SetParamsResult(
            {"input_selection": {"soil_schematization": {"soil_scen_array": aquifer_prop_array_content}}}
        )

    def intersect_ditches_with_buffer_zone(self, params: Munch, entity_id: int, **kwargs) -> SetParamsResult:
        """Return and save the portions of the ditches located inside the buffer zone behind the dike."""
        this_segment = self.get_segment(entity_id, params)
        ditch_data = self.get_api(entity_id).get_ditches()

        buffer_poly = this_segment.create_ditches_hull(params.buffer_zone)
        ditches_gdf = gpd.GeoDataFrame(ditch_data["ditches"])
        dry_ditches_gdf = gpd.GeoDataFrame(ditch_data["dry_ditches"])

        intersection_ditches = self.intersect_gdf_with_polygon(ditches_gdf, buffer_poly)

        intersection_dry_ditches = self.intersect_gdf_with_polygon(dry_ditches_gdf, buffer_poly)
        return SetParamsResult(
            {
                "segment_ditches": intersection_ditches,
                "segment_dry_ditches": intersection_dry_ditches,
                "input_selection": {"general": {"show_selected_ditches": True}},
            }
        )

    ####################################################################################################################
    #                                                   STEP 2                                                         #
    ####################################################################################################################

    @MapAndDataView("Leklengte Kaart (1e aquifer)", duration_guess=10)
    def map_leakage_length_1(self, params: Munch, entity_id: int, **kwargs) -> MapAndDataResult:
        """Visualize the MapView displaying the leakage length ob both the hinterland and foreland at the GEOTOP voxel
        location, for the first aquifer"""
        return self.get_leakage_length_MapResult(params, entity_id, second_aquifer=False)

    @MapAndDataView("Leklengte Kaart (2e aquifer)", duration_guess=10)
    def map_leakage_length_2(self, params: Munch, entity_id: int, **kwargs) -> MapAndDataResult:
        """Visualize the MapView displaying the leakage length ob both the hinterland and foreland at the GEOTOP voxel
        location, for the second aquifer"""
        return self.get_leakage_length_MapResult(params, entity_id, second_aquifer=True)

    def get_leakage_length_MapResult(self, params: Munch, entity_id: int, second_aquifer: bool):
        map_features, map_labels = [], []

        # get models and files from API
        segment_api = self.get_api(entity_id)
        this_segment = self.get_segment(entity_id, params)
        dyke = segment_api.get_dyke()
        tno_model = segment_api.get_tno_ground_model()

        # add crest, entry/exit lines, ditches ... as required
        if params.exit_point_creation.general.show_entry_exit_lines:
            add_dike_trajectory_and_entry_line_to_map_features(
                map_features,
                dike_trajectory=convert_linestring_to_geo_polyline(dyke.interpolated_trajectory()),
                entry_line=entry_line_to_params(dyke.params.entry_line),
            )
        if params.segment_polygon:
            add_segment_trajectory_to_map_features(
                map_features, convert_linestring_to_geo_polyline(this_segment.trajectory)
            )
        add_hinterland_polygon_to_map_features(
            map_features,
            segment=this_segment,
            length_hinterland=params.hinterland_length_schematization,
            buffer_length_hinterland=0,
        )
        add_foreland_polygon_to_map_features(
            map_features,
            segment=this_segment,
            length_foreland=params.foreland_length_schematization,
        )

        # get leakage length data
        poly_hinterland = this_segment.create_hinterland_hull(params.hinterland_length_schematization, 0)[0]
        poly_foreland = this_segment.create_foreland_hull(params.foreland_length_schematization, 0)
        leakage_points = tno_model.get_fore_and_hinterland_leakage_length_properties(
            params, poly_foreland, poly_hinterland, for_second_aquifer=second_aquifer
        )

        # add to map
        legend = add_all_leakage_points_to_map_features(map_features, map_labels, leakage_points["all"])
        return MapAndDataResult(
            features=map_features,
            labels=map_labels,
            legend=legend,
            data=self.make_data_group_leakage_point(leakage_points["foreland"], leakage_points["hinterland"]),
        )

    @PlotlyView("Gridpunt punt layout", duration_guess=10)
    def visualise_soil_leakage_point(self, params: Munch, entity_id: int, **kwargs):

        if not params.leakage_point_to_visualise:
            raise UserException("Selecteer een lek-punt id om te visualiseren")
        # get models
        segment_api = self.get_api(entity_id)
        this_segment = self.get_segment(entity_id, params)
        tno_model = segment_api.get_tno_ground_model()

        # find leakage point
        poly_hinterland = this_segment.create_hinterland_hull(params.hinterland_length_schematization, 0)[0]
        poly_foreland = this_segment.create_foreland_hull(params.foreland_length_schematization, 0)
        leakage_points = tno_model.get_fore_and_hinterland_leakage_length_properties(
            params, poly_foreland, poly_hinterland, for_second_aquifer=False
        )
        try:
            selected_point = leakage_points["all"][params.leakage_point_to_visualise]
        except IndexError:
            raise UserException(f"Geen lek-punt {params.leakage_point_to_visualise} gevonden")

        # find associated TNO soil layout and visualise
        soil_layout = tno_model.get_soil_layouts(Point((selected_point["x"], selected_point["y"])))
        material_tables = get_materials_tables(params)

        classified_soil_layout = classify_tno_soil_model(
            soil_layout,
            material_tables.get("classification_table"),
            material_tables.get("table"),
            params.minimal_aquifer_thickness,
        )
        if params.use_representative_layout:
            scenario = get_soil_scenario(
                scenario_name=params.soil_schematization.leakage_length_map.scenario,
                soil_scenario_array=params.input_selection.soil_schematization.soil_scen_array,
            )

            _, rep_soil_layout = get_representative_soil_layouts(params, scenario)
            return PlotlyResult(
                visualize_leakage_point_layouts(soil_layout, classified_soil_layout, params, rep_soil_layout)
            )

        return PlotlyResult(visualize_leakage_point_layouts(soil_layout, classified_soil_layout, params))

    @staticmethod
    def make_data_group_leakage_point(
        leakage_length_foreland_properties: List[dict], leakage_length_hinterland_properties: List[dict]
    ) -> DataGroup:
        """Fill the Datagroup to display the average leakage lengths of both hinterland and foreland."""
        data = DataGroup(
            DataItem(
                "gemiddeld leklengte achterland",
                mean([lp["ll"] for lp in leakage_length_hinterland_properties if lp["ll"] is not None]),
                number_of_decimals=0,
                suffix="m",
            ),
            DataItem(
                "gemiddeld leklengte voorland",
                mean([lp["ll"] for lp in leakage_length_foreland_properties if lp["ll"] is not None]),
                number_of_decimals=0,
                suffix="m",
            ),
        )
        return data

    ####################################################################################################################
    #                                                   STEP 3                                                         #
    ####################################################################################################################

    @MapView("Visualise Exit Points", duration_guess=4)
    def map_exit_point_creation(self, params: Munch, entity_id: int, **kwargs) -> MapResult:
        """Visualize the MapView with both the exit point to be generated and the already existing exit points."""
        map_features, map_labels, legend_list = [], [], LEGEND_LIST_EXIT_POINT_CREATION
        this_segment = self.get_segment(entity_id, params)
        dyke = self.get_api(entity_id).get_dyke()

        if params.exit_point_creation.general.show_cpts:
            add_cpts_to_mapfeatures(map_features, self.get_api(entity_id).all_cpts, map_labels)

        if params.exit_point_creation.general.show_entry_exit_lines:
            add_dike_trajectory_and_entry_line_to_map_features(
                map_features,
                dike_trajectory=convert_linestring_to_geo_polyline(dyke.interpolated_trajectory()),
                entry_line=entry_line_to_params(dyke.params.entry_line),
            )
        if params.segment_polygon:
            add_segment_trajectory_to_map_features(
                map_features, convert_linestring_to_geo_polyline(this_segment.trajectory)
            )

        if params.exit_point_creation.general.show_selected_ditches:
            add_intersected_segment_ditches_to_map_features(map_features, segment_params=params)
        else:
            ditch_features = self.get_api(entity_id).get_ditches()
            if ditch_features:
                add_ditches_to_map_features(map_features, ditch_features)
        if (
            params.segment_polygon
            and params.exit_point_creation.exit_point_tab.length_hinterland
            and params.exit_point_creation.exit_point_tab.buffer_length_hinterland
        ):
            add_hinterland_polygon_to_map_features(
                map_features,
                segment=this_segment,
                length_hinterland=params.exit_point_creation.exit_point_tab.length_hinterland,
                buffer_length_hinterland=params.exit_point_creation.exit_point_tab.buffer_length_hinterland,
            )

            # Add future exit points
            for point in this_segment.get_all_draft_exit_point_locations().geoms:
                map_features.append(
                    MapPoint.from_geo_point(GeoPoint.from_rd((point.x, point.y)), color=FUTURE_EXIT_POINT_COLOR)
                )

            # Add already saved exit points
            if params.exit_point_creation.general.show_existing_exit_points:
                exit_point_entities = self.get_api(entity_id).get_all_children_exit_point_entities()
                add_existing_exit_point_to_map_features(map_features, map_labels, exit_point_entities)

        if params.is_lowest_point:
            x, y, z = this_segment.find_lowest_point_hinterland()
            map_features.append(
                MapPoint.from_geo_point(
                    GeoPoint.from_rd((x, y)),
                    color=LOWEST_POINT_COLOR,
                    description=f"Laagste maaiveld in achterland \n\nMaaiveld: {z:.3f} m",
                )
            )
            legend_list.append((LOWEST_POINT_COLOR, "Laagste maaiveld"))

        return MapResult(map_features, map_labels, legend=MapLegend(legend_list))

    def create_exit_point_entities(self, params: Munch, entity_id: int, **kwargs) -> SetParamsResult:
        """Create a new entity for each exit point of the segment"""

        # Call API
        segment_api = self.get_api(entity_id)
        segment = self.get_segment(entity_id, params)
        tno_ground_model = segment_api.get_tno_ground_model()
        check_validity_of_classification_table(params.input_selection.materials.classification_table)

        # Get ditches data
        segment_ditches_pol, segment_dry_ditches_pol = segment.get_ditches_as_multipolygons

        # Get some data
        counter_exit_point = params.get("counter_exit_point_entities", 1) or 1
        exit_point_locations = segment.get_all_draft_exit_point_locations()
        materials_tables = get_materials_tables(params)

        if params.ditch_water_level is not None:
            ditch_water_level = params.ditch_water_level
        else:
            raise UserException("Waterstand voor slootbodem dient aangegeven te worden onder de Geohydrologie tab.")

        # Loop over each exit point
        for index, (tno_soil_layout, x, y, z) in enumerate(
            tno_ground_model.get_zipped_point_coordinates_and_layout(exit_point_locations), 1
        ):
            progress_message(f"Genereer Uittredepunt {index}/{len(exit_point_locations)} \n\n {x} {y}")

            # Classify the tno model
            classified_soil_layout = classify_tno_soil_model(
                tno_soil_layout,
                materials_tables.get("classification_table"),
                materials_tables.get("table"),
                minimal_aquifer_thickness=params.minimal_aquifer_thickness,
            )

            # Ditches
            new_entity_params = {}
            point = Point(x, y)
            # check if point falls into ditch polygons
            check_ditch_bool, type_ditch = check_if_point_in_polygons(
                segment_ditches_pol, segment_dry_ditches_pol, point
            )
            if check_ditch_bool is True:
                try:
                    if type_ditch == "wet":
                        ditch_points, talu_slope = get_ditch_points_data(
                            params.segment_ditches, point, ditch_water_level
                        )
                        ditch_param = {
                            "ditch_points": ditch_points,
                            "talu_slope": talu_slope,
                            "is_wet": True,
                        }
                    else:
                        ditch_points, talu_slope = get_ditch_points_data(
                            params.segment_dry_ditches, point, ditch_water_level
                        )
                        ditch_param = {
                            "ditch_points": ditch_points,
                            "talu_slope": talu_slope,
                            "is_wet": False,
                        }

                except (ConnectionError, AHNEmptyDfError):
                    progress_message(f"Uittredepunt {index} dropped: could not fetch AHN data")  # TODO TRANSLATE
                    continue
                except DitchPolygonIntersectionError:
                    progress_message(
                        f"Uittredepunt {index} dropped: ditch width could not be determined"
                    )  # TODO TRANSLATE

                new_entity_params.update(
                    {
                        "ditch_points": ditch_param["ditch_points"],
                        "is_wet": ditch_param["is_wet"],
                        "talu_slope": ditch_param["talu_slope"],
                    }
                )
                # update z with the top of the ditch
                z = min(ditch_param["ditch_points"][0]["z"], ditch_param["ditch_points"][-1]["z"])

            # Update the soil layout from the TNO conversion with the actual ground level from AHN or ditch bottom.
            intersected_soil_layout = intersect_soil_layout_table_with_z(classified_soil_layout, round(z, 3))

            new_entity_params.update(
                {
                    "exit_point_data": {"x_coordinate": x, "y_coordinate": y, "ground_level": z},
                    "tno_soil_layout": tno_soil_layout.serialize(),
                    "classified_soil_layout": intersected_soil_layout.serialize(),
                }
            )

            segment_api.create_exit_point_entity(
                new_entity_params=new_entity_params,
                new_entity_name=f"Uittredepunt {counter_exit_point}",
            )
            counter_exit_point += 1
        return SetParamsResult({"counter_exit_point_entities": counter_exit_point})

    ####################################################################################################################
    #                                                   STEP 4                                                         #
    ####################################################################################################################
    @MapView("Kaart", duration_guess=2)
    def map_calculations_overview(self, params: Munch, entity_id: int, **kwargs) -> MapResult:
        """Visualize the MapView of the saved exit point. This Map is used to select wich exit point to update"""
        map_features, map_labels, interaction_point_list = [], [], []
        this_segment = self.get_segment(entity_id, params)

        if params.segment_polygon:
            add_segment_trajectory_to_map_features(
                map_features, convert_linestring_to_geo_polyline(this_segment.trajectory)
            )
        add_intersected_segment_ditches_to_map_features(map_features, segment_params=params)

        # Add existing exit points
        if params.segment_polygon and params.exit_point_creation.general.show_existing_exit_points:
            exit_point_entities = self.get_api(entity_id).get_all_children_exit_point_entities()
            add_existing_exit_point_to_map_features(
                map_features, map_labels, exit_point_entities, interaction_point_list
            )

        # visualise CPTs
        add_cpts_to_mapfeatures(map_features, self.get_api(entity_id).all_cpts, map_labels)

        legend = MapLegend(
            [
                (EXISTING_EXIT_POINT_COLOR, "Opgeslagen uittredepunten"),
            ]
        )
        interaction_group = {"points": interaction_point_list}
        return MapResult(map_features, map_labels, legend=legend, interaction_groups=interaction_group)

    @PlotlyView("Bodemopbouw inspectie", duration_guess=10)
    def compare_soil_layouts(self, params: Munch, entity_id: int, **kwargs) -> PlotlyResult:
        """Return a Plotly plot to compare for a select exit point the following objects:
            - TNO default soil layout
            - Saved geotechnical soil layout
            - Pre-visualization of the soil layout user table.

        If selected, the cone resistance of a CPT can be displayed as well.
        """

        if params.calculations.soil_profile.results_settings.scenario_selection is None:
            raise UserException("Kies een scenario")

        scenario = get_soil_scenario(
            scenario_name=params.calculations.soil_profile.results_settings.scenario_selection,
            soil_scenario_array=params.input_selection.soil_schematization.soil_scen_array,
        )
        _, rep_soil_layout = get_representative_soil_layouts(params, scenario)

        if params.show_cpt:
            if not params.selected_cpt_id:
                raise UserException("Selecteer een CPT om te visualiseren")

            classification = Classification(munchify(CLASSIFICATION_PARAMS))
            soils = classification.soil_mapping
            cpt_entity = self.get_api(entity_id).get_cpt_entity(params.selected_cpt_id)
            gef = CPT(cpt_params=cpt_entity.last_saved_params, soils=soils, entity_id=params.selected_cpt_id)
            return PlotlyResult(
                visualize_exit_point_soil_layouts(
                    params,
                    get_selected_exit_point_params(params),
                    cpt=gef,
                    rep_soil_layout=rep_soil_layout,
                )
            )

        return PlotlyResult(
            visualize_exit_point_soil_layouts(
                params,
                get_selected_exit_point_params(params),
                cpt=None,
                rep_soil_layout=rep_soil_layout,
            )
        )

    @MapView("Piping berekening", duration_guess=15)
    def visualize_piping_results(self, params: Munch, entity_id: int, **kwargs) -> MapResult:
        map_features, map_labels = self.get_map_features_for_piping_results(entity_id, params)
        return MapResult(map_features, map_labels, PIPING_LEGEND)

    @MapView("Opbarsten", duration_guess=15)
    def visualize_uplift_results(self, params: Munch, entity_id: int, **kwargs) -> MapResult:
        map_features, map_labels = self.get_map_features_for_piping_results(
            entity_id, params, calculation_type="uplift"
        )
        return MapResult(map_features, map_labels, PIPING_LEGEND)

    @MapView("Heave", duration_guess=15)
    def visualize_heave_results(self, params: Munch, entity_id: int, **kwargs) -> MapResult:
        map_features, map_labels = self.get_map_features_for_piping_results(entity_id, params, calculation_type="heave")
        return MapResult(map_features, map_labels, PIPING_LEGEND)

    @MapView("Sellmeijer", duration_guess=15)
    def visualize_sellmeijer_results(self, params: Munch, entity_id: int, **kwargs) -> MapResult:
        map_features, map_labels = self.get_map_features_for_piping_results(
            entity_id, params, calculation_type="sellmeijer"
        )
        return MapResult(map_features, map_labels, PIPING_LEGEND)

    def apply_to_exit_point(self, params: Munch, entity_id: int, event: InteractionEvent, **kwargs):
        """Update the cover layer of all the selected exit points. Selection of exit points can be either interactive
        (event is not None) or from a drawn polygon on the MapView.
        """
        if event:  # Interactive selection of exit points
            selected_exit_point_entities = []
            api = self.get_api(entity_id)

            for exit_point_id in event.value:
                selected_exit_point_entities.append(api.get_entity(exit_point_id))

        else:  # Fetch all exit point entities within a polygon
            if not params.calculations.soil_profile.exit_point_modification.polygon_selection:
                raise UserException(
                    "Een polygon dient te worden getekend in de Kaart tab om de selectie van de uittredepunten te updaten"
                )

            exit_point_entities = self.get_api(entity_id).get_all_children_exit_point_entities()
            selected_exit_point_entities = get_all_exit_point_entities_within_polygon(
                exit_point_entities, params.calculations.soil_profile.exit_point_modification.polygon_selection
            )

        for exit_point in selected_exit_point_entities:
            exit_point_params = exit_point.last_saved_params
            saved_soil_layout = exit_point_params.classified_soil_layout

            exit_point_params.update(
                {
                    "classified_soil_layout": self.update_cover_layer_for_exit_point_layout(
                        saved_soil_layout,
                        top_cover=params.calculations.soil_profile.exit_point_modification.top_cover,
                        bottom_cover=params.calculations.soil_profile.exit_point_modification.bottom_cover,
                        soil_type=params.calculations.soil_profile.exit_point_modification.soil_type,
                        material_table=params.input_selection.materials.table,
                    )
                }
            )
            self.get_api(entity_id).update_exit_point_properties(exit_point_params, exit_point)

    @staticmethod
    def update_cover_layer_for_exit_point_layout(
        saved_soil_layout: Munch, top_cover: float, bottom_cover: float, soil_type: str, material_table: List[Munch]
    ) -> Dict[str, List[Munch]]:
        """
        Replace and overwrite all the cover layers of the classified soil layout of an exit point with a provided soil_type.
        :param saved_soil_layout: Previously saved classified soil layout in the parametrization of an exit point
        :param top_cover: top level of the new cover layer in m NAP.
        :param bottom_cover: bottom level of the new cover layer in m NAP
        :param soil_type: soil_type for the new cover layer
        :param material_table: library of soil types
        :return:
        """
        layers = deepcopy(saved_soil_layout.get("layers"))
        for layer in saved_soil_layout.get("layers"):
            if layer["bottom_of_layer"] < bottom_cover:
                break
            layers.pop(0)  # all the non aquifer layers in saved_soil_layout are removed
        new_cover_soil_layer = munchify(
            get_soil_layer_from_soil_type(
                material_table=material_table, soil_type=soil_type, bottom_of_layer=bottom_cover, top_of_layer=top_cover
            ).serialize()
        )
        if layers:
            layers[0].top_of_layer = bottom_cover  # Readjust the level of the first aquifer layer in saved_soil_layout
        return {"layers": [new_cover_soil_layer] + layers}

    def reset_exit_point(self, params: Munch, entity_id: int, event: InteractionEvent, **kwargs):
        """Reset layout of all the selected exit points. Selection of exit points can be either interactive
        (event is not None) or from a drawn polygon on the MapView.
        """
        if event:  # Interactive selection of exit points
            selected_exit_point_entities = []
            api = self.get_api(entity_id)

            for exit_point_id in event.value:
                selected_exit_point_entities.append(api.get_entity(exit_point_id))

        else:  # Fetch all exit point entities within a polygon
            if not params.calculations.soil_profile.exit_point_modification.polygon_selection:
                raise UserException(
                    "Een polygon dient te worden getekend in de Kaart tab om de selectie van de uittredepunten te updaten"
                )

            exit_point_entities = self.get_api(entity_id).get_all_children_exit_point_entities()
            selected_exit_point_entities = get_all_exit_point_entities_within_polygon(
                exit_point_entities, params.calculations.soil_profile.exit_point_modification.polygon_selection
            )

        for exit_point in selected_exit_point_entities:
            exit_point_params = exit_point.last_saved_params

            materials_tables = get_materials_tables(params)

            classified_soil_layout = classify_tno_soil_model(
                exit_point_params.tno_soil_layout,
                materials_tables.get("classification_table"),
                materials_tables.get("table"),
                minimal_aquifer_thickness=params.minimal_aquifer_thickness,
            )
            # Update the soil layout from the TNO conversion with the actual ground level from AHN or ditch bottom.
            intersected_soil_layout = intersect_soil_layout_table_with_z(
                classified_soil_layout, round(exit_point_params.exit_point_data.ground_level, 3)
            )

            exit_point_params.update({"classified_soil_layout": intersected_soil_layout.serialize()})
            self.get_api(entity_id).update_exit_point_properties(exit_point_params, exit_point)

    def fill_closest_cpt(self, params: Munch, entity_id: int, **kwargs) -> SetParamsResult:
        """Fill the option Field with the closest CPT to the selected exit point"""
        exit_point = get_selected_exit_point_params(params).exit_point_data
        cpt = self.get_api(entity_id).closest_cpt_to_RD_coordinates(exit_point.x_coordinate, exit_point.y_coordinate)
        return SetParamsResult({"selected_cpt_id": cpt.id})

    def download_piping_results(self, params: Munch, entity_id: int, **kwargs) -> DownloadResult:
        """Return an Excel sheet with the intermediate results of all piping calculation. Each row corresponds to a
        combination (ExitPoint, aquifer)."""

        excel_files = {}

        segment_name = self.get_api(entity_id).segment_name()

        scenarios = self.get_segment(entity_id, params).get_all_scenarios(
            params.soil_schematization.geohydrology.level2.leakage_length_array, geohyromodel=params.geohydrology_method
        )
        exit_point_list = self.get_api(entity_id).get_all_children_exit_point_entities()
        segment = self.get_segment(entity_id, params)

        all_res_serialized = segment.get_serialized_piping_results(exit_point_list)
        for scenario in scenarios:
            result_file = self.generate_piping_results(params, all_res_serialized, scenario)

            excel_files[f"piping_result_segment_{scenario.name_of_scenario}.xlsx"] = BytesIO(
                result_file.getvalue_binary()
            )

        return DownloadResult(zipped_files=excel_files, file_name=f"piping_result_segment_{segment_name}.zip")

    def generate_piping_results(self, params: Munch, all_res_serialized: List[dict], scenario: Scenario) -> File:
        """
        Generate piping results as a bytes file
        """

        scenario_name = scenario.name_of_scenario
        filtered_result = [e for e in all_res_serialized if e["scenario_name"] == scenario_name]
        return PipingExcelBuilder(filtered_result, params, scenario).get_rendered_file()

    ####################################################################################################################
    #                                                   GENERIC FUNCTIONS                                              #
    ####################################################################################################################

    def get_segment(self, entity_id: int, segment_params: Munch) -> Segment:
        """create Segment Object for this entity"""
        return self.get_api(entity_id).get_segment_model(segment_params)

    def get_map_features_for_piping_results(
        self, entity_id: int, params: Munch, calculation_type: Optional[str] = None
    ) -> Tuple[List[MapFeature], List[MapLabel]]:
        """
        Create and return a list of custom map points for the results of piping calculations
        :param entity_id:
        :param params:
        :param calculation_type: One of ['uplift', 'heave', 'sellmeijer']
        :return:
        """

        exit_point_list = self.get_api(entity_id).get_all_children_exit_point_entities()
        segment = self.get_segment(entity_id, params)

        all_res_serialized = segment.get_serialized_piping_results(exit_point_list)
        if params.calculations.soil_profile.results_settings.composite_result_switch:
            return segment.get_map_features_for_combined_piping_results(
                all_res_serialized, calculation_type=calculation_type
            )
        else:
            if params.calculations.soil_profile.results_settings.scenario_selection is not None:
                selected_scenario = get_soil_scenario(
                    scenario_name=params.calculations.soil_profile.results_settings.scenario_selection,
                    soil_scenario_array=params.input_selection.soil_schematization.soil_scen_array,
                )
                return segment.get_map_features_for_uncombined_piping_results(
                    all_res_serialized, selected_scenario.name_of_scenario, calculation_type=calculation_type
                )
            raise UserException("Kies een scenario")

    @staticmethod
    def intersect_gdf_with_polygon(gdf: gpd.GeoDataFrame, polygon: Polygon) -> dict:
        """
        Intersect GeoDataFrame with polygon

        Parameters
        ----------
        gdf:
            Should contain columns: ditch_polygon and ditch_center_line
        polygon
            Shapely polygon
        Returns
        -------

        """
        gdf["geometry"] = [Polygon(coords) for coords in gdf["ditch_polygon"]]
        # {'contains', 'crosses', 'intersects', 'within', 'touches', 'overlaps', None, 'covers', 'contains_properly'}

        intersection_ditches = gpd.sjoin(gdf, gpd.GeoDataFrame(geometry=[polygon]), predicate="intersects")

        # gpd.sjoin doesn't intersect all the geometries but only returns the ones that fall within the polygon
        # we have to intersect again all the returned geometries
        intersection_ditches["ditch_polygon"] = [
            list(geom.intersection(polygon).exterior.coords) for geom in intersection_ditches["geometry"]
        ]
        clipped_linestrings = []
        for line in intersection_ditches["ditch_center_line"]:
            intersect = LineString(line).intersection(polygon)
            # If the buffer zone cuts the ditch center line in a weird way, then intersect becomes a MultiLineString
            # instead of a LineString. User should manually adjust the bufferzone length.
            if isinstance(intersect, MultiLineString):
                raise UserException("Aanpassen bufferzone lengte.")
            clipped_linestrings.append(list(intersect.coords))
        intersection_ditches["ditch_center_line"] = clipped_linestrings

        intersection_ditches = intersection_ditches.drop(["geometry", "index_right"], axis=1).to_dict("records")
        return intersection_ditches
