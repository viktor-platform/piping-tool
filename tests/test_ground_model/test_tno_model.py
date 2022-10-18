import json
from pathlib import Path
from unittest import TestCase

from app.ground_model.tno_model import agglomerate_tno_layers
from viktor.geo import SoilLayout


class TestTNOGroundModel(TestCase):
    def test_agglomerate_tno_layers(self):
        soil_layout_1 = Path(__file__).parent / "soil_layout_fixtures.json"
        with open(soil_layout_1, "r") as json_file:
            soil_layout = json.load(json_file)
            res_soil_layout_layers = agglomerate_tno_layers(SoilLayout.from_dict(soil_layout)).layers

            self.assertEqual(res_soil_layout_layers[0].bottom_of_layer, 1.375)
            self.assertEqual(res_soil_layout_layers[0].top_of_layer, 5.125)
