from viktor.api_v1 import API
from viktor.parametrization import DownloadButton
from viktor.parametrization import HiddenField
from viktor.parametrization import LineBreak
from viktor.parametrization import NumberField
from viktor.parametrization import OptionField
from viktor.parametrization import OptionListElement
from viktor.parametrization import Parametrization
from viktor.parametrization import Section
from viktor.parametrization import ToggleButton


def _get_scenario_options(entity_id: int, **kwargs):
    """Return as options all the scenarios created in the parent Segment entity"""
    parent_entity_params = API().get_entity_parent(entity_id).last_saved_params
    return [
        OptionListElement(value=index, label=row["name_of_scenario"])
        for index, row in enumerate(parent_entity_params.input_selection.soil_schematization.soil_scen_array)
    ]


class ExitPointParametrization(Parametrization):
    exit_point_data = Section("Algemeen")
    exit_point_data.x_coordinate = NumberField("X coordinaat", suffix="m")
    exit_point_data.y_coordinate = NumberField("Y coordinaat", suffix="m")
    exit_point_data.ground_level = NumberField("Z coordinaat (ahn)")
    exit_point_data.tno_soil_layout = HiddenField("Bodemopbouw", name="tno_soil_layout")
    exit_point_data.scenarios = HiddenField("Bodemopbouw", name="scenarios")
    exit_point_data.classified_soil_layout = HiddenField("classified_soil_layout", name="classified_soil_layout")

    cross_section = Section("Doorsnede")
    cross_section.extension_river_side = NumberField(
        "Verleng dwarsdoorsnede tot voorbij de intredelijn", suffix="m", default=0, flex=50
    )
    cross_section.extension_exit_point_side = NumberField(
        "Verleng dwarsdoorsnede tot voorbij de uitredepunt",
        suffix="m",
        default=30,
        flex=50,
        description="Extend the cross to the side of the exit point. Value is typically 3x the leakage length.",
    )  # TODO TRANSLATE
    cross_section.lb = LineBreak()
    cross_section.spatial_resolution = NumberField(
        "Ruimtelijke resolutie", suffix="m", default=0.5, name="spatial_resolution"
    )
    cross_section.element_size = NumberField(
        "FEM maat", min=0.1, default=1, description="Size of the elements in DGeoflow"
    )  # TODO TRANSLATE
    cross_section.lb1 = LineBreak()
    cross_section.download_stix = DownloadButton("Download stix", method="download_stix")
    cross_section.download_flox = DownloadButton("Download flox", method="download_flox")

    visualisation = Section("Visualisatie")
    visualisation.scenario_selection = OptionField("Selecteer een scenario", options=_get_scenario_options)
    visualisation.river_to_the_right = ToggleButton(
        "Kant van de rivier",
        default=True,
        description="Deze knop veranderd de kant van de rivier in de dwarsdoorsnede (links of rechts)",
    )
    visualisation.autoscale = ToggleButton(
        "autoscale",
        default=True,
        description="Als dit aan staat gebruikt het figuur de volledige hoogte, <br> "
        "als dit uitstaat is de dijk op schaal: "
        "een stap in x is even groot als een stap in y",
    )
