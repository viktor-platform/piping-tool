import copy
from unittest import TestCase

from munch import munchify

from app.piping_tool.PipingCalculationUtilities import PipingCalculation
from app.piping_tool.PipingCalculationUtilities import calculate_leakage_length
from tests.test_piping_tool.parameters import PIPING_PARAMETERS
from tests.test_piping_tool.parameters import PIPING_PARAMETERS_DITCH


class TestPipingCalculation(TestCase):
    def setUp(self):
        """This setup function is automatically called before every test.

        It will set-up instantiate PipingCalculation classes with different test cases

        case_1: Cover layer consists of one layer, no ditch, geohydrological level 1 and no probabilistics
        case_2: Cover layer consists of one layer, no ditch, geohydrological level 2 and no probabilistics
        case_ditch_1: Cover layer consists of one layer, ditch, geohydrological level 1 and no probabilistics
        """
        self.piping_calculation_case_1 = PipingCalculation.from_parameter_set(munchify(PIPING_PARAMETERS["case_1"]))
        self.piping_calculation_case_2 = PipingCalculation.from_parameter_set(munchify(PIPING_PARAMETERS["case_2"]))
        self.piping_calculation_case_ditch_1 = PipingCalculation.from_parameter_set(munchify(PIPING_PARAMETERS_DITCH))

    def test_phi_exit_average(self):
        """Unit-test for the average hydraulic head at the exit point"""

        expected_phi_exit_average = PIPING_PARAMETERS["case_1"]["polder_level"]
        calculated_phi_exit_average = self.piping_calculation_case_1.phi_exit_average_hinterland
        self.assertEqual(expected_phi_exit_average, calculated_phi_exit_average)

    def test_h_exit(self):
        """ "Unit-test for the phreatic level at the exit point used for the piping calculations"""

        expected_h_exit_case_1 = 2
        calculated_h_exit_case_1 = self.piping_calculation_case_1.calc_h_exit
        self.assertEqual(expected_h_exit_case_1, calculated_h_exit_case_1)

        # Wet ditch
        calculated_h_exit_case_ditch = self.piping_calculation_case_ditch_1.calc_h_exit
        self.assertEqual(calculated_h_exit_case_ditch, 2)
        # Dry ditch
        piping_calculation_case_ditch_1_dry = copy.deepcopy(self.piping_calculation_case_ditch_1)
        piping_calculation_case_ditch_1_dry.is_ditch_wet = False
        calculated_h_exit_case_ditch = piping_calculation_case_ditch_1_dry.calc_h_exit
        self.assertEqual(calculated_h_exit_case_ditch, 0)

    def test_phi_exit(self):
        """ "Unit-test for the potential at the exit point used for the piping calculations"""

        expected_phi_exit_case_1 = 4.4
        calculated_h_exit_case_1 = self.piping_calculation_case_1.calc_phi_exit
        self.assertEqual(expected_phi_exit_case_1, round(calculated_h_exit_case_1, 2))

        expected_phi_exit_case_2 = 4.49
        calculated_h_exit_case_2 = self.piping_calculation_case_2.calc_phi_exit
        self.assertEqual(expected_phi_exit_case_2, round(calculated_h_exit_case_2, 2))

    def test_uplift_critical_potential(self):
        """ "Unit-test for calculating the critical potential for uplift"""

        expected_potential_case_1 = 1.47
        calculated_potential_case_1 = self.piping_calculation_case_1.calc_uplift_critical_potential_difference
        self.assertEqual(expected_potential_case_1, round(calculated_potential_case_1, 2))

        expected_potential_case_2 = 0.85
        calculated_potential_case_2 = self.piping_calculation_case_2.calc_uplift_critical_potential_difference
        self.assertEqual(expected_potential_case_2, round(calculated_potential_case_2, 2))

    def test_uplift_limit_state(self):
        """ "Unit-test for the limit state function of uplift"""

        expected_z_uplift_case_1 = -0.93
        calculated_z_uplift_case_1 = self.piping_calculation_case_1.uplift_limit_state
        self.assertEqual(expected_z_uplift_case_1, round(calculated_z_uplift_case_1, 2))

    def test_uplift_limit_state_schematisation_factor(self):
        piping_calculation_case_1_schematisation_factor = copy.deepcopy(self.piping_calculation_case_1)
        piping_calculation_case_1_schematisation_factor.schematisation_factor_uplift = 1.3

        expected_z_uplift_case_1 = -1.27
        calculated_z_uplift_case_1 = piping_calculation_case_1_schematisation_factor.uplift_limit_state
        self.assertEqual(expected_z_uplift_case_1, round(calculated_z_uplift_case_1, 2))

    def test_uplift_limit_state_safety_factor(self):
        piping_calculation_case_2_safety_factor = copy.deepcopy(self.piping_calculation_case_2)
        piping_calculation_case_2_safety_factor.safety_factor_uplift = 2.3

        expected_z_uplift_case_2 = -2.12
        calculated_z_uplift_case_2 = piping_calculation_case_2_safety_factor.uplift_limit_state
        self.assertEqual(expected_z_uplift_case_2, round(calculated_z_uplift_case_2, 2))

    def test_uplift_limit_state_schematisation_and_safety_factor(self):
        piping_calculation_case_1_schematisation_and_safety_factor = copy.deepcopy(self.piping_calculation_case_1)
        piping_calculation_case_1_schematisation_and_safety_factor.schematisation_factor_uplift = 1.3
        piping_calculation_case_1_schematisation_and_safety_factor.safety_factor_uplift = 1.8

        expected_z_uplift_case_1 = -1.77
        calculated_z_uplift_case_1 = piping_calculation_case_1_schematisation_and_safety_factor.uplift_limit_state
        self.assertEqual(expected_z_uplift_case_1, round(calculated_z_uplift_case_1, 2))

    def test_uplift_unity_check(self):
        """ "Unit-test for the unity check of uplift"""

        expected_sf_uplift_case_1 = 0.61
        calculated_sf_uplift_case_1 = self.piping_calculation_case_1.uplift_unity_check
        self.assertEqual(expected_sf_uplift_case_1, round(calculated_sf_uplift_case_1, 2))

        expected_sf_uplift_case_2 = 0.34
        calculated_sf_uplift_case_2 = self.piping_calculation_case_2.uplift_unity_check
        self.assertEqual(expected_sf_uplift_case_2, round(calculated_sf_uplift_case_2, 2))

    def test_uplift_unity_check_schematisation_factor(self):
        piping_calculation_case_1_schematisation_factor = copy.deepcopy(self.piping_calculation_case_1)
        piping_calculation_case_1_schematisation_factor.schematisation_factor_uplift = 1.3

        expected_sf_uplift = 0.47
        calculated_sf_uplift = piping_calculation_case_1_schematisation_factor.uplift_unity_check
        self.assertEqual(expected_sf_uplift, round(calculated_sf_uplift, 2))

    def test_uplift_unity_check_safety_factor(self):
        piping_calculation_case_2_safety_factor = copy.deepcopy(self.piping_calculation_case_2)
        piping_calculation_case_2_safety_factor.safety_factor_uplift = 1.9

        expected_sf_uplift = 0.18
        calculated_sf_uplift = piping_calculation_case_2_safety_factor.uplift_unity_check
        self.assertEqual(expected_sf_uplift, round(calculated_sf_uplift, 2))

    def test_uplift_unity_check_schematisation_and_safety_factor(self):
        piping_calculation_case_2_schematisation_and_safety_factor = copy.deepcopy(self.piping_calculation_case_2)
        piping_calculation_case_2_schematisation_and_safety_factor.schematisation_factor_uplift = 1.2
        piping_calculation_case_2_schematisation_and_safety_factor.safety_factor_uplift = 1.9

        expected_sf_uplift = 0.15
        calculated_sf_uplift = piping_calculation_case_2_schematisation_and_safety_factor.uplift_unity_check
        self.assertEqual(expected_sf_uplift, round(calculated_sf_uplift, 2))

    def test_heave_limit_state(self):
        """Unit-test for the limit state function of heave"""

        expected_z_heave_case_1 = -0.9
        calculated_z_heave_case_1 = self.piping_calculation_case_1.heave_limit_state
        self.assertEqual(expected_z_heave_case_1, round(calculated_z_heave_case_1, 2))

    def test_heave_limit_state_schematisation_factor(self):
        piping_calculation_case_1_schematisation_factor = copy.deepcopy(self.piping_calculation_case_1)
        piping_calculation_case_1_schematisation_factor.schematisation_factor_heave = 1.1

        expected_z_heave_case_1 = -0.93
        calculated_z_heave_case_1 = piping_calculation_case_1_schematisation_factor.heave_limit_state
        self.assertEqual(expected_z_heave_case_1, round(calculated_z_heave_case_1, 2))

    def test_heave_limit_state_safety_factor(self):
        piping_calculation_case_1_safety_factor = copy.deepcopy(self.piping_calculation_case_1)
        piping_calculation_case_1_safety_factor.safety_factor_heave = 1.1

        expected_z_heave_case_1 = -0.93
        calculated_z_heave_case_1 = piping_calculation_case_1_safety_factor.heave_limit_state
        self.assertEqual(expected_z_heave_case_1, round(calculated_z_heave_case_1, 2))

    def test_heave_limit_state_schematisation_and_safety_factor(self):
        piping_calculation_case_1_schematisation_and_safety_factor = copy.deepcopy(self.piping_calculation_case_1)
        piping_calculation_case_1_schematisation_and_safety_factor.schematisation_factor_heave = 1.14
        piping_calculation_case_1_schematisation_and_safety_factor.safety_factor_heave = 1.11

        expected_z_heave_case_1 = -0.96
        calculated_z_heave_case_1 = piping_calculation_case_1_schematisation_and_safety_factor.heave_limit_state
        self.assertEqual(expected_z_heave_case_1, round(calculated_z_heave_case_1, 2))

    def test_heave_unity_check(self):
        """Unit-test for the unity check for heave"""
        expected_sf_heave_case_1 = 0.25
        calculated_sf_heave_case_1 = self.piping_calculation_case_1.heave_unity_check
        self.assertEqual(expected_sf_heave_case_1, round(calculated_sf_heave_case_1, 2))

    def test_heave_unity_check_schematisation_factor(self):
        piping_calculation_case_2_schematisation_factor = copy.deepcopy(self.piping_calculation_case_2)
        piping_calculation_case_2_schematisation_factor.schematisation_factor_heave = 1.03

        expected_sf_heave = 0.23
        calculated_sf_heave = piping_calculation_case_2_schematisation_factor.heave_unity_check
        self.assertEqual(expected_sf_heave, round(calculated_sf_heave, 2))

    def test_heave_unity_check_safety_factor(self):
        piping_calculation_case_2_safety_factor = copy.deepcopy(self.piping_calculation_case_2)
        piping_calculation_case_2_safety_factor.safety_factor_heave = 1.6

        expected_sf_heave = 0.15
        calculated_sf_heave = piping_calculation_case_2_safety_factor.heave_unity_check
        self.assertEqual(expected_sf_heave, round(calculated_sf_heave, 2))

    def test_heave_unity_check_schematisation_and_safety_factor(self):
        piping_calculation_case_2_schematisation_and_safety_factor = copy.deepcopy(self.piping_calculation_case_2)
        piping_calculation_case_2_schematisation_and_safety_factor.schematisation_factor_heave = 1.3213
        piping_calculation_case_2_schematisation_and_safety_factor.safety_factor_heave = 2.3123

        expected_sf_heave = 0.08
        calculated_sf_heave = piping_calculation_case_2_schematisation_and_safety_factor.heave_unity_check
        self.assertEqual(expected_sf_heave, round(calculated_sf_heave, 2))

    def test_critical_head_difference_sellmeijer(self):
        """ "Unit-test for evaluating the critical head difference using the Sellmeijer equation"""

        expected_crit_head_dif_case_1 = 4.64
        calculated_crit_head_dif_case_1 = self.piping_calculation_case_1.calc_critical_head_difference_sellmeijer
        self.assertEqual(expected_crit_head_dif_case_1, round(calculated_crit_head_dif_case_1, 2))

    def test_reduced_head_difference(self):
        """Unit-test for evaluating the reduced head difference"""

        expected_red_head_dif_case_1 = 2.4
        calculated_red_head_case_1 = self.piping_calculation_case_1.calc_reduced_head_difference
        self.assertEqual(expected_red_head_dif_case_1, round(calculated_red_head_case_1, 2))

    def test_backward_erosion_unity_check(self):
        """Unit-test for evaluating the unity check for Sellmeijer"""

        expected_sf_erosion_case_1 = 1.94
        calculated_sf_erosion_case_1 = self.piping_calculation_case_1.backward_erosion_unity_check
        self.assertEqual(expected_sf_erosion_case_1, round(calculated_sf_erosion_case_1, 2))

    def test_backward_erosion_unity_check_schematisation_factor(self):
        piping_calculation_case_1_schematisation_factor = copy.deepcopy(self.piping_calculation_case_1)
        piping_calculation_case_1_schematisation_factor.schematisation_factor_piping = 1.29999999

        expected_sf_backward_erosion = 1.49
        calculated_sf_backward_erosion = piping_calculation_case_1_schematisation_factor.backward_erosion_unity_check
        self.assertEqual(expected_sf_backward_erosion, round(calculated_sf_backward_erosion, 2))

    def test_backward_erosion_unity_check_safety_factor(self):
        piping_calculation_case_2_safety_factor = copy.deepcopy(self.piping_calculation_case_2)
        piping_calculation_case_2_safety_factor.safety_factor_piping = 4

        expected_sf_backward_erosion = 0.48
        calculated_sf_backward_erosion = piping_calculation_case_2_safety_factor.backward_erosion_unity_check
        self.assertEqual(expected_sf_backward_erosion, round(calculated_sf_backward_erosion, 2))

    def test_backward_erosion_unity_check_schematisation_and_safety_factor(self):
        piping_calculation_case_1_schematisation_and_safety_factor = copy.deepcopy(self.piping_calculation_case_1)
        piping_calculation_case_1_schematisation_and_safety_factor.schematisation_factor_piping = 1.15
        piping_calculation_case_1_schematisation_and_safety_factor.safety_factor_piping = 1.0

        expected_sf_backward_erosion = 1.68
        calculated_sf_backward_erosion = (
            piping_calculation_case_1_schematisation_and_safety_factor.backward_erosion_unity_check
        )
        self.assertEqual(expected_sf_backward_erosion, round(calculated_sf_backward_erosion, 2))

    def test_ditch_2d_effect(self):
        """
        Unit test to for uplift in ditch
        """
        uplift_unity_check = self.piping_calculation_case_ditch_1.uplift_unity_check
        self.assertEqual(round(uplift_unity_check, 2), 0.83)

    def test_calculate_leakage_length(self):
        """
        Unit test for the calculation of the leakage length
        """
        expected_sf_erosion_case_1 = 71
        calculated_leakage_length = calculate_leakage_length(
            cover_layer_thickness=5, first_aquifer_thickness=10, k_cover_layer=0.01, k_first_aquifer_layer=1
        )
        self.assertEqual(round(calculated_leakage_length), expected_sf_erosion_case_1)

    def test_ground_level(self):
        """
        Test ground level value
        """
        ground_level = self.piping_calculation_case_ditch_1.ground_level
        assert ground_level == 2

    def test_calc_cover_thickness(self):
        cover_thickness = self.piping_calculation_case_1.get_cover_layer_properties["thickness"]
        cover_thickness_2 = self.piping_calculation_case_ditch_1.get_cover_layer_properties["thickness"]
        self.assertEqual(cover_thickness, 2)
        self.assertEqual(cover_thickness_2, 0)
