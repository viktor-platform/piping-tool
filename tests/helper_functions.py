import json
import os
from typing import List
from typing import Union


def load_from_json(file_dir, json_files) -> Union[dict, List[dict]]:
    """Helper function that returns a list of dictionaries from the given list of json files"""
    json_files = json_files if isinstance(json_files, list) else [json_files]
    output_list = []
    for json_file in json_files:
        with open(os.path.join(file_dir, json_file), "r") as file_content:
            output_list.append(json.load(file_content))
    return output_list[0] if len(output_list) == 1 else output_list
