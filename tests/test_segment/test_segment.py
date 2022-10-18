# pylint: disable-all
import unittest
from unittest import TestCase
from unittest.mock import MagicMock
from unittest.mock import patch

import numpy as np
from munch import munchify

import app
from app.dyke.dyke_model import Dyke
from app.ground_model.tno_model import TNOGroundModel
from app.segment.controller import Controller as SegmentController
from app.segment.segment_model import Segment
from app.segment.segmentAPI import SegmentAPI
from tests.fixtures.mocked_files import DITCH_ENTITIES
from tests.fixtures.mocked_files import DYKES_ENTITIES
from tests.fixtures.mocked_files import ENTRY_LINE_ENTITIES
from tests.fixtures.mocked_files import EXIT_POINT_ENTITIES
from tests.fixtures.mocked_files import SEGMENT_ENTITIES
from tests.fixtures.mocked_files import STE_GROUND_MODEL_ENTITY
from tests.fixtures.mocked_files import STE_GROUND_MODEL_FILE
from tests.test_segment.fixtures_segment import DETAILED_REP_SOIL_LAYOUT_1
from tests.test_segment.fixtures_segment import DETAILED_REP_SOIL_LAYOUT_2
from tests.test_segment.fixtures_segment import SCENARIO_EXCEL_RESULTS
from tests.test_segment.fixtures_segment import SIMPLIFIED_REP_SOIL_LAYOUT_1
from tests.test_segment.fixtures_segment import SIMPLIFIED_REP_SOIL_LAYOUT_2
from viktor import File
from viktor.geo import SoilLayout
from viktor.result import DownloadResult
from viktor.result import SetParamsResult
from viktor.views import MapAndDataResult
from viktor.views import MapResult
from viktor.views import PlotlyResult

EXIT_POINT_PARAMS = EXIT_POINT_ENTITIES[0].last_saved_params


def get_representative_soil_layouts_mock(*args):
    return SoilLayout.from_dict(DETAILED_REP_SOIL_LAYOUT_1), SoilLayout.from_dict(SIMPLIFIED_REP_SOIL_LAYOUT_1)


def get_representative_soil_layouts_mock_2(*args):
    return SoilLayout.from_dict(DETAILED_REP_SOIL_LAYOUT_2), SoilLayout.from_dict(SIMPLIFIED_REP_SOIL_LAYOUT_2)


def get_selected_exit_point_params_mock(*args):
    return munchify(EXIT_POINT_PARAMS)


class TestSegmentController(TestCase):
    """This class tests the Controller of the Segment entity type"""

    controller_type = SegmentController
    default_entity = SEGMENT_ENTITIES[0]

    def setUp(self) -> None:
        """This setup function is automatically called before every test.

        It will set-up the default params and controller with default mocked functions
        """
        # Load relevant test data
        self.params = self.default_entity.last_saved_params
        self.entity_id = 1
        dyke_params = DYKES_ENTITIES[0].last_saved_params
        entry_line_params = ENTRY_LINE_ENTITIES[0].last_saved_params
        ditch_data_params = DITCH_ENTITIES[0].last_saved_params
        tno_ground_model_params = STE_GROUND_MODEL_ENTITY.last_saved_params

        # Mock API calls
        self.controller = self.controller_type(params=self.params)
        api = SegmentAPI(self.entity_id)
        api.get_dyke = MagicMock(return_value=Dyke(params=dyke_params))
        api.get_tno_ground_model = MagicMock(
            return_value=TNOGroundModel(tno_ground_model_params, STE_GROUND_MODEL_FILE)
        )
        api.create_exit_point_entity = MagicMock(return_value=None)
        api.update_exit_point_properties = MagicMock(return_value=None)
        api.get_all_children_exit_point_entities = MagicMock(return_value=EXIT_POINT_ENTITIES)
        api.get_ditches = MagicMock(return_value=ditch_data_params)
        api.create_exit_point_entity = MagicMock(return_value=None)
        api.update_exit_point_properties = MagicMock(return_value=None)
        api.get_cpt_folder_from_parent = MagicMock(return_value=None)
        api.get_borehole_folder_from_parent = MagicMock(return_value=None)
        api.segment_name = MagicMock(return_value="PLACEHOLDER_NAME")
        self.controller.get_api = MagicMock(return_value=api)

    def tearDown(self) -> None:
        """This setup function is automatically called after every test.

        It will the previously set-up variable to ensure that no state is stored
        """
        self.params = None
        self.controller = None

    ####################################################################################################################
    #                                                   STEP 1                                                         #
    ####################################################################################################################
    def test_map_ditch_selection_returns_MapResult(self):
        """Test that the visualize_map function returns a MapResult"""
        # Act
        result = self.controller.map_ditch_selection(self.controller, self.params, self.entity_id)

        # Assert
        self.assertIsInstance(result, MapResult)

    def test_visualize_ground_model_along_segment_return_PlotlyResult(self):
        # Act
        result = self.controller.visualize_ground_model_along_segment(self.controller, self.params, self.entity_id)

        # Asser
        self.assertIsInstance(result, PlotlyResult)

    @patch("app.segment.controller.get_representative_soil_layouts", get_representative_soil_layouts_mock)
    def test_visualize_representative_layout_return_PlotlyResult(self):
        # Act
        result = self.controller.visualize_representative_layout(self.controller, self.params, self.entity_id)

        # Assert
        self.assertIsInstance(result, PlotlyResult)

    @patch("app.segment.controller.get_representative_soil_layouts", get_representative_soil_layouts_mock)
    def test_calculate_effective_aquifer_properties_return_SetParamsResult(self):
        # Act
        result = self.controller.calculate_effective_aquifer_properties(self.params, self.entity_id)

        # Assert
        self.assertIsInstance(result, SetParamsResult)

    def fetch_soil_layout_at_location_returns_SetParamsResult(self):
        # Act
        result = self.controller.fetch_soil_layout_at_location(self.params, self.entity_id)

        # Assert
        self.assertIsInstance(result, SetParamsResult)

    ####################################################################################################################
    #                                                   STEP 2                                                         #
    ####################################################################################################################

    def test_map_map_leakage_length_1_returns_MapAndDataResult(self):
        # Act
        result = self.controller.map_leakage_length_1(self.controller, self.params, self.entity_id)

        # Assert
        self.assertIsInstance(result, MapAndDataResult)

    def test_map_map_leakage_length_2_returns_MapAndDataResult(self):
        # Act
        result = self.controller.map_leakage_length_2(self.controller, self.params, self.entity_id)

        # Assert
        self.assertIsInstance(result, MapAndDataResult)

    def test_leakage_point_soil_visualisation(self):
        # Act
        result = self.controller.visualise_soil_leakage_point(self.controller, self.params, self.entity_id)

        # Assert
        self.assertIsInstance(result, PlotlyResult)

    ####################################################################################################################
    #                                                   STEP 3                                                         #
    ####################################################################################################################

    def test_map_exit_point_creation_returns_MapResult(self):
        # Act
        result = self.controller.map_exit_point_creation(self.controller, self.params, self.entity_id)

        # Assert
        self.assertIsInstance(result, MapResult)

    def test_create_exit_point_entities_returns_SetParamsResult(self):
        """ """
        img_array = np.genfromtxt("./tests/fixtures/ahn_points.csv", delimiter=",")

        app.lib.ahn.ahn_helper_functions.request_data = MagicMock(return_value=img_array)
        # Act
        result = self.controller.create_exit_point_entities(self.params, self.entity_id)

        # Assert
        self.assertIsInstance(result, SetParamsResult)

    ####################################################################################################################
    #                                                   STEP 4                                                         #
    ####################################################################################################################

    @patch("app.segment.controller.get_selected_exit_point_params", get_selected_exit_point_params_mock)
    @patch("app.segment.controller.get_representative_soil_layouts", get_representative_soil_layouts_mock)
    def test_compare_soil_layouts_returns_PlotlyResult(self):
        """Test that the compare_soil_layouts view returns a PlotlyResult"""
        # Act
        result = self.controller.compare_soil_layouts(self.controller, self.params, self.entity_id)

        # Assert
        self.assertIsInstance(result, PlotlyResult)

    @patch("app.segment.controller.get_representative_soil_layouts", get_representative_soil_layouts_mock)
    def test_visualize_piping_results_returns_MapResult(self):
        """ """
        # Act
        result = self.controller.visualize_piping_results(self.controller, self.params, self.entity_id)

        # Assert
        self.assertIsInstance(result, MapResult)

    @unittest.skip("to be re-adapted")
    def test_generate_piping_results(self):
        # Act
        results = self.controller.generate_piping_results(
            self.params, self.entity_id, scenario=munchify(SCENARIO_EXCEL_RESULTS)
        )

        # Assert
        self.assertIsInstance(results, File)

    def test_download_piping_results_returns_DownloadResult(self):
        # Act
        results = self.controller.download_piping_results(self.params, self.entity_id)

        # Assert
        self.assertIsInstance(results, DownloadResult)

    ####################################################################################################################
    #                                                 OTHERS                                                           #
    ####################################################################################################################
    def test_create_segment_model(self):
        segment_model = self.controller.get_segment(self.entity_id, self.params)
        self.assertIsInstance(segment_model, Segment)

    def test_local_unit_vectors(self):
        """test that the local unit vectors based on the local reference frame are correct"""
        # act
        segment_model = self.controller.get_segment(self.entity_id, self.params)
        parallel_vector = segment_model.parallel_unit_vector
        perp_vector = segment_model.perpendicular_unit_vector

        # assert
        self.assertAlmostEqual(np.linalg.norm(perp_vector), 1)  # it's actually a unit vector
        self.assertAlmostEqual(perp_vector[0], 0.15125452)  # it's the correct unit vector
        self.assertAlmostEqual(perp_vector[1], 0.98849484)

        self.assertAlmostEqual(np.linalg.norm(parallel_vector), 1)  # it's actually a unit vector
        self.assertAlmostEqual(parallel_vector[0], 0.988494849)  # it's the correct unit vector
        self.assertAlmostEqual(parallel_vector[1], -0.15125452)

    def test_transformation_to_local_coordinates(self):
        """test that the transformation from RD to local coordinates works"""
        # arrange
        segment_model = self.controller.get_segment(self.entity_id, self.params)
        origin_in_rd = np.array([125742.12570581288, 441799.2224608529])  # origin local coordinate system in RD
        point1 = np.array([125741.89348359889, 441804.31618962885])  # point that should have local coordinates -1, 5

        # act
        origin_in_lc = segment_model.transform_rd_to_local_coordinates(origin_in_rd)
        point1_in_lc = segment_model.transform_rd_to_local_coordinates(point1)

        # assert no distorsion on lengths
        self.assertAlmostEqual(np.linalg.norm(point1_in_lc), np.linalg.norm(np.array([-1, 5])))

        # assert the correct point is found
        self.assertAlmostEqual(origin_in_lc[0], 0)
        self.assertAlmostEqual(origin_in_lc[1], 0)

        self.assertAlmostEqual(point1_in_lc[0], -1)
        self.assertAlmostEqual(point1_in_lc[1], 5)

    def test_transformation_RD_coordinates(self):
        """test that the transformation from local coordinates to RD works"""
        # arrange
        segment_model = self.controller.get_segment(self.entity_id, self.params)
        origin = np.array([0, 0])  # point that should have RD coordinates [125740, 441799]
        point = np.array([-1, 5])  # point that should have RD coordinates [125739, 441804]

        # act
        origin_in_rd = segment_model.transform_local_coordinates_to_rd(origin)
        point_in_rd = segment_model.transform_local_coordinates_to_rd(point)

        # assert the correct point is found
        self.assertAlmostEqual(origin_in_rd[0], 125742.12570581288)
        self.assertAlmostEqual(origin_in_rd[1], 441799.2224608529)

        self.assertAlmostEqual(point_in_rd[0], 125741.89348359889)
        self.assertAlmostEqual(point_in_rd[1], 441804.31618962885)
