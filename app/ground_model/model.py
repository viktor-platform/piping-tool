import gc
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from io import StringIO
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import numpy as np
import polars as pl
from dataclasses_json import dataclass_json
from munch import Munch
from numpy import array
from numpy import average
from numpy import mean
from numpy import nan
from pandas import DataFrame as PandasDataFrame
from polars import DataFrame as PolarDataFrame
from scipy.spatial import distance
from shapely.geometry import LineString
from shapely.geometry import MultiPoint
from shapely.geometry import Point

from app.ground_model.constants import AQUIFER_TNO_SOIL_CODES
from app.ground_model.constants import COVER_LAYER_COLOR
from app.ground_model.constants import FIRST_AQUIFER_COLOR
from app.ground_model.constants import INTERMEDIATE_COLOR
from app.ground_model.constants import LITHOLOGY_CODE_NAME_MAPPING
from app.ground_model.constants import LITHOLOGY_COLOR_DICT
from app.ground_model.constants import SECOND_AQUIFER_COLOR
from app.lib.shapely_helper_functions import convert_rgb_string_to_tuple
from viktor import Color
from viktor import UserException
from viktor.geo import Soil
from viktor.geo import SoilLayer
from viktor.geo import SoilLayout
from viktor.utils import memoize


@dataclass_json
@dataclass
class SoilParameters:
    aquifer: bool
    gamma_wet: float
    gamma_dry: float
    vertical_permeability: float
    horizontal_permeability: float
    grain_size_d70: float


def build_soil_layout_from_tno_dataframe(
    tno_dataframe: Union[PolarDataFrame, PandasDataFrame], point_coordinates: Tuple[float, float]
) -> SoilLayout:
    """
    Create a SoilLayout class from the VIKTOR SDK from the TNO ground model.
    By default, the TNO measurement are given from bottom to top for a given location. The z measurement is given
    in meters.
    :param tno_dataframe: Subset of the TNO csv ground model for a specific profile. This is a Polar DataFrame
    :param point_coordinates: (x, y) coordinates of a TNO Voxel for which filtering is applied.
    :return: instance of the SoilLayout class
    """
    # Get the TNO data for the specified point only.
    tno_dataframe = tno_dataframe.filter((pl.col("x") == point_coordinates[0]) & (pl.col("y") == point_coordinates[1]))

    if isinstance(tno_dataframe, PolarDataFrame):
        tno_dataframe = tno_dataframe.to_pandas()

    BUFFER_BELOW_LOWEST_MEASUREMENT = 0.5  # m
    bottom = tno_dataframe["z"].iloc[0] - BUFFER_BELOW_LOWEST_MEASUREMENT
    # TODO: convert logic below in Polars
    tno_dataframe["bottom"] = [bottom] + tno_dataframe["z"].shift(1).to_list()[1:]
    tno_dataframe["layers"] = tno_dataframe.apply(from_row_build_layers, axis=1)

    soil_layers = tno_dataframe["layers"].to_list()
    soil_layers.reverse()
    return SoilLayout(soil_layers=soil_layers)


def from_row_build_layers(row):
    soil_code = row.lithoklasse
    soil = Soil(name=LITHOLOGY_CODE_NAME_MAPPING[soil_code], color=LITHOLOGY_COLOR_DICT[soil_code])

    return SoilLayer(
        soil=soil,
        top_of_layer=row.z,
        bottom_of_layer=row.bottom,
        properties={
            "horizontal_permeability": abs(row.k_hor),
            "vertical_permeability": abs(row.k_vert),
            "gamma": row.v_gewicht,
            "aquifer": soil_code in AQUIFER_TNO_SOIL_CODES,  # check if the soil type is a default aquifer
            "kans_1_veen": row.kans_1_veen * 100,
            "kans_2_klei": row.kans_2_klei * 100,
            "kans_3_kleiig_zand": row.kans_3_kleiig_zand * 100,
            "kans_5_zand_fijn": row.kans_5_zand_fijn * 100,
            "kans_6_zand_matig_grof": row.kans_6_zand_matig_grof * 100,
            "kans_7_zand_grof": row.kans_7_zand_grof * 100,
        },
    )


def convert_soil_layout_to_input_table(soil_layout: SoilLayout) -> List[dict]:
    """Converts a SoilLayout to the parametrisation representation (Field = InputTable).
    inputs:   tno_soil_layout -- viktor SoilLayout
    returns:  List [ dictionaries ] with Structure:     [ {'name': 'Zand grof', 'top_of_layer': -5},
                                                          {'name': 'Zand grof', 'top_of_layer': -8},
                                                          ...
                                                        ]"""
    table_input_soil_layers = [
        {"name": layer.soil.name, "top_of_layer": layer.top_of_layer, "aquifer": layer.properties.aquifer}
        for layer in soil_layout.layers
    ]
    return table_input_soil_layers


def convert_input_table_to_soil_layout(
    bottom_of_soil_layout_user: Union[float, str],
    soil_layers_from_table_input: List[dict],
    material_table: List,
) -> SoilLayout:
    """Creates a SoilLayout from the user input.

    :param bottom_of_soil_layout_user: Bottom of soil layout in [m]
    :param soil_layers_from_table_input: Table where a row represents a layer.
    Each row should contain a soil name and top of layer [m].
    :param soils: Dictionary with soil names and their respective Soil.
    :return: SoilLayout
    """

    bottom = bottom_of_soil_layout_user
    soil_layers = []
    for layer in reversed(soil_layers_from_table_input):
        soil_name = layer["name"]
        top_of_layer = layer["top_of_layer"]
        aquifer = layer.get("aquifer")

        try:

            soil_layers.append(
                get_soil_layer_from_soil_type(
                    material_table,
                    soil_type=soil_name,
                    bottom_of_layer=bottom,
                    top_of_layer=top_of_layer,
                    overwrite_aquifer=aquifer,
                )
            )
        except KeyError:
            raise UserException(f"{soil_name} is niet beschikbaar in de materiaaltabel.\n")
        bottom = top_of_layer  # Set bottom of next soil layer to top of current layer.
    return SoilLayout(soil_layers[::-1])


def read_tno_csv(tno_file_content: str) -> PolarDataFrame:
    """Read and return the TNO ground model csv as a PolarDataFrame"""

    tno_df = pl.read_csv(
        StringIO(tno_file_content),
        columns=[
            "x",
            "y",
            "z",
            "lithostrat",
            "lithoklasse",
            "v_gewicht",
            "k_hor",
            "k_vert",
            "kans_1_veen",
            "kans_2_klei",
            "kans_3_kleiig_zand",
            "kans_5_zand_fijn",
            "kans_6_zand_matig_grof",
            "kans_7_zand_grof",
        ],
        dtype={
            "x": pl.datatypes.Float32,
            "y": pl.datatypes.Float32,
            "z": pl.datatypes.Float32,
            "lithostrat": pl.datatypes.Int32,
            "lithoklasse": pl.datatypes.Int32,
            "v_gewicht": pl.datatypes.Float32,
            "k_hor": pl.datatypes.Float32,
            "k_vert": pl.datatypes.Float32,
            "kans_1_veen": pl.datatypes.Float32,
            "kans_2_klei": pl.datatypes.Float32,
            "kans_3_kleiig_zand": pl.datatypes.Float32,
            "kans_5_zand_fijn": pl.datatypes.Float32,
            "kans_6_zand_matig_grof": pl.datatypes.Float32,
            "kans_7_zand_grof": pl.datatypes.Float32,
        },
    )

    return tno_df


@memoize
def get_filtered_tno_data_serialized(
    tno_file_content: str,
    target_points: List[Tuple[float, float]],
    ground_model_params: dict,
    are_target_points_voxels: bool = False,
) -> List[dict]:
    """Memoizable version of `get_filtered_tno_data` to avoid building Soil
    Use this function cautiously: it will improve speed on the one hand but might also shoot up the memory usage
    """
    tno_df = read_tno_csv(tno_file_content)

    ground_model_coordinates_data = ground_model_params.get("data")

    # Get coordinates of the TNO voxels for which the model will be filtered
    x_list, y_list = [], []
    try:
        for point_coord in target_points:
            if are_target_points_voxels:  # if target point is already at the voxel, no need to get the closest voxel.
                x, y = point_coord
            else:
                x, y = get_closest_tno_points(point_coord, ground_model_coordinates_data)
            x_list.append(x)
            y_list.append(y)

        # Filter dataframe
        filtered_df = tno_df.filter(pl.col("x").is_in(x_list) & pl.col("y").is_in(y_list))

        # release memory storage
        del tno_df
        gc.collect()

        return [
            build_soil_layout_from_tno_dataframe(tno_dataframe=filtered_df, point_coordinates=(x, y)).serialize()
            for x, y in zip(x_list, y_list)
        ]
    except TypeError:  # is target_points is an empty collection
        raise UserException("Te smalle voorland of achterland lengte")


def get_filtered_tno_data(
    tno_file_content: str,
    target_points: Union[MultiPoint, LineString, Point],
    ground_model_params: Munch,
    are_target_points_voxels: bool = False,
) -> List[SoilLayout]:
    """Read the TNO csv model and filter it to only keep the data close to the exit points.
    This is a necessary step to prevent the memory from shooting up.
    Use of Polars DataFrame is *necessary* here? Pandas is using too much memory.

    :return: Returns a subset of the TNO model as a PolarDataFrame, and also lists of x,y coordinates of the
    closest TNO voxel for each exit point
    """

    if isinstance(target_points, MultiPoint):
        target_points = target_points.geoms
    elif isinstance(target_points, (LineString, Point)):
        target_points = target_points.coords

    tno_df = read_tno_csv(tno_file_content)

    ground_model_coordinates_data = ground_model_params.data

    # Get coordinates of the TNO voxels for which the model will be filtered
    x_list, y_list = [], []
    try:
        for point_coord in target_points:
            if are_target_points_voxels:  # if target point is already at the voxel, no need to get the closest voxel.
                x, y = point_coord
            else:
                x, y = get_closest_tno_points(point_coord, ground_model_coordinates_data)
            x_list.append(x)
            y_list.append(y)

        # Filter dataframe
        filtered_df = tno_df.filter(pl.col("x").is_in(x_list) & pl.col("y").is_in(y_list))

        # release memory storage
        del tno_df
        gc.collect()

        return [
            build_soil_layout_from_tno_dataframe(tno_dataframe=filtered_df, point_coordinates=(x, y))
            for x, y in zip(x_list, y_list)
        ]
    except TypeError:  # is target_points is an empty collection
        raise UserException("Te smalle voorland of achterland lengte")


def get_closest_tno_points(
    target_point: Union[Point, Tuple[float, float]], tno_data: List[List[float]]
) -> Tuple[float, float]:
    """Return the closest point coordinates of a target point from the TNO ground model
    :param target_point: Shapely point or List coordinates of the target point for which the closest TNO point
    must be returned
    :param tno_data: Dataframe of the tno ground model
    :return: RD coordinates (x, y) of the closest TNO point
    """
    if isinstance(target_point, Point):
        closest_point_index = distance.cdist([*target_point.coords], tno_data).argmin()
    else:
        closest_point_index = distance.cdist([[*target_point]], tno_data).argmin()
    return tuple(tno_data[closest_point_index])


def check_validity_of_classification_table(classification_table: List):
    """Checks validity of classification table"""
    classification_table_temp = deepcopy(classification_table)

    classification_table_temp = [
        Munch({k: (str(999) if (v == "-" and k == "top_of_layer") else v) for k, v in row.items()})
        for row in classification_table_temp
    ]  # Temp for "-" conditions
    classification_table_temp = [
        Munch({k: (str(-999) if (v == "-" and k == "bottom_of_layer") else v) for k, v in row.items()})
        for row in classification_table_temp
    ]  # Temp for "-" conditions

    for i, row_loop_1 in enumerate(classification_table_temp):  # Check for empty cells
        if row_loop_1.layer is None:
            raise UserException(f"Classificatietabel fout: geef lithoklasse van {row_loop_1.layer}")

        if row_loop_1.top_of_layer is None:
            raise UserException(f"Classificatietabel fout: geef bovenkant laag van {row_loop_1.layer}.")

        if row_loop_1.bottom_of_layer is None:
            raise UserException(f"Classificatietabel fout: geef onderland laag van {row_loop_1.layer}.")

        if row_loop_1.soil_type is None:
            raise UserException(f"Classificatietabel fout: geef grondsoort van{row_loop_1.layer}.")

        for row_loop_2 in classification_table_temp[i + 1 :]:
            if (row_loop_1.layer == row_loop_2.layer) and (
                float(row_loop_2.top_of_layer) > float(row_loop_1.bottom_of_layer)
            ):  # Check for overlapping layers of same type
                raise UserException(f"Classificatietabel fout: bovenkant laag van {row_loop_1.layer} is in conflict.")


def classify_tno_soil_model(
    tno_soil_layout: SoilLayout,
    classification_table: List,
    material_table: List,
    minimal_aquifer_thickness: float,
) -> Union[List[SoilLayout], SoilLayout]:
    """Classify the raw tno soil model based on the classification table and return a SoilLayout object"""
    base_soil_layers = []
    previous_soil_type = ""
    for tno_layer in tno_soil_layout.layers:  # Loop over all the rows of the TNO profile
        tno_soil_name = tno_layer.soil.name
        soil_type = None

        for row in classification_table:
            if row.layer == tno_soil_name:
                row.bottom_of_layer = row.bottom_of_layer
                row.top_of_layer = row.top_of_layer
                # If the bottom boundary is set to '-' by user, then it is converted to the lowest possibly value, that is to say the bottom of the tno_soil_layout
                if row.bottom_of_layer == "-":
                    # This has to be converted into a string because the classification table has TextField rows instead of NumberField (to accomodate the infinity '-'). Therefore not converting into string here migth result in TypeError and inconsitencies later on
                    row.bottom_of_layer = -99999
                # If the top boundary is set to '-' by user, then it is converted to the highest possibly value, that is to say the top of the tno_soil_layout
                if row.top_of_layer == "-":
                    row.top_of_layer = 99999

                if tno_layer.top_of_layer >= float(row.bottom_of_layer) and tno_layer.top_of_layer <= float(
                    row.top_of_layer
                ):
                    soil_type = row.soil_type

        if soil_type is None:
            raise UserException(f"TNO grondsoort {tno_soil_name} is niet in classificatietabel")

        # Skip this voxel to agglomerate it with the previous one if they both share the same soil type
        if soil_type == previous_soil_type:
            continue

        # Extend the bottom of the last non-agglomerated layer to the right level
        if previous_soil_type != "":
            base_soil_layers[-1].bottom_of_layer = tno_layer.top_of_layer

        base_soil_layers.append(
            get_soil_layer_from_soil_type(
                material_table,
                soil_type,
                bottom_of_layer=tno_layer.bottom_of_layer,
                top_of_layer=tno_layer.top_of_layer,
                overwrite_aquifer=tno_layer.properties.aquifer,
            )
        )
        previous_soil_type = soil_type

    # ensure that the bottom of the layout is passed when last layer is aggregated with previous ones
    base_soil_layers[-1].bottom_of_layer = tno_soil_layout.layers[-1].bottom_of_layer
    check_aquifer_thickness(base_soil_layers, minimal_aquifer_thickness)
    return SoilLayout(base_soil_layers)


def generate_layouts_per_aquifer(base_soil_layers: List[SoilLayer]) -> List[List[SoilLayer]]:
    """
    The base_soil_layers is a soil layout for which multiple layers are considered as aquifer (2 max). This function
     returns a collection of soil layouts which contains only one aquifer.
     Example:

     This base_soil_layers         results in 2 layouts:


     layer | aquifer |                       layer | aquifer                         layer | aquifer
     --------------------                   -----------------                       ------------------
       1   |  False  |                           1  | False                             1   |  False
       2   |  True   |                           2  | True            and               2   |  False
       3   |  False  |                           3  |  False                            3   |  False
       4   |  True   |                           4  |  False                            4   |  True

    :param base_soil_layers: List of SoilLayers
    :return:
    """
    # if the base soil layers has only one aquifer, it is unnecessary to deepcopy (it saves some memory)
    if has_single_aquifer(base_soil_layers):
        return [base_soil_layers]
    list_duplicated_layouts = []
    soil_layers_copy = deepcopy(base_soil_layers)
    for layer in soil_layers_copy:
        layer.properties.aquifer = False

    has_aquifer = False
    for index, layer in enumerate(base_soil_layers):
        if layer.properties.aquifer:
            has_aquifer = True
            copy_soil_layer = deepcopy(soil_layers_copy)
            copy_soil_layer[index].properties.aquifer = True
            list_duplicated_layouts.append(copy_soil_layer)

    if not has_aquifer:  # Fallback when the original soil layout does not have an aquifer.
        list_duplicated_layouts.append(soil_layers_copy)

    return list_duplicated_layouts


def has_single_aquifer(base_soil_layout: List[SoilLayer]) -> bool:
    """Return True is the base_soil_layout has one or no aquifer, and false otherwise."""
    counter = 0
    for layer in base_soil_layout:
        if layer.properties.aquifer:
            counter += 1
    if counter in [0, 1]:
        return True
    return False


def check_aquifer_thickness(layers: List[SoilLayer], minimal_aquifer_thickness: float):
    """
    Checks if the permeables soil layers are thick enough to be considered an aquifer based on a threshold value and updates the SoilLayer properties accordingly
    :param layers: list of SoilLayer to iterate
    :param minimal_aquifer_thickness: minimal thickness for a permeable layer to be considered aquifer
    :return:
    """
    for layer in layers:
        if layer.properties.aquifer and (layer.top_of_layer - layer.bottom_of_layer) < minimal_aquifer_thickness:
            layer.properties.aquifer = False


def get_soil_layer_from_soil_type(
    material_table: List[Munch],
    soil_type: str,
    bottom_of_layer: Union[float, str],
    top_of_layer: float,
    overwrite_aquifer: Optional[bool] = None,
) -> SoilLayer:
    """
    :param material_table: list of all the soils defined with their properties
    :param soil_type: name of the user defined soil type
    :param bottom_of_layer: bottom of the later in m
    :param top_of_layer: top of the layer in m
    :param overwrite_aquifer:
    :return: SoilLayer object with the corresponding properties from the material table
    """
    material_properties = {row.name: row for row in material_table}.get(soil_type)
    soil_parameters = SoilParameters(
        gamma_wet=material_properties.gamma_wet,
        gamma_dry=material_properties.gamma_dry,
        vertical_permeability=material_properties.k_vert,
        horizontal_permeability=material_properties.k_hor,
        grain_size_d70=material_properties.d_70,
        aquifer=material_properties.aquifer if overwrite_aquifer is None else overwrite_aquifer,
    )
    if not material_properties.color:
        raise UserException(f"Ontbrekende kleurcode van grondsoort {material_properties.name}")
    soil = Soil(name=material_properties.name, color=Color(*convert_rgb_string_to_tuple(material_properties.color)))
    return SoilLayer(
        soil=soil,
        top_of_layer=top_of_layer,
        bottom_of_layer=bottom_of_layer,
        properties=soil_parameters.to_dict(),  # pylint: disable=no-member
    )


def get_leakage_length_properties(
    soil_layout: SoilLayout,
    simplified_1d_rep_soil_layout: Optional[SoilLayout] = None,
    from_representative_layout: bool = False,
    for_second_aquifer: bool = False,
) -> Tuple[float, float, float, float]:
    """Return the properties of a TNO voxel required for the calculation of the leakage_length:
    Permeability and thickness of both cover layer and aquifer

    :param soil_layout: SoilLayout object for which the leakage properties are derived from
    :param simplified_1d_rep_soil_layout: dict storing the representative layers of the whole segment.
    :param from_representative_layout: bool to enable/disable if the leakage properties should be derived from the soil
    layout of the leakage point only or also from the representative layout.
    :param for_second_aquifer: False if the leakage properties should be calculated for the first aquifer, True for the
    second aquifer
    :return: return as a tuple the 4 parameters required for the calculation of the leakage length: permeability and
    thickness of the cover layer and first aquifer
    """
    if from_representative_layout:
        if not simplified_1d_rep_soil_layout:
            raise UserException("Geen representatieve bodemopbouw is geselecteerd voor dit segment")
        return get_leakage_length_properties_from_representative_layout(
            soil_layout, simplified_1d_rep_soil_layout, for_second_aquifer
        )
    return get_properties_from_leakage_point(soil_layout, for_second_aquifer)


def get_leakage_length_properties_from_representative_layout(
    soil_layout_leakage_point: SoilLayout,
    simplified_1d_rep_soil_layout: SoilLayout,
    for_second_aquifer: bool = False,
) -> Tuple[float, float, float, float]:
    """Get the leakage length parameters from:
    - the representative layers of the segment: thickness and permeability of the first aquifer (global variables)
    - the soil layout of the leakage point: thickness and permeability of the cover layer
    :param soil_layout_leakage_point: SoilLayout at the location of the leakage point (which corresponds to a GEOTOP
    voxel). It can be either the raw GEOTOP Soilayout or it's classified counterpart.
    :param simplified_1d_rep_soil_layout: representative simplified 1d SoilLayout of the segment (dijkvak)
    :param for_second_aquifer: False if the leakage properties should be calculated for the first aquifer, True for the
    second aquifer
    """

    # Cover layer properties
    k_cover_layer = []
    for layer in soil_layout_leakage_point.layers:
        if layer.properties.aquifer:
            break
        k_cover_layer.append(layer.properties.vertical_permeability)
        cover_layer_bottom = layer.bottom_of_layer

    cover_layer_thickness = soil_layout_leakage_point.layers[0].top_of_layer - cover_layer_bottom
    k_cover_layer = np.mean([k for k in k_cover_layer if k is not None])

    if not for_second_aquifer:
        # First aquifer properties
        cover, first_aquifer, *others = simplified_1d_rep_soil_layout.layers  # pylint: disable=unused-variable
        first_aquifer_thickness = first_aquifer.thickness
        k_first_aquifer = first_aquifer.properties.get("horizontal_permeability")
        return cover_layer_thickness, k_cover_layer, first_aquifer_thickness, k_first_aquifer
    try:
        cover, first_aquifer, intermediate, second_aquifer = simplified_1d_rep_soil_layout.layers
    except ValueError:
        raise UserException("De representatieve grondopbouw heeft geen 2e aquifer.")

    cover_layer_thickness = cover.thickness + first_aquifer.thickness + intermediate.thickness
    # TODO: check if k_cover_layer is correct
    k_cover_layer = mean(
        [
            cover.properties.vertical_permeability,
            first_aquifer.properties.vertical_permeability,
            intermediate.properties.vertical_permeability,
        ]
    )

    second_aquifer_thickness = second_aquifer.thickness
    k_second_aquifer = second_aquifer.properties.get("horizontal_permeability")
    return cover_layer_thickness, k_cover_layer, second_aquifer_thickness, k_second_aquifer


def get_properties_from_leakage_point(
    soil_layout_leakage_point: SoilLayout, for_second_aquifer: bool = False
) -> Tuple[float, float, float, float]:
    """
    Return the properties that are necessary for the calculation of the leakage length, based solely on the layout
    of the leakage point (= GEOTOP voxel).
    :param soil_layout_leakage_point: SoilLayout at the location of the leakage point (which corresponds to a GEOTOP
    voxel). It can be either the raw GEOTOP Soilayout or it's classified counterpart.
    :param for_second_aquifer: False if the leakage properties should be calculated for the first aquifer, True for the
    second aquifer
    :return:
    """

    grouped_layers = group_layers(soil_layout_leakage_point)
    aquifer_properties = get_aquifers_effective_properties_from_grouped_layers(grouped_layers)

    if for_second_aquifer:
        aquifer = "second_aquifer"
        k_cover_layer = mean(
            list(
                filter(
                    None,
                    [
                        layer.properties.vertical_permeability
                        for layer in grouped_layers["cover_layer"]
                        + grouped_layers["first_aquifer"]
                        + grouped_layers["intermediate"]
                    ],
                )
            )
        )
    else:
        aquifer = "first_aquifer"
        k_cover_layer = mean(
            list(filter(None, [layer.properties.vertical_permeability for layer in grouped_layers["cover_layer"]]))
        )

    cover_layer_thickness = grouped_layers["cover_layer"][0].top_of_layer - grouped_layers[aquifer][0].top_of_layer

    aquifer_thickness = grouped_layers[aquifer][0].top_of_layer - grouped_layers[aquifer][-1].bottom_of_layer
    k_aquifer = aquifer_properties[aquifer].get("permeability")
    return cover_layer_thickness, k_cover_layer, aquifer_thickness, k_aquifer


def group_layers(soil_layout: SoilLayout) -> Dict[str, List[SoilLayer]]:
    """
    Group SoilLayers together and determine if they belong to on the following affiliation ["cover_layer", "first_aquifer",
    "intermediate", "second_aquifer"].
    :param soil_layout: base soil layout, obtained from a converted user soil layout table, for which the layers are
    grouped
    :return: dictionary with the following structure : {"cover_layer": [SoilLayer(), ...], "first_aquifer": [...], ...}
    """
    is_cover_layer, is_first_aquifer, is_intermediate_aquitard, is_second_aquifer = True, False, False, False
    layer_mapping = defaultdict(list)
    for layer in soil_layout.layers:
        if is_cover_layer:
            if layer.properties.aquifer:  # we have reached the first aquifer
                is_cover_layer = False
                is_first_aquifer = True

            else:
                layer_mapping["cover_layer"].append(layer)

        if is_first_aquifer:
            if layer.properties.aquifer:
                layer_mapping["first_aquifer"].append(layer)
            else:  # This is then no longer the first aquifer
                is_first_aquifer = False
                is_intermediate_aquitard = True

        if is_intermediate_aquitard:
            if layer.properties.aquifer:
                is_intermediate_aquitard = False
                is_second_aquifer = True
            else:
                layer_mapping["intermediate"].append(layer)

        if is_second_aquifer:
            if layer.properties.aquifer:
                layer_mapping["second_aquifer"].append(layer)

            else:
                is_second_aquifer = False

    return layer_mapping


def get_aquifer_effective_properties(soil_layout: SoilLayout) -> dict:
    """Get the calculated effective aquifer properties based on a soil layout. The base soil layout can be obtained from
    the conversion of the user soil layout table"""
    grouped_layers = group_layers(soil_layout)
    return get_aquifers_effective_properties_from_grouped_layers(grouped_layers)


def get_aquifers_effective_properties_from_grouped_layers(grouped_layers: Dict[str, List[SoilLayer]]) -> dict:
    if not grouped_layers["first_aquifer"]:
        raise UserException("De classificatietabel mist ten minste een aquifer.")
    k_avg_first_aquifer = calc_effective_aquifer_permeability(grouped_layers["first_aquifer"])
    d70_first_aquifer = grouped_layers["first_aquifer"][0].properties.get("grain_size_d70")

    if grouped_layers["second_aquifer"]:
        k_avg_second_aquifer = calc_effective_aquifer_permeability(grouped_layers["second_aquifer"])

        # The effective grain size of the aquifer is the grain size of the highest sandy layer.
        d70_second_aquifer = grouped_layers["second_aquifer"][0].properties.get("grain_size_d70")
        return {
            "first_aquifer": {"permeability": k_avg_first_aquifer, "d70": d70_first_aquifer},
            "second_aquifer": {
                "permeability": k_avg_second_aquifer,
                "d70": d70_second_aquifer,
                "is_second_aquifer": True,
            },
        }
    return {
        "first_aquifer": {"permeability": k_avg_first_aquifer, "d70": d70_first_aquifer},
        "second_aquifer": {"permeability": None, "d70": None, "is_second_aquifer": False},
    }


def calc_effective_aquifer_permeability(layers: List[SoilLayer]) -> float:
    """Calculate the effective permeability of an aquifer made up of several layers.
    Source: https://www.helpdeskwater.nl/publish/pages/157029/sh-piping-28-mei-2021-v4.pdf page 110
    :param layers: List of consecutive sandy layers composing an aquifer.
    """
    permeabilities = [layer.properties.horizontal_permeability for layer in layers]
    thicknesses = array([layer.thickness for layer in layers])

    # Check if the first layer is of the aquifer is the least permeable (<=> has the smallest permeability)
    if any(layer_k < permeabilities[0] for layer_k in permeabilities[1:]):
        # If the highest layer has the highest permeability and if this layer is at least 1m and at least bigger than
        # 10% of the total aquifer thickness, then the permeability of the highest layer is kept.
        if layers[0].thickness > 1 and layers[0].thickness > sum(thicknesses) / 10:
            return permeabilities[0]

    # In any other case, the effective permeability is the weighted average of the permeability of each layer, the
    # weights being the respective thicknesses.
    return average(array(permeabilities), weights=thicknesses)


def agglomerate_repr_soil_layer(
    layer_list: List[SoilLayer], soil: Soil, aquifer_params: Optional[Munch] = None
) -> SoilLayer:
    """Agglomerate a list of grouped SoilLayer into a single SoilLayer. The effective 'average' properties of the
    agglomerated layer depends on its nature: whether it's an aquifer or not
    :param layer_list: List of grouped SoilLayers that must be agglomerated
    :param soil: Soil object to be assigned to the agglomerated SoilLayer
    :param aquifer_params: aquifer parameters to be added to the properties of the agglomerated SoilLayer when relevant
    """

    if aquifer_params is None:
        properties = {
            "vertical_permeability": mean(
                [
                    layer.properties.vertical_permeability
                    for layer in layer_list
                    if layer.properties.vertical_permeability is not None
                ]
            ),
            "horizontal_permeability": mean(
                [
                    layer.properties.horizontal_permeability
                    for layer in layer_list
                    if layer.properties.horizontal_permeability is not None
                ]
            ),
            "gamma_dry": mean(
                [layer.properties.gamma_dry for layer in layer_list if layer.properties.gamma_dry is not None]
            ),
            "gamma_wet": mean(
                [layer.properties.gamma_wet for layer in layer_list if layer.properties.gamma_wet is not None]
            ),
            "grain_size_d70": None,
            "aquifer": False,
        }
    else:
        properties = {
            "vertical_permeability": aquifer_params.permeability,
            "horizontal_permeability": aquifer_params.permeability,
            "gamma_dry": mean(
                [layer.properties.gamma_dry for layer in layer_list if layer.properties.gamma_dry is not None]
            ),
            "gamma_wet": mean(
                [layer.properties.gamma_wet for layer in layer_list if layer.properties.gamma_wet is not None]
            ),
            "grain_size_d70": aquifer_params.d70,
            "aquifer": True,
        }
    return SoilLayer(
        top_of_layer=layer_list[0].top_of_layer,
        bottom_of_layer=layer_list[-1].bottom_of_layer,
        properties=properties,
        soil=soil,
    )


def build_simplified_1d_rep_soil_layout(base_soil_layout: SoilLayout, aquifer_params: Munch) -> SoilLayout:
    """Return a 1d representative SoilLayout which is simplified into 4 layers: cover_layer, first_aquifer,
    intermediate_aquitard and second_aquifer. This simplified SoilLayout is built from a base soil layout and the
    aquifer parameters defined by the user in the segment parametrization.

    :param base_soil_layout: base 1d detailed SoilLayout
    :param aquifer_params: dict-like structure with the user input properties of the aquifers: {'first_aquifer': {
    'permeability': 123, 'd70': 200}, 'second_aquifer': {'is_second_aquifer': True, ...}}
    """
    output_layers = []
    grouped_layers = group_layers(base_soil_layout)
    cover_layers = grouped_layers["cover_layer"]
    if cover_layers:
        output_layers.append(
            agglomerate_repr_soil_layer(
                cover_layers, soil=Soil(name="cover_layer", color=COVER_LAYER_COLOR, properties={"ui_name": "Deklaag"})
            )
        )

    first_aquifer_layers = grouped_layers["first_aquifer"]
    if first_aquifer_layers:
        output_layers.append(
            agglomerate_repr_soil_layer(
                first_aquifer_layers,
                soil=Soil(name="first_aquifer", color=FIRST_AQUIFER_COLOR, properties={"ui_name": "Eerste aquifer"}),
                aquifer_params=aquifer_params.first_aquifer,
            )
        )

    intermediate_layers = grouped_layers["intermediate"]
    if intermediate_layers:
        output_layers.append(
            agglomerate_repr_soil_layer(
                intermediate_layers,
                soil=Soil(
                    name="intermediate_aquitard",
                    color=INTERMEDIATE_COLOR,
                    properties={"ui_name": "Tussenligende aquitard"},
                ),
            )
        )

    second_aquifer_layers = grouped_layers["second_aquifer"]
    if aquifer_params.second_aquifer.is_second_aquifer and second_aquifer_layers:
        output_layers.append(
            agglomerate_repr_soil_layer(
                second_aquifer_layers,
                soil=Soil(name="second_aquifer", color=SECOND_AQUIFER_COLOR, properties={"ui_name": "Tweede aquifer"}),
                aquifer_params=aquifer_params.second_aquifer,
            )
        )
    return SoilLayout(output_layers)


def build_combined_rep_and_exit_point_layout(
    exit_point_layout: Munch, representative_segment_layout: SoilLayout
) -> SoilLayout:
    """
    Build a combined SoilLayout from the simplified representative SoilLayout of the segment (dijkvak) modified at the
    location of an exit point. The returned SoilLayout keeps the properties of the first aquifer and of all the layers
    below, the cover layer is obtained from the SoilLayout of the exit point.
    :param exit_point_layout: serialized SoilLayout at the exit point
    :param representative_segment_layout: simplified representative SoilLayout of the segment (dijkvak)
    :return:
    """
    # Adapt the first cover layer of the rep layout with the exit point
    rep_layout = deepcopy(representative_segment_layout)
    if len(representative_segment_layout.layers) <= 1:
        raise UserException("The dijkvak does not have an aquifer")  # TODO TRANSLATE
    exit_point_bottom_cover_layer = exit_point_layout.get("layers")[-1].get("bottom_of_layer")
    gamma_dry, gamma_wet, k_ver, k_h, thicknesses = [], [], [], [], []
    for layer in exit_point_layout.get("layers"):
        if layer["properties"]["aquifer"]:
            break
        thicknesses.append(layer.top_of_layer - layer.bottom_of_layer)
        exit_point_bottom_cover_layer = layer.get("bottom_of_layer")
        gamma_dry.append(layer["properties"].get("gamma_dry"))
        gamma_wet.append(layer["properties"].get("gamma_wet"))
        k_ver.append(layer["properties"].get("vertical_permeability"))
        k_h.append(layer["properties"].get("horizontal_permeability"))

    cover_layer = SoilLayer(
        top_of_layer=exit_point_layout.get("layers")[0].get("top_of_layer"),
        bottom_of_layer=exit_point_bottom_cover_layer,
        soil=representative_segment_layout.layers[0].soil,
        properties={
            "gamma_dry": safe_execute_average(nan, gamma_dry, thicknesses),
            "gamma_wet": safe_execute_average(nan, gamma_wet, thicknesses),
            "vertical_permeability": safe_execute_average(nan, k_ver, thicknesses),
            "horizontal_permeability": safe_execute_average(nan, k_h, thicknesses),
            "aquifer": False,
        },
    )

    if exit_point_bottom_cover_layer > rep_layout.layers[0].bottom_of_layer:
        # if the cover layer of the exit point is above the bottom of the dijkvak cover, then only the top of first
        # aquifer is updated.
        rep_layout.layers[1].top_of_layer = cover_layer.bottom_of_layer
    else:
        # Else, the layers of the dijvak are simply lowered by the difference between the bottom levels of the dijvak's
        # cover and the exit point layout's cover.
        extension_cover = rep_layout.layers[0].bottom_of_layer - exit_point_bottom_cover_layer
        for layer in rep_layout.layers[1:]:
            layer.top_of_layer = layer.top_of_layer - extension_cover
            layer.bottom_of_layer = layer.bottom_of_layer - extension_cover

    return SoilLayout([cover_layer, *rep_layout.layers[1:]])


def safe_execute_average(default: Any, values: List, thickness: List):
    """
    Try to safely execute the function average and return a default output if it fails for the TypeError exception.
    This allows to do try/except tests as one-liners.
    :param default: default output to be returned if test failed
    :param values: list of values to be averaged, can contain None values
    :param thickness: list of the weight thicknesses
    :return:
    """
    try:
        return average(array(values), weights=thickness)
    except TypeError:
        return default
