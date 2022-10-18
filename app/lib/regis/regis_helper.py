import urllib.request
from pathlib import Path
from typing import Dict
from typing import List
from typing import Tuple

import numpy as np
import xarray
from scipy.spatial import distance
from shapely.geometry import LineString
from shapely.geometry import Polygon

from app.lib.regis.regis_soil_lib import REGIS_MIDDLE_FORMATION_NAME_CODE_MAPPING
from app.lib.regis.regis_soil_lib import REGIS_PRIMARY_FORMATION_NAME_CODE_MAPPING
from app.lib.regis.regis_soil_lib import REGIS_SECONDARY_FORMATION_NAME_CODE_MAPPING
from viktor import Color
from viktor.geo import Soil
from viktor.geo import SoilLayer
from viktor.geo import SoilLayout

PATH_REGIS_FILE = Path(__file__).parent / "REGIS.nc"


# isolated for testing purposes
def save_regis_data_from_url(url: str) -> None:
    urllib.request.urlretrieve(url, PATH_REGIS_FILE)


def get_regis_dataset(x_min: int, y_min: int, x_max: int, y_max: int, bottom_level_query: int) -> xarray.Dataset:
    """
    Extract a Dataset based on a domain/boundary box (x_min, y_min, x_max, xy_max, bottom) of Regis.
    More info: https://www.dinodata.nl/opendap/REGIS/REGIS.nc.html

    :param x_min, y_min, x_max, y_max: RD coodinates of the boundaries
    :param bottom_level_query: bottom level in meters of the REGIS selection data, all data below 'bottom' is dropped.
    :return: Dataset containing the top levels of each geological formation for every grid point within the boundary box
    """

    # Transform RD coordinates to local query coordinates
    x_min = int(x_min / 100)
    x_max = int(x_max / 100)
    y_max = int(y_max / 100) - 3000
    y_min = int(y_min / 100) - 3000

    if x_min > x_max:
        raise ValueError("west coordinate is larger than east coordinate")

    if y_min > y_max:
        raise ValueError("south coordinate is larger than north coordinate")

    # Retrieve REGIS data from an API call on the custom url and write the content into "REGIS.nc" file
    url = f"https://www.dinodata.nl/opendap/REGIS/REGIS.nc.nc4?top%5B0:1:131%5D%5B{y_min}:1:{y_max}%5D%5B{x_min}:1:{x_max}%5D"
    save_regis_data_from_url(url)
    ds = xarray.open_dataset(PATH_REGIS_FILE)
    ds = ds.dropna("layer", how="all")
    ds = ds.where(ds.top > bottom_level_query, drop=True)
    return ds


def get_longitudinal_regis_soil_layouts(
    polygon: Polygon, trajectory: LineString, bottom_level_query: int
) -> List[SoilLayout]:
    """
    - polygon: Region within which to parse REGIS [RD coordinates]
    - trajectory: linestring of points for which the soillayouts need to be found (m, RD)
    - bottom level query: until wat depth to parse the regis model [m]
    Returns: a list for each point on the trajectory, the closest regis_soilLayout that was found within the
    polygon"""
    all_regis_soil_layouts = get_regis_soil_layouts_in_region(polygon, bottom_level_query)
    coords = [key for key in all_regis_soil_layouts.keys()]
    regis_soil_layouts = []
    for point in trajectory.coords:
        closest_point_index = distance.cdist([[*point]], coords).argmin()
        regis_soil_layouts.append(all_regis_soil_layouts[coords[closest_point_index]])
    return regis_soil_layouts


def get_regis_soil_layouts_in_region(
    polygon: Polygon, bottom_level_query: int = -30
) -> Dict[Tuple[int, int], SoilLayout]:
    """
    - polygon: Region within which to parse REGIS [RD coordinates]
    - bottom level query: until wat depth to parse the regis model [m]
    returns:
    - dict[(x,y)]: SoilLayout
    """
    x_min, y_min, x_max, y_max = polygon.bounds
    ds = get_regis_dataset(x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max, bottom_level_query=bottom_level_query)
    regis_data = parse_regis_top_layer(ds)
    soil_layouts = {}

    for location in regis_data:
        sorted_top_of_layers = sorted(regis_data[location].keys())  # sort by depth
        bottom_of_layer = sorted_top_of_layers[0]
        soil_layers = []
        previous_soil_name = get_REGIS_hydrogeological_name(regis_data[location][bottom_of_layer])
        soil_name = ""

        for top_of_layer in sorted_top_of_layers:
            soil_name = get_REGIS_hydrogeological_name(regis_data[location][top_of_layer])
            # if the soil is still the same, do nothing
            if soil_name not in previous_soil_name:  # new soil!
                # save previous soilLayer
                soil = Soil(previous_soil_name, find_regis_color(previous_soil_name))
                soil_layers.append(SoilLayer(soil, top_of_layer, bottom_of_layer))

                # start new layer
                bottom_of_layer = top_of_layer
                previous_soil_name = soil_name

        # also add last detected soil
        soil = Soil(soil_name, find_regis_color(previous_soil_name))
        soil_layers.append(SoilLayer(soil, sorted_top_of_layers[-1], bottom_of_layer))
        soil_layouts[location] = SoilLayout(soil_layers)

    return soil_layouts


def find_regis_color(soil_name):
    """add a color to each layer based on the regis name"""
    if "zandige" in soil_name:
        return Color(255, 255, 0)
    if "venige" in soil_name:
        return Color(157, 78, 64)
    if "kleiige" in soil_name:
        return Color(157, 78, 64)
    # else complex
    return Color(0, 146, 0)


def parse_regis_top_layer(dataset: xarray.Dataset) -> Dict[Tuple[int, int], dict]:
    """Parse a REGIS x.array.Dataset and return a dictionnary with soil name by depth and by location
    :param dataset: xarray.Dataset obtained from a .nc file
    :return: dictionary with following structure :
             - key: (x, y): Tuple[int, int]  coordinates in RD
             - value: dict with the following structure:
                      - key: dapth of top layer: float [mNAP]
                      - value: soil_name: str
    """
    layers = dataset.coords.get("layer").values
    data = {layer.decode(): data.values for layer, data in zip(layers, dataset.top)}

    soils_by_depth = {}

    for i, (x, y) in enumerate(zip(dataset["x"].values, dataset["y"].values)):
        soils_by_depth[(x, y)] = {}
        for soil_name in data.keys():  # for each soil type
            for layer in data[soil_name]:  # there can be more than one layer with a given soil
                if not np.isnan(layer[i]):
                    soils_by_depth[(x, y)][layer[i]] = soil_name  # if there is height for the layer, add it

    return soils_by_depth


def get_REGIS_hydrogeological_name(layer_code: str) -> str:
    """
    Return the full name of the REGIS geological layer based on its code.
    Source: https://www.dinoloket.nl/sites/default/files/file/DINOloket_Modeleenheden_REGIS_II_v2r2_20170814.pdf
    """
    try:
        primary_name = layer_code[0:2]
        if len(layer_code) == 3:
            secondary_name = layer_code[-1]
            return (
                REGIS_PRIMARY_FORMATION_NAME_CODE_MAPPING[primary_name]
                + ","
                + REGIS_SECONDARY_FORMATION_NAME_CODE_MAPPING[secondary_name]
            )

        secondary_name = layer_code[-2]
        number = layer_code[-1]
        if len(layer_code) == 4:
            return (
                REGIS_PRIMARY_FORMATION_NAME_CODE_MAPPING[primary_name]
                + ", "
                + number
                + "e "
                + REGIS_SECONDARY_FORMATION_NAME_CODE_MAPPING[secondary_name]
            )
        middle_name = layer_code[2:4]
        return (
            REGIS_PRIMARY_FORMATION_NAME_CODE_MAPPING[primary_name]
            + ", "
            + REGIS_MIDDLE_FORMATION_NAME_CODE_MAPPING[middle_name]
            + ", "
            + number
            + "e "
            + REGIS_SECONDARY_FORMATION_NAME_CODE_MAPPING[secondary_name]
        )
    except KeyError:
        print(f"WARNING: Found unknown layer code in REGIS model: {layer_code}")
        return "onbekend"
