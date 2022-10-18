import unittest
from math import sqrt

import numpy as np

from app.lib.shapely_helper_functions import WaterDirection
from app.lib.shapely_helper_functions import get_unit_vector
from app.lib.shapely_helper_functions import rotate_90_deg


class TestCoordinateTransformations(unittest.TestCase):
    """Tests if the transformation between RD and the local reference frame are correct,
    these are used for creating grid points for instance"""

    def test_rotate_90_deg(self):
        # arrange
        start_point = np.array((0, 0))
        end_point = np.array((0, 1))
        # act
        rotated_counter_clockwise = rotate_90_deg(start_point, end_point, WaterDirection.COUNTER_CLOCKWISE)
        rotated_clockwise = rotate_90_deg(start_point, end_point, WaterDirection.CLOCKWISE)
        # assert
        np.testing.assert_allclose(rotated_counter_clockwise, (-1.0, 0.0))
        np.testing.assert_allclose(rotated_clockwise, (1.0, 0.0))

        # arrange
        start_point = np.array((4, 3))
        end_point = np.array((6, 5))
        # act
        rotated_counter_clockwise = rotate_90_deg(start_point, end_point, WaterDirection.COUNTER_CLOCKWISE)
        rotated_clockwise = rotate_90_deg(start_point, end_point, WaterDirection.CLOCKWISE)
        # assert
        np.testing.assert_allclose(rotated_counter_clockwise, (2.0, 5.0))
        np.testing.assert_allclose(rotated_clockwise, (6.0, 1.0))

    def test_get_unit_vector(self):
        start_point = np.array((4, 3))
        end_point = np.array((8, 7))
        unit_vector = get_unit_vector(start_point, end_point)
        np.testing.assert_allclose(unit_vector, np.array([sqrt(2) / 2, sqrt(2) / 2]))
