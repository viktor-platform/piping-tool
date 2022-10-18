import unittest

from shapely.geometry import LineString
from shapely.geometry import Point

from app.lib.shapely_helper_functions import get_exit_point_projection_on_entry_line


class TestShapelyHelper(unittest.TestCase):
    """Tests if the transformation between RD and the local reference frame are correct,
    these are used for creating grid points for instance"""

    def test_get_exit_point_projection_on_entry_line(self):
        exit_point = Point(0, 0)
        dike_trajectory = LineString([Point(10, -1), Point(10, 0), Point(10, 1)])
        entry_line = LineString([Point(20, -1), Point(20, 0), Point(20, 1)])
        extension = 10
        expected_result = Point(30, 0)

        calculated_results = get_exit_point_projection_on_entry_line(exit_point, dike_trajectory, entry_line, extension)
        self.assertIsInstance(calculated_results, Point)
        self.assertAlmostEqual(expected_result.x, calculated_results.x)
        self.assertAlmostEqual(expected_result.y, calculated_results.y)
