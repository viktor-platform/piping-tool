from typing import Any
from typing import Optional
from typing import Tuple
from typing import Union

from munch import Munch
from munch import munchify
from numpy import Inf
from numpy import exp
from numpy import float64
from numpy import isnan
from numpy import pi
from numpy import sqrt
from numpy import tan

from app.ditch.model import Ditch
from app.piping_tool.constants import CRITICAL_HEAVE_GRADIENT
from app.piping_tool.constants import D70_REF
from app.piping_tool.constants import GAMMA_P_SUB
from app.piping_tool.constants import GAMMA_W
from app.piping_tool.constants import GRAVITY
from app.piping_tool.constants import M_P
from app.piping_tool.constants import R_C
from app.piping_tool.constants import THETA
from app.piping_tool.constants import VISCOSITY
from app.piping_tool.constants import WHITE_COEFFICIENT
from app.piping_tool.constants import PipingDataFrameColumns
from viktor import UserException


class PipingCalculation:
    def __init__(
        self,
        polder_level: float,
        river_level: float,
        damping_factor: float,
        leakage_length_hinterland: float,
        leakage_length_foreland: float,
        dike_width: float,
        distance_from_ref_line: float,
        distance_from_entry_line: float,
        geohydrologic_model: str,
        soil_layout: dict,
        ditch: Optional[Ditch] = None,
        aquifer_hydraulic_head_hinterland: Optional[float] = None,
        user_phi_avg_hinterland: Optional[float] = None,
        user_phi_avg_river: Optional[float] = None,
    ):
        """
        :param polder_level:
        :param river_level: level of the river in m NAP
        :param damping_factor: damping factor for the river head
        :param leakage_length_foreland: Leakage length to the foreland side in m
        :param leakage_length_hinterland: Leakage length to the hinterland side in m
        :param dike_width: width of the dike in m
        :param distance_from_ref_line: distance of the exit point to the crest of the dike in m
        :param distance_from_entry_line: distance of the exit point to the entry line of the dike in m
        :param geohydrologic_model: boolean if a ditch is present at exit point or not.
        :param soil_layout: list of layers containing the soil properties and layer boundaries
        :param ditch: Ditch object containing the geometry and variables associated with the ditch.
        :param aquifer_hydraulic_head_hinterland: user input of the hydraulic head in the hinterland in m
        (in case geohydrological model 0 is chosen)
        :param user_phi_exit_average: user of the hydraulic head in the hinterland under normal conditions in m, if the
        user wants to overwrite it
        :return: negative or positive float
        """
        self.soil_layout = munchify(soil_layout)
        self.polder_level = polder_level
        self.river_level = river_level
        self.damping_factor = damping_factor
        self.leakage_length_hinterland = leakage_length_hinterland
        self.leakage_length_foreland = leakage_length_foreland
        self.dike_width = dike_width
        self.distance_from_ref_line = distance_from_ref_line
        self.distance_from_entry_line = distance_from_entry_line
        self.geohydrologic_model = geohydrologic_model
        self.ditch = ditch
        self.is_ditch = bool(self.ditch)
        self.aquifer_hydraulic_head_hinterland = aquifer_hydraulic_head_hinterland
        self.user_phi_exit_average_hinterland = user_phi_avg_hinterland
        self.user_phi_exit_average_river = user_phi_avg_river
        if self.is_ditch:
            self.is_ditch_wet = self.ditch.is_wet
        else:
            self.is_ditch_wet = False

    @classmethod
    def from_parameter_set(cls, parameter_set: Union[dict, Munch]):
        """Instantiate PipingCalculation from a Munch storing as keys all the necessary geohydrologic parameters"""
        return cls(**parameter_set)

    # TODO: add more cases for this validator, also for uplift and heave
    def validator_sellmeijer(self):
        aquifer_layer = self.aquifer_layer
        if aquifer_layer.properties.grain_size_d70 is None:
            raise UserException("Geen d70 voor aquifer")
        if aquifer_layer.properties.horizontal_permeability is None:
            raise UserException("Geen horizontaal doorlatendheid voor aquifer")

    @property
    def ground_level(self) -> float:
        """
        Ground level is the top of the first layer
        """
        layers = self.soil_layout
        return layers[0]["top_of_layer"]

    @property
    def aquifer_layer(self) -> Munch:
        """Return the layer of the aquifer"""
        for layer in self.soil_layout:
            # Stop if aquifer layer is reached
            if layer.properties["aquifer"]:
                return layer
        raise UserException("Geen aquifer gevonden in de bodemopbouw")

    @property
    def phi_exit_average_hinterland(self):
        """The polder level is assumed to be the hydraulic head in the aquifer at the exit point under regular
        circumstances."""
        if self.user_phi_exit_average_hinterland is None:
            return self.polder_level
        return self.user_phi_exit_average_hinterland

    @property
    def phi_exit_average_river(self):
        """The polder level is assumed to be the hydraulic head in the aquifer at the river under regular
        circumstances."""
        if self.user_phi_exit_average_river is None:
            return self.polder_level
        return self.user_phi_exit_average_river

    @property
    def uplift_limit_state(self) -> float:
        """
        Return the z limit state score for uplift at a specific exit point. Negative z-score is failure, positive is
        safety compliant.
        """
        potential_uplift = self.calc_uplift_critical_potential_difference
        water_level_exit_point = self.calc_h_exit
        aquifer_hydraulic_head = self.calc_phi_exit
        return potential_uplift - (aquifer_hydraulic_head - water_level_exit_point)

    @property
    def uplift_unity_check(self) -> float:
        """
        Return the unity check (or safety factor) for uplift at a specific exit point.
        """
        potential_uplift = self.calc_uplift_critical_potential_difference
        water_level_exit_point = self.calc_h_exit
        aquifer_hydraulic_head = self.calc_phi_exit
        return potential_uplift / (aquifer_hydraulic_head - water_level_exit_point)

    @property
    def heave_limit_state(self) -> float:
        """
        Return the z limit state score for heave at a specific exit point. Negative z-score is failure, positive is
        safety compliant.
        """
        water_level_exit_point = self.calc_h_exit
        aquifer_hydraulic_head = self.calc_phi_exit
        cover_thickness = self.get_cover_layer_properties["thickness"]

        return CRITICAL_HEAVE_GRADIENT - (aquifer_hydraulic_head - water_level_exit_point) / cover_thickness

    @property
    def heave_unity_check(self) -> float:
        """
        Return the unity check for backwards erosion at a specific exit point.
        """
        water_level_exit_point = self.calc_h_exit
        aquifer_hydraulic_head = self.calc_phi_exit
        cover_thickness = self.get_cover_layer_properties["thickness"]

        if aquifer_hydraulic_head - water_level_exit_point == 0:
            return Inf
        return CRITICAL_HEAVE_GRADIENT / ((aquifer_hydraulic_head - water_level_exit_point) / cover_thickness)

    @property
    def backward_erosion_unity_check(self) -> float:
        """
        Return the unity check for backwards erosion at a specific exit point.
        """
        self.validator_sellmeijer()
        return M_P * self.calc_critical_head_difference_sellmeijer / self.calc_reduced_head_difference

    def get_piping_summary_results(self) -> dict:
        column_names = PipingDataFrameColumns
        aquifer_properties = self.aquifer_layer.get("properties")
        aquifer_thickness = self.aquifer_layer.top_of_layer - self.aquifer_layer.bottom_of_layer
        cover_thickness = self.get_cover_layer_properties["thickness"]

        res = {
            column_names.DITCH.value: "Ja" if self.is_ditch else "Nee",
            column_names.DITCH_SMALL_B.value: self.ditch.small_b if self.is_ditch else "-",
            column_names.DITCH_LARGE_B.value: self.ditch.large_b if self.is_ditch else "-",
            column_names.GROUND_LEVEL.value: self.ground_level,
            column_names.RIVER_LEVEL.value: self.river_level,
            column_names.PHREATIC_LEVEL.value: self.calc_h_exit,
            column_names.COVER_LAYER_THICKNESS.value: cover_thickness,
            column_names.AQUIFER_THICKNESS.value: convert_nan(aquifer_thickness),
            column_names.AQUIFER_PERMEABILITY.value: convert_nan(aquifer_properties.get("horizontal_permeability")),
            column_names.AQUIFER_INTR_PERMEABILITY.value: convert_nan(
                self.calc_intrinsic_permeability(aquifer_properties.get("horizontal_permeability"))
            ),
            column_names.AQUIFER_D_70.value: aquifer_properties.grain_size_d70 / 1e3,
            column_names.M_P.value: M_P,
            column_names.F_1.value: convert_nan(self.calc_f_resistance),
            column_names.WHITE_COEFFICIENT.value: WHITE_COEFFICIENT,
            column_names.THETA.value: THETA,
            column_names.D_70_REF.value: D70_REF,
            column_names.R_C.value: R_C,
            column_names.F_2.value: convert_nan(self.calc_f_scale),
            column_names.F_3.value: convert_nan(self.calc_f_geometry),
            column_names.SEEPAGE_LENGTH.value: self.distance_from_entry_line,
            column_names.CRITICAL_HEAD_DIFFERENCE_SELLMEIJER.value: convert_nan(
                self.calc_critical_head_difference_sellmeijer
            ),
            column_names.REDUCED_HEAD_DIFFERENCE.value: convert_nan(self.calc_reduced_head_difference),
            column_names.UNITY_CHECK.value: convert_nan(self.uplift_unity_check),
            column_names.POTENTIAL_UPLIFT.value: convert_nan(self.calc_uplift_critical_potential_difference),
            column_names.AQUIFER_HYDRAULIC_HEAD.value: convert_nan(self.calc_phi_exit),
            column_names.WATER_LEVEL_EXIT_POINT.value: self.calc_h_exit,
            column_names.CRITICAL_HEAVE_GRADIENT.value: CRITICAL_HEAVE_GRADIENT,
            column_names.UPLIFT_UNITY_CHECK.value: convert_nan(self.uplift_unity_check),
            column_names.HEAVE_UNITY_CHECK.value: convert_nan(self.heave_unity_check),
            column_names.SELLMEIJER_UNITY_CHECK.value: convert_nan(self.backward_erosion_unity_check),
            column_names.UPLIFT_LIMIT_STATE_SCORE.value: convert_nan(self.uplift_limit_state),
            column_names.HEAVE_LIMIT_STATE_SCORE.value: convert_nan(self.heave_limit_state),
        }
        return res

    def average_volumetric_weight_cover_layers(
        self,
        ditch_phreatic_level: Optional[float] = None,
        cutoff_top: Optional[float] = None,
    ) -> Tuple[float, float]:
        """
        Get average volumetric weight of the cover layers.
        :param ditch_phreatic_level: Optional phreatic level in the ditch in m NAP.
        :param cutoff_top: NAP level of the bottom of the ditch (if present). All the layers above this cutoff must
        be ignored.
        """
        thickness = 0
        thickness_gamma = 0
        phreatic_level = self.calc_h_exit if ditch_phreatic_level is None else ditch_phreatic_level
        for layer in self.soil_layout:
            # Stop if aquifer layer is reached
            if layer.properties["aquifer"]:
                break

            if cutoff_top is not None:
                # If there is a ditch, the top of the first layer of the cover must be updated with the bottom level of
                # the ditch
                if layer.top_of_layer > cutoff_top and layer.bottom_of_layer > cutoff_top:
                    continue  # discard current layer
                if layer.top_of_layer > cutoff_top > layer.bottom_of_layer:
                    layer.top_of_layer = cutoff_top  # update top of layer with cutoff

            # Phreatic level is below the soil layer
            if phreatic_level <= layer.bottom_of_layer:
                thickness_gamma += (layer.top_of_layer - layer.bottom_of_layer) * layer.properties["gamma_dry"]
                thickness += layer.top_of_layer - layer.bottom_of_layer

            # Phreatic level is in the soil layer
            elif layer.bottom_of_layer < phreatic_level < layer.top_of_layer:
                thickness_gamma += (layer.top_of_layer - phreatic_level) * layer.properties["gamma_dry"]
                thickness += layer.top_of_layer - phreatic_level

                thickness_gamma += (phreatic_level - layer.bottom_of_layer) * (layer.properties["gamma_wet"] - GAMMA_W)
                thickness += phreatic_level - layer.bottom_of_layer

            # Phreatic level is above the soil layer
            else:
                thickness_gamma += (layer.top_of_layer - layer.bottom_of_layer) * (
                    layer.properties["gamma_wet"] - GAMMA_W
                )
                thickness += layer.top_of_layer - layer.bottom_of_layer

        return thickness_gamma / thickness, thickness

    @property
    def calc_uplift_critical_potential_difference(self) -> float:
        """
        Return the uplift potential difference delta_phi_c,u in m. Function accounts for volumetric weights above the
        phreatic level (gamma_dry) and below the phreatic level.
        """
        effective_stress = self.get_cover_layer_properties["effective_stress"]
        return effective_stress / GAMMA_W

    @property
    def get_cover_layer_properties(self) -> dict:
        """
        Get the average weight, thickness and effective stress of the cover layer. Two cases are distinguished depending
        on the presence of a ditch or not.
        :return:
        """
        # The phreatic level is set equal to h_exit, which is equal to the surface level when no ditch is present.
        # By default the phreatic level should be determined this way but the user should be able to alter the
        # phreatic level on exit point level. When initiating an exit point there should be a set_params function to
        # set the phreatic level as is done with self.calc_h_exit() in the code below.
        phreatic_level = self.calc_h_exit

        if self.is_ditch:
            if not self.is_ditch_wet and phreatic_level >= self.ditch.left_point_bottom.y:
                phreatic_level = min(self.ditch.left_point_bottom.y, self.ditch.right_point_bottom.y)
            z_top_aquifer = self.aquifer_layer["top_of_layer"]
            thickness = self.ditch.h_eff(z_top_aquifer)
            avg_gam, _ = self.average_volumetric_weight_cover_layers(
                ditch_phreatic_level=phreatic_level, cutoff_top=z_top_aquifer + thickness
            )
            if self.ditch.case == "h1":
                effective_stress = thickness * avg_gam
            elif self.ditch.case == "h2" or self.ditch.case == "h3":
                if self.is_ditch_wet:
                    effective_stress = thickness * avg_gam + (phreatic_level - self.ditch.left_point_bottom.y) * GAMMA_W
                else:
                    effective_stress = thickness * avg_gam
            else:
                raise UserException("De aangewezen sloot valt niet in een van de volgende situaties: h1, h2, h3.")
        else:
            avg_gam, thickness = self.average_volumetric_weight_cover_layers()
            effective_stress = thickness * avg_gam
        return {"avg_gamma": avg_gam, "thickness": thickness, "effective_stress": effective_stress}

    @property
    def calc_h_exit(self) -> float:
        """
        Return the water level at the exit point. Original name: 'FreatischNiveauUittredepunt'
        Full saturation is here assumed.
        :return:
        """
        if self.is_ditch and self.is_ditch_wet:
            ground_level_ditch = min(self.ditch.left_point_bottom.y, self.ditch.right_point_bottom.y)
            return max(self.polder_level, ground_level_ditch)
        elif self.is_ditch and not self.is_ditch_wet:
            ground_level_ditch = min(self.ditch.left_point_bottom.y, self.ditch.right_point_bottom.y)
            return ground_level_ditch
        else:
            return self.ground_level

    @property
    def calc_phi_exit(self) -> float:
        """
        Calculate and return the hydraulic head in the aquifer at the exit point.
        """
        if self.geohydrologic_model == "0":
            return self.aquifer_hydraulic_head_hinterland
        if self.geohydrologic_model == "1":
            if self.damping_factor > 1 or self.damping_factor < 0:
                raise ValueError("Incorrect damping factor")
            return self.calc_phi_exit_level_1
        elif self.geohydrologic_model == "2":
            return self.calc_phi_exit_level_2
        else:
            raise UserException(f"{self.geohydrologic_model} is geen valide Geohydrologisch model")

    @property
    def calc_phi_exit_level_1(self) -> float:
        """Calculate the hydraulic head in the aquifer at the exit point according to the Geohydrologic model 1"""
        return self.phi_exit_average_hinterland + self.damping_factor * (self.river_level - self.phi_exit_average_river)

    @property
    def calc_phi_exit_level_2(self) -> float:
        """Calculate the hydraulic head in the aquifer at the exit point according to the Geohydrologic model 2"""

        phi_2 = self.polder_level + (self.river_level - self.polder_level) * self.leakage_length_hinterland / (
            self.leakage_length_foreland + self.dike_width + self.leakage_length_hinterland
        )
        phi_exit = self.polder_level + (phi_2 - self.polder_level) * exp(
            (self.dike_width / 2 - self.distance_from_ref_line) / self.leakage_length_hinterland
        )
        return phi_exit

    @property
    def calc_reduced_head_difference(self) -> float:
        """Calculate the head difference. The head difference is corrected with the 0.3D rule"""
        cover_thickness = self.get_cover_layer_properties["thickness"]

        return max(0.01, (self.river_level - self.calc_h_exit - R_C * cover_thickness))

    @property
    def calc_critical_head_difference_sellmeijer(self) -> float:
        """Calculate the Sellmeijer delta_Hc factor"""
        seepage_length = self.distance_from_entry_line
        f_1, f_2, f_3 = self.calc_f_resistance, self.calc_f_scale, self.calc_f_geometry

        return f_1 * f_2 * f_3 * seepage_length

    @property
    def calc_f_resistance(self) -> float:
        """Calculate the resistance factor for Sellmeijer"""
        f_res = WHITE_COEFFICIENT * GAMMA_P_SUB / GAMMA_W * tan(THETA * pi / 180.00)
        return f_res

    @property
    def calc_f_scale(self) -> float:
        """Calculate the scale factor"""
        seepage_length = self.distance_from_entry_line
        aquifer_properties = self.aquifer_layer.get("properties")
        d_70_m = aquifer_properties.grain_size_d70 / 1e3  # convert to m (input field in mm)
        intr_permeability = self.calc_intrinsic_permeability(aquifer_properties.get("horizontal_permeability"))
        f_scale = D70_REF / (intr_permeability * seepage_length) ** (1 / 3) * (d_70_m / D70_REF) ** 0.4
        return f_scale

    @property
    def calc_f_geometry(self) -> float:
        """Calculate the geometry factor. Special case handling for d_sand == distance_from_ref_line"""

        seepage_length = self.distance_from_entry_line
        aquifer_thickness = self.aquifer_layer.top_of_layer - self.aquifer_layer.bottom_of_layer
        if aquifer_thickness == seepage_length:
            aquifer_thickness = aquifer_thickness - 0.001
        exponent = 0.04 + (0.28 / ((aquifer_thickness / seepage_length) ** 2.8 - 1))
        return 0.91 * (aquifer_thickness / seepage_length) ** exponent

    def calc_intrinsic_permeability(self, horizontal_permeability) -> float:
        """Calculate the intrinsic permeability from the Darcy permeability.
        The permeability is in [m/day] and the resulting intrinsic permeability is [m/s]"""
        return (VISCOSITY / GRAVITY) * horizontal_permeability / (24 * 3600)


def calculate_leakage_length(cover_layer_thickness, k_cover_layer, first_aquifer_thickness, k_first_aquifer_layer):
    return sqrt(k_first_aquifer_layer * cover_layer_thickness * first_aquifer_thickness / k_cover_layer)


def convert_nan(value: Any) -> Any:
    """Convert numpy nan type into string"""
    if isinstance(value, float64) and isnan(value):
        return "nan"
    return value
