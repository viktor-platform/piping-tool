from typing import List

from munch import Munch

from app.dyke.constants import DEFAULT_CLASSIFICATION_TABLE
from app.dyke.constants import DEFAULT_MATERIAL_TABLE
from app.ground_model.constants import LITHOLOGY_CODE_NAME_MAPPING
from viktor.api_v1 import API
from viktor.parametrization import ChildEntityOptionField
from viktor.parametrization import DownloadButton
from viktor.parametrization import DynamicArray
from viktor.parametrization import FileField
from viktor.parametrization import GeoPolygonField
from viktor.parametrization import GeoPolylineField
from viktor.parametrization import IsEqual
from viktor.parametrization import Lookup
from viktor.parametrization import NumberField
from viktor.parametrization import OptionField
from viktor.parametrization import OptionListElement
from viktor.parametrization import Or
from viktor.parametrization import Parametrization
from viktor.parametrization import Section
from viktor.parametrization import SetParamsButton
from viktor.parametrization import SiblingEntityOptionField
from viktor.parametrization import Tab
from viktor.parametrization import TableInput
from viktor.parametrization import Text
from viktor.parametrization import TextField
from viktor.parametrization import ToggleButton


def _get_tno_ground_model_options(**kwargs) -> List[OptionListElement]:
    """Callback to get the TNO GroundModel entities and return a list of options"""
    root_models_entity = API().get_root_entities(entity_type_names=["Models"])[0]
    tno_model_entities = root_models_entity.children(entity_type_names=["GroundModel"])
    return [OptionListElement(entity.id, entity.name) for entity in tno_model_entities]


def _get_entry_lines_options(**kwargs) -> List[OptionListElement]:
    """Callback to get the entry lines entities and return a list of options"""
    root_models_entity = API().get_root_entities(entity_type_names=["ProjectFolder"])[0]
    entry_line_entities = root_models_entity.children(entity_type_names=["Dyke"])[0].children(
        entity_type_names=["EntryLine"]
    )
    return [OptionListElement(entity.id, entity.name) for entity in entry_line_entities]


def _get_soil_options(params: Munch, **kwargs) -> List[OptionListElement]:
    """Return as options all the soils defined in the material table"""
    return [OptionListElement(material.name) for material in params.models.materials.table]


_tno_lithoclass_options = [
    OptionListElement(value=soil_name)
    for soil_code, soil_name in LITHOLOGY_CODE_NAME_MAPPING.items()
    if soil_code not in (4, 8)
]

_2D_visualization_baseline_options = [
    OptionListElement(value="crest_line", label="Dijk traject"),
    OptionListElement(value="uploaded_line", label="Geüploade lijn"),
    OptionListElement(value="custom_line", label="Getrokken lijn"),
]


class DykeParametrization(Parametrization):
    geometry = Tab("Data input")
    geometry.dyke = Section("Traject")
    geometry.dyke.trajectory = GeoPolylineField("Dijkas", name="dyke_geo_coordinates", visible=True)
    geometry.dyke.chainage_step = NumberField(
        "Stapgrootte voor metrering",
        default=25,
        suffix="m",
        name="chainage_step",
        description="stapgrote voor metrering in kaart en voor soillayout: om de hoeveel meter is er een datapunt",
    )
    geometry.dyke.reverse_direction_chainage = ToggleButton(
        "Richting metrering",
        default=False,
        description="Dit veranderd aan welke kant het nulpunt van de metrering is",
    )
    geometry.dyke.clockwise_direction_to_water = ToggleButton(
        "Oriëntatie t.o.v. rivier",
        default=False,
        description="De kleine blauwe driehoek aan het uiteinde van de dijk moet richting de rivier wijzen",
    )
    geometry.dyke.set_chainage_btn = SetParamsButton("Detecteer automatisch aslengte", method="get_chainage_length")

    geometry.data_selection = Section("Input data selectie")
    geometry.data_selection.entry_line = FileField("Upload intredelijn", file_types=[".zip"], name="entry_line")
    geometry.data_selection.ditch_data = FileField("Upload sloten data", file_types=[".zip"], name="ditch_data")
    geometry.data_selection.ground_model = OptionField(
        "3D model", options=_get_tno_ground_model_options, autoselect_single_option=False
    )
    geometry.data_selection.cpt_folder = SiblingEntityOptionField(
        "CPT folder",
        entity_type_names=["CPTFolder"],
        name="cpt_folder",
    )
    geometry.data_selection.bore_folder = SiblingEntityOptionField(
        "Boringenfolder", entity_type_names=["BoreFolder"], name="bore_folder"
    )
    geometry.data_selection.bathymetry_file = FileField(
        "Bathymetrie", file_types=[".tif"], description="Enkel Raster files .tif"
    )
    geometry.data_selection.dijkpalen = FileField("Upload dijkpalen", file_types=[".zip"], name="dijkpalen")

    soil_profile = Tab("Visualisatie opties")
    soil_profile.lb0 = Text("## Traject oorsprong voor 2D grondopbouw")
    soil_profile.select_base_line_for_2D_view = OptionField(
        "Traject lijn voor 2D Grondopbouw", options=_2D_visualization_baseline_options, default="crest_line", flex=60
    )
    soil_profile.custom_geopolyline = GeoPolylineField(
        "Draw a polyline for 2D Grondopbouw",
        visible=IsEqual(Lookup("soil_profile.select_base_line_for_2D_view"), "custom_line"),
    )  # TODO TRANSLATE
    soil_profile.line_select = FileField(
        "Overige lijn opties",
        description="Upload andere lijn (teenlijn, intredelijn etc)",
        visible=IsEqual(Lookup("soil_profile.select_base_line_for_2D_view"), "uploaded_line"),
        name="line_for_2d_soil_layout",
        file_types=[".zip"],
    )
    soil_profile.line_offset = NumberField(
        "Afstand tot aangegeven lijn",
        default=0,
        suffix="m",
        visible=Or(
            IsEqual(Lookup("soil_profile.select_base_line_for_2D_view"), "uploaded_line"),
            IsEqual(Lookup("soil_profile.select_base_line_for_2D_view"), "crest_line"),
        ),
        description="De richting van de afstand tot de gekozen lijn is positief in de linker richting (vanaf de"
        "metrering)",
    )
    soil_profile.lb1 = Text("## Schaalfactoren grondonderzoek")
    soil_profile.scale_measurement_cpt_qc = NumberField(
        "Schaalfactor qc waarden", default=5, name="scale_measurement_cpt_qc"
    )
    soil_profile.scale_measurement_cpt_rf = NumberField(
        "Schaalfactor Rf waarden", default=5, name="scale_measurement_cpt_rf"
    )
    soil_profile.scale_measurement_cpt_u2 = NumberField(
        "Schaalfactor u2 waarden", default=100, name="scale_measurement_cpt_u2"
    )
    soil_profile.buffer_zone_cpts_bore = NumberField(
        "Maximale afstand",
        default=30,
        name="buffer_zone_cpts_bore",
        suffix="m",
        description="maximale afstand van de dijkas tot de geselecteerde lijn waarbij een boring of cpt wordt "
        "gevisualiseerd ",
    )
    soil_profile.lb2 = Text("## Regis")
    soil_profile.bottom_level_query = NumberField("Onderkant van Regis model", default=-30, suffix="m", max=0)
    models = Tab("Grondopbouw")
    models.materials = Section("Materialen")
    models.materials.table = TableInput("Materiaaltabel", default=DEFAULT_MATERIAL_TABLE)
    models.materials.table.name = TextField("Naam grondlaag")
    models.materials.table.color = TextField("kleur", description="R,G,B format")
    models.materials.table.aquifer = ToggleButton("Aquifer", description="Selecteer als deze grondlaag een aquifer is")
    models.materials.table.gamma_dry = NumberField("Gewicht droog", suffix="kN/m3")
    models.materials.table.gamma_wet = NumberField("Gewicht nat", suffix="kN/m3")
    models.materials.table.k_hor = NumberField("Doorlatendheid vert", suffix="m/d")
    models.materials.table.k_vert = NumberField("Doorlatendheid hor", suffix="m/d")
    models.materials.table.d_70 = NumberField("d70", suffix="mm")

    models.materials.classification_table_explanation = Text(
        "## Classificatietabel 3D bodemopbouw \n"
        + 'Defineer onder de classificatietabel om de 3D bodemopbouw in een geotechnisch model om te zetten. Ten minste 1 grondlaag moet worden gedefinieerd per TNO lithoklasse. De bovenkant en onderkant moet worden aangegeven in elke rij. \n\n Een streepje "-" staat voor oneindig. \n\n Een streepje "-" in de kolom onderkant grondlaag staat voor - oneindig.'
    )
    models.materials.classification_table = TableInput("Classificatietabel", default=DEFAULT_CLASSIFICATION_TABLE)
    models.materials.classification_table.layer = OptionField("TNO lithoklasse", options=_tno_lithoclass_options)
    models.materials.classification_table.top_of_layer = TextField("Bovenkant", suffix="m NAP")
    models.materials.classification_table.bottom_of_layer = TextField("Onderkant", suffix="m NAP")
    models.materials.classification_table.soil_type = OptionField("Grondsoort", options=_get_soil_options)

    segment_generation = Tab("Genereren dijkvakken")
    segment_generation.segment_array = DynamicArray("Dijkvak definitie")
    segment_generation.segment_array.segment_name = TextField("Dijkvak naam")
    segment_generation.segment_array.segment_start_chainage = NumberField(
        "Start kilometrering",
        description="Fill from where the dijkvak section should start from the kilometrering of the dijkv",
    )  # TODO TRANSLATE
    segment_generation.segment_array.segment_end_chainage = NumberField(
        "Eind kilometrering",
        description="Fill from where the dijkvak section should end from the kilometrering of the dijkv",
    )  # TODO TRANSLATE
    segment_generation.create_segments_from_dynamic_array = SetParamsButton(
        "Maak dijkvak", method="create_segments_from_dynamic_array"
    )
    segment_generation.polygon = GeoPolygonField("Pas segmentgrenzen aan waar nodig", visible=False)

    downloads = Tab("Downloads")
    downloads.segment_select = ChildEntityOptionField("Selecteer dijkvak", entity_type_names=["Segment"])
    downloads.segment_trajectory_download = DownloadButton("Download traject", "get_segment_trajectories")
    downloads.lb2 = Text("## Results")
    downloads.all_sellmeijer_results_download = DownloadButton(
        "Download sellmeijer uitvoer voor alle dijkvaken", "get_all_piping_results"
    )
