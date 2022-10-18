from io import StringIO

import numpy as np
import pandas as pd
from munch import Munch
from shapely.geometry import MultiPoint

from app.ground_model.parametrization import GroundModelParametrization
from viktor import Color
from viktor import File
from viktor import ParamsFromFile
from viktor import ViktorController
from viktor.geometry import GeoPoint
from viktor.geometry import GeoPolygon
from viktor.views import MapPolygon
from viktor.views import MapResult
from viktor.views import MapView


class Controller(ViktorController):
    """
    Controller to show embankment designs
    """

    label = "3D Grond model"
    parametrization = GroundModelParametrization

    @ParamsFromFile(file_types=[".csv"], max_size=int(200e6))
    def process_file(self, file: File, entity_id: int, **kwargs) -> dict:
        """Process the TNO Groundmodel as convex_hull csv file as it is uploaded to the application.
        Max_size successfully uploaded: 117MB (March 2022)
        Max_size test: 407 MB (Out Of memory Error, Marche 2022)
        """
        file_content = file.getvalue("utf-8")
        # Trying to gain some RAM importing only x, y coodinates amd changing the dtype
        df = pd.read_csv(StringIO(file_content), usecols=["x", "y"], dtype={"Ward Number ": "int8"})

        # Get convex_hull list with all the unique locations (x,y) in the csv
        data = df.drop_duplicates(["x", "y"]).values
        convex_hull_coordinates = MultiPoint(data).convex_hull.exterior.coords.xy

        # Get chainage resolution
        df = df.sort_values("x")
        unique_x_list = np.unique(np.array(df["x"]))
        df = df.sort_values("y")
        unique_y_list = np.unique(np.array(df["y"]))
        x_diff = abs(unique_x_list[0] - unique_x_list[1])
        y_diff = abs(unique_y_list[0] - unique_y_list[1])
        chainage_length = max(x_diff, y_diff)

        return {
            "data": data,
            "convex_hull": GeoPolygon(*[GeoPoint.from_rd(pt) for pt in list(zip(*convex_hull_coordinates))]),
            "chainage_length": chainage_length,
        }

    @MapView("Map", duration_guess=1)
    def visualization(self, params: Munch, entity_id: int, **kwargs):
        """Visualise the convex hull of the current and the siblings ground models"""
        polygon_feature = []

        # Add covered area of the current ground model
        polygon_feature.append(MapPolygon.from_geo_polygon(params.convex_hull, color=Color.blue()))

        return MapResult([*polygon_feature])
