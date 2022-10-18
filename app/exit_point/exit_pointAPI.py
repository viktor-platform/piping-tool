from typing import List
from typing import Tuple

from munch import Munch

from app.dyke.dyke_model import Dyke
from app.lib.api.api_helper import APIHelper
from app.segment.param_parser_functions import get_representative_soil_layouts
from viktor import UserException
from viktor.geo import SoilLayout


class ExitPointAPI(APIHelper):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)

    def get_name(self) -> str:
        return self._get_name()

    def get_segment_params(self) -> Munch:
        """
        :return: Segment params
        """
        segment_params = self._get_parent().last_saved_params
        return segment_params

    def get_dyke(self) -> Dyke:
        """
        :return: Dyke object
        """
        dyke = self._get_grand_parent()
        return Dyke(dyke.last_saved_params)

    def get_representative_segment_layout(self, scenario_index: int) -> Tuple[SoilLayout, SoilLayout]:
        segment_params = self.get_segment_params()
        scenario = segment_params.input_selection.soil_schematization.soil_scen_array[scenario_index]
        return get_representative_soil_layouts(segment_params, scenario)

    def get_polder_level(self):
        water_level = self.get_segment_params().get("polder_level")
        if water_level is None:
            raise UserException("Geen polderpeil gevonden voor dit segment, onder geohydrologie: algemeen")
        return water_level  # m NAP

    def get_river_level(self):
        river_level = self.get_segment_params().get("river_level")
        if river_level is None:
            raise UserException("Geen riverpeil gevonden voor dit segment, onder geohydrologie: algemeen")
        return river_level  # m NAP

    def get_ditches(self) -> List[dict]:
        """Return the params of the selected ditch entity"""
        segment_params = self.get_segment_params()
        if not segment_params.segment_dry_ditches and not segment_params.segment_ditches:
            return []
        if segment_params.segment_dry_ditches:
            for ditch in segment_params.segment_dry_ditches:
                ditch["is_wet"] = False
        if segment_params.segment_ditches:
            for ditch in segment_params.segment_ditches:
                ditch["is_wet"] = True
        return segment_params.segment_ditches + segment_params.segment_dry_ditches
