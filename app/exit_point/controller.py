from pathlib import Path

import plotly.graph_objects as go
from munch import Munch
from shapely.geometry import LineString
from shapely.geometry import Point

from app.exit_point.exit_pointAPI import ExitPointAPI
from app.exit_point.parametrization import ExitPointParametrization
from app.lib.shapely_helper_functions import convert_linestring_to_geo_polyline
from app.lib.shapely_helper_functions import convert_viktor_polygon_to_shapely
from app.lib.shapely_helper_functions import extend_line
from app.lib.shapely_helper_functions import get_exit_point_projection_on_entry_line
from viktor import Color
from viktor import File
from viktor import UserException
from viktor import ViktorController
from viktor.geometry import RDWGSConverter
from viktor.result import DownloadResult
from viktor.views import MapPoint
from viktor.views import MapPolyline
from viktor.views import MapResult
from viktor.views import MapView
from viktor.views import PlotlyResult
from viktor.views import PlotlyView
from viktor.views import Summary
from viktor.views import SummaryItem

from ..lib.d_geoflow.create_geolib_models import generate_dgeoflow_model
from ..lib.d_geoflow.create_geolib_models import generate_dstability_model
from ..lib.map_view_helper_functions import add_intersected_segment_ditches_to_map_features
from .soil_geometry_model import SoilGeometry


class Controller(ViktorController):
    """
    Controller to show embankment designs
    """

    label = "Exit point"
    parametrization = ExitPointParametrization
    summary = Summary(
        x_coordinate=SummaryItem("X coordinate", float, "parametrization", "exit_point_data.x_coordinate", suffix="m"),
        y_coordinate=SummaryItem("Y coordinate", float, "parametrization", "exit_point_data.y_coordinate", suffix="m"),
    )

    def __init__(self, *args, api: ExitPointAPI = None, **kwargs):
        """Intializes controller class.
        :api: API to be used for querying. Default is none. This is done for mocking purposes.
        """
        self._api = api
        super().__init__(*args, **kwargs, perform_string_to_number_conversion=False)

    def get_api(self, entity_id):
        """Lazy loaded API entity."""
        self._api = self._api or ExitPointAPI(entity_id)
        return self._api

    @MapView("Kaart", duration_guess=2)
    def map_view(self, params: Munch, entity_id: int, **kwargs):
        soil_geom = self.create_soil_geometry(params, entity_id)
        cross_section = convert_linestring_to_geo_polyline(soil_geom.trajectory)

        map_line = MapPolyline.from_geo_polyline(
            cross_section,
            color=Color.green(),
            description="Dyke central axis",
        )
        map_features = [map_line]
        segment_params = self.get_api(entity_id).get_segment_params()
        add_intersected_segment_ditches_to_map_features(map_features, segment_params=segment_params)
        map_features.append(
            MapPoint(
                *RDWGSConverter.from_rd_to_wgs(
                    (params.exit_point_data.x_coordinate, params.exit_point_data.y_coordinate)
                ),
                description="Uittredepunt",
            )
        )

        return MapResult(map_features)

    @PlotlyView("Dwarsdoorsnede", duration_guess=7)
    def cross_section_visualisation(self, params: Munch, entity_id: int, **kwargs):
        """visualise the cross-section of the dyke based on the detailed 1D soil layout and AHN data using a
        PlotlyView"""
        fig = go.Figure()
        soil_geom = self.create_soil_geometry(params, entity_id)
        ditch_data = self.get_api(entity_id).get_ditches()
        soil_layout = (
            soil_geom.soil_layout_2d_with_ditches_removed(ditch_data) if ditch_data else soil_geom.soil_layout_2d
        )
        water_level = self.get_api(entity_id).get_polder_level()
        river_level = self.get_api(entity_id).get_river_level()

        dyke = self.get_api(entity_id).get_dyke()
        exit_point = Point(params.exit_point_data.x_coordinate, params.exit_point_data.y_coordinate)
        crest_line_x_value = soil_geom.start_point.distance(dyke.get_base_trajectory())
        entry_line_x_value = soil_geom.start_point.distance(dyke.entry_line) - crest_line_x_value
        exit_point_x_value = soil_geom.start_point.distance(exit_point) - crest_line_x_value

        fig.add_hline(
            y=water_level,
            line_width=2,
            line_color="blue",
            name="polderpeil",
            annotation=dict(
                text=f"Polderpeil <br>{round(water_level)}m NAP",
                bgcolor="rgba(255,255,255,0.5)",
                bordercolor="blue",
                borderwidth=2,
            ),
        )
        fig.add_hline(
            y=river_level,
            line_width=2,
            line_color="blue",
            name="polderpeil",
            annotation=dict(
                text=f"Rivierpeil <br>{round(river_level)}m NAP",
                bgcolor="rgba(255,255,255,0.5)",
                bordercolor="blue",
                borderwidth=2,
            ),
        )
        for layer in soil_layout.layers:
            hovertext = f"""
                        Laag: {layer.soil.name} <br>
                        Verticale doorlatendheid: {layer.properties.vertical_permeability} <br>
                        Horizontale doorlatendheid: {layer.properties.horizontal_permeability} <br>
                        Gamma droog: {layer.properties.gamma_dry} <br>
                        Gamma nat: {layer.properties.gamma_wet}
                        """
            for polygon in layer.polygons():  # if thickness goes to 0, there could be more than one polygon in a layer
                polygon = convert_viktor_polygon_to_shapely(polygon)
                fig.add_trace(
                    go.Scatter(
                        x=[point[0] - crest_line_x_value for point in polygon.exterior.coords],
                        y=[point[1] for point in polygon.exterior.coords],
                        marker=dict(color="black"),
                        fillcolor=layer.soil.color.hex,
                        mode="lines",
                        fill="toself",
                        name=layer.soil.name,
                        hoverinfo="text",
                        hovertext=hovertext,
                        connectgaps=True,
                    )
                )

        for ditch in soil_geom.intersecting_ditches(ditch_data):
            if ditch.is_wet:
                color = "blue"
                name = "Sloot"
            else:
                color = "black"
                name = "Droge sloot"
            fig.add_trace(
                go.Scatter(
                    x=[point[0] - crest_line_x_value for point in ditch.surface_line(extend=0).coords],
                    y=[point[1] for point in ditch.surface_line(extend=0).coords],
                    marker=dict(color=color),
                    mode="lines",
                    fill="toself",
                    name=name,
                    hovertext=name,
                    connectgaps=True,
                )
            )

        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)")
        fig.update_xaxes(title="Afstand vanaf kruin [m]")
        fig.update_yaxes(title="Diepte [m NAP]")
        if not params.visualisation.autoscale:
            fig.update_yaxes(scaleanchor="x", scaleratio=1)  # use the same scale in x and in y: dyke is to scale

        fig.add_vline(
            x=0,
            line_width=3,
            line_dash="dash",
            line_color="red",
            annotation=dict(
                text="Kruin",
                bgcolor="rgba(255,255,255,0.5)",
                bordercolor="red",
                borderwidth=2,
            ),
        )
        fig.add_vline(
            x=entry_line_x_value,
            line_width=3,
            line_dash="dash",
            line_color="green",
            annotation=dict(
                text=f"Entry lijn<br>{round(entry_line_x_value)}m <br> van kruin",
                bgcolor="rgba(255,255,255,0.5)",
                bordercolor="green",
                borderwidth=2,
            ),
        )
        fig.add_vline(
            x=exit_point_x_value,
            line_width=3,
            line_dash="dash",
            line_color="green",
            annotation=dict(
                text=f"Uitredepunt<br>{round(exit_point_x_value)}m <br> van kruin",
                bgcolor="rgba(255,255,255,0.5)",
                bordercolor="green",
                borderwidth=2,
            ),
        )
        if dyke.bathymetry_points.is_empty:
            fig.update_layout(
                title_text="Geen bathymetrische gegevens geïmporteerd op dijkniveau", title_font_color="red"
            )
        return PlotlyResult(fig.to_json())

    def create_soil_geometry(self, params: Munch, entity_id: int) -> SoilGeometry:
        """Create a soil Geometry class for this exit point"""
        if params.visualisation.scenario_selection is None:
            raise UserException("Selecteer een scenario")

        detailed_1d_soil_layout, _ = self.get_api(entity_id).get_representative_segment_layout(
            scenario_index=params.visualisation.scenario_selection
        )
        dyke = self.get_api(entity_id).get_dyke()
        polder_level = self.get_api(entity_id).get_polder_level()
        river_level = self.get_api(entity_id).get_river_level()

        exit_point = Point(params.exit_point_data.x_coordinate, params.exit_point_data.y_coordinate)
        projected_exit_point_on_entry_line = get_exit_point_projection_on_entry_line(
            exit_point, dyke.get_base_trajectory(), dyke.entry_line
        )

        start_point = exit_point
        end_point = projected_exit_point_on_entry_line

        cross_section_line = extend_line(
            line=LineString([start_point, end_point]),
            offset=params.cross_section.extension_exit_point_side,
            side="start",
        )
        cross_section_line = extend_line(
            line=cross_section_line,
            offset=params.cross_section.extension_river_side,
            side="end",
        )

        if params.visualisation.river_to_the_right:
            start_point = Point(cross_section_line.coords[0])
            end_point = Point(cross_section_line.coords[-1])
        else:
            start_point = Point(cross_section_line.coords[-1])
            end_point = Point(cross_section_line.coords[0])

        return SoilGeometry(
            detailed_1d_soil_layout,
            start_point,
            end_point,
            dyke.bathymetry_points,
            params.spatial_resolution,
            params.cross_section.element_size,
            polder_level,
            river_level,
        )

    def download_flox(self, params: Munch, entity_id: int, **kwargs) -> DownloadResult:
        """Download the DGeoflow model as a .flox file with the geometry of the current exit point"""
        ditch_data = self.get_api(entity_id).get_ditches()
        soil_geometry = self.create_soil_geometry(params, entity_id)
        dyke = self.get_api(entity_id).get_dyke()
        model = generate_dgeoflow_model(soil_geometry, dyke, ditch_data)
        file = File()
        path = Path(file.source)  # request its path. Path has an is_dir() method, which is required.
        model.serialize(path)  # let GEOLIB write to the file
        name = self.get_api(entity_id).get_name()
        return DownloadResult(file.getvalue_binary(), f"{name}.flox")

    def download_stix(self, params: Munch, entity_id: int, **kwargs) -> DownloadResult:
        """Download the DStability model as a .stix file with the geometry of the current exit point, just for fun"""
        ditch_data = self.get_api(entity_id).get_ditches()
        soil_geometry = self.create_soil_geometry(params, entity_id)
        model = generate_dstability_model(soil_geometry, ditch_data)
        file = File()
        path = Path(file.source)  # request its path. Path has an is_dir() method, which is required.
        model.serialize(path)  # let GEOLIB write to the file
        name = self.get_api(entity_id).get_name()
        return DownloadResult(file.getvalue_binary(), f"{name}.stix")
