from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from shapely.geometry import Point

from app.ditch.model import Ditch
from app.lib.helper_read_files import entry_line_to_params
from app.lib.shapely_helper_functions import calc_minimum_distance
from app.lib.shapely_helper_functions import convert_geo_polyline_to_linestring
from viktor.geo import SoilLayout

from ..dyke.dyke_model import Dyke
from ..ground_model.model import generate_layouts_per_aquifer
from ..piping_tool.PipingCalculationUtilities import PipingCalculation


class ExitPointProperties:
    def __init__(
        self,
        coordinates: Tuple[float, float],
        soil_layout_piping: dict,
        dyke: Dyke,
        ditch: Optional[Ditch] = None,
        leakage_lengths: Optional = None,
    ):
        self.coordinates = coordinates
        self._uplift_parameters = {}
        self.soil_layout_piping = soil_layout_piping
        self.dyke = dyke
        self.ditch = ditch
        self.leakage_lengths = leakage_lengths

    @property
    def uplift_parameters(self):
        return self._uplift_parameters

    @uplift_parameters.setter
    def uplift_parameters(self, parameter_dict: dict):
        self._uplift_parameters["river_level"] = parameter_dict.get("river_level")
        self._uplift_parameters["polder_level"] = parameter_dict.get("polder_level")
        self._uplift_parameters["damping_factor"] = parameter_dict.get("damping_factor")
        self._uplift_parameters["dike_width"] = parameter_dict.get("dike_width")
        self._uplift_parameters["geohydrologic_model"] = parameter_dict.get("geohydrologic_model")
        self._uplift_parameters["distance_from_ref_line"] = self.calc_distance_from_ref_line()
        self._uplift_parameters["distance_from_entry_line"] = self.calc_distance_exit_point_to_entry_line()
        self._uplift_parameters["ditch"] = self.ditch
        self._uplift_parameters["aquifer_hydraulic_head_hinterland"] = parameter_dict.get("user_hydraulic_head")
        self._uplift_parameters["user_phi_avg_hinterland"] = (
            parameter_dict.get("user_phi_avg_hinterland") if parameter_dict.get("overwrite_phi_avg") else None
        )
        self._uplift_parameters["user_phi_avg_river"] = (
            parameter_dict.get("user_phi_avg_river") if parameter_dict.get("overwrite_phi_avg") else None
        )

    def get_exit_point_summary_piping_results(self, piping_parameters: dict) -> List[dict]:
        """Generator to return the serialized piping calculation for both the 1st adn 2nd aquifer of an exit point
        :param piping_parameters: Parameters necessary for the piping calculations
        :return:
        """
        self.uplift_parameters = piping_parameters
        self.uplift_parameters["soil_layout"] = self.soil_layout_piping

        duplicated_layouts = generate_layouts_per_aquifer(SoilLayout.from_dict(self.soil_layout_piping).layers)
        number_of_aquifers = len(duplicated_layouts)
        if number_of_aquifers > 2:
            raise ValueError("There cannot be more than 2 aquifers")

        for i, soil_layout in enumerate(duplicated_layouts, 1):
            ordinal = ["zeroth", "first", "second", "third"][i]

            self.uplift_parameters["soil_layout"] = [layer.serialize() for layer in soil_layout]

            self.uplift_parameters["leakage_length_hinterland"] = self.leakage_lengths.get(
                f"leakage_length_hinterland_{ordinal}_aquifer"
            )
            self.uplift_parameters["leakage_length_foreland"] = self.leakage_lengths.get(
                f"leakage_length_foreland_{ordinal}_aquifer"
            )
            res_dict = self._get_results_piping_dict(piping_parameters)
            res_dict["aquifer"] = i
            yield res_dict

    def _get_results_piping_dict(self, uplift_parameters: Dict):
        self.uplift_parameters = uplift_parameters
        return PipingCalculation.from_parameter_set(self.uplift_parameters).get_piping_summary_results()

    def calc_distance_from_ref_line(self) -> float:
        """Calculate distance between the exit point and the ref line"""
        return calc_minimum_distance(Point(self.coordinates), self.dyke.interpolated_trajectory())

    def calc_distance_exit_point_to_entry_line(self) -> float:
        """Calculate distance between the exit point and the entry line"""
        entry_line_geopolyline = entry_line_to_params(self.dyke.params.entry_line)
        entry_line = convert_geo_polyline_to_linestring(entry_line_geopolyline)
        return calc_minimum_distance(Point(self.coordinates), entry_line)
