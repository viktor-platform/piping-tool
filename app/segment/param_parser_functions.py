from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from munch import Munch
from munch import munchify

from app.ground_model.model import build_simplified_1d_rep_soil_layout
from app.ground_model.model import convert_input_table_to_soil_layout
from viktor import UserException
from viktor.geo import SoilLayout


class Scenario:
    def __init__(self, scenario: Munch, geohydromodel: str, leakage_lengths: Optional[Munch] = None):

        """

        :param scenario: scenario parametrization from the a row of the DynamicArray at the segment entity
        :param leakage_lengths:
        :param geohydromodel: selected geohydro model, one of ["0", "1", "2"]

        The attributes are the following:
          "name_of_scenario": str,
          "weight_of_scenario": float,
          "bottom_of_soil_layout": float,
          "soil_layout_table": list,
          "first_aquifer_d70": float,
          "first_aquifer_permeability": float
          "second_aquifer_activate": bool
          "second_aquifer_d70": float,
          "second_aquifer_permeability": float,
          "leakage_length_foreland_aquifer_1": Optional[float],
          "leakage_length_foreland_aquifer_2": Optional[float],
          "leakage_length_hinterland_aquifer_1": Optional[float],
          "leakage_length_hinterland_aquifer_2": Optional[float],
        """

        if geohydromodel in ["0", "1"]:

            scenario["leakage_lengths"] = dict(
                leakage_length_hinterland_first_aquifer=None,
                leakage_length_hinterland_second_aquifer=None,
                leakage_length_foreland_first_aquifer=None,
                leakage_length_foreland_second_aquifer=None,
            )

        elif geohydromodel == "2":
            scenario["leakage_lengths"] = dict(
                leakage_length_hinterland_first_aquifer=leakage_lengths.get("leakage_length_hinterland_aquifer_1"),
                leakage_length_hinterland_second_aquifer=leakage_lengths.get("leakage_length_hinterland_aquifer_2"),
                leakage_length_foreland_first_aquifer=leakage_lengths.get("leakage_length_foreland_aquifer_1"),
                leakage_length_foreland_second_aquifer=leakage_lengths.get("leakage_length_foreland_aquifer_2"),
            )
        else:
            raise NotImplementedError
        for key, value in scenario.items():
            setattr(self, key, value)


def get_materials_tables(params: Munch) -> Dict[str, List]:
    """
    Return the material tables, either from the dike entity parent of from the current params if the toggle overwrite is turned on
    """
    if params.input_selection.materials.table:
        return {
            "table": params.input_selection.materials.table,
            "classification_table": params.input_selection.materials.classification_table,
        }
    raise UserException("Materiaal en classificatie tabellen zijn leeg")


def get_piping_hydro_parameters(params: Munch) -> dict:
    """Return the Geohydrology parameters from the params of the segment."""
    if params.river_level is None:
        raise UserException("Rivierpeil ontbreekt")
    if params.polder_level is None:
        raise UserException("Polderpeil ontbreekt")
    if params.geohydrology_method == "2":
        if not params.soil_schematization.geohydrology.level2.leakage_length_array:
            raise UserException("Geohydro level 2: Vuul de leklength tabel.")  # TODO TRANSLATE
        for scenario in params.soil_schematization.geohydrology.level2.leakage_length_array:
            for field in scenario.values():
                if field is None:
                    raise UserException("Leakage length data incomplete for GeoHydro model 2.")  # TODO TRANSLATE
    if params.geohydrology_method == "3":
        raise UserException("Geohydromodel level 3 is not yet implemented.")  # TODO TRANSLATE

    return {
        "river_level": params.river_level,
        "polder_level": params.polder_level,
        "damping_factor": params.damping_factor,
        "dike_width": params.dike_width,
        "geohydrologic_model": params.geohydrology_method,
        "leakage_length_array": params.soil_schematization.geohydrology.level2.leakage_length_array,
        "user_hydraulic_head": params.soil_schematization.geohydrology.level0.hydraulic_head,
        "overwrite_phi_avg": params.soil_schematization.geohydrology.level1.overwrite_phi_avg,
        "user_phi_avg_hinterland": params.user_phi_avg_hinterland,
        "user_phi_avg_river": params.user_phi_avg_river,
    }


def get_selected_exit_point_params(params: Munch) -> Munch:
    """Return the params of the selected exit point.
    Mainly used for Mocking purposes
    """
    selected_exit_point = params.calculations.soil_profile.visualisation_settings.select_single_exit_point
    if selected_exit_point is None:
        raise UserException("Selecteer een uittredepunt")
    return selected_exit_point.last_saved_params


def get_aquifer_params(params: Munch, scenarios_index: int = 0) -> Munch:
    return munchify(
        {
            "first_aquifer": {
                "permeability": params.input_selection.soil_schematization.soil_scen_array[
                    scenarios_index
                ].first_aquifer_permeability,
                "d70": params.input_selection.soil_schematization.soil_scen_array[scenarios_index].first_aquifer_d70,
            },
            "second_aquifer": {
                "permeability": params.input_selection.soil_schematization.soil_scen_array[
                    scenarios_index
                ].second_aquifer_permeability,
                "d70": params.input_selection.soil_schematization.soil_scen_array[scenarios_index].second_aquifer_d70,
                "is_second_aquifer": params.input_selection.soil_schematization.soil_scen_array[
                    scenarios_index
                ].second_aquifer_activate,
            },
        }
    )


def get_representative_soil_layouts(params: Munch, scenario: Scenario) -> Tuple[SoilLayout, SoilLayout]:
    """Return both the detailed and simplified representative soil layouts of the segment based on the
    parametrization of the segment.
    The detailed rep soil layout is the converted soil layout from the user soil layout table.
    The simplified rep soil layout is built from the detailed rep soil layout and the aquifer properties and is made
    of 4 layers maximum: cover_layer, first_aquifer, intermediate_aquitard, second_aquifer"""

    detailed_1d_soil_layout = convert_input_table_to_soil_layout(
        bottom_of_soil_layout_user=scenario.bottom_of_soil_layout,
        soil_layers_from_table_input=scenario.soil_layout_table,
        material_table=params.input_selection.materials.table,
    )
    if not detailed_1d_soil_layout.layers:
        raise UserException("De representatieve bodemopbouw is niet gegenereerd")
    rep_soil_layout = build_simplified_1d_rep_soil_layout(
        aquifer_params=get_aquifer_params(params), base_soil_layout=detailed_1d_soil_layout
    )
    return detailed_1d_soil_layout, rep_soil_layout


def get_soil_scenario(scenario_name: str, soil_scenario_array: List[Munch]) -> Munch:
    """Return the row from the scenario DynamicArray of step 1 which has the corresponding scenario name."""
    for scenario in soil_scenario_array:
        if scenario.name_of_scenario == scenario_name:
            return scenario
    raise ValueError
