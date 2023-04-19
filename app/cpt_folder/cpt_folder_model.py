import numpy as np

from viktor import UserException
from viktor.api_v1 import EntityList


class CPTFolder:
    def __init__(self, cpt_entities: EntityList, folder_name: str):
        self._cpt_entities = cpt_entities
        self.name = folder_name

    def closest_cpt_to_point(self, x: float, y: float):
        if not self._cpt_entities:
            raise UserException(f"Upload at least one cpt to the folder {self.name}")
        min_dist = 10**9
        closest_cpt = None
        point = np.array([x, y])
        for cpt in self._cpt_entities:
            cpt_summary = cpt.last_saved_summary
            coordinate = np.array([cpt_summary.x_coordinate["value"], cpt_summary.y_coordinate["value"]])
            distance = np.linalg.norm(point - coordinate)
            if distance < min_dist:
                closest_cpt = cpt
                min_dist = distance
        return closest_cpt
