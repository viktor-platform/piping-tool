from io import StringIO

import plotly.graph_objects as go
from munch import Munch
from pygef import Bore

from app.lib.plotly_2d_profile_helper_functions import add_borehole_soil_table
from viktor import ViktorController
from viktor.core import File
from viktor.core import ParamsFromFile
from viktor.views import WebResult
from viktor.views import WebView

from .parametrization import BoreParametrization


class Controller(ViktorController):
    label = "Boring"
    parametrization = BoreParametrization

    @ParamsFromFile(file_types=[".gef"])
    def process_file(self, file: File, entity_id: int, **kwargs) -> dict:
        """Process the CPT file when it is first uploaded"""
        bore = Bore(content=dict(file_type="gef", string=file.getvalue()))
        soil_table = bore.df.to_pandas()
        soil_table["top_nap"] = [bore.zid - top for top in soil_table["depth_top"]]
        soil_table["bottom_nap"] = [bore.zid - bottom for bottom in soil_table["depth_bottom"]]
        soil_table["loam_component"] = soil_table["loam_component"] + soil_table["silt_component"]
        soil_table = soil_table[
            [
                "top_nap",
                "bottom_nap",
                "soil_code",
                "gravel_component",
                "sand_component",
                "clay_component",
                "loam_component",
                "peat_component",
            ]
        ]
        return {
            "x_rd": bore.x,
            "y_rd": bore.y,
            "z": bore.zid,
            "test_id": bore.test_id,
            "soil_table": soil_table.to_dict("records"),
        }

    @WebView("Plot", duration_guess=3)
    def visualize(self, params: Munch, entity_id: int, **kwargs) -> WebResult:
        """Visualizes the borehole plots"""
        soil_table = params.soil_table
        fig = go.Figure()
        fig.update_xaxes(range=[-0.1, 1.1], title_text="Percentage [-]")
        fig.update_yaxes(
            range=[soil_table[-1]["bottom_nap"] - 0.5, soil_table[0]["top_nap"] + 0.5], title_text="z NAP [m]"
        )
        fig = add_borehole_soil_table(fig, soil_table)
        fig.update_shapes(dict(xref="x", yref="y"))

        return WebResult(html=StringIO(fig.to_html()))
