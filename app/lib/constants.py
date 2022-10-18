from enum import IntEnum

from viktor import Color
from viktor.views import MapLegend

MAP_LEGEND_LIST = [
    (Color.green(), "Dyke trajectory"),
    (Color.blue(), "Selected segment"),
    (Color.lime(), "Entry line"),
    (Color.viktor_yellow(), "Bore/Cpts buffer zone"),
]
MAP_LEGEND = MapLegend(MAP_LEGEND_LIST)  # TODO TRANSLATE

MAP_LEGEND_SEGMENT_ENTITY = MapLegend(  # TODO TRANSLATE
    [
        (Color.green(), "Dyke trajectory"),
        (Color.blue(), "Selected segment"),
        (Color.red(), "Cross-section"),
        (Color.viktor_blue(), "Foreland"),
        (Color.black(), "Hinterland"),
    ]
)

COLOR_MAP_GROUND_MODEL = Color(169, 169, 169)

DRY_DITCH_COLOR = Color(0, 255, 255)

WET_DITCH_COLOR = Color(0, 139, 139)

EXISTING_EXIT_POINT_COLOR = Color(255, 140, 0)

FUTURE_EXIT_POINT_COLOR = Color.black()

LOWEST_POINT_COLOR = Color.from_hex("#CCCCFF")

LEGEND_LIST_EXIT_POINT_CREATION = [
    (WET_DITCH_COLOR, "Sloot"),
    (DRY_DITCH_COLOR, "Droog sloot"),
    (EXISTING_EXIT_POINT_COLOR, "Aanwezig Uittedepunt"),
    (FUTURE_EXIT_POINT_COLOR, "Toekomst uittredepunt"),
]


class WaterDirection(IntEnum):
    CLOCKWISE = 1
    COUNTER_CLOCKWISE = -1
