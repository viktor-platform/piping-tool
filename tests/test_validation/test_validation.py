# pylint: disable-all
from unittest import TestCase

from app.piping_tool.constants import GAMMA_W
from app.piping_tool.PipingCalculationUtilities import PipingCalculation
from app.segment.controller import Controller as SegmentController
from tests.fixtures.mocked_files import EXIT_POINT_ENTITIES
from tests.test_validation.input_data import piping_parameters_ditch_1
from tests.test_validation.input_data import uplift_parameters_exit_point_28_first_aquifer
from tests.test_validation.input_data import uplift_parameters_exit_point_28_second_aquifer

EXIT_POINT_PARAMS = EXIT_POINT_ENTITIES[0].last_saved_params


class TestValidationPipingResults(TestCase):
    """Test if the piping results returned from the application are still correct.
    The default data has been used for validation of the application by Daniel Kentrop (RPS). If the tests below are
    failing, then the calculations from the application are deviating from what they should return.
    """

    controller_type = SegmentController

    def setUp(self) -> None:
        """This setup function is automatically called before every test.

        It will set-up the default params and controller with default mocked functions
        """

        uplift_parameters_28_first_aq = uplift_parameters_exit_point_28_first_aquifer
        uplift_parameters_28_second_aq = uplift_parameters_exit_point_28_second_aquifer
        self.piping_calculation_class_28_first_aquifer = PipingCalculation.from_parameter_set(
            uplift_parameters_28_first_aq
        )
        self.piping_calculation_class_28_second_aquifer = PipingCalculation.from_parameter_set(
            uplift_parameters_28_second_aq
        )
        self.piping_calculation_class_ditch = PipingCalculation.from_parameter_set(piping_parameters_ditch_1)

    def tearDown(self) -> None:
        """This setup function is automatically called after every test.

        It will the previously set-up variable to ensure that no state is stored
        """
        self.params = None
        self.controller = None

    def test_exit_point_28_first_aquifer(self):
        cover_thickness = self.piping_calculation_class_28_first_aquifer.get_cover_layer_properties["thickness"]
        potential_uplift = self.piping_calculation_class_28_first_aquifer.calc_uplift_critical_potential_difference
        water_level_exit_point = self.piping_calculation_class_28_first_aquifer.calc_h_exit
        aquifer_hydraulic_head = self.piping_calculation_class_28_first_aquifer.calc_phi_exit
        sellmeijer_head_diff = self.piping_calculation_class_28_first_aquifer.calc_critical_head_difference_sellmeijer
        seepage_length = self.piping_calculation_class_28_first_aquifer.distance_from_entry_line
        f_1, f_2, f_3 = (
            self.piping_calculation_class_28_first_aquifer.calc_f_resistance,
            self.piping_calculation_class_28_first_aquifer.calc_f_scale,
            self.piping_calculation_class_28_first_aquifer.calc_f_geometry,
        )
        uplift_uc = self.piping_calculation_class_28_first_aquifer.uplift_unity_check
        heave_uc = self.piping_calculation_class_28_first_aquifer.heave_unity_check
        sellmeijer_uc = self.piping_calculation_class_28_first_aquifer.backward_erosion_unity_check

        self.assertEqual(cover_thickness, 12.314)
        self.assertEqual(aquifer_hydraulic_head, 4.36)
        self.assertEqual(water_level_exit_point, 3.439)
        self.assertEqual(potential_uplift, 6.552972477064219)
        self.assertEqual(uplift_uc, 7.115062407235849)
        self.assertEqual(heave_uc, 4.0110749185667744)
        self.assertEqual(f_1, 0.3109082586942976)
        self.assertEqual(f_2, 0.23145649818264458)
        self.assertEqual(f_3, 1.16936217325768)
        self.assertEqual(seepage_length, 57.671996701324574)
        self.assertEqual(sellmeijer_head_diff, 4.853060052401508)
        self.assertEqual(sellmeijer_uc, 485.3060052401508)

    def test_exit_point_28_second_aquifer(self):
        cover_thickness = self.piping_calculation_class_28_second_aquifer.get_cover_layer_properties["thickness"]
        potential_uplift = self.piping_calculation_class_28_second_aquifer.calc_uplift_critical_potential_difference
        water_level_exit_point = self.piping_calculation_class_28_second_aquifer.calc_h_exit
        aquifer_hydraulic_head = self.piping_calculation_class_28_second_aquifer.calc_phi_exit
        sellmeijer_head_diff = self.piping_calculation_class_28_second_aquifer.calc_critical_head_difference_sellmeijer
        seepage_length = self.piping_calculation_class_28_second_aquifer.distance_from_entry_line
        f_1, f_2, f_3 = (
            self.piping_calculation_class_28_second_aquifer.calc_f_resistance,
            self.piping_calculation_class_28_second_aquifer.calc_f_scale,
            self.piping_calculation_class_28_second_aquifer.calc_f_geometry,
        )
        uplift_uc = self.piping_calculation_class_28_second_aquifer.uplift_unity_check
        heave_uc = self.piping_calculation_class_28_second_aquifer.heave_unity_check
        sellmeijer_uc = self.piping_calculation_class_28_second_aquifer.backward_erosion_unity_check

        self.assertEqual(cover_thickness, 37.314)
        self.assertEqual(aquifer_hydraulic_head, 4.36)
        self.assertEqual(water_level_exit_point, 3.439)
        self.assertEqual(potential_uplift, 29.361331294597345)
        self.assertEqual(uplift_uc, 31.879838539193635)
        self.assertAlmostEqual(heave_uc, 12.1543973941368)
        self.assertAlmostEqual(f_1, 0.3109082586942976)
        self.assertAlmostEqual(f_2, 0.25864194091236)
        self.assertAlmostEqual(f_3, 1.51199553654247)
        self.assertAlmostEqual(seepage_length, 57.671996701324574)
        self.assertAlmostEqual(sellmeijer_head_diff, 7.01207747491458)
        self.assertAlmostEqual(sellmeijer_uc, 701.207747491458)

    def test_piping_result_with_ditch_1(self):
        cover_thickness = self.piping_calculation_class_ditch.get_cover_layer_properties["thickness"]
        uplift_uc = self.piping_calculation_class_ditch.uplift_unity_check
        heave_uc = self.piping_calculation_class_ditch.heave_unity_check
        sellmeijer_uc = self.piping_calculation_class_ditch.backward_erosion_unity_check

        self.assertAlmostEqual(cover_thickness, 0.875)
        self.assertEqual(uplift_uc, 0.14063997696714567)
        self.assertAlmostEqual(heave_uc, 0.05833333333333335)
        self.assertAlmostEqual(sellmeijer_uc, 3.13634757833764)
