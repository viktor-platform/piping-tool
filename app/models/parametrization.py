from viktor.parametrization import DownloadButton
from viktor.parametrization import GeoPolygonField
from viktor.parametrization import OptionField
from viktor.parametrization import Parametrization
from viktor.parametrization import Section
from viktor.parametrization import TextField

from .constants import CSV_CUTTER_SOURCE_OPTIONS


class ModelParametrization(Parametrization):
    csv_cutter = Section("CSV afsnijden")
    csv_cutter.model_select = OptionField("Selecteer de bron voor data extractie", options=CSV_CUTTER_SOURCE_OPTIONS)
    csv_cutter.polygon = GeoPolygonField(
        "Data selectie gebied",
        name="csv_cut_polygon",
        description="Selecteer het gebied waaruit de data dient worden gehaald",
    )
    csv_cutter.file_name = TextField("Vul gewenste bestandsnaam in")
    csv_cutter.set_data = DownloadButton("Haal relevante data op", method="cut_csv")
