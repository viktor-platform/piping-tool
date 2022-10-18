from typing import Tuple

from munch import Munch
from shapely.geometry import Point

from app.lib.constants import MAP_LEGEND
from app.lib.helper_read_files import process_dijkpalen_shape_file
from app.lib.helper_read_files import shape_file_to_geo_poly_line
from app.lib.shapely_helper_functions import convert_linestring_to_geo_polyline
from app.lib.shapely_helper_functions import convert_shapely_linestring_to_shapefile
from app.lib.shapely_helper_functions import find_intersection_with_polygon_on_map
from viktor import Color
from viktor import File
from viktor import ParamsFromFile
from viktor import UserException
from viktor import ViktorController
from viktor.api_v1 import API
from viktor.api_v1 import EntityList
from viktor.geometry import GeoPoint
from viktor.geometry import RDWGSConverter
from viktor.result import DownloadResult
from viktor.result import SetParamsResult
from viktor.views import MapLabel
from viktor.views import MapPoint
from viktor.views import MapPolygon
from viktor.views import MapResult
from viktor.views import MapView
from viktor.views import PlotlyResult
from viktor.views import PlotlyView

from ..dyke.dyke_model import Dyke
from ..dyke.dykeAPI import DykeAPI
from ..dyke.parametrization import DykeParametrization
from ..lib.helper_read_files import entry_line_to_params
from ..lib.helper_read_files import process_ditch_shape_file
from ..lib.map_view_helper_functions import add_2D_longitudinal_line_to_mapfeatures
from ..lib.map_view_helper_functions import add_bore_to_mapfeatures
from ..lib.map_view_helper_functions import add_cpts_to_mapfeatures
from ..lib.map_view_helper_functions import add_dijkpalen_points_to_map_features
from ..lib.map_view_helper_functions import add_dike_trajectory_and_entry_line_to_map_features
from ..lib.map_view_helper_functions import add_ditches_to_map_features
from ..lib.map_view_helper_functions import add_ground_model_hull_to_map_features
from ..lib.map_view_helper_functions import add_segment_trajectory_to_map_features
from ..lib.shapely_helper_functions import convert_shapely_polgon_to_geopolygon
from ..lib.shapely_helper_functions import create_line_by_point_and_vector
from ..lib.shapely_helper_functions import create_perpendicular_vector_at_chainage
from ..lib.shapely_helper_functions import create_polygon_from_linestring_offset
from ..lib.shapely_helper_functions import get_point_from_trajectory


class Controller(ViktorController):
    """
    Controller to show embankment designs
    """

    label = "Dyke"
    children = ["Segment"]
    show_children_as = "Table"  # or 'Table'
    parametrization = DykeParametrization

    def __init__(self, *args, api: DykeAPI = None, **kwargs):
        """Intializes controller class.

        :api: API to be used for querying. Default is none. This is done for mocking purposes.
        """
        self._api = api
        super().__init__(*args, **kwargs, perform_string_to_number_conversion=False)

    def get_api(self, entity_id, params):
        """Lazy loaded API entity."""
        self._api = self._api or DykeAPI(entity_id, params)
        return self._api

    @ParamsFromFile(file_types=[".zip"])
    def process_shape_file(self, file: File, entity_id: int, **kwargs) -> dict:
        """Process shape files upon uploading and create a Dyke entity.
        Several files extension must be present in the uploaded file: .shp, .shx, and .dbf. The content of these
        files is overwritten into the corresponding temp files.
        """
        geo_poly_line = shape_file_to_geo_poly_line(file)
        return {"dyke_geo_coordinates": geo_poly_line}

    @MapView("Kaart", duration_guess=4)
    def visualize_map(self, params: Munch, entity_id: int, **kwargs) -> MapResult:
        """Visualize the MapView of the dyke location represented with a polyline"""
        map_features, map_labels = [], []

        api = self.get_api(entity_id, params)
        segment_api_list = api.get_children_by_entity_type(entity_type="Segment", entity_id=entity_id)

        if params.geometry.data_selection.ground_model:
            tno_ground_model = api.get_ground_model()
            tno_ground_model_params = api.get_tno_entity().last_saved_params
            add_ground_model_hull_to_map_features(map_features, ground_model_hull=tno_ground_model_params.convex_hull)
            dyke = Dyke(params, tno_ground_model)
        else:
            dyke = Dyke(params)

        # Add dike trajectory and entry line
        if params.dyke_geo_coordinates:
            add_dike_trajectory_and_entry_line_to_map_features(
                map_features,
                dike_trajectory=params.dyke_geo_coordinates,
                entry_line=entry_line_to_params(params.entry_line) if params.entry_line else None,
            )

        # Add prevision segment
        if params.segment_generation.polygon:
            selected_trajectory = find_intersection_with_polygon_on_map(
                params.dyke_geo_coordinates, params.segment_generation.polygon
            )
            add_segment_trajectory_to_map_features(
                map_features, convert_linestring_to_geo_polyline(selected_trajectory)
            )

        # Add start and end chainage lines
        if segment_api_list:
            polyline_list, description_list = self.get_start_end_chainage_polyline(params, segment_api_list)
            for idx, polyline in enumerate(polyline_list):
                add_segment_trajectory_to_map_features(map_features, polyline, description_list[idx])

        # Add ditches
        if params.ditch_data:
            ditch_features = process_ditch_shape_file(params.ditch_data)
            add_ditches_to_map_features(map_features, ditch_features)

        # add blue polygon to show direction to the river
        if params.dyke_geo_coordinates:
            third_point = GeoPoint.from_rd(Dyke(params).perpendicular_to_river())
            map_features.append(
                MapPolygon(
                    [
                        MapPoint.from_geo_point(GeoPoint.from_rd(dyke.interpolated_trajectory().coords[0])),
                        MapPoint.from_geo_point(GeoPoint.from_rd(dyke.interpolated_trajectory().coords[1])),
                        MapPoint.from_geo_point(third_point),
                    ],
                    color=Color.viktor_blue(),
                )
            )
            # add chainage (metrering) labels to the map)
            map_labels.extend(
                [
                    MapLabel(
                        lat=RDWGSConverter.from_rd_to_wgs(point)[0],
                        lon=RDWGSConverter.from_rd_to_wgs(point)[1],
                        text=str(params.chainage_step * i),
                        scale=17,
                    )
                    for i, point in enumerate(dyke.interpolated_trajectory().coords)
                ]
            )

        if params.cpt_folder:
            cpt_entity_list = params.cpt_folder.children(entity_type_names=["CPT"])

            add_cpts_to_mapfeatures(map_features, cpt_entity_list, map_labels)
        if params.bore_folder:
            bore_entity_list = params.bore_folder.children(entity_type_names=["Bore"])
            add_bore_to_mapfeatures(map_features, bore_entity_list, map_labels)

        # Add dijkpalen
        if params.dijkpalen:
            dijkpalen = process_dijkpalen_shape_file(params.dijkpalen)
            add_dijkpalen_points_to_map_features(map_features, map_labels, dijkpalen)

        # Add line used for the view "2D grondopbouw" and the buffer zone around it
        add_2D_longitudinal_line_to_mapfeatures(map_features, dyke)

        return MapResult(map_features, map_labels, legend=MAP_LEGEND)

    @PlotlyView("2D grondopbouw", duration_guess=5)
    def visualize_ground_model_along_dyke(self, params: Munch, entity_id: int, **kwargs) -> PlotlyResult:
        tno_groundmodel = self.get_api(entity_id, params).get_ground_model()
        dyke = Dyke(params, tno_groundmodel)
        fig = dyke.get_visualisation_along_trajectory()
        return PlotlyResult(fig.to_dict())

    def create_segments_from_dynamic_array(self, params: Munch, entity_id: int, **kwargs) -> SetParamsResult:
        dyke = Dyke(params)
        trajectory_points = [Point(coord) for coord in dyke.interpolated_trajectory().coords]
        for segment in params.segment_generation.segment_array:
            segment_geopolygon = convert_shapely_polgon_to_geopolygon(
                create_polygon_from_linestring_offset(
                    trajectory_points, segment.segment_start_chainage, segment.segment_end_chainage
                )
            )[0]
            API().create_child_entity(
                parent_entity_id=entity_id,
                entity_type_name="Segment",
                name=f"Segment {segment.segment_name}",
                params={
                    "segment_polygon": segment_geopolygon,
                    "counter_exit_point_entities": 0,
                    "start_chainage": segment.segment_start_chainage,
                    "end_chainage": segment.segment_end_chainage,
                },
            )

        return SetParamsResult({"segment_generation": {"segment_array": None}})

    def get_chainage_length(self, params: Munch, entity_id, **kwargs) -> SetParamsResult:
        """Get the chainage length from the ground model"""

        api = self.get_api(entity_id, params)
        tno_ground_model_params = api.get_tno_entity().last_saved_params
        chainage_length = tno_ground_model_params.chainage_length

        return SetParamsResult({"chainage_step": chainage_length})

    @staticmethod
    def get_segment_trajectories(params: Munch, **kwargs) -> DownloadResult:
        """Get the selected segment entity and return the requested DownloadResult"""
        if not params.downloads.segment_select:
            raise UserException("Geen segment geselecteerd")
        segment_entity = params.downloads.segment_select
        segment_polygon = segment_entity.last_saved_params.segment_polygon
        shapefiles = convert_shapely_linestring_to_shapefile(params, segment_polygon, segment_entity.name)

        return DownloadResult(zipped_files=shapefiles, file_name=f"{segment_entity.name}_trajectory.zip")

    @staticmethod
    def get_start_end_chainage_polyline(params: Munch, segment_entity_list: EntityList) -> Tuple[list, list]:
        """Get the start and end chainage values with corresponding names from created segment entities"""
        dyke = Dyke(params)
        trajectory_points = [Point(coord) for coord in dyke.interpolated_trajectory().coords]
        polyline_list = []
        description_list = []

        for segment_api in segment_entity_list:
            segment_params = segment_api.last_saved_params
            if segment_params.start_chainage is None or segment_params.end_chainage is None:
                raise UserException("Dijkvak mist een start of eind kilometrering")
            start_point = get_point_from_trajectory(trajectory_points, (segment_params.start_chainage))
            end_point = get_point_from_trajectory(trajectory_points, (segment_params.end_chainage))
            mid_point = Point(((start_point.x + end_point.x) / 2), ((start_point.y + end_point.y) / 2))
            perpendicular_vector = create_perpendicular_vector_at_chainage([start_point, mid_point, end_point], 1, 20)
            polyline_list.append(
                convert_linestring_to_geo_polyline(create_line_by_point_and_vector(start_point, perpendicular_vector))
            )
            description_list.append(f"{segment_api.name} start kilometrering")
            polyline_list.append(
                convert_linestring_to_geo_polyline(create_line_by_point_and_vector(end_point, perpendicular_vector))
            )
            description_list.append(f"{segment_api.name} eind kilometrering")

        return polyline_list, description_list


# TODO Update code below with new segment controller methods
# def get_all_piping_results(self, params: Munch, entity_id, **kwargs) -> DownloadResult:
#     """
#     Download all the results in a zip file.
#     Note that all the necessary parameters for the piping calculation (river level, material table, etc...)
#     should be defined by the user in the segment UI.
#     """
#     excel_files = {}
#
#     for segment_entity in self.get_api(entity_id, params).get_children_by_entity_type("Segment", entity_id):
#         segment_params = segment_entity.last_saved_params
#         scenarios = SegmentController()
#         for scenario in scenarios:
#             file_content = (
#                 SegmentController()
#                 .generate_piping_results(segment_params, entity_id=segment_entity.id, scenario=scenario)
#                 .getvalue_binary()
#             )
#             excel_files[f"piping_result_segment_{segment_entity.name}_{scenario.name_of_scenario}.xlsx"] = BytesIO(
#                 file_content
#             )
#     return DownloadResult(zipped_files=excel_files, file_name="results.zip")
