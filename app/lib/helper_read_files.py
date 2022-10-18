import zipfile
from collections import defaultdict
from io import BytesIO
from typing import List

import geopandas as gpd
import shapefile as pyshp
from fiona.io import ZipMemoryFile
from shapely.geometry import LineString

from viktor import File
from viktor import UserException
from viktor.api_v1 import FileResource
from viktor.geometry import GeoPoint
from viktor.geometry import GeoPolyline
from viktor.utils import memoize


def round_to_nearest_0_05(number: float) -> float:
    return round(number * 2 * 10) / 20


def shape_file_to_geo_poly_line(file: File) -> GeoPolyline:
    """Process shape files and convert it into a GeoPolyline.
    Several files extension must be present in the uploaded file: .shp, .shx, and .dbf. The content of these
    files is overwritten into the corresponding temp files.
    """
    zipshape = zipfile.ZipFile(BytesIO(file.getvalue_binary()))  # Open zip

    # Check if the zip contains the right file extensions
    file_names = zipshape.namelist()
    filename_mapping = {f"{file_name[-3:]}": file_name for file_name in file_names}
    for extension in ["shp", "shx", "dbf"]:
        if extension not in filename_mapping.keys():
            raise UserException(f"Shapefile ontbreekt van .{extension} bestand")

    # Read the content of the shapesfiles and create a shapefile object
    shapefile = pyshp.Reader(
        shp=zipshape.open(filename_mapping["shp"]),
        shx=zipshape.open(filename_mapping["shx"]),
        dbf=zipshape.open(filename_mapping["dbf"]),
    )

    # Pre-process data before setting the parametrization
    data_shapefile = []
    for shape in shapefile.shapes():
        data_shapefile.extend([*shape.points])
    if data_shapefile[0][1] > 180:  # check whether the coordinates of the LineString are given in RD coordinates
        return GeoPolyline(*[GeoPoint.from_rd(pt) for pt in data_shapefile])
    return GeoPolyline(*[GeoPoint(lon=pt[0], lat=pt[1]) for pt in data_shapefile])


@memoize
def entry_line_to_params(file: FileResource) -> GeoPolyline:
    """Process shape files upon uploading and create a EntryLine entity.
    Several files extension must be present in the uploaded file: .shp, .shx, and .dbf. The content of these
    files is overwritten into the corresponding temp files.
    """
    geo_poly_line = shape_file_to_geo_poly_line(file.file)
    return geo_poly_line


def process_dijkpalen_shape_file(file: FileResource) -> List[dict]:
    with zipfile.ZipFile(BytesIO(file.file.getvalue_binary())) as zf:
        # Fill mapping dictionary for the file names in the uploaded zipfile.
        filename_mapping = defaultdict(dict)
        for file_name in zf.namelist():
            if file_name[-1] == "/":  # exclude the folder name from namelist()
                continue
            root_name, extension = file_name.split(".")
            filename_mapping[root_name][extension] = file_name

    with ZipMemoryFile(BytesIO(file.file.getvalue_binary())) as zip_file:
        for root_name, files in filename_mapping.items():
            collection = zip_file.open(files.get("shp"))
            gdf = gpd.GeoDataFrame.from_features(list(collection))

            dijkpalen = []
            for _, point in gdf.iterrows():
                dijkpalen.append({"geometry": point["geometry"], "value": point["DIJKPLNR"]})

    return dijkpalen


def process_ditch_shape_file(file: FileResource, **kwargs) -> dict:
    """
    /! ONLY HDSR DITCH DATA CAN BE PROCESSED WITH THIS METHOD. Please write your own script to parse ditch data
    from a different source (another Waterschap) /!
    Process and parse a zip file of the ditch shapefile data and store into the parametrization.
    The zipfile can include multiple shapefile objects. The distinctions between polygon and polyline shapefiles is
    automatic but the distinction between dry and wet ditches is checked with the name of the shapefile. The polygon
    of the water at the surface is also distinguished from other polygons based on its name:

        - A polygon shapefile with the string 'water' in its name is classified as Watervlek: it's the polygon of the
         visible water level at the surface.
        - A polygon shapefile with the string 'droge' in its name is classified as a dry ditch's coverage.
        - A polyline shapefile with the string 'droge' in its name is classified as a center line of a dry ditch.
    """
    try:
        # Initialize shapefile data to None
        (
            dry_ditch_polygons,
            dry_ditch_center_lines,
            ditch_polygons,
            ditch_center_lines,
            water_ditch_polygons,  # pylint: disable=unused-variable
        ) = (
            None,
            None,
            None,
            None,
            None,
        )

        with zipfile.ZipFile(BytesIO(file.file.getvalue_binary())) as zf:
            # Fill mapping dictionary for the file names in the uploaded zipfile.
            filename_mapping = defaultdict(dict)
            for file_name in zf.namelist():
                if file_name[-1] == "/":  # exclude the folder name from namelist()
                    continue
                root_name, extension = file_name.split(".")
                filename_mapping[root_name][extension] = file_name

        with ZipMemoryFile(BytesIO(file.file.getvalue_binary())) as zip_file:
            for root_name, files in filename_mapping.items():
                collection = zip_file.open(files.get("shp"))
                gdf = gpd.GeoDataFrame.from_features(list(collection))

                if collection.schema.get("geometry") == "Polygon":
                    if "water" in root_name:
                        water_ditch_polygons = gdf  # pylint: disable=unused-variable

                    elif "droge" in root_name:
                        dry_ditch_polygons = gdf

                    else:
                        ditch_polygons = gdf
                elif collection.schema.get("geometry") == "LineString":

                    if "droge" in root_name:
                        dry_ditch_center_lines = gdf

                    else:
                        ditch_center_lines = gdf

        ditches = create_ditches_from_hdsr_data(ditch_polygons, ditch_center_lines)
        dry_ditches = create_ditches_from_hdsr_data(dry_ditch_polygons, dry_ditch_center_lines)

        return {
            "ditches": ditches,
            "dry_ditches": dry_ditches,
        }
    except:
        raise UserException("Incorrect ditch files data")


def create_ditches_from_hdsr_data(ditch_polygons: gpd.GeoDataFrame, ditch_center_lines: gpd.GeoDataFrame):
    """Ditch data from HDSR is a bit messy. The ditch polygons and center lines are not linked together and the
    relationship poylgon-center_line must be established. This is the reason behind the double loop below, to reassign
    the center line to each ditch polygon. A lot of shapely methods applied to the polygons and linestrings were tested
    without success. The criteria that returned the most satisfaction so far was to check if the middle point of each
    ditch linestring lies within the polygon of a ditch. If True, then the polygon and Linestring are linked together,
    they constitute a "Ditch object".

    """
    ditches = []
    ditch_center_lines.columns = map(str.lower, ditch_center_lines.columns)  # Make all the df keys lowercase

    # Code smell (double loop on df rows!!) but seems to work.
    for _, polygon_data in ditch_polygons.iterrows():
        base_polygon = polygon_data["geometry"].buffer(0)
        for _, var in ditch_center_lines.iterrows():
            line: LineString = var["geometry"]
            mid_point = line.interpolate(0.5, normalized=True)
            if mid_point.within(base_polygon):
                try:
                    ditches.append(
                        {
                            "ditch_polygon": base_polygon.exterior.coords,
                            "ditch_center_line": line.coords,
                            "water_depth": var["iws_w_watd"],
                            "talu_slope": var["iws_w_talu"],
                            "maintenance_depth": var["ws_onderho"],
                        }
                    )
                except KeyError:
                    raise UserException("Incorrect key for ditch data, please comply with HDSR format.")
    return ditches
