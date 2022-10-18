from collections import OrderedDict

from viktor import Color

LITHOLOGY_COLOR_DICT = {
    0: Color(0, 0, 0),
    1: Color(157, 78, 64),
    2: Color(0, 146, 0),
    3: Color(194, 207, 92),
    5: Color(255, 255, 0),
    6: Color(243, 225, 6),
    7: Color(231, 195, 22),
    8: Color(0, 0, 0),
}

STRATIGRAPHY_COLOR_DICT = {
    1000: Color(200, 200, 200),
    1070: Color(170, 255, 245),
    6000: Color(118, 147, 60),
    6100: Color(102, 205, 171),
    1090: Color(208, 130, 40),
    6200: Color(170, 196, 255),
    6300: Color(102, 153, 205),
    6400: Color(27, 101, 175),
    2010: Color(170, 255, 245),
    1130: Color(152, 47, 10),
    4000: Color(86, 0, 0),
}

LITHOLOGY_CODE_NAME_MAPPING = OrderedDict(
    {
        0: "Niet geclassificeerd",
        1: "Veen",
        2: "Klei",
        3: "Kleiig zand/ zandige klei",
        4: "lithoklasse 4",
        5: "Fijn zand",
        6: "Matig grof zand",
        7: "Grof zand",
        8: "lithoklasse 8",
    }
)

UNIQUE_TNO_SOIL_TYPES = list(LITHOLOGY_CODE_NAME_MAPPING.values())
UNIQUE_TNO_SOIL_TYPES.remove("lithoklasse 4")
UNIQUE_TNO_SOIL_TYPES.reverse()

# Soil types from the TNO model that are defined as aquifer by default
AQUIFER_TNO_SOIL_CODES = [5, 6, 7]

COVER_LAYER_COLOR = Color(192, 192, 192)
FIRST_AQUIFER_COLOR = Color.from_hex("cabc91")
INTERMEDIATE_COLOR = Color.from_hex("#9ACD32")
SECOND_AQUIFER_COLOR = Color.from_hex("#dbd1b4")
