import json
from io import BytesIO
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd
from munch import Munch
from shapely.geometry import MultiPoint

from app.lib.map_view_helper_functions import add_ground_model_hull_to_map_features
from app.models.constants import HULL_FILES
from app.models.constants import SOURCEFILE_DICT
from app.models.parametrization import ModelParametrization
from viktor import Color
from viktor import UserException
from viktor import ViktorController
from viktor.core import progress_message
from viktor.external.generic import GenericAnalysis
from viktor.geometry import GeoPoint
from viktor.geometry import GeoPolygon
from viktor.result import DownloadResult
from viktor.views import MapPolygon
from viktor.views import MapResult
from viktor.views import MapView


class Controller(ViktorController):
    """
    Controller to show embankment designs
    """

    label = "Models folder"
    children = ["GroundModel"]
    show_children_as = "Table"  # or 'Table'
    parametrization = ModelParametrization

    @MapView("Kaart", duration_guess=1)
    def visualization(self, params: Munch, entity_id: int, **kwargs):
        """Visualise the convex hull of the current and the siblings ground models"""

        mapfeatures = []

        if params.csv_cut_polygon:
            csv_polygon_feature = [MapPolygon.from_geo_polygon(params.csv_cut_polygon, color=Color.red())]
            # Add covered area of the selected polygon
            mapfeatures.append(*csv_polygon_feature)

        if params.csv_cutter.model_select:
            # Add covered area of the selected ground model
            hull_csv_filepath = Path(__file__).parent / f"tno_fixtures/{HULL_FILES[params.csv_cutter.model_select]}"

            data = np.genfromtxt(hull_csv_filepath, delimiter=",")
            convex_hull_coordinates = MultiPoint(data).convex_hull.exterior.coords.xy
            convex_hull = GeoPolygon(*[GeoPoint.from_rd(pt) for pt in list(zip(*convex_hull_coordinates))])

            add_ground_model_hull_to_map_features(mapfeatures, convex_hull, color=Color.blue())

        return MapResult(mapfeatures)

    def cut_csv(self, params: Munch, **kwargs) -> DownloadResult:
        """Based on the polygon entered by the user, define a boundary box and use the generic worker on an external
        machine to cut the source files to an appropriate size.
        """
        polygon = params.csv_cut_polygon

        input_dict = {
            "selection_polygon": [point.rd for point in polygon.points],
            "sourcefile": SOURCEFILE_DICT[params.csv_cutter.model_select],
        }

        # Generate the input file(s)
        input_data = BytesIO(json.dumps(input_dict).encode())
        # Run the analysis and obtain the output file.
        output = self.run_generic_worker_csv_cutter(input_data)

        # # Process output file
        df = pd.read_csv(output, sep=",")
        df.drop(df.columns[0], axis=1, inplace=True)

        return DownloadResult(df.to_csv(), f"{params.csv_cutter.file_name}.csv")

    @staticmethod
    def run_generic_worker_csv_cutter(input_file: BytesIO) -> StringIO:
        """Run analysis and obtain output file of csv_cutter"""
        generic_analysis_input = [("input.json", input_file)]
        progress_message("Kan een paar minuten duren.")

        generic_analysis = GenericAnalysis(
            files=generic_analysis_input, executable_key="TNO_csv_cutter", output_filenames=["output.csv"]
        )
        generic_analysis.execute(timeout=600)
        output_file = generic_analysis.get_output_file("output.csv")
        output_df = output_file.getvalue().decode()
        if "Error_file_size_excessive" in output_df:
            raise UserException(
                "De file die je probeert te maken is te groot (> 50mb), probeer een kleinere polygon te maken"
            )

        if not output_file:
            raise UserException("Geen bestand teruggegeven. Externe csv snijder faalt.")

        # get output file
        return StringIO(output_file.getvalue().decode())
