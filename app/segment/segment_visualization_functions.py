from typing import Optional

import plotly.graph_objects as go
from munch import Munch
from munch import munchify
from plotly.graph_objs import Figure
from plotly.subplots import make_subplots

from app.cpt.model import CPT
from app.ground_model.constants import UNIQUE_TNO_SOIL_TYPES
from app.ground_model.model import build_combined_rep_and_exit_point_layout
from viktor import Color
from viktor.geo import SoilLayout


def visualize_exit_point_soil_layouts(
    segment_params: Munch, exit_point_params: Munch, cpt: Optional[CPT], rep_soil_layout: SoilLayout
) -> str:
    """Returns the Plotly plot for the comparison of the two soil layouts of a selected exit point"""
    number_columns = 2 if segment_params.show_cpt else 1
    fig = make_subplots(
        rows=1,
        cols=number_columns,
        shared_yaxes=True,
        horizontal_spacing=0.00,
        column_widths=[3] * number_columns,
    )

    if segment_params.show_cpt:
        add_cpt_trace(fig, cpt)

    add_bar_soil_layouts(segment_params, exit_point_params, fig, number_columns, rep_soil_layout)

    fig.update_layout(barmode="stack", template="plotly_white", legend=dict(x=1.10, y=0.5))

    return fig.to_json()


def visualize_representative_layouts(
    detailed_soil_layout: SoilLayout, simplified_soil_layout: SoilLayout, segment_params: Munch
) -> str:
    fig = make_subplots(
        rows=1,
        cols=1,
        shared_yaxes=True,
        horizontal_spacing=0.00,
        column_widths=[3],
    )
    unique_user_soil_types = [soil.name for soil in segment_params.input_selection.materials.table]

    add_trace_classified_layout(
        fig,
        nb_columns=1,
        soil_layout=munchify(detailed_soil_layout.serialize()),
        unique_user_soil_types=unique_user_soil_types,
        x_name="1D representatieve layout",
    )
    add_trace_repr_layout(
        fig, munchify(simplified_soil_layout.serialize()), nb_columns=1, x_name="1D rep. gesimplificeerde layout"
    )

    fig.update_layout(barmode="stack", template="plotly_white", legend=dict(x=1.10, y=0.5))

    return fig.to_json()


def visualize_leakage_point_layouts(
    tno_soil_layout: SoilLayout,
    classified_soil_layout: SoilLayout,
    segment_params: Munch,
    rep_soil_layout: Optional[SoilLayout] = None,
) -> str:
    unique_user_soil_types = [soil.name for soil in segment_params.input_selection.materials.table]
    fig = make_subplots(
        rows=1,
        cols=2,
        shared_yaxes=True,
        horizontal_spacing=0.00,
        column_widths=[3, 3],
    )
    add_trace_tno_layout(fig, tno_soil_layout, 1)

    add_trace_classified_layout(
        fig, munchify(classified_soil_layout.serialize()), 1, unique_user_soil_types, x_name="Geïnterpreteerd lagen"
    )

    if rep_soil_layout:
        add_trace_repr_layout(fig, munchify(rep_soil_layout.serialize()), nb_columns=2, x_name="Dijkvak")

    fig.update_layout(barmode="stack", template="plotly_white", legend=dict(x=1.10, y=0.5))
    return fig.to_json()


def add_cpt_trace(fig: Figure, cpt: CPT):
    """Add the trace of the cone resistance for the selected CPT"""
    fig.add_trace(
        go.Scatter(
            name="Cone Resistance",
            x=cpt.parsed_cpt.qc,
            y=[el * 1e-3 for el in cpt.parsed_cpt.elevation],
            mode="lines",
            line=dict(color="mediumblue", width=1),
            legendgroup="Cone Resistance",
        ),
        row=1,
        col=1,
    )
    standard_line_options = dict(showline=True, linewidth=2, linecolor="LightGrey")
    fig.update_yaxes(**standard_line_options, dtick=1, showticklabels=True, col=1)


def add_bar_soil_layouts(
    segment_params: Munch, exit_point_params: Munch, fig: Figure, number_columns: int, rep_soil_layout: SoilLayout
):
    """Add the traces for the Soil layouts bar charts:
    - TNO soil layout
    - Saved soil layout of the exit point entity (actual soil layout used for Uplift and heave calculations)
    - Prevision soil layout translated from the user soil layout table.
    - Representative soil layout of the segment at the exit point location.
    """
    unique_user_soil_types = [soil.name for soil in segment_params.input_selection.materials.table]

    # Add bars for each soil type separately in order to be able to set legend labels
    # TNO and user layouts are kept separated so that the legend groups can be distinguished
    add_trace_tno_layout(fig, exit_point_params.tno_soil_layout, number_columns)

    add_trace_classified_layout(
        fig,
        exit_point_params.classified_soil_layout,
        number_columns,
        unique_user_soil_types,
        x_name="Geïnterpreteerd",
    )

    soil_layout_piping = build_combined_rep_and_exit_point_layout(
        exit_point_params.classified_soil_layout, rep_soil_layout
    )

    add_trace_repr_layout(fig, munchify(rep_soil_layout.serialize()), number_columns, "Dijkvak <br>(Stap 1)")
    add_trace_repr_layout(
        fig,
        munchify(soil_layout_piping.serialize()),
        number_columns,
        "Dijkvak <br>(Piping berekening)",
        showlegend=False,
    )

    standard_line_options = dict(showline=True, linewidth=2, linecolor="LightGrey")
    fig.update_yaxes(
        **standard_line_options,
        dtick=1,
        showticklabels=True,
        side="right",
        title="Elevation [m NAP]",
        col=number_columns,
    )
    fig.update_layout(legend=dict(groupclick="toggleitem"))


def add_trace_tno_layout(fig: Figure, tno_soil_layout: SoilLayout, nb_columns: int):
    for ui_name in UNIQUE_TNO_SOIL_TYPES:
        original_layers = [layer for layer in tno_soil_layout.layers if layer.soil.name == ui_name]

        soil_type_layers = [*original_layers]
        fig.add_trace(
            go.Bar(
                name=ui_name,
                x=["TNO"] * len(original_layers),
                y=[-(layer.top_of_layer - layer.bottom_of_layer) for layer in soil_type_layers],
                width=0.5,
                marker=dict(
                    color=[f"rgb{Color(*layer.soil.color).rgb}" for layer in soil_type_layers],
                    pattern_shape=["/" for layer in soil_type_layers if layer.properties.get("aquifer")],
                ),
                hovertext=[
                    f"Grondsoort: {layer.soil.name}<br>"
                    f"Bovenkant laag: {layer.top_of_layer:.2f} m NAP<br>"
                    f"Onderkant laag: {layer.bottom_of_layer:.2f} m NAP<br>"
                    f"Horizontale doorlatendheid: {layer.properties.horizontal_permeability:.2f} m/d<br>"
                    f"Verticale doorlatendheid: {layer.properties.vertical_permeability:.2f} m/d<br>"
                    f"Kans op veen: {layer.properties.kans_1_veen:.2f} %<br>"
                    f"Kans op klei: {layer.properties.kans_2_klei:.2f} %<br>"
                    f"Kans op zandige klei: {layer.properties.kans_3_kleiig_zand:.2f} %<br>"
                    f"Kans op los gepakt zand: {layer.properties.kans_5_zand_fijn:.2f} %<br>"
                    f"Kans op matig gepakt zand: {layer.properties.kans_6_zand_matig_grof:.2f} %<br>"
                    f"Kans op vast gepakt zand: {layer.properties.kans_7_zand_grof:.2f} %"
                    for layer in soil_type_layers
                ],
                hoverinfo="text",
                legendgroup="TNO",
                legendgrouptitle_text="TNO lagen",
                base=[layer.top_of_layer for layer in soil_type_layers],
            ),
            col=nb_columns,
            row=1,
        )


def add_trace_repr_layout(fig: Figure, representative_layout, nb_columns: int, x_name: str, showlegend: bool = True):
    for ui_name in ["cover_layer", "first_aquifer", "intermediate_aquitard", "second_aquifer"]:
        representative_layers = [layer for layer in representative_layout.layers if layer.soil.name == ui_name]
        layer_type_name = representative_layers[0].soil.properties.ui_name if representative_layers else None
        try:
            hovertext = [
                f"Grondsoort: {layer.soil.name}<br>"
                f"Bovenkant laag: {layer.top_of_layer:.2f}<br>"
                f"Onderkant laag: {layer.bottom_of_layer:.2f}<br>"
                f"Verticale doorlatendheid: {layer.properties.get('vertical_permeability'):.2f} m/d<br>"
                f"Horizontale doorlatendheid: {layer.properties.get('horizontal_permeability'):.2f} m/d<br>"
                f"Gewicht droog: {layer.properties.get('gamma_dry'):.1f} kN/m3<br>"
                f"Gewicht nat: {layer.properties.get('gamma_wet'):.1f} kN/m3<br>"
                f"d70: {layer.properties.get('grain_size_d70')} mm"
                for layer in representative_layers
            ]
        except TypeError:
            hovertext = [
                f"Grondsoort: {layer.soil.name}<br>"
                f"Bovenkant laag: {layer.top_of_layer:.2f}<br>"
                f"Onderkant laag: {layer.bottom_of_layer:.2f}<br>"
                f"Verticale doorlatendheid: {layer.properties.get('vertical_permeability')} m/d<br>"
                f"Horizontale doorlatendheid: {layer.properties.get('horizontal_permeability')} m/d<br>"
                f"Gewicht droog: {layer.properties.get('gamma_dry')} kN/m3<br>"
                f"Gewicht nat: {layer.properties.get('gamma_wet')} kN/m3<br>"
                f"d70: {layer.properties.get('grain_size_d70')} mm"
                for layer in representative_layers
            ]
        fig.add_trace(
            go.Bar(
                name=layer_type_name,
                x=[x_name] * len(representative_layers),
                y=[-(layer.top_of_layer - layer.bottom_of_layer) for layer in representative_layers],
                width=0.5,
                marker=dict(
                    color=[f"rgb{Color(*layer.soil.color).rgb}" for layer in representative_layers],
                    pattern_shape=["/" if layer.properties.get("aquifer") else "" for layer in representative_layers],
                ),
                hovertext=hovertext,
                hoverinfo="text",
                legendgroup="representative_layout",
                legendgrouptitle_text="Dijvak",
                showlegend=showlegend,
                base=[layer.top_of_layer for layer in representative_layers],
            ),
            col=nb_columns,
            row=1,
        )


def add_trace_classified_layout(
    fig: Figure,
    soil_layout: Munch,
    nb_columns: int,
    unique_user_soil_types,
    x_name: str = "saved_layout",
    showlegend=True,
):
    """Add traces for the classified soil layouts:
    - the saved layout of the exit point
    - the prevision soil layout translated from the user table.
    """

    for ui_name in unique_user_soil_types:
        soil_type_layers = [layer for layer in soil_layout.layers if layer.soil.name == ui_name]
        fig.add_trace(
            go.Bar(
                name=ui_name,
                x=[x_name] * len(soil_type_layers),
                y=[-(layer.top_of_layer - layer.bottom_of_layer) for layer in soil_type_layers],
                width=0.5,
                marker=dict(
                    color=[f"rgb{Color(*layer.soil.color).rgb}" for layer in soil_type_layers],
                    pattern_shape=["/" if layer.properties.get("aquifer") else "" for layer in soil_type_layers],
                ),
                hovertext=[
                    f"Grondsoort: {layer.soil.name}<br>"
                    f"Bovenkant laag: {layer.top_of_layer:.2f}<br>"
                    f"Onderkant laag: {layer.bottom_of_layer:.2f}"
                    for layer in soil_type_layers
                ],
                hoverinfo="text",
                legendgroup="user_defined_layout",
                legendgrouptitle_text="Geïnterpreteerd lagen",
                showlegend=showlegend,
                base=[layer.top_of_layer for layer in soil_type_layers],
            ),
            col=nb_columns,
            row=1,
        )
