from munch import Munch

from app.ground_model.tno_model import TNOGroundModel
from app.lib.api.api_helper import APIHelper
from viktor import UserException
from viktor.api_v1 import API
from viktor.api_v1 import Entity
from viktor.api_v1 import EntityList
from viktor.utils import memoize


class DykeAPI(APIHelper):
    def __init__(self, entity_id: int, params: Munch = None) -> None:
        super().__init__(entity_id)
        self._params = params

    def get_ditch_data(self):
        ditch = self._params.ditch_data
        return ditch.last_saved_params

    def get_tno_entity(self) -> Entity:
        tno_model_id = self._params.geometry.data_selection.ground_model
        return self._get_entity(tno_model_id)

    def get_ground_model(self) -> TNOGroundModel:
        try:
            tno_entity = self.get_tno_entity()
            return TNOGroundModel(tno_entity.last_saved_params, tno_entity.get_file())
        except TypeError:
            raise UserException("Geen 3D model geselecteerd")

    def get_ground_model_with_memoize(self) -> TNOGroundModel:
        """
        Return a TNOGroundModel object and memoize the string content of the TNO file.
        :return:
        """
        tno_entity = self.get_tno_entity()
        return TNOGroundModel(
            tno_entity.last_saved_params,
            self.get_ground_model_content_memoized(self._params.geometry.data_selection.ground_model),
        )

    def get_children_by_entity_type(self, entity_type: str, entity_id: int) -> EntityList:
        """
        :return: dyke children by entity type
        """
        children_list = self._get_children_by_entity_type(entity_type=entity_type, entity_id=entity_id)
        return children_list

    @staticmethod
    @memoize
    def get_ground_model_content_memoized(tno_model_entity_id: int) -> str:
        """DO NOT USE IN PRODUCTION: this will lead to memory problems.
        Memoize the string content of the TNO file"""
        tno_entity = API().get_entity(tno_model_entity_id)
        return tno_entity.get_file().getvalue("utf-8")
