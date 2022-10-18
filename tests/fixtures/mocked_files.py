import json
from pathlib import Path
from typing import Optional
from typing import Union

from munch import Munch
from munch import munchify
from munch import unmunchify

from viktor.core import File
from viktor.geometry import GeoPoint
from viktor.geometry import GeoPolygon
from viktor.geometry import GeoPolyline

FILE_DIR = Path(__file__).parent

EXIT_POINT_SUMMARY = {"x_coordinate": {"value": 125694.68005327464}, "y_coordinate": {"value": 441831.1866900831}}


class MockFileResource:
    """Class to wrap around a file to mock the result of a FileField"""

    def __init__(self, file: File):
        self.file = file

    def file(self):
        return self.file


class MockedEntity:
    """Class to be used for mocking the response of VIKTOR API (api_v1) calls"""

    def __init__(self, id_: int, name: str, params: Union[dict, Munch], summary: Optional[dict] = None):
        self.id = id_
        self.name = name
        self.last_saved_params = convert_filefield_to_file_object(
            unmunchify(convert_lat_lon_to_geopolyline(params if isinstance(params, Munch) else munchify(params)))
        )

        self.last_saved_summary = munchify(summary) or {}

    @classmethod
    def from_json(cls, path: Union[Path, str], id_, name, summary) -> "MockedEntity":
        """Class method that allows construction from a path to a json file"""
        with open(path, "r") as json_file:
            params = json.load(json_file)
        return cls(id_, name, params, summary)


def convert_lat_lon_to_geopolyline(params):
    """This function is added to accommodate the switch from lat,lon coordinates to a GeoPolyline
    The whole loaded json is iterated recursively"""
    if isinstance(params, dict):
        for key, value in params.items():
            if _is_list_of_x_y_coordinates(value):
                points = [GeoPoint(row["lat"], row["lon"]) for row in value]
                if "polygon" in key and "ditch" not in key:
                    params[key] = GeoPolygon(*points)
                else:
                    params[key] = GeoPolyline(*points)
            else:
                convert_lat_lon_to_geopolyline(value)
    return munchify(params)


def convert_filefield_to_file_object(params):
    """Used for mocking FileField objects"""
    if isinstance(params, dict):
        for key, value in params.items():
            if key in ["line_for_2d_soil_layout", "entry_line", "ditch_data"]:
                path_of_file = FILE_DIR / value
                file = File.from_path(path_of_file)
                params[key] = MockFileResource(file)
    return munchify(params)


def _is_list_of_x_y_coordinates(value):
    """Checks whether the value is a list and whether it contains a dictionary with keys 'x' and 'y' in it."""
    try:
        row = value[0].keys()
    except (IndexError, AttributeError, KeyError, TypeError):
        row = []
    return "lat" in row and "lon" in row


SEGMENT_ENTITIES = [
    MockedEntity.from_json(FILE_DIR / f"segment_{i}.json", 10 + i, f"segment_{i}", {}) for i in range(1, 2)
]
DYKES_ENTITIES = [MockedEntity.from_json(FILE_DIR / f"dyke_{i}.json", 20 + i, f"dyke_{i}", {}) for i in range(1, 2)]
ENTRY_LINE_ENTITIES = [
    MockedEntity.from_json(FILE_DIR / f"entry_line_{i}.json", 30 + i, f"entry_line_{i}", {}) for i in range(1, 2)
]
EXIT_POINT_ENTITIES = [
    MockedEntity.from_json(FILE_DIR / f"exit_point_{i}.json", 40 + i, f"exit_point_{i}", EXIT_POINT_SUMMARY)
    for i in range(1, 2)
]
STE_GROUND_MODEL_ENTITY = MockedEntity.from_json(FILE_DIR / "ste_ground_model.json", 100, "ste_ground_model.json", {})
STE_GROUND_MODEL_FILE = File.from_path(FILE_DIR / "STE.csv").getvalue("utf-8")

DITCH_ENTITIES = [
    MockedEntity.from_json(FILE_DIR / f"ditch_data_{i}.json", 50 + i, f"ditch_data_{i}", {}) for i in range(1, 2)
]

MODELS_FOLDER_ENTITIES = [
    MockedEntity.from_json(FILE_DIR / f"models_folder_{i}.json", 60 + i, f"models_folder_{i}", {}) for i in range(1, 2)
]
