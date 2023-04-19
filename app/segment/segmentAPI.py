from typing import List
from typing import Optional
from typing import Union

from viktor import UserException
from viktor.api_v1 import Entity
from viktor.api_v1 import EntityList
from viktor.errors import EntityNotFoundError

from ..cpt_folder.cpt_folder_model import CPTFolder
from ..dyke.dyke_model import Dyke
from ..ground_model.tno_model import TNOGroundModel
from ..lib.api.api_helper import APIHelper
from ..lib.helper_read_files import entry_line_to_params
from ..lib.helper_read_files import process_ditch_shape_file
from ..lib.shapely_helper_functions import convert_geo_polyline_to_linestring
from ..lib.shapely_helper_functions import convert_geopolygon_to_shapely_polgon
from .segment_model import Segment


class SegmentAPI(APIHelper):
    def __init__(self, entity_id: int):
        super().__init__(entity_id)
        self.entity_id = entity_id

    def get_dyke(self, with_tno_groundmodel: bool = False) -> Dyke:
        """

        :param with_tno_groundmodel: boolean to indicate if the Dike class should be instantiated with or without the
        argument tno_groundmodel. It is faster when with_tno_groundmodel is set to False.
        :return: Dyke object
        """
        dyke_params = self._get_parent().last_saved_params
        if with_tno_groundmodel:
            tno_groundmodel = self.get_tno_ground_model()
            return Dyke(dyke_params, tno_groundmodel)
        return Dyke(dyke_params)

    def get_tno_ground_model(self) -> TNOGroundModel:
        tno_ground_model_entity_id = self.get_dyke().ground_model_entity_id
        if tno_ground_model_entity_id is None:
            raise UserException("Selecteer een TNO grondmodel voor de dijk")

        try:
            tno_params = self._get_entity(tno_ground_model_entity_id).last_saved_params
            tno_file = self._get_entity_file(tno_ground_model_entity_id)
            return TNOGroundModel(tno_params, tno_file)
        except EntityNotFoundError:
            raise UserException("The 3D Ground model entity cannot be retrieved or has been deleted.")  # TODO TRANSLATE

    def get_cpt_entity(self, cpt_entity_id: int) -> Entity:
        return self._get_entity(cpt_entity_id)

    def segment_name(self) -> str:
        return self._get_entity(self.entity_id).name

    def get_all_children_exit_point_entities(self) -> EntityList:
        """Get all the children exit point entities of the segment."""
        return self._get_children_by_entity_type(entity_type="ExitPoint", entity_id=self._entity_id)

    def create_exit_point_entity(self, new_entity_name: str, new_entity_params: dict):
        """Create an exit point entity with the provided new name and params"""
        self.raw.create_child_entity(
            parent_entity_id=self._entity_id,
            entity_type_name="ExitPoint",
            name=new_entity_name,
            params=new_entity_params,
        )

    @staticmethod
    def update_exit_point_properties(exit_point_params: dict, exit_point_entity: Entity):
        """Update the params of a exit point entity"""
        exit_point_entity.set_params(exit_point_params)

    def get_ditches(self) -> Optional[dict]:
        """Return the params of the selected ditch entity"""
        dyke = self._get_parent()
        try:
            ditch = dyke.last_saved_params.ditch_data
        except (EntityNotFoundError, AttributeError):
            raise UserException(f"Geen sloten gevonden voor dijk {dyke.name}")

        if ditch:
            return process_ditch_shape_file(ditch)
        return None

    @property
    def all_cpts(self) -> Union[EntityList, List]:
        cpt_folder = self._get_parent().last_saved_params.cpt_folder
        if cpt_folder:
            return cpt_folder.children(include_params=False)
        return []

    def get_cpt_folder_from_parent(self) -> Entity:
        return self._get_parent().last_saved_params.cpt_folder

    def get_borehole_folder_from_parent(self) -> Entity:
        return self._get_parent().last_saved_params.bore_folder

    def closest_cpt_to_RD_coordinates(self, x: float, y: float) -> Entity:
        all_cpts = self.all_cpts
        folder_name = self._get_parent().last_saved_params.cpt_folder
        cpt_id = CPTFolder(all_cpts, folder_name).closest_cpt_to_point(x, y).id
        return self._get_entity(cpt_id)

    def get_segment_model(self, segment_params=None) -> Segment:
        dyke = self.get_dyke()

        # find the segment trajectory trough the intersection of the dyke trajectory and the polygon
        if segment_params.segment_polygon is None:
            raise UserException(
                "Geen traject voor het dijkvak: vul start en eind kilometrering, en click op 'Update traject'"
            )
        polygon = convert_geopolygon_to_shapely_polgon(segment_params.segment_polygon)
        segment_trajectory = polygon.intersection(dyke.interpolated_trajectory())

        # find the entry line for this segment
        if not dyke.params.entry_line:
            raise UserException("Selecteer intredelijn voor de dijk.")
        entry_line_geopolygon = entry_line_to_params(dyke.params.entry_line)
        entry_line = polygon.intersection(convert_geo_polyline_to_linestring(entry_line_geopolygon))
        return Segment(segment_params, segment_trajectory, dyke, entry_line)

    def get_parent_dike_params(self):
        return self._get_parent().last_saved_params

    def get_entity(self, entity_id: int) -> Entity:
        return self.raw.get_entity(entity_id)
