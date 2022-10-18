import json
import unittest
from pathlib import Path

from app.ditch.model import Ditch
from app.lib.helper_read_files import process_ditch_shape_file
from viktor import File


class TestMyEntityController(unittest.TestCase):
    @unittest.skip("params is too large")
    def test_process_file(self):
        path_zip = Path(__file__).parent.parent / "fixtures/ditches.zip"
        file = File.from_path(path_zip)
        returned_dict = process_ditch_shape_file(file)

        path_output = Path(__file__).parent / "params_ditch.json"
        with open(path_output, "r") as json_file:
            data = json.load(json_file)
            self.assertDictEqual(returned_dict, data)


class TestDitchModel(unittest.TestCase):
    def test_case_1(self) -> None:
        left_point_top = {"x": 2, "z": 0}
        left_point_bottom = {"x": 3, "z": -2}
        right_point_bottom = {"x": 5, "z": -2}
        right_point_top = {"x": 6, "z": -1}
        z_aquifer = -5
        ditch = Ditch(left_point_top, left_point_bottom, right_point_bottom, right_point_top, True, talu_slope=1)

        assert ditch.large_b == 3.5
        assert ditch.small_b == 2
        assert ditch.h1(z_aquifer) == 4
        assert ditch.h2(z_aquifer) == 3
        assert ditch.h3(z_aquifer) == 4

    def test_case_2(self) -> None:
        left_point_top = {"x": 2, "z": 0}
        left_point_bottom = {"x": 3, "z": -2}
        right_point_bottom = {"x": 5, "z": -2}
        right_point_top = {"x": 6, "z": 0}
        z_aquifer = -5
        ditch = Ditch(left_point_top, left_point_bottom, right_point_bottom, right_point_top, True, talu_slope=2)
        print(ditch.h3(z_aquifer))

        assert ditch.large_b == 4
        assert ditch.small_b == 2
        assert ditch.h1(z_aquifer) == 5
        assert ditch.h2(z_aquifer) == 3
        assert ditch.h3(z_aquifer) == 5

    def test_case_3(self) -> None:
        left_point_top = {"x": 2, "z": -1}
        left_point_bottom = {"x": 3, "z": -2}
        right_point_bottom = {"x": 5, "z": -2}
        right_point_top = {"x": 6, "z": 0}
        z_aquifer = -5
        ditch = Ditch(left_point_top, left_point_bottom, right_point_bottom, right_point_top, True, talu_slope=2)
        print(ditch.h3(z_aquifer))
        assert ditch.large_b == 3.5
        assert ditch.small_b == 2
        assert ditch.h1(z_aquifer) == 5
        assert ditch.h2(z_aquifer) == 3
        assert ditch.h3(z_aquifer) == 4
