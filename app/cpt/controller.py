from munch import Munch
from munch import munchify
from munch import unmunchify

from viktor import UserException
from viktor import ViktorController
from viktor.core import File
from viktor.core import ParamsFromFile
from viktor.core import progress_message
from viktor.geo import SoilLayout
from viktor.result import SetParametersResult
from viktor.views import DataGroup
from viktor.views import DataItem
from viktor.views import DataResult
from viktor.views import DataView
from viktor.views import Summary
from viktor.views import SummaryItem
from viktor.views import WebResult
from viktor.views import WebView

from .constants import CLASSIFICATION_PARAMS
from .constants import GEF_FILE_ENCODING
from .cpt import GEFFile
from .cpt import IMBROFile
from .cpt.imbro_file import _is_xml
from .model import CPT
from .parametrization import Parametrization
from .soil_layout_conversion_functions import Classification
from .soil_layout_conversion_functions import convert_input_table_field_to_soil_layout
from .soil_layout_conversion_functions import convert_soil_layout_from_mm_to_m
from .soil_layout_conversion_functions import convert_soil_layout_to_input_table_field


class Controller(ViktorController):
    label = "CPT"
    parametrization = Parametrization
    model = CPT
    encoding = GEF_FILE_ENCODING
    summary = Summary(
        ground_level_wrt_reference_m=SummaryItem(
            "Maaiveld", float, "summarize", "ground_level_wrt_reference_m", suffix="m"
        ),
        height_system=SummaryItem("Hoogtereferentie", str, "summarize", "height_system"),
        x_coordinate=SummaryItem("X-coordinaat", float, "parametrization", "x_rd", suffix="m"),
        y_coordinate=SummaryItem("Y-coordinaat", float, "parametrization", "y_rd", suffix="m"),
    )

    @ParamsFromFile(file_types=[".gef", ".xml"])
    def process_file(self, file: File, entity_id: int, **kwargs) -> dict:
        """Process the CPT file when it is first uploaded"""
        classification = Classification(munchify(CLASSIFICATION_PARAMS))
        if _is_xml(file, self.encoding):
            cpt_file = IMBROFile(file.getvalue_binary())
        else:
            cpt_file = GEFFile(file.getvalue(self.encoding))
        return classification.classify_cpt_file(cpt_file)

    @WebView("GEF", duration_guess=3)
    def visualize(self, params: Munch, entity_id: int, **kwargs) -> WebResult:
        """Visualizes the Qc and Rf line plots and also the soil layout bar plots"""
        classification = Classification(munchify(CLASSIFICATION_PARAMS))
        soils = classification.soil_mapping
        headers = params.get("headers")
        if not headers:
            raise UserException("GEF file has no headers")
        gef = self.model(cpt_params=params, soils=soils, entity_id=entity_id)
        return WebResult(html=gef.visualize())

    @DataView("Samenvatting", duration_guess=1)
    def summarize(self, params: Munch, entity_id: int, **kwargs) -> DataResult:
        """Summarizes the data inside the GEF headers"""
        headers = params.get("headers")
        if not headers:
            raise UserException("GEF file heeft geen headers")
        data = self._get_data_group(params)
        return DataResult(data)

    @staticmethod
    def _get_data_group(params: Munch) -> DataGroup:
        """Collect the necessary information from the GEF headers and return a DataGroup with the data"""
        height_system = ground_level_wrt_ref_m = None
        headers = params.get("headers")
        if headers:
            try:
                x, y = params.x_rd, params.y_rd
            except AttributeError:
                x, y = headers.x_y_coordinates
            height_system = headers.height_system
            ground_level_wrt_ref_m = headers.ground_level_wrt_reference_m
        return DataGroup(
            ground_level_wrt_reference_m=DataItem("Grond level (NAP)", ground_level_wrt_ref_m or -999, suffix="m"),
            ground_water_level=DataItem("Freatisch level (NAP)", params.ground_water_level),
            height_system=DataItem("Hoogte systeem", height_system or "-"),
            coordinates=DataItem(
                "Coordinaten",
                "",
                subgroup=DataGroup(
                    x_coordinate=DataItem("X-coordinaat", x or 0, suffix="m"),
                    y_coordinate=DataItem("Y-coordinaat", y or 0, suffix="m"),
                ),
            ),
        )

    def filter_soil_layout_on_min_layer_thickness(self, params: Munch, entity_id: int, **kwargs) -> SetParametersResult:
        """Remove all user defined layers below the filter threshold."""
        progress_message("Dunne lagen uit bodemopbouw filteren")
        soil_mapping = Classification(munchify(CLASSIFICATION_PARAMS)).soil_mapping
        # Create TNOSoilLayout and filter.
        soil_layout_user = convert_input_table_field_to_soil_layout(
            params.bottom_of_soil_layout_user, params.soil_layout, soil_mapping
        )
        soil_layout_user.filter_layers_on_thickness(
            params.gef.cpt_data.min_layer_thickness, merge_adjacent_same_soil_layers=True
        )
        soil_layout_user = convert_soil_layout_from_mm_to_m(soil_layout_user)
        table_input_soil_layers = convert_soil_layout_to_input_table_field(soil_layout_user)

        return SetParametersResult({"tno_soil_layout": table_input_soil_layers})

    def reset_soil_layout_user(self, params: Munch, **kwargs) -> SetParametersResult:
        """Place the original soil layout (after parsing) in the table input."""
        progress_message("Resetting soil layout to original unfiltered result")
        soil_layout_original = SoilLayout.from_dict(unmunchify(params.soil_layout_original))
        table_input_soil_layers = convert_soil_layout_to_input_table_field(
            convert_soil_layout_from_mm_to_m(soil_layout_original)
        )
        return SetParametersResult(
            {
                "tno_soil_layout": table_input_soil_layers,
                "bottom_of_soil_layout_user": soil_layout_original.bottom / 1e3,
            }
        )
