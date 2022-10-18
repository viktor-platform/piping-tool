import copy
import os

from app.ditch.model import Ditch
from tests.helper_functions import load_from_json

file_dir = os.path.dirname(__file__)

PIPING_PARAMETERS = load_from_json(file_dir, "piping_parameter_set.json")
PIPING_PARAMETERS_DITCH = copy.copy(PIPING_PARAMETERS["case_1"])
PIPING_PARAMETERS_DITCH["ditch"] = Ditch({"x": 0, "z": 2}, {"x": 1, "z": 0}, {"x": 4, "z": 0}, {"x": 5, "z": 2}, True)
