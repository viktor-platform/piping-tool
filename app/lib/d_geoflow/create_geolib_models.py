from typing import List
from typing import Optional

from geolib.soils import StorageParameters

from app.exit_point.soil_geometry_model import SoilGeometry
from viktor.geo import Soil as ViktorSoil
from viktor.geo import SoilLayout
from viktor.geometry import Polygon as ViktorPolygon
from viktor.geometry import Polyline

from ...dyke.dyke_model import Dyke
from ...geolib_helpers.geolib import DStabilityModel
from ...geolib_helpers.geolib.geometry import Point as GeolibPoint
from ...geolib_helpers.geolib.models.dgeoflow import DGeoflowModel
from ...geolib_helpers.geolib.soils import Soil as GeolibSoil
from ...geolib_helpers.geolib.soils.soil_utils import Color as GeolibColor

DSETTLEMENT_POINT_PRECISION = 3


def _to_geolib_soil(soil: ViktorSoil) -> GeolibSoil:
    """
    Convert a ViktorSoil object into a GeolibSoil object with the required parameters for a DGeoflow analysis.
    The necessary soil parameters are:
        - soil code and soil name (standard in GEOLib)
        - horizontal permeability as a storage parameter
        - vertical permeability as a storage parameter
    :param soil: ViktorSoil object to be converted
    :return:
    """
    gl_soil = GeolibSoil()
    gl_soil.name = gl_soil.code = soil.name
    gl_soil.color = GeolibColor(soil.color.rgb)
    gl_soil.storage_parameters = StorageParameters(
        horizontal_permeability=soil.properties.horizontal_permeability / (60 * 60 * 24),  # Convert m/d in m/s
        vertical_permeability=soil.properties.horizontal_permeability / (60 * 60 * 24),
    )  # Convert m/d in m/s
    return gl_soil


def get_geolib_points_from_viktor_polygon(polygon: ViktorPolygon) -> List[GeolibPoint]:
    """Takes a viktor polygon and returns a list of GeoLib points of the exterior boundary"""
    return [
        GeolibPoint(x=round(p.x, DSETTLEMENT_POINT_PRECISION), y=0, z=round(p.y, DSETTLEMENT_POINT_PRECISION))
        for p in polygon.points
    ]


def get_boundary_condition_contour(line: Polyline) -> List[GeolibPoint]:
    """Takes a viktor polyline and returns a list of Geolib points for a boundary of the DGeoflow model."""
    return [
        GeolibPoint(x=round(p.x, DSETTLEMENT_POINT_PRECISION), y=0, z=round(p.y, DSETTLEMENT_POINT_PRECISION))
        for p in line.points
    ]


def generate_dstability_model(soil_geometry: SoilGeometry, ditch_data: Optional[List[dict]] = None) -> DStabilityModel:
    """create a DStability model that only contains a geometry and the soils"""
    dm = DStabilityModel()
    transfer_layer_properties_to_soil(soil_geometry.soil_layout)

    if ditch_data is None:
        soil_layout_2d = soil_geometry.soil_layout_2d
    else:
        soil_layout_2d = (
            soil_geometry.soil_layout_2d_with_ditches_removed(ditch_data)
            if ditch_data
            else soil_geometry.soil_layout_2d
        )

    for soil in soil_geometry.soil_layout.filter_unique_soils():
        dm.add_soil(_to_geolib_soil(soil))

    for layer in soil_layout_2d.layers:
        for polygon in layer.polygons():
            geolib_polygon = get_geolib_points_from_viktor_polygon(polygon)
            dm.add_layer(geolib_polygon, layer.soil.name)

    return dm


def generate_dgeoflow_model(soil_geometry: SoilGeometry, dike: Dyke, ditch_data: List[dict] = None) -> DGeoflowModel:
    """create a DGeoflow model"""

    dm = DGeoflowModel()
    transfer_layer_properties_to_soil(soil_geometry.soil_layout)

    if ditch_data is None:
        soil_layout_2d = soil_geometry.soil_layout_2d
    else:
        soil_layout_2d = (
            soil_geometry.soil_layout_2d_with_ditches_removed(ditch_data)
            if ditch_data
            else soil_geometry.soil_layout_2d
        )
    for soil in soil_geometry.soil_layout.filter_unique_soils():
        dm.add_soil(_to_geolib_soil(soil))

    for layer in soil_layout_2d.layers:
        for polygon in layer.polygons():
            geolib_polygon = get_geolib_points_from_viktor_polygon(polygon)
            layer_id = dm.add_layer(geolib_polygon, soil_code=layer.soil.name)

            # TODO Below: how to assign the right layer id??
            layeractivation_id = dm.add_layeractivation(layer_id=layer_id)
            mesh_properties_id = dm.add_meshproperties(element_size=soil_geometry.element_size, layer_id=layer_id)

    bc_id = add_side_boundary_conditions(dm, soil_geometry, dike)
    dm.add_scenario(
        boundaryconditions_id=bc_id,
        layeractivations_id=layeractivation_id,
        meshproperties_id=mesh_properties_id,
        soillayers_id=dm.datastructure.soillayers[-1].Id,
        geometry_id=dm.datastructure.geometries[-1].Id,
        calculations_label="Calculation 1",
        stage_label="Stage 1",
        label="MyScenario",
        notes="a few notes",
    )

    return dm


def add_side_boundary_conditions(dm: DGeoflowModel, soil_geometry: SoilGeometry, dike: Dyke) -> id:
    """Add the boundary conditions on the left and right sides of the model. The method automatically recognizes if
    the left side is the hinterland or the foreland and assigns the head level of the boundary conditions accordingly"""
    left_bc = get_boundary_condition_contour(soil_geometry.soil_layout_2d.get_left_boundary_polyline())
    right_bc = get_boundary_condition_contour(soil_geometry.soil_layout_2d.get_right_boundary_polyline())

    crest_line_x_value = soil_geometry.start_point.distance(dike.get_base_trajectory())
    entry_line_x_value = soil_geometry.start_point.distance(dike.entry_line)
    if entry_line_x_value > crest_line_x_value:  # right side of layout is the river side
        bc_id = dm.add_boundarycondition(left_bc, head_level=soil_geometry.polder_level, label="Polder head")
        dm.add_boundarycondition(right_bc, head_level=soil_geometry.river_level, label="River head")
    else:
        bc_id = dm.add_boundarycondition(left_bc, head_level=soil_geometry.river_level, label="River head")
        dm.add_boundarycondition(right_bc, head_level=soil_geometry.polder_level, label="Polder head")
    return bc_id


def transfer_layer_properties_to_soil(soil_layout: SoilLayout) -> None:
    """For all layers in a soil layout, add the properties of the layer to its attached ViktorSoil Object. Necessary
    because parameters like the permeability are stored at the SoilLayer level."""
    for layer in soil_layout.layers:
        layer.soil.properties.update(layer.properties)
