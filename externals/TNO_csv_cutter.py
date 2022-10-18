import json
import os
from pathlib import Path

import pandas as pd
from shapely.geometry import Point
from shapely.geometry import Polygon

working_directory = Path(__file__).parent
path_input_json = working_directory / "input.json"

# Read input data
with open(path_input_json, "r", encoding="utf-8") as f:
    input_data = json.load(f)


# Load dataset
df = pd.read_csv(working_directory / f"{input_data['sourcefile']}.csv")

# Parse data
df['point'] = df.apply(lambda row: Point(row['x'], row['y']), axis=1)
polygon = Polygon(input_data["selection_polygon"])
df = df[df['point'].apply(polygon.contains)]

with open(working_directory / "output.csv", "w") as f:
    f.write(df.to_csv())

# Check for file size and enter error value if excessive
file = open(working_directory / "output.csv")
file.seek(0, os.SEEK_END)
file_size = file.tell()
files_size_limit = 100_000_000

if file_size > files_size_limit:
    df_error = pd.DataFrame(columns=[f"Error_file_size_excessive {file_size}"])
    with open(working_directory / "output.csv", "w") as f:
        f.write(df_error.to_csv())