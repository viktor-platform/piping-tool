from typing import List

from munch import munchify

from viktor.api_v1 import API
from viktor.api_v1 import Entity
from viktor.parametrization import HiddenField
from viktor.parametrization import LineBreak
from viktor.parametrization import NumberField
from viktor.parametrization import OptionField
from viktor.parametrization import OptionListElement
from viktor.parametrization import Parametrization as ParametrizationBaseClass
from viktor.parametrization import Section
from viktor.parametrization import SetParamsButton
from viktor.parametrization import Tab
from viktor.parametrization import TableInput

from .constants import CLASSIFICATION_PARAMS
from .constants import DEFAULT_MIN_LAYER_THICKNESS
from .soil_layout_conversion_functions import Classification


def _get_project_entity(entity_id: int) -> Entity:
    """Obtains the Project entity"""
    return API().get_entity(entity_id).parent()


def _get_soils_options(entity_id: int, **kwargs) -> List[OptionListElement]:
    """Options all possible soil type from the Classification parameter in the Project entity."""
    classification = Classification(munchify(CLASSIFICATION_PARAMS))
    return [OptionListElement(soil) for soil in classification.soil_mapping]


def visible(file_type):
    def _vis(params, **kwargs):
        return params.name.lower().endswith(file_type)

    return _vis


class Parametrization(ParametrizationBaseClass):
    gef = Tab("GEF")
    gef.cpt_data = Section("Eigenschappen en bodemopbouw")
    gef.cpt_data.ground_water_level = NumberField("Freatische waterstand", suffix="m", name="ground_water_level")
    gef.cpt_data.x_rd = NumberField("X-coordinaat", suffix="m", name="x_rd")
    gef.cpt_data.y_rd = NumberField("Y-coordinaat", suffix="m", name="y_rd")

    gef.cpt_data.lb1 = LineBreak()
    gef.cpt_data.bottom_of_soil_layout_user = NumberField(
        "Onderste lagen", name="bottom_of_soil_layout_user", suffix="m"
    )
    gef.cpt_data.min_layer_thickness = NumberField(
        "Minimum Laagdikte", suffix="mm", min=0, step=50, default=DEFAULT_MIN_LAYER_THICKNESS
    )
    gef.cpt_data.lb2 = LineBreak()
    gef.cpt_data.reset_original_layers = SetParamsButton("Oorspronkelijke bodemopbouw", method="reset_soil_layout_user")
    gef.cpt_data.filter_thin_layers = SetParamsButton(
        "Filter Laagdikte", method="filter_soil_layout_on_min_layer_thickness"
    )
    gef.cpt_data.lb3 = LineBreak()
    gef.cpt_data.soil_layout = TableInput("Bodemopbouw", name="tno_soil_layout")
    gef.cpt_data.soil_layout.name = OptionField("Materiaal", options=_get_soils_options)
    gef.cpt_data.soil_layout.top_of_layer = NumberField("Bovenkant NAP [m]", num_decimals=1)

    gef.cpt_data.gef_headers = HiddenField("GEF Headers", name="headers")
    gef.cpt_data.measurement_data = HiddenField("GEF Meetdata", name="measurement_data")
    gef.cpt_data.soil_layout_original = HiddenField("Oorspronkelijke bodemopbouw", name="soil_layout_original")
    gef.cpt_data.soil_layout_original = HiddenField("Oorspronkelijke bodemopbouw", name="soil_layout_original")
