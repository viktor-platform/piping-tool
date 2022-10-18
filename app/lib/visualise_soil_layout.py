import plotly.graph_objects as go
from plotly.graph_objs import Figure

from viktor.geo import SoilLayout


def add_soil_layout_to_fig(fig: Figure, soil_layout: SoilLayout, column_number: int, name: str):
    """Add traces for a given soil layout to a plotly figure, for the given color number"""
    unique_soils = set(soil.name for soil in soil_layout.filter_unique_soils())

    for ui_name in unique_soils:
        soil_type_layers = [layer for layer in soil_layout.layers if layer.soil.name == ui_name]
        fig.add_trace(
            go.Bar(
                name=ui_name,
                x=[name] * len(soil_type_layers),
                y=[-(layer.top_of_layer - layer.bottom_of_layer) for layer in soil_type_layers],
                width=0.5,
                marker=dict(
                    color=[f"rgb{layer.soil.color.rgb}" for layer in soil_type_layers],
                ),
                hovertext=[
                    f"Grondsoort: {layer.soil.name}<br>"
                    f"Bovenkant laag: {layer.top_of_layer:.2f}<br>"
                    f"Onderkant laag: {layer.bottom_of_layer:.2f}"
                    for layer in soil_type_layers
                ],
                hoverinfo="text",
                legendgroup=name,
                base=[layer.top_of_layer for layer in soil_type_layers],
            ),
            col=column_number,
            row=1,
        )
        fig.update_layout(showlegend=True)
