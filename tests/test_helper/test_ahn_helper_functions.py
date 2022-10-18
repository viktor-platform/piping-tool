import unittest
from unittest.mock import MagicMock

import numpy as np
import pandas as pd

import app
from app.lib.ahn.ahn_helper_functions import fetch_ahn_z_values
from app.lib.shapely_helper_functions import get_unity_check_color
from app.lib.shapely_helper_functions import intersect_soil_layout_table_with_z
from viktor import Color
from viktor.geo import Soil
from viktor.geo import SoilLayer
from viktor.geo import SoilLayout


class TestAHNHelperFunctions(unittest.TestCase):
    def test_intersect_soil_layout_table_with_ahn(self):
        soil_layout = SoilLayout(
            [
                SoilLayer(
                    top_of_layer=-5, properties={}, soil=Soil(name="Zand grof", color=Color.red()), bottom_of_layer=0
                ),
                SoilLayer(top_of_layer=-8, properties={}, soil=Soil(name="clay", color=Color.red()), bottom_of_layer=0),
                SoilLayer(
                    top_of_layer=-10, properties={}, soil=Soil(name="peat", color=Color.red()), bottom_of_layer=0
                ),
            ]
        )

        z = -2
        soil_layout_table_mod = intersect_soil_layout_table_with_z(soil_layout, z)
        assert soil_layout_table_mod.layers[0].top_of_layer == z
        assert soil_layout_table_mod.layers[0].soil.name == "Zand grof"

        z = -6
        soil_layout_table_mod = intersect_soil_layout_table_with_z(soil_layout, z)

        assert soil_layout_table_mod.layers[0].top_of_layer == z
        assert soil_layout_table_mod.layers[0].soil.name == "Zand grof"

        z = -8.5
        soil_layout_table_mod = intersect_soil_layout_table_with_z(soil_layout, z)

        assert soil_layout_table_mod.layers[0].top_of_layer == z
        assert soil_layout_table_mod.layers[0].soil.name == "clay"

    def test_get_unity_check_color(self):
        unity_checks_1 = [0.5, 1.1]
        unity_checks_2 = [1.5, 0.7]
        unity_checks_3 = [1.5, 1.7]
        unity_checks_4 = [0.5, 0.7]
        assert get_unity_check_color(unity_checks_1) == Color.green()
        assert get_unity_check_color(unity_checks_2) == Color.green()
        assert get_unity_check_color(unity_checks_3) == Color.green()
        assert get_unity_check_color(unity_checks_4) == Color.red()

    def test_fetch_z_values(self) -> None:
        """
        Check the function fetch_z_values with 2 points.
        """
        img_array = np.array(
            [
                [2.822, 2.811, 2.826, 2.814, 2.807, 2.81],
                [2.81, 2.827, 2.809, 2.799, 2.819, 2.782],
                [2.801, 2.82, 2.795, 2.802, 2.826, 2.817],
                [2.806, 2.815, 2.8, 2.802, 2.811, 2.805],
                [2.818, 2.814, 2.799, 2.795, 2.798, 2.796],
                [2.808, 2.802, 2.818, 2.812, 2.806, 2.829],
            ]
        )
        app.lib.ahn.ahn_helper_functions.request_data = MagicMock(return_value=img_array)

        data_points = pd.DataFrame(
            {"x": [158014.2294224724, 158015.10290132507], "y": [418222.5674693175, 418223.5674693175]}
        )
        res = fetch_ahn_z_values(data_points)
        assert len(res["z"]) == 2

    def test_single_point(self):
        """
        Check that the AHN value at (82194.68, 437740.98) == 2.435 at ahn3_05m_dtm
        This point has been checked manually.
        """
        img_array = np.array(
            [
                [2.39, 2.352, 2.432, 2.377],
                [2.384, 2.36, 2.435, 2.455],
                [2.465, 2.396, 2.501, 2.486],
                [2.474, 2.438, 2.47, 2.507],
            ]
        )
        app.lib.ahn.ahn_helper_functions.request_data = MagicMock(return_value=img_array)

        point = (82194.68, 437740.98)
        z = 2.435
        data_points = pd.DataFrame({"x": [point[0]], "y": [point[1]]})
        res = fetch_ahn_z_values(data_points)
        assert np.isclose(res["z"][0], z)
