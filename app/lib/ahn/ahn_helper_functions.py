import io
import math
from typing import List
from typing import Tuple

import numpy as np
import pandas as pd
import PIL
import requests
from pandas import DataFrame
from PIL import Image
from shapely.geometry import MultiPoint
from sklearn.cluster import KMeans

from viktor import UserException


def fetch_ahn_z_values(
    df_data_points: pd.DataFrame, coverage: str = "ahn3_05m_dtm", resolution: float = 0.5, skip_clustering: bool = False
) -> pd.DataFrame:
    """
    Fetch height values from the AHN3.

    Parameters
    ----------
    df_data_points:
        Pandas DataFrame containing the following columns:
            +---+---+
            | x | y |
            +---+---+
            |   |   |
            +---+---+
    coverage:
        Dataset to be used. Possibilities at : https://www.pdok.nl/geo-services/-/article/actueel-hoogtebestand-nederland-ahn3-
        example: "ahn3_05m_dtm" ahn3 DTM with 0.5 m resolution
                 "ahn3_05m_dsm" ahn3 DSM with 0.5 m resolution
                 "ahn3_5m_dsm" ahn3 DSM with resolution of 5 m
    resolution:
        Resolution of the returned image. Should always be >= then the resolution of the coverage.
    skip_clustering:
        If False the clustering is skipped, do this only if points are few and close to each other
    Returns
    -------
    df_data_points
    +---+---+---+
    | x | y | z |
    +---+---+---+
    |   |   |   |
    +---+---+---+
    """
    # Cluster points to optimize the download process
    if skip_clustering:
        df_data_points = df_data_points.assign(cluster=0)
        dict_cluster_bbox = compute_bbox_from_cluster(df_data_points, resolution)
    else:
        df_data_points, dict_cluster_bbox = cluster_points(df_data_points, resolution)

    df_data_points = df_data_points.assign(z=None)
    # Fetch z values for each cluster
    for cluster, bbox in dict_cluster_bbox.items():
        img_array = request_data(bbox=bbox, coverage=coverage, resolution=resolution)
        df_data_points["z"].loc[df_data_points["cluster"] == cluster] = get_z_values(
            df_data_points[["x", "y"]].loc[df_data_points["cluster"] == cluster],
            bbox,
            img_array,
            resolution,
        )
        del img_array
    df_data_points["z"] = df_data_points["z"].apply(lambda x: round(x, 3))
    df_data_points["z"].loc[df_data_points["z"] >= 20000000] = np.nan
    df_data_points = df_data_points.drop(["cluster"], axis=1)
    return df_data_points


def request_data(bbox: List[float], coverage: str = "ahn3_05m_dtm", resolution: float = 0.5) -> np.ndarray:
    """
    Function that returns the tiff image within a bbox.

    Parameters
    ----------
    bbox:
        list of 4 elements:
        [bottom_left_x_coordinate,
        bottom_left_y_coordinate,
        top_right_x_coordinate,
        top_right_y_coordinate]
    coverage:
        Dataset to be used. Possibilities at : https://www.pdok.nl/geo-services/-/article/actueel-hoogtebestand-nederland-ahn3-
        example: "ahn3_05m_dtm" ahn3 DTM with 0.5 m resolution
                 "ahn3_05m_dsm" ahn3 DSM with 0.5 m resolution
                 "ahn3_5m_dsm" ahn3 DSM with resolution of 5 m
    resolution:
        Resolution of the returned image. Should always be >= then the resolution of the coverage.
    Returns
    -------
    np.ndarray
    """
    width = (bbox[2] - bbox[0]) / resolution
    height = (bbox[3] - bbox[1]) / resolution

    url = "https://geodata.nationaalgeoregister.nl/ahn3/wcs"
    params = dict(
        service="WCS",
        version="1.0.0",
        request="GetCoverage",
        format="GEOTIFF_FLOAT32",
        coverage=coverage,
        BBOX=f"{str(bbox[0])}, {str(bbox[1])}, {str(bbox[2])}, {str(bbox[3])}",
        crs="EPSG:28992",
        response_crs="EPSG:28992",
        width=str(width),
        height=str(height),
    )
    # Parse the URL with parameters
    q = requests.Request("GET", url, params=params).prepare().url
    if q is None:
        raise ValueError("request is None")
    if requests.get(q).status_code == 200:
        try:
            return np.array(Image.open(io.BytesIO(requests.get(q).content)))
        except PIL.UnidentifiedImageError:
            raise UserException("AHN unavailable, retry later.")
    else:
        requests.get(q).raise_for_status()
        return None


def get_z_values(df_x_y: pd.DataFrame, bbox: List[float], img_array: np.ndarray, resolution: float) -> List[float]:
    """
    Returns z values for a pd.DataFrame and img_array
    Parameters
    ----------
    df_x_y:
        Dataframe with columns: [x, y]
    bbox:
        list of 4 elements:
        [bottom_left_x_coordinate,
        bottom_left_y_coordinate,
        top_right_x_coordinate,
        top_right_y_coordinate]
    img_array:
        Array of the downloaded tiff Image
    resolution:
        Resolution of the returned image.
    Returns
    -------
    List of z values
    """
    # Add bathymetry check
    return [z_value(x, y, img_array, resolution, bbox) for x, y in zip(df_x_y["x"], df_x_y["y"])]


def z_value(x: float, y: float, img_array: np.ndarray, resolution: float, bbox: List[float]) -> float:
    """
    Given the x and y coordinates return the correspondent z value
    Parameters
    ----------
    x
        X-coordinate RD system
    y
        Y-coordinate RD system
    img_array
        Array of the downloaded tiff Image
    resolution:
        Resolution of the returned image.
    bbox:
        list of 4 elements:
        [bottom_left_x_coordinate,
        bottom_left_y_coordinate,
        top_right_x_coordinate,
        top_right_y_coordinate]

    Returns
    -------
    Z value
    """
    col = math.floor((x - bbox[0]) / resolution)
    row = math.floor((bbox[3] - y) / resolution)
    try:
        return img_array[row][col]
    except TypeError:
        raise UserException("AHN unavailable, retry later.")


def cluster_points(
    df_data_points: pd.DataFrame, resolution: float, limits: tuple = (2000, 2000)
) -> Tuple[pd.DataFrame, dict]:
    """
    Create clusters of points

    Parameters
    ----------
    df_data_points:
        Pandas DataFrame containing the following columns:
            +---+---+
            | x | y |
            +---+---+
            |   |   |
            +---+---+
    resolution:
        Resolution of the returned image. Should always be >= then the resolution of the coverage.
    limits:
        Maximum height and width of bbox
    Returns
    -------
    Tuple of:
        - df_data_points
            +---+---+---------+
            | x | y | cluster |
            +---+---+--------+
            |   |   |        |
            +---+---+--------+
        - dict_cluster_bbox
            Dictionary with clusters bbox
    """
    n = 1  # initial number of clusters
    df_data_points = df_data_points.assign(cluster=0)
    while True:
        km = KMeans(n_clusters=n, random_state=0).fit(df_data_points[["x", "y"]])
        df_data_points["cluster"] = km.labels_
        dict_cluster_bbox = compute_bbox_from_cluster(df_data_points, resolution)
        limits_validation = check_limits(dict_cluster_bbox, limits)
        if not any(limits_validation):  # loop until at least 1 cluster meet the condition
            n += 1
        else:
            while True:
                for cluster, _ in dict_cluster_bbox.items():
                    if limits_validation[cluster]:
                        pass
                    else:
                        km = KMeans(n_clusters=2, random_state=0).fit(
                            df_data_points[["x", "y"]].loc[df_data_points["cluster"] == cluster]
                        )

                        df_data_points["cluster"].loc[df_data_points["cluster"] == cluster] = (
                            df_data_points["cluster"].loc[df_data_points["cluster"] == cluster] + km.labels_
                        )
                        dict_cluster_bbox = compute_bbox_from_cluster(df_data_points, resolution)
                        limits_validation = check_limits(dict_cluster_bbox, limits)
                if all(limits_validation):
                    break
        if all(limits_validation):
            break

    return df_data_points, dict_cluster_bbox


def compute_bbox_from_cluster(df_data_points: pd.DataFrame, resolution: float) -> dict:
    """
    Compute bbox for each cluster of points.

    Parameters
    ----------
    df_data_points:
        Pandas DataFrame containing the following columns:
            +---+---+
            | x | y |
            +---+---+
            |   |   |
            +---+---+
    resolution:
        Resolution of the returned image. Should always be >= then the resolution of the coverage.
    Returns
    -------
    dict_cluster_bbox
        Dictionary linking clusters with bboxes
    """
    dict_cluster_bbox = {}
    for cluster in np.unique(df_data_points["cluster"]):
        df_cluster = df_data_points.loc[df_data_points["cluster"] == cluster].reset_index(drop=True)
        bbox = [
            math.floor(df_cluster["x"].min()) - resolution,
            math.floor(df_cluster["y"].min()) - resolution,
            math.ceil(df_cluster["x"].max()) + resolution,
            math.ceil(df_cluster["y"].max()) + resolution,
        ]
        dict_cluster_bbox[cluster] = bbox
    return dict_cluster_bbox


def check_limits(dict_cluster_bbox: dict, limits) -> list:
    """
    Check if the limits are respected for all the bboxes.

    Parameters
    ----------
    dict_cluster_bbox:
        Dictionary linking clusters with bboxes
    limits:
        Maximum height and width of bbox
    Returns
    -------

    """
    limits_validation = []
    for bbox in dict_cluster_bbox.values():
        if bbox[2] - bbox[0] <= limits[0] and bbox[3] - bbox[1] <= limits[1]:
            limits_validation.append(True)
        else:
            limits_validation.append(False)
    return limits_validation


def get_xyz_df_from_multipoints(multi_points: MultiPoint) -> DataFrame:
    # If the TNO model does not cover the area around the segment trajectory, then multi_points can be empty and a
    # proper error message is returned
    if isinstance(multi_points, MultiPoint):
        df_points = DataFrame(
            {
                "x": [point.x for point in multi_points.geoms],
                "y": [point.y for point in multi_points.geoms],
            }
        )
    else:
        raise UserException("3D ground model does not cover the area around the dijkvak")  # TODO Translate

    # Call AHN API to fetch ground level data
    try:
        return fetch_ahn_z_values(df_points)
    except Exception:
        raise UserException("Ophalen AHN data ging verkeerd, probeer het opnieuw.")
