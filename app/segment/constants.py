from cmath import nan
from enum import Enum

from app.ground_model.constants import LITHOLOGY_CODE_NAME_MAPPING
from viktor import Color
from viktor.parametrization import OptionListElement
from viktor.views import MapLegend


class PipingCalculationType(Enum):
    UPLIFT = "uplift"
    HEAVE = "heave"
    SELLMEIJER = "sellmeijer"


GEOHYDROLOGICAL_OPTIONS = [OptionListElement(value=i, label=f"level {i}") for i in ["0", "1", "2", "3"]]

TNO_LITHOCLASS_OPTIONS = [
    OptionListElement(soil_name)
    for soil_code, soil_name in LITHOLOGY_CODE_NAME_MAPPING.items()
    if soil_code not in (4, 8)
]

LEAKAGE_LENGTH_OPTIONS = [
    OptionListElement(label="Van TNO model", value="from_tno_model"),
    OptionListElement(label="Van materiaal tabel", value="from_material_table"),
]

SPATIAL_RESOLUTION_SEGMENT_CHAINAGE = 10

PIPING_LEGEND = MapLegend(
    [(Color.red(), "Voldoet niet"), (Color.from_hex("#FFC300"), "uc niet berekend"), (Color.green(), "Voldoet")]
)

DEFAULT_PIPING_ERROR_RESULTS = {
    "Sloot": "-",
    "Maaiveld [m NAP]": 9999,
    "RivierPeil [m NAP]": 9999,
    "FreatischNiveauUittredepunt [m NAP]": 9999,
    "DeklaagDikte [m]": 9999,
    "AquiferDikte [m]": 9999,
    "AquiferDarcyDoorlatenheid [m/d]": 9999,
    "AquiferIntrinsiekDoorlatenkeid [m/s]": 9999,
    "d70_m [mm]": 9999,
    "m_p [-]": 9999,
    "f_1 [-]": 9999,
    "CoefficientvanWhite [-]": 9999,
    "Theta [-]": 9999,
    "d70_ref [mm]": 9999,
    "R_c": 9999,
    "f_2 [-]": 9999,
    "f_3 [-]": 9999,
    "KwelwegLengte [m]": 9999,
    "KritiekVervalPipingSellmeijer [m]": 9999,
    "GereduceerdOptredendVerval [m]": 9999,
    "uc_sellmeijer": nan,
    "KritiekStijghoogteVerschilOpbarsten [m]": "nan",
    "StijghoogteWaterVoerendPakketBijUittredepunt [m NAP]": 9999,
    "KritiekeGradientHeave": 9999,
    "uc_opbarsten": nan,
    "uc_heave": nan,
    "z opbarsten": nan,
    "z heave": nan,
    "aquifer": 1,
}

# Reasons for which a UC is not calculated:
#  - Ditches parameters are invalid, see class: DitchHeffError
#  - Invalid input parameters, which can result in a division by 0 for example.
