from typing import Dict
from typing import List
from typing import Union

from viktor.api_v1 import API
from viktor.api_v1 import Entity
from viktor.api_v1 import EntityList


class APIHelper:
    """This API helper class is the common denominator for communicating to the API in this project.

    It contains methods that are useful in every controller,
    and abstracts the API away from classes that don't immediately need them.
    """

    def __init__(self, entity_id: int, api: API = None):
        try:
            self._api = api if api else API()
        except OSError:
            self._api = 0  # Set dummy API when APIHelper call is made but object not required.
        self._entity_id = entity_id

    @property
    def raw(self):
        """Allows for direct access to raw API object."""
        return self._api

    @raw.setter
    def raw(self, new_value):
        self._api = new_value

    def update_entity(self, entity_id: int, properties: Union[List, Dict]) -> None:
        """Updates an entity with a given entity_id with the defined dict, or list."""
        self._api.get_entity(entity_id).set_params(properties)

    def _get_root_entities(self) -> EntityList:
        """Generic helper function to get the root entity from the API.

        This step is repeated in pretty much every function that retrieves data from the API.

        :returns: The root entity of the database
        """
        return self._api.get_root_entities()

    def _get_root_entities_by_entity_type(self, entity_type: str):
        return self._api.get_root_entities(entity_type_names=[entity_type])

    def _get_children(self, entity_id: int = None) -> EntityList:
        """Returns children belonging to this project.

        Children of other entities can be fetched by passing the entity_id argument.

        :returns: Children of the current entity.
        """
        entity_id = entity_id or self._entity_id

        return self._api.get_entity_children(entity_id) if self._entity_id is not None else []

    def _get_children_by_entity_type(self, entity_type: str, entity_id: int = None) -> EntityList:
        """Returns a list of children defined by entity_type."""
        entity_id = entity_id or None
        return self._api.get_entity_children(entity_id, entity_type_names=[entity_type])

    def _get_entity(self, entity_id: int) -> Entity:
        """Returns the Entity of the provided entity_id"""
        return self._api.get_entity(entity_id) if self._api != 0 else None

    def _get_parent(self, entity_id: int = None) -> Entity:
        """Returns the parent of a given entity."""
        entity_id = entity_id or self._entity_id
        return self._api.get_entity_parent(entity_id)

    def _get_grand_parent(self, entity_id: int = None) -> Entity:
        """Returns the parent of a given entity."""
        entity_id = entity_id or self._entity_id
        parent_id = self._get_parent(entity_id).id
        return self._api.get_entity_parent(parent_id)

    def _get_siblings_by_entity_type(self, entity_type: str, entity_id: int = None) -> EntityList:
        """Returns a list of siblings defined by entity_type."""
        entity_id = entity_id or self._entity_id
        return self._api.get_entity_siblings(entity_id, entity_type_names=[entity_type])

    def _get_entity_file(self, entity_id: int):
        """Return the file associated with the entity id"""
        return self._api.get_entity_file(entity_id)

    def _get_name(self) -> str:
        """Return the name of the entity"""
        return self._get_entity(self._entity_id).name
