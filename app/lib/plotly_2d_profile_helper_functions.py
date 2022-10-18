from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import numpy as np
import plotly.graph_objects as go
from numpy import floor
from shapely.geometry import LineString
from shapely.geometry import Point

from app.cpt.model import CPT
from app.ground_model.constants import UNIQUE_TNO_SOIL_TYPES
from app.ground_model.model import classify_tno_soil_model
from app.lib.helper_read_files import round_to_nearest_0_05
from viktor import Color
from viktor import UserException
from viktor.geo import GEFData
from viktor.geo import SoilLayout

DICT_SOIL_TYPES = {
    "gravel_component": "grey",
    "sand_component": "yellow",
    "loam_component": "blue",
    "clay_component": "green",
    "peat_component": "brown",
}


def add_borehole_soil_table(
    fig: go.Figure, soil_table: dict, width: float = 1, x_start: float = 0, return_trace_counter=False
) -> Union[go.Figure, Tuple[int, go.Figure]]:
    trace_counter = 0
    for layer in soil_table:
        start = x_start
        for soil_type, color in DICT_SOIL_TYPES.items():
            per = layer[soil_type]
            if per > 0:
                trace_counter += 1
                end = start + per * width
                fig.add_trace(
                    go.Scatter(
                        x=[start, start, end, end, start],
                        y=[
                            layer["bottom_nap"],
                            layer["top_nap"],
                            layer["top_nap"],
                            layer["bottom_nap"],
                            layer["bottom_nap"],
                        ],
                        fill="toself",
                        line=dict(color=color),
                        fillcolor=color,
                        text=f"{layer['soil_code']}" f"<br>{soil_type}: {per}<br>",
                        hovertemplate="%{text}",
                        showlegend=False,
                        mode="lines",
                        hoverlabel=dict(namelength=0),
                        legendgroup="boreholes",
                    )
                )
                start = end
    if return_trace_counter:
        return trace_counter, fig
    else:
        return fig


def add_u2(fig: go.Figure, cpt: GEFData, scale_factor: float = 1, distance: float = 0) -> go.Figure:
    fig.add_trace(
        go.Scatter(
            x=list(-np.array(cpt.u2) * scale_factor + distance),
            y=list(np.array(cpt.elevation) * 1e-3),
            mode="lines",
            line=dict(color="brown", width=1),
            customdata=cpt.u2,
            legendgroup="u2",
            showlegend=False,
            hoverinfo="text",
            hovertemplate=f"CPT naam: {cpt.name} <br>"
            + "<br><b>Diepte</b>: %{y:.2f} m NAP"
            + "<br><b>u2</b>: %{customdata:.2f} MPa<br>"
            + "<extra></extra>",
        )
    )
    return fig


def add_Rf(fig: go.Figure, cpt: GEFData, scale_factor: float = 1, distance: float = 0) -> go.Figure:
    rf = -np.array(cpt.Rf) * 100
    fig.add_trace(
        go.Scatter(
            x=list(rf * scale_factor + distance),
            y=list(np.array(cpt.elevation) * 1e-3),
            mode="lines",
            line=dict(color="mediumblue", width=1),
            customdata=list(rf),
            legendgroup="Rf",
            showlegend=False,
            hoverinfo="text",
            hovertemplate=f"CPT naam: {cpt.name} <br>"
            + "<br><b>Diepte</b>: %{y:.2f} m NAP"
            + "<br><b>Rf</b>: %{customdata:.2f} %<br>"
            + "<extra></extra>",
        )
    )
    return fig


def add_qc(fig: go.Figure, cpt: GEFData, scale_factor: float = 1, distance: float = 0) -> go.Figure:
    fig.add_trace(
        go.Scatter(
            x=list(np.array(cpt.qc) * scale_factor + distance),
            y=list(np.array(cpt.elevation) * 1e-3),
            mode="lines",
            line=dict(color="red", width=1),
            customdata=cpt.qc,
            legendgroup="qc",
            showlegend=False,
            hoverinfo="text",
            hovertemplate=f"CPT naam: {cpt.name} <br>"
            + "<br><b>Diepte</b>: %{y:.2f} m NAP"
            + "<br><b>qc</b>: %{customdata:.2f} kN<br>"
            + "<extra></extra>",
        )
    )
    return fig


def get_visualisation_along_trajectory(
    trajectory: LineString,
    longitudinal_soil_layout: List[SoilLayout],
    classification_table: List,
    materials_table: List,
    chainage_step: float = 25,
    min_max_permeabilities: Optional[dict] = None,
    segment_array: Optional[List] = None,
    vertical_line_location: float = None,
    cpt_params: Optional[dict] = None,
    bore_entity_list: Optional[List] = None,
    regis_layouts: Optional[List[SoilLayout]] = None,
) -> go.Figure:
    """
    Generate a 2d profile along a trajectory.
    """
    layout = go.Layout(yaxis=dict(title="diepte [m NAP]"), xaxis=dict(title="meetpunt langs traject [m]"))
    fig = go.Figure(layout=layout)

    traj_as_points = [Point(coord) for coord in trajectory.coords]
    distance_left_side_barchart = 0
    distance_right_side_barchart = traj_as_points[0].distance(traj_as_points[1]) / 2
    width = chainage_step / 2
    bottom_list, top_list = [], []
    button_options_list = []

    for i, soil_layout in enumerate(longitudinal_soil_layout):

        if regis_layouts:
            regis_layout = regis_layouts[i]
        else:
            regis_layout = None

        # get global min and max elevations
        bottom_list.append(soil_layout.layers[-1].bottom_of_layer)
        top_list.append(soil_layout.layers[0].top_of_layer)
        distances = dict(
            distance_leftside=distance_left_side_barchart, distance_rightside=distance_right_side_barchart, width=width
        )

        # add the corresponding traces at this
        button_options_list = add_2d_soil_traces_to_fig(
            fig,
            soil_layout,
            classification_table,
            materials_table,
            button_options_list,
            distances,
            min_max_permeabilities=min_max_permeabilities,
            showlegend=i == 1,
            regis_layout=regis_layout,
        )

        distance_left_side_barchart = distance_right_side_barchart
        distance_right_side_barchart += chainage_step
        width = chainage_step

    if segment_array:
        for segment in segment_array:
            start_segment = segment.segment_start_chainage
            end_segment = segment.segment_end_chainage
            fig.add_trace(
                go.Scatter(
                    name=f"Segment {segment.segment_name}",
                    x=[start_segment, start_segment, end_segment, end_segment, start_segment],
                    y=[max(top_list), min(bottom_list), min(bottom_list), max(top_list), max(top_list)],
                    mode="lines",
                    line=dict(color="Blue", dash="dot", width=1),
                    showlegend=True,
                    legendgroup="lines",
                    hovertemplate=f"Segment {segment.segment_name}<br>"
                    + f"Start segment: {start_segment:.0f} m<br>"
                    + f"Eind segment: {end_segment:.0f} m"
                    + "<extra></extra>",
                )
            )

    segment_trace_activator = [True]
    if bore_entity_list is not None:
        n_traces, fig = add_boreholes_to_2d_profile(fig, trajectory, bore_entity_list)
        boreholes_trace_activator = [True] * n_traces
    else:
        boreholes_trace_activator = []
    if cpt_params is not None:
        n_traces, fig = add_cpts_to_2d_profile(fig, cpt_params, trajectory)
        cpt_traces_activator = [True] * n_traces
    else:
        cpt_traces_activator = []

    fig.update_layout(
        template="plotly_white",
        updatemenus=[
            dict(
                type="dropdown",
                direction="down",
                active=0,
                x=0.57,
                y=1.1,
                buttons=list(
                    [
                        dict(
                            label="3D bodemopbouw",
                            method="update",
                            args=[
                                {
                                    "visible": [bool(scenario == "tno_model") for scenario in button_options_list]
                                    + segment_trace_activator
                                    + boreholes_trace_activator
                                    + cpt_traces_activator
                                }
                            ],
                        ),
                        dict(
                            label="Geclassificeerde bodemopbouw",
                            method="update",
                            args=[
                                {
                                    "visible": [bool(scenario == "classified") for scenario in button_options_list]
                                    + segment_trace_activator
                                    + boreholes_trace_activator
                                    + cpt_traces_activator
                                }
                            ],
                        ),
                        dict(
                            label="Verticale permeabiliteit (3D model)",
                            method="update",
                            args=[
                                {
                                    "visible": [
                                        bool(scenario == "vertical permeability") for scenario in button_options_list
                                    ]
                                    + segment_trace_activator
                                    + boreholes_trace_activator
                                    + cpt_traces_activator
                                }
                            ],
                        ),
                        dict(
                            label="Horizontale permeabiliteit (3D model)",
                            method="update",
                            args=[
                                {
                                    "visible": [
                                        bool(scenario == "horizontal permeability") for scenario in button_options_list
                                    ]
                                    + segment_trace_activator
                                    + boreholes_trace_activator
                                    + cpt_traces_activator
                                }
                            ],
                        ),
                    ]
                ),
            )
        ],
    )

    if vertical_line_location is not None:
        fig.add_vline(x=vertical_line_location)

    return fig


def add_boreholes_to_2d_profile(fig: go.Figure, trajectory: LineString, bore_entity_list) -> Tuple[int, go.Figure]:
    """
    Add borehole to 2d profile.
    """
    n_traces = 0
    distance_0 = 0
    height_0 = 0
    for i, bore in enumerate(bore_entity_list):
        params = bore.last_saved_params
        coords = (float(params["x_rd"]), float(params["y_rd"]))
        bore_point = Point(coords)
        distance = trajectory.project(bore_point)
        trace_counter, fig = add_borehole_soil_table(
            fig, params.soil_table, width=15, x_start=distance, return_trace_counter=True
        )
        n_traces += trace_counter
        if i == 0:
            distance_0 = distance
            height_0 = params.soil_table[0]["top_nap"]
    # Add a fake point for legend
    fig.add_trace(
        go.Scatter(
            x=[distance_0],
            y=[height_0],
            name="boreholes",
            showlegend=True,
            legendgroup="boreholes",
            visible=True,
            marker=dict(color="red", size=1),
        )
    )
    return n_traces + 1, fig


def add_cpts_to_2d_profile(
    fig: go.Figure,
    cpt_params: dict,
    trajectory: LineString,
) -> Tuple[int, go.Figure]:
    """Add CPTs of CPT folder to the 2D profile figure"""
    cpt_entity_list = cpt_params["cpt_entity_list"]
    scale_factor_qc = cpt_params["scale_measurement_cpt_qc"]
    scale_factor_rf = cpt_params["scale_measurement_cpt_rf"]
    scale_factor_u2 = cpt_params["scale_measurement_cpt_u2"]
    distance_0 = 0
    height_0 = 0
    is_rf = False
    is_u2 = False
    n_traces = 0
    for cpt in cpt_entity_list:
        try:
            gef = CPT(cpt_params=cpt.last_saved_params, entity_id=cpt)
            params = cpt.last_saved_params
            coords = (float(params["x_rd"]), float(params["y_rd"]))
            cpt_point = Point(coords)
            distance = trajectory.project(cpt_point)

            fig = add_qc(fig, gef.parsed_cpt, scale_factor=scale_factor_qc, distance=distance)
            n_traces += 1
            if hasattr(gef.parsed_cpt, "Rf"):
                is_rf = True
                n_traces += 1
                fig = add_Rf(fig, gef.parsed_cpt, scale_factor=scale_factor_rf, distance=distance)
            if hasattr(gef.parsed_cpt, "u2"):
                is_u2 = True
                n_traces += 1
                fig = add_u2(fig, gef.parsed_cpt, scale_factor=scale_factor_u2, distance=distance)
        except AttributeError as e:
            raise UserException(e)

    # Add a fake points for legend
    n_traces += 1
    fig.add_trace(
        go.Scatter(
            x=[distance_0],
            y=[height_0],
            name="qc",
            showlegend=True,
            legendgroup="qc",
            visible=True,
            marker=dict(color="red", size=1),
        )
    )
    if is_rf:
        n_traces += 1
        fig.add_trace(
            go.Scatter(
                x=[distance_0],
                y=[height_0],
                name="Rf",
                showlegend=True,
                legendgroup="Rf",
                visible=True,
                marker=dict(color="mediumblue", size=1),
            )
        )
    if is_u2:
        n_traces += 1
        fig.add_trace(
            go.Scatter(
                x=[distance_0],
                y=[height_0],
                name="u2",
                showlegend=True,
                legendgroup="u2",
                visible=True,
                marker=dict(color="brown", size=1),
            )
        )
    return n_traces, fig


def add_2d_soil_traces_to_fig(
    fig: go.Figure,
    soil_layout: SoilLayout,
    classification_table: List,
    materials_table: List,
    button_options_list: List,
    distances: dict,
    min_max_permeabilities: Optional[dict] = None,
    regis_layout: Optional[SoilLayout] = None,
    showlegend: Optional[bool] = False,
) -> List[str]:
    """
    The function adds to the Plotly figure the bar traces for one x coordinate the following data:
        - Raw TNO data: "tno_model"
        - Classified TNO data based on provided materials and classification table: "classified"
        - Gradient scale for the TNO vertical permeability: vertical permeability
        - Gradient scale for the TNO horizontal permeability: horizontal permeability

    This function also returns a list of string to make the Widget Plotly button to switch between the 4 traces
    mentioned above.
    :param fig: Plotly fig to which the traces are appended
    :param option: one of ["classified", "tno_model", "vertical permeability", "horizontal permeability"]
    :param soil_layout: raw TNO SoilLayout
    :param classification_table:
    :param materials_table:
    :param distances: dictionary containing the following keys: "distance_along_dyke", "dist_to_prev_point",
    "midpoint_distance_along_dyke"
    :param min_max_permeabilities: min and max permeability from the TNO data, is used to make the color gradient
    :param regis_layout
    :param showlegend:
    :return:
    """

    # to distinguish (non-)categorised soillayouts
    unique_soil_types = UNIQUE_TNO_SOIL_TYPES
    layers = soil_layout

    if regis_layout:
        regis_soil_types = [soil.name for soil in regis_layout.filter_unique_soils()]
        for soil_name in regis_soil_types:
            regis_layers = [layer for layer in regis_layout.layers if layer.soil.name == soil_name]
            button_options_list.append("tno_model")
            legendgroup = "Regis"
            hovertext = [
                f"Grondsoort: {layer.soil.name}<br>"
                f"Bovenkant laag: {layer.top_of_layer:.2f}<br>"
                f"Onderkant laag: {layer.bottom_of_layer:.2f}"
                for layer in regis_layers
            ]
            fig.add_trace(
                go.Bar(
                    name=soil_name,
                    x=[distances["distance_leftside"]] * len(regis_layers),
                    y=[-(layer.top_of_layer - layer.bottom_of_layer) for layer in regis_layers],
                    width=distances["width"],
                    offset=0,
                    marker=dict(color=[f"rgb{Color(*layer.soil.color).rgb}" for layer in regis_layers]),
                    showlegend=showlegend,
                    hoverinfo="text",
                    hovertext=hovertext,
                    legendgroup=legendgroup,
                    legendgrouptitle_text="REGIS lagen",
                    base=[layer.top_of_layer for layer in regis_layers],
                    visible=True,
                )
            )

    for ui_name in unique_soil_types:
        original_layers = [layer for layer in layers.layers if layer.soil.name == ui_name]
        soil_type_layers = [*original_layers]
        button_options_list.append("tno_model")
        hovertext = [
            f"{floor(distances['distance_leftside']):.0f} m van startpunt <br>"
            f"diepte:  {round_to_nearest_0_05(layer.top_of_layer):.2f}"
            f"tot {round_to_nearest_0_05(layer.bottom_of_layer):.2f} m NAP <br>"
            f"Geclassificeerd als {layer.soil.name} <br>"
            f"{layer.properties.kans_1_veen:.0f} % kans op veen <br>"
            f"{layer.properties.kans_2_klei:.0f} % kans op klei <br>"
            f"{layer.properties.kans_3_kleiig_zand:.0f} % kans op kleig zand <br>"
            f"{layer.properties.kans_5_zand_fijn:.0f} % kans op fijn zand <br>"
            f"{layer.properties.kans_6_zand_matig_grof:.0f} % kans op matig grof zand <br>"
            f"{layer.properties.kans_7_zand_grof:.0f} % kans op grof zand"
            for layer in soil_type_layers
        ]
        legendgroup = "TNO"
        fig.add_trace(
            go.Bar(
                name=ui_name,
                x=[distances["distance_leftside"]] * len(soil_type_layers),
                y=[-(layer.top_of_layer - layer.bottom_of_layer) for layer in soil_type_layers],
                width=distances["width"],
                offset=0,
                marker=dict(color=[f"rgb{Color(*layer.soil.color).rgb}" for layer in soil_type_layers]),
                showlegend=showlegend,
                hoverinfo="text",
                hovertext=hovertext,
                legendgroup=legendgroup,
                legendgrouptitle_text="3D model lagen",
                base=[layer.top_of_layer for layer in soil_type_layers],
            )
        )
        button_options_list.append("verticale doorlatendheid")
        hovertext = [
            f"diepte: {layer.bottom_of_layer} tot {layer.top_of_layer} m NAP <br>"
            f"Geclassificeerd als {layer.soil.name} <br>"
            f"{layer.properties.vertical_permeability:.2f} m/d verticale doorlatendheid <br>"
            f"{layer.properties.horizontal_permeability:.2f} m/d horizontale doorlatendheid <br>"
            for layer in soil_type_layers
        ]
        fig.add_trace(
            go.Bar(
                name=ui_name,
                x=[distances["distance_leftside"]] * len(soil_type_layers),
                y=[-(layer.top_of_layer - layer.bottom_of_layer) for layer in soil_type_layers],
                width=distances["width"],
                offset=0,
                marker=dict(
                    color=[layer.properties.vertical_permeability for layer in soil_type_layers],
                    cmin=min_max_permeabilities["min_perm_v"],
                    cmax=min_max_permeabilities["max_perm_v"],
                    colorbar=dict(
                        title="Schaal doorlatendheid",
                        tickfont=dict(family="Arial"),
                        ticksuffix="m/d",
                        showticksuffix="all",
                        y=0.45,
                    ),
                    colorscale=[[0, "red"], [0.5, "yellow"], [1, "green"]],
                ),
                showlegend=False,
                hoverinfo="text",
                hovertext=hovertext,
                base=[layer.top_of_layer for layer in soil_type_layers],
                visible=False,
            )
        )

        button_options_list.append("horizontal permeability")
        hovertext = [
            f"diepte: {layer.bottom_of_layer} tot {layer.top_of_layer} m NAP <br>"
            f"Geclassificeerd als {layer.soil.name} <br>"
            f"{layer.properties.vertical_permeability:.2f} m/d verticale doorlatendheid <br>"
            f"{layer.properties.horizontal_permeability:.2f} m/d horizontale doorlatendheid <br>"
            for layer in soil_type_layers
        ]
        fig.add_trace(
            go.Bar(
                name=ui_name,
                x=[distances["distance_leftside"]] * len(soil_type_layers),
                y=[-(layer.top_of_layer - layer.bottom_of_layer) for layer in soil_type_layers],
                width=distances["width"],
                offset=0,
                marker=dict(
                    color=[layer.properties.horizontal_permeability for layer in soil_type_layers],
                    cmin=min_max_permeabilities["min_perm_h"],
                    cmax=min_max_permeabilities["max_perm_h"],
                    colorbar=dict(
                        title="Schaal doorlatendheid",
                        tickfont=dict(family="Arial"),
                        ticksuffix="m/d",
                        showticksuffix="all",
                        y=0.45,
                    ),
                    colorscale=[[0, "red"], [0.5, "yellow"], [1, "green"]],
                ),
                showlegend=False,
                hoverinfo="text",
                hovertext=hovertext,
                base=[layer.top_of_layer for layer in soil_type_layers],
                visible=False,
            )
        )

    # classify
    layers = classify_tno_soil_model(
        layers,
        classification_table,
        materials_table,
        minimal_aquifer_thickness=1,
    )
    unique_soil_types = [soil.name for soil in materials_table]

    for ui_name in unique_soil_types:
        original_layers = [layer for layer in layers.layers if layer.soil.name == ui_name]
        soil_type_layers = [*original_layers]

        button_options_list.append("classified")
        legendgroup = "classified"
        hovertext = [
            f"Grondsoort: {layer.soil.name}<br>"
            f"Bovenkant laag: {layer.top_of_layer:.2f}<br>"
            f"Onderkant laag: {layer.bottom_of_layer:.2f}"
            for layer in soil_type_layers
        ]

        fig.add_trace(
            go.Bar(
                name=ui_name,
                x=[distances["distance_leftside"]] * len(soil_type_layers),
                y=[-(layer.top_of_layer - layer.bottom_of_layer) for layer in soil_type_layers],
                width=distances["width"],
                offset=0,
                marker=dict(color=[f"rgb{Color(*layer.soil.color).rgb}" for layer in soil_type_layers]),
                showlegend=showlegend,
                hoverinfo="text",
                hovertext=hovertext,
                legendgroup=legendgroup,
                base=[layer.top_of_layer for layer in soil_type_layers],
                visible=False,
            )
        )
        fig.update_layout(showlegend=True)

    return button_options_list
