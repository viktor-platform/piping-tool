from typing import List
from typing import Union

import numpy as np
from munch import Munch

from app.segment.segmentAPI import SegmentAPI
from viktor.api_v1 import API
from viktor.api_v1 import Entity
from viktor.parametrization import ActionButton
from viktor.parametrization import ChildEntityOptionField
from viktor.parametrization import DownloadButton
from viktor.parametrization import DynamicArray
from viktor.parametrization import DynamicArrayConstraint
from viktor.parametrization import GeoPolygonField
from viktor.parametrization import GeoPolylineField
from viktor.parametrization import HiddenField
from viktor.parametrization import IntegerField
from viktor.parametrization import IsEqual
from viktor.parametrization import IsFalse
from viktor.parametrization import IsTrue
from viktor.parametrization import LineBreak
from viktor.parametrization import Lookup
from viktor.parametrization import MapSelectInteraction
from viktor.parametrization import NumberField
from viktor.parametrization import OptionField
from viktor.parametrization import OptionListElement
from viktor.parametrization import OutputField
from viktor.parametrization import Parametrization
from viktor.parametrization import Section
from viktor.parametrization import SetParamsButton
from viktor.parametrization import Step
from viktor.parametrization import Tab
from viktor.parametrization import TableInput
from viktor.parametrization import Text
from viktor.parametrization import TextField
from viktor.parametrization import ToggleButton

from .constants import GEOHYDROLOGICAL_OPTIONS
from .constants import LEAKAGE_LENGTH_OPTIONS
from .constants import TNO_LITHOCLASS_OPTIONS


def _get_distance_cpt_to_exitpoint(params: Munch, entity_id: int, **kwargs) -> Union[float, str]:
    if not params.selected_cpt_id:
        return "geen CPT geselecteerd"
    cpt_summary = SegmentAPI(entity_id).get_cpt_entity(params.selected_cpt_id).last_saved_summary
    cpt_coord = (cpt_summary.x_coordinate["value"], cpt_summary.y_coordinate["value"])

    exit_point = params.calculations.soil_profile.visualisation_settings.select_single_exit_point.last_saved_summary
    exit_point_coord = (exit_point.x_coordinate["value"], exit_point.y_coordinate["value"])

    distance = np.linalg.norm(np.array(cpt_coord) - np.array(exit_point_coord))
    return np.round(distance, decimals=2)


def _get_soil_options(params: Munch, **kwargs) -> List[OptionListElement]:
    """Return as options all the soils defined in the material table"""
    return [OptionListElement(material.name) for material in params.input_selection.materials.table]


def _get_cpt_options(params: Munch, entity_id: int, **kwargs) -> List[OptionListElement]:
    """Return as options all the CPT from the CPT folder selected at the dyke entity"""
    if params.show_cpt:
        cpt_folder_entity: Entity = API().get_entity(entity_id).parent().last_saved_params.cpt_folder
        if cpt_folder_entity is None:
            return []
        return [OptionListElement(label=cpt.name, value=cpt.id) for cpt in cpt_folder_entity.children()]
    return []


def _get_scenarios_list(params: Munch, **kwargs) -> Union[List[OptionListElement], str]:
    """Return as options all the scenarios created in the Input selection"""
    scenario_list = []
    for row in params.input_selection.soil_schematization.soil_scen_array:
        scenario_list.append(OptionListElement(value=row["name_of_scenario"], label=row["name_of_scenario"]))
    return scenario_list


_options_grid_hinterland = [
    OptionListElement(value="option_1", label="1"),
    OptionListElement(value="option_2", label="2"),
    OptionListElement(value="option_3", label="3"),
]

_get_exit_point_modification_options = [
    OptionListElement(value="interactive", label="Interactief kaart selectie"),
    OptionListElement(value="polygon", label="Polygon tekenen"),
]

_main_grid_visibility = Lookup("is_hinterland_grid")
_manual_exit_point_visibility = Lookup("is_manual_exit_point")
_ditch_points_visibility = Lookup("is_ditch_points")
_lowest_point_visibility = Lookup("is_lowest_point")
_cpt_selection_visibility = Lookup("show_cpt")
_buffer_zone_visibility = Lookup("select_with_buffer_zone")
_aquifer_prop_array_visibility_constraint = DynamicArrayConstraint(
    "input_selection.soil_schematization.soil_scen_array",
    IsTrue(Lookup("$row.second_aquifer_activate")),
)


class SegmentParametrization(Parametrization):
    ####################################################################################################################
    #                                                   STEP 1                                                         #
    ####################################################################################################################
    input_selection = Step(
        "Input selectie",
        views=["map_ditch_selection", "visualize_ground_model_along_segment", "visualize_representative_layout"],
        next_label="Stap 2: Geohydro",
    )

    input_selection.general = Tab("Algemeen")
    input_selection.general.segment_polygon = GeoPolygonField(
        "Geselecteerde gebied voor het maken van een segment", name="segment_polygon", visible=False
    )
    input_selection.general.start_chainage = NumberField("Start kilometrering", suffix="m", name="start_chainage")
    input_selection.general.end_chainage = NumberField("Eind kilometrering", suffix="m", name="end_chainage")
    input_selection.general.adjust_segment_polygon = SetParamsButton(
        "Update traject van het segment", "adjust_segment_polygon_by_chainage"
    )

    input_selection.general.show_entry_exit_lines = ToggleButton(
        "Toon intredelijn en uittredelijn", flex=50, default=True
    )
    input_selection.general.show_selected_ditches = ToggleButton(
        "Toon enkel geselecteerde sloten",
        flex=50,
        default=False,
        description="Toon alle sloten als deze knop uit staat, of alleen de opgeslagen sloten in het achterland als deze aan staat",
    )
    input_selection.general.show_ground_model = ToggleButton("Toon dekking 3D grondmodel", flex=50, default=False)
    input_selection.general.show_cpts = ToggleButton("Toon CPTs", flex=50, default=False)

    input_selection.safety = Tab("Veiligheid")
    input_selection.safety.schematisation_factor_piping = NumberField(
        "Schematiseringsfactor piping $γ_{b,pip}$", min=1.0, max=1.3, default=1.0, num_decimals=1, step=0.1, suffix="-"
    )
    input_selection.safety.safety_factor_piping = NumberField(
        "Veiligheidsfactor piping $γ_{pip}$", min=0.0, default=1.0, num_decimals=1, step=0.1, suffix="-"
    )
    input_selection.safety.lb1 = LineBreak()
    input_selection.safety.schematisation_factor_uplift = NumberField(
        "Schematiseringsfactor opbarsten $γ_{b,up}$",
        min=1.0,
        max=1.3,
        default=1.0,
        num_decimals=1,
        step=0.1,
        suffix="-",
    )
    input_selection.safety.safety_factor_uplift = NumberField(
        "Veiligheidsfactor opbarsten $γ_{up}$", min=0.0, default=1.0, num_decimals=1, step=0.1, suffix="-"
    )
    input_selection.safety.lb2 = LineBreak()
    input_selection.safety.schematisation_factor_heave = NumberField(
        "Schematiseringsfactor heave $γ_{b,he}$", min=1.0, max=1.3, default=1.0, num_decimals=1, step=0.1, suffix="-"
    )
    input_selection.safety.safety_factor_heave = NumberField(
        "Veiligheidsfactor heave $γ_{he}$", min=0.0, default=1.0, num_decimals=1, step=0.1, suffix="-"
    )

    input_selection.materials = Tab("Materialen")
    input_selection.materials.fetch_tables_from_project = SetParamsButton(
        "Reset tabellen naar de algemene dijkwaarden", "fetch_table_from_dike"
    )
    input_selection.materials.table = TableInput("Materiaaltabel")
    input_selection.materials.table.name = TextField("Naam grondlaag")
    input_selection.materials.table.color = TextField("Kleur", description="R,G,B format")
    input_selection.materials.table.aquifer = ToggleButton(
        "Aquifer", description="Selecteer als deze grondlaag een aquifer is"
    )
    input_selection.materials.table.gamma_dry = NumberField("Gewicht droog", suffix="kN/m3")
    input_selection.materials.table.gamma_wet = NumberField("Gewicht nat", suffix="kN/m3")
    input_selection.materials.table.k_hor = NumberField("Doorlatendheid hor", suffix="m/d")
    input_selection.materials.table.k_vert = NumberField("Doorlatendheid vert", suffix="m/d")
    input_selection.materials.table.d_70 = NumberField("d70", suffix="mm")
    input_selection.materials.classification_table_explanation = Text(
        "## Classificatietabel 3D ground model \n"
        + 'Defineer onder de classificatietabel om het 3D bodemopbouw in een geotechnisch model om te zetten. Ten minste 1 grondlaag moet worden gedefinieerd per TNO lithoklasse. De bovenkant en onderkant moet worden aangegeven in elke rij. \n\n Een streepje "-" staat voor oneindig. \n\n Een streepje "-" in de kolom onderkant grondlaag staat voor - oneindig.'
    )
    input_selection.materials.classification_table = TableInput("Classificatietabel")
    input_selection.materials.classification_table.layer = OptionField(
        "3D model lithoklasse", options=TNO_LITHOCLASS_OPTIONS
    )
    input_selection.materials.classification_table.top_of_layer = TextField("Bovenkant", suffix="m NAP")
    input_selection.materials.classification_table.bottom_of_layer = TextField("Onderkant", suffix="m NAP")
    input_selection.materials.classification_table.soil_type = OptionField("Grondsoort", options=_get_soil_options)
    input_selection.materials.lb = LineBreak()
    input_selection.materials.minimal_aquifer_thickness = NumberField(
        "Minimale aquifer dikte",
        suffix="m",
        default=1,
        name="minimal_aquifer_thickness",
        description="Minimale dikte van de zandlaag om te classificeren als aquifer",
    )
    input_selection.materials.bottom_level_query = NumberField(
        "Onderkant van Regis model", default=-30, suffix="m", max=0
    )

    # -----------------------
    #      SOIL SCHEMATIZATION
    # -----------------------
    input_selection.soil_schematization = Tab("Ondergrondschematisatie")
    input_selection.soil_schematization.text1 = Text(
        "Click first on 'Haal bodempbouw' to create a dijkvak and fill its soil layout table. Then click on 'Bereken effetieve' \n\n Several dijkvaken (of scenario) can be defined below."
    )  # TODO: TRANSLATE
    input_selection.soil_schematization.distance_from_start = NumberField(
        "Locatie meetpunt langs dijk", suffix="m", min=0
    )

    input_selection.soil_schematization.fetch_soil_layout_along_trajectory = SetParamsButton(
        "Haal bodemopbouw op locatie op",
        "fetch_soil_layout_at_location",
        description="The soil layout is fetched at the entered location on the segment trajectory."
        # TODO TRANSLATE
    )
    input_selection.soil_schematization.lb2 = LineBreak()

    input_selection.soil_schematization.calculate_effective_aquifer_properties = SetParamsButton(
        "Bereken effectieve aquifer eigenschappen",
        "calculate_effective_aquifer_properties",
        description="Calculate the effective paramters for the first and second aquifers defined in the soil layout table, for every scenario."
        # TODO: TRANSLATE
    )
    input_selection.soil_schematization.lb1 = LineBreak()

    input_selection.soil_schematization.soil_scen_array = DynamicArray("Scenario definitie", copylast=True)
    input_selection.soil_schematization.soil_scen_array.name_of_scenario = TextField("Naam van scenario")
    input_selection.soil_schematization.soil_scen_array.weight_of_scenario = NumberField(
        "Gewicht van dit scenario in berekeningen",
        min=0,
        max=1,
        step=0.01,
        description="Vul een gewicht in van tussen de 0 en 1 wat uitdrukt hoe "
        "zwaar dit scenario mee telt in de berekeningen",
    )
    input_selection.soil_schematization.soil_scen_array.lb1 = LineBreak()
    input_selection.soil_schematization.soil_scen_array.bottom_of_soil_layout = NumberField(
        "Onderkant van de bodemopbouw"
    )
    input_selection.soil_schematization.soil_scen_array.soil_layout_table = TableInput("Bodemopbouw")
    input_selection.soil_schematization.soil_scen_array.soil_layout_table.name = OptionField(
        "Grondlaag", options=_get_soil_options
    )
    input_selection.soil_schematization.soil_scen_array.soil_layout_table.top_of_layer = NumberField(
        "Bovenkant laag", suffix="m NAP"
    )
    input_selection.soil_schematization.soil_scen_array.soil_layout_table.aquifer = ToggleButton("Aquifer")
    input_selection.soil_schematization.soil_scen_array.first_aquifer_permeability = NumberField(
        "Doorlatendheid eerste aquifer", suffix="m/d", num_decimals=5, flex=40
    )
    input_selection.soil_schematization.soil_scen_array.first_aquifer_d70 = NumberField("d70", suffix="mm", flex=20)
    input_selection.soil_schematization.soil_scen_array.lb2 = LineBreak()
    input_selection.soil_schematization.soil_scen_array.second_aquifer_activate = ToggleButton(
        "Is er een tweede aquifer?"
    )
    input_selection.soil_schematization.soil_scen_array.lb3 = LineBreak()
    input_selection.soil_schematization.soil_scen_array.second_aquifer_permeability = NumberField(
        "Doorlatendheid tweede aquifer ",
        suffix="m/d",
        visible=_aquifer_prop_array_visibility_constraint,
        num_decimals=5,
        flex=40,
    )
    input_selection.soil_schematization.soil_scen_array.second_aquifer_d70 = NumberField(
        "d70", suffix="mm", visible=_aquifer_prop_array_visibility_constraint, flex=20
    )

    input_selection.soil_schematization.scenario_to_visualise = OptionField(
        "Scenario te visualiseren",
        options=_get_scenarios_list,
        description="Choose which scenario to visualise in view 'Dijkvak' ",
    )

    # -----------------------
    #      DITCHES
    # -----------------------
    input_selection.select_ditches = Tab("Selecteer sloten")
    input_selection.select_ditches.segment_ditches = HiddenField("UI", name="segment_ditches")
    input_selection.select_ditches.segment_dry_ditches = HiddenField("UI", name="segment_dry_ditches")
    input_selection.select_ditches.select_with_buffer_zone = ToggleButton(
        "uit/aan", name="select_with_buffer_zone", default=False, flex=10
    )
    input_selection.select_ditches.select_with_buffer_zone_text = Text("## Selecteer sloten", flex=90)
    input_selection.select_ditches.lb = LineBreak()
    input_selection.select_ditches.select_with_buffer_zone_text_2 = Text(
        "Klik op 'Snij sloten' om sloten binnen de bufferzone achter de dijk te selecteren en op te slaan. De geselecteerde sloten kunnen later gebruikt worden om uittredepunten mee te definiëren.",
        flex=90,
        visible=_buffer_zone_visibility,
    )
    input_selection.select_ditches.buffer_zone = NumberField(
        "Lengte bufferzone", suffix="m", name="buffer_zone", default=150, visible=_buffer_zone_visibility
    )
    input_selection.select_ditches.lb1 = LineBreak()
    input_selection.select_ditches.create_select_ditches = SetParamsButton(
        "Snij sloten", "intersect_ditches_with_buffer_zone", visible=_buffer_zone_visibility
    )

    ####################################################################################################################
    #                                                   STEP 2                                                         #
    ####################################################################################################################
    soil_schematization = Step(
        "Geohydrologie",
        views=["map_leakage_length_1", "map_leakage_length_2", "visualise_soil_leakage_point"],
        previous_label="Stap 1: Input selectie",
        next_label="Stap 3: Genereren uittredepunt",
    )

    # -----------------------
    #      GEOHYDROLOGY
    # -----------------------

    soil_schematization.geohydrology = Tab("Geohydro models")
    soil_schematization.geohydrology.general = Section("Algemeen")
    soil_schematization.geohydrology.general.explanation = Text(
        "Kies tussen drie detailniveaus om het geohydrologische model te definieren. \n"
        + "- Niveau 1: Enkel het waterpeil van de rivier en het polderpeil. \n"
        + "- Niveau 2: De leklengte van het achterland als het voorland samen met de dijkbreedte worden gebruikt. \n"
        + "- Niveau 3: Het waterpeil is bepaald op basis van een polderpeil bestand."
    )
    soil_schematization.geohydrology.general.method = OptionField(
        "Selecteer Methode",
        options=GEOHYDROLOGICAL_OPTIONS,
        flex=100,
        autoselect_single_option=True,
        name="geohydrology_method",
    )
    soil_schematization.geohydrology.general.river_level = NumberField(
        "Rivier waterpeil", suffix="m NAP", flex=30, name="river_level"
    )
    soil_schematization.geohydrology.general.polder_level = NumberField(
        "Waterstand binnendijks tijdens hoogwater", suffix="m NAP", flex=30, name="polder_level"
    )
    soil_schematization.geohydrology.general.ditch_water_level = NumberField(
        "Waterstand voor slootbodem",
        suffix="m NAP",
        flex=35,
        name="ditch_water_level",
        description="De slootbodem wordt bepaald aan de hand van een onderhoudsdiepte t.o.v. "
        "een referentiewaterstand. Meestal wordt hiervoor het winterpeil gebruikt. "
        "Vul hier deze referentiewaterstand in.",
    )
    soil_schematization.geohydrology.level0 = Section("Niveau 0")
    soil_schematization.geohydrology.level0.hydraulic_head = NumberField(
        "Buitenwaterstand", suffix="m", description="Waterstand in het achterland"
    )
    soil_schematization.geohydrology.level1 = Section("Niveau 1", description="gebaseerd op het (gedempte) waterpeil")
    soil_schematization.geohydrology.level1.explanation = Text(
        "Dempingsfactor is toegepast op het waterpeil in de rivier. Met een dempingsfactor van 1 is de stijghoogte in de aquifer gelijk aan het waterpeil in de rivier. Met een dempingsfactor van 0 is de stijghoogte in de aquifer gelijk aan het polderpeil."
    )
    soil_schematization.geohydrology.level1.damping_factor = NumberField(
        "Dempingsfactor $r$", min=0, max=1, default=1, name="damping_factor", description="met r=1 is er geen demping"
    )
    soil_schematization.geohydrology.level1.overwrite_phi_avg = ToggleButton("Overwrite phi_avg", default=False)
    soil_schematization.geohydrology.level1.lb = LineBreak()
    soil_schematization.geohydrology.level1.user_phi_avg_hinterland = NumberField(
        "Referentie polderpeil tbhv bepalen dempingsfactor",
        suffix="m",
        visible=Lookup("soil_schematization.geohydrology.level1.overwrite_phi_avg"),
        name="user_phi_avg_hinterland",
    )
    soil_schematization.geohydrology.level2 = Section("Niveau 2", description="gebaseerd op leklengte")
    soil_schematization.geohydrology.level2.dyke_width = NumberField("Dijkbreedte", suffix="m", name="dike_width")
    soil_schematization.geohydrology.level2.text = Text(
        "Specify below the leakage lengths for every scenario defined in step 1."
    )  # TODO TRANSLATE
    soil_schematization.geohydrology.level2.leakage_length_array = DynamicArray("Leklengte voor scenario")
    soil_schematization.geohydrology.level2.leakage_length_array.scenario = OptionField(
        "Scenario", options=_get_scenarios_list
    )
    soil_schematization.geohydrology.level2.leakage_length_array.lb0 = LineBreak()
    soil_schematization.geohydrology.level2.leakage_length_array.leakage_length_foreland_aquifer_1 = NumberField(
        "Leklengte voorland eerste aquifer", suffix="m", flex=40
    )
    soil_schematization.geohydrology.level2.leakage_length_array.leakage_length_hinterland_aquifer_1 = NumberField(
        "Leklengte achterland eerste aquifer", suffix="m", flex=40
    )
    soil_schematization.geohydrology.level2.leakage_length_array.lb = LineBreak()
    soil_schematization.geohydrology.level2.leakage_length_array.leakage_length_foreland_aquifer_2 = NumberField(
        "Leklengte voorland tweede aquifer", suffix="m", flex=40
    )
    soil_schematization.geohydrology.level2.leakage_length_array.leakage_length_hinterland_aquifer_2 = NumberField(
        "Leklengte achterland tweede aquifer", suffix="m", flex=40
    )
    soil_schematization.geohydrology.level3 = Section(
        "Niveau 3", description="gebaseerd op stijghoogte uit een stijghoogtebestand die is geupload door de gebruiker"
    )
    soil_schematization.geohydrology.level3.temp_text = Text("Niet beschikbaar")
    soil_schematization.geohydrology.level3.selected_model = OptionField(
        "Geselecteerde model", options=["test"], autoselect_single_option=True, name="geohydrology_selected_model"
    )
    # -----------------------
    #      LEAKAGE LENGTH MAP
    # -----------------------
    soil_schematization.leakage_length_map = Tab("Leklengte kaart")
    soil_schematization.leakage_length_map.foreland_length = NumberField(
        "Lengte voorland",
        suffix="m",
        name="foreland_length_schematization",
        default=25,
        min=0,
    )
    soil_schematization.leakage_length_map.hinterland_length = NumberField(
        "Lengte achterland",
        suffix="m",
        name="hinterland_length_schematization",
        default=25,
        min=25,
    )
    soil_schematization.leakage_length_map.lb = LineBreak()
    soil_schematization.leakage_length_map.visible_param = OptionField(
        "Toon parameter op de kaart",
        options=LEAKAGE_LENGTH_OPTIONS,
        default="from_material_table",
        description="Kies of de doorlatendheid en de leklengte wordt gebaseerd op het TNO model of de materiaaltabel.",
    )
    soil_schematization.leakage_length_map.representative_layout = HiddenField("UI_name", name="representative_layout")
    soil_schematization.leakage_length_map.point_to_visualise = IntegerField(
        "Vak voor Leklengte profiel", name="leakage_point_to_visualise", min=1
    )
    soil_schematization.leakage_length_map.lb1 = LineBreak()
    soil_schematization.leakage_length_map.use_representative_layout = ToggleButton(
        "Dijkvak lagen gebruiken",
        default=True,
        name="use_representative_layout",
        description="Choose if the leakage length should be calculated from the dijkvak or from the TNO grid point only."
        # TODO Translate
    )
    soil_schematization.leakage_length_map.scenario = OptionField(
        "Scenario", options=_get_scenarios_list, visible=Lookup("use_representative_layout")
    )
    ####################################################################################################################
    #                                                   STEP 3                                                         #
    ####################################################################################################################
    exit_point_creation = Step(
        "Genereren uittredepunten",
        views=["map_exit_point_creation"],
        previous_label="Stap 2: Geohydro",
        next_label="Stap 4: Berekeningen",
    )

    exit_point_creation.exit_point_tab = Tab("Instellingen uittredepunten")
    exit_point_creation.exit_point_tab.is_hinterland_grid = ToggleButton(
        " ",
        name="is_hinterland_grid",
        default=True,
        flex=10,
        description="Zet aan om de uittredepunten in het achterland te tonen",
    )
    exit_point_creation.exit_point_tab.general_text = Text("## Grid achterland", flex=90)
    exit_point_creation.exit_point_tab.option_grid_hinterland = OptionField(
        "Optie grid type",
        options=_options_grid_hinterland,
        variant="radio-inline",
        name="option_grid_hinterland",
        visible=_main_grid_visibility,
        default="option_2",
        description="",
    )
    exit_point_creation.exit_point_tab.lb5 = LineBreak()
    exit_point_creation.exit_point_tab.length_hinterland = NumberField(
        "Lengte achterland tot de kruin", default=50, suffix="m", flex=50, visible=_main_grid_visibility
    )
    exit_point_creation.exit_point_tab.buffer_length_hinterland = NumberField(
        "Buffer lengte achterland (tot de kruin)", default=10, suffix="m", flex=50, visible=_main_grid_visibility
    )
    exit_point_creation.exit_point_tab.lb0 = LineBreak()
    exit_point_creation.exit_point_tab.delta_x = NumberField(
        "Frequentie parallel aan de dijk",
        default=10,
        suffix="m",
        flex=50,
        name="hinterland_delta_x",
        visible=_main_grid_visibility,
    )
    exit_point_creation.exit_point_tab.delta_y = NumberField(
        "Frequentie loodrecht op de dijk",
        default=10,
        suffix="m",
        flex=50,
        name="hinterland_delta_y",
        visible=_main_grid_visibility,
    )
    # MANUAL EXIT POINTS
    exit_point_creation.exit_point_tab.lb1 = LineBreak()
    exit_point_creation.exit_point_tab.is_manual_exit_point = ToggleButton(
        " ",
        name="is_manual_exit_point",
        default=False,
        flex=10,
        description="Zet aan om handmatig uittredepunten op de kaart te zetten",
    )
    exit_point_creation.exit_point_tab.is_manual_exit_point_text = Text("## Gebruik handmatige uittredepunten", flex=90)
    exit_point_creation.exit_point_tab.manual_exit_point = GeoPolylineField(
        "Plaats een uittredepunt", visible=_manual_exit_point_visibility, name="manual_exit_point"
    )

    # EXIT POINTS IN DITCH
    exit_point_creation.exit_point_tab.lb2 = LineBreak()
    exit_point_creation.exit_point_tab.is_ditch_points = ToggleButton(
        " ",
        name="is_ditch_points",
        default=False,
        flex=10,
        description="Zet aan om uittredpunten in de sloten te genereren",
    )
    exit_point_creation.exit_point_tab.is_ditch_grid_text = Text("## Uittredepunten in de sloten", flex=90)
    exit_point_creation.exit_point_tab.delta_ditch = NumberField(
        "Frequentie parallel aan de sloot-as",
        default=15,
        suffix="m",
        flex=50,
        visible=_ditch_points_visibility,
        name="delta_ditch",
    )
    # LOWEST POINT IN HINTERLAND
    exit_point_creation.exit_point_tab.lb4 = LineBreak()
    exit_point_creation.exit_point_tab.find_lowest_point_hinterland = ToggleButton(" ", name="is_lowest_point", flex=10)
    exit_point_creation.exit_point_tab.find_lowest_text = Text("## Laagste uitteredepunt", flex=90)
    exit_point_creation.exit_point_tab.resolution_lowest_point = NumberField(
        "Resolutie", min=0.5, visible=_lowest_point_visibility, description="Minimaal AHN resolutie: 0.5 m"
    )
    exit_point_creation.exit_point_tab.lb3 = LineBreak()
    exit_point_creation.exit_point_tab.create_exit_point_entities = SetParamsButton(
        "Maak uittredepunt entiteiten", "create_exit_point_entities"
    )
    exit_point_creation.exit_point_tab.counter_exit_point_entities = HiddenField(
        "counter", name="counter_exit_point_entities"
    )

    exit_point_creation.general = Tab("Algemeen")
    exit_point_creation.general.show_entry_exit_lines = ToggleButton(
        "Toon intrede- en uittredelijnen", flex=50, default=True
    )
    exit_point_creation.general.show_selected_ditches = ToggleButton(
        "Toon enkel geselecteerde sloten",
        flex=50,
        default=True,
        description="Toon alle geuploade sloten als deze uit staat, anders enkel de opgeslagen sloten in het achterland als deze aan staat",
    )
    exit_point_creation.general.show_cpts = ToggleButton("Toon CPTs", flex=50, default=False)
    exit_point_creation.general.show_existing_exit_points = ToggleButton(
        "Toon opgeslagen uittredepunten",
        flex=50,
        default=True,
        description="Zet aan om de gegenereerde en opgeslagen uittredepunten te tonen",
    )

    ####################################################################################################################
    #                                                   STEP 4                                                         #
    ####################################################################################################################
    calculations = Step(
        "Berekeningen",
        views=[
            "map_calculations_overview",
            "compare_soil_layouts",
            "visualize_piping_results",
            "visualize_uplift_results",
            "visualize_heave_results",
            "visualize_sellmeijer_results",
        ],
        previous_label="Stap 3: Genereren uittredepunt",
    )
    calculations.soil_profile = Tab("Bodemopbouw")
    calculations.soil_profile.results_settings = Section("Instellingen uitvoer")

    calculations.soil_profile.results_settings.composite_result_switch = ToggleButton(
        "Gecombineerde resultaten",
        description="De gecombineerde resultaten worden gegenereerd door de resultaten voor verschillende "
        "scenarios te wegen volgens gewicht als opgegeven onder Stap 1: Input selectie",
    )
    calculations.soil_profile.results_settings.scenario_selection = OptionField(
        "Selecteer scenario voor berekening",
        options=_get_scenarios_list,
        visible=IsFalse(Lookup("calculations.soil_profile.results_settings.composite_result_switch")),
    )
    calculations.soil_profile.visualisation_settings = Section("Uittredepunten visualisatie")

    calculations.soil_profile.visualisation_settings.select_single_exit_point = ChildEntityOptionField(
        "Selecteer uittredepunten om te visualiseren", entity_type_names=["ExitPoint"]
    )

    calculations.soil_profile.visualisation_settings.show_cpt = ToggleButton(
        "Toon CPT met bodemopbouw", name="show_cpt", default=False
    )
    calculations.soil_profile.visualisation_settings.lb = LineBreak()
    calculations.soil_profile.visualisation_settings.cpt_selection = OptionField(
        "Selecteer CPT",
        options=_get_cpt_options,
        visible=_cpt_selection_visibility,
        name="selected_cpt_id",
        autoselect_single_option=False,
    )
    calculations.soil_profile.visualisation_settings.distance_to_cpt = OutputField(
        "afstand tot uittredepunt", value=_get_distance_cpt_to_exitpoint, suffix="m", visible=_cpt_selection_visibility
    )
    calculations.soil_profile.visualisation_settings.fill_cpt = SetParamsButton(
        "Vul dichtsbijzijnste CPT",
        "fill_closest_cpt",
        visible=_cpt_selection_visibility,
        description="Vul de 'Selecteer CPT' met het dichtbijzijnste TNO grondmodel.",
    )
    calculations.soil_profile.exit_point_modification = Section("Uittredepunt wijziging")
    calculations.soil_profile.exit_point_modification.selection_exit_points = OptionField(
        "Selectie", options=_get_exit_point_modification_options, variant="radio-inline"
    )
    calculations.soil_profile.exit_point_modification.update_exit_point = ActionButton(
        "Klik en update uittredepunten",
        "apply_to_exit_point",
        visible=IsEqual(
            Lookup("calculations.soil_profile.exit_point_modification.selection_exit_points"), "interactive"
        ),
        interaction=MapSelectInteraction("map_calculations_overview", selection=["points"], max_select=20),
    )
    calculations.soil_profile.exit_point_modification.update_exit_point_polygon = ActionButton(
        "Update uittredepunten",
        "apply_to_exit_point",
        description="Update all the exit point inside the drawn polygon",
        visible=IsEqual(
            # TODO TRANSLATE
            Lookup("calculations.soil_profile.exit_point_modification.selection_exit_points"),
            "polygon",
        ),
    )
    calculations.soil_profile.exit_point_modification.polygon_selection = GeoPolygonField(
        "Polygon",
        visible=IsEqual(Lookup("calculations.soil_profile.exit_point_modification.selection_exit_points"), "polygon"),
    )
    calculations.soil_profile.exit_point_modification.lb = LineBreak()
    calculations.soil_profile.exit_point_modification.top_cover = NumberField("Deklaag Bovenkant", suffix="m")
    calculations.soil_profile.exit_point_modification.bottom_cover = NumberField("Deklaag Onderkant", suffix="m")
    calculations.soil_profile.exit_point_modification.soil_type = OptionField("Grond", options=_get_soil_options)
    calculations.soil_profile.exit_point_modification.lb1 = LineBreak()
    calculations.soil_profile.exit_point_modification.reset_exit_point = ActionButton(
        "Reset uittredepunten",
        "reset_exit_point",
        visible=IsEqual(
            Lookup("calculations.soil_profile.exit_point_modification.selection_exit_points"), "interactive"
        ),
        interaction=MapSelectInteraction("map_calculations_overview", selection=["points"], max_select=20),
    )
    calculations.soil_profile.exit_point_modification.reset_exit_point_poly = ActionButton(
        "Reset uittredepunten",
        "reset_exit_point",
        description="Update all the exit point inside the drawn polygon",
        visible=IsEqual(
            # TODO TRANSLATE
            Lookup("calculations.soil_profile.exit_point_modification.selection_exit_points"),
            "polygon",
        ),
    )

    calculations.downloable_result = Tab("Downloaden")
    calculations.downloable_result.export_results = DownloadButton("Export to Excel", "download_piping_results")
