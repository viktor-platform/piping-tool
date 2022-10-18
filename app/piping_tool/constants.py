from enum import Enum

GAMMA_W = 9.81
GRAVITY = 9.81

# Model factors
M_P = 1.00
M_U = 1.00
M_HE = 1.00

R_C = 0.30  # Reduction factor for the resistance of the cover layer at the exit point

WHITE_COEFFICIENT = 0.25  # [-]
THETA = 37.0  # standard "rolweerstandshoek" for Sellmeijer [degree]
D70_REF = 0.000208  # Reference grain size d70 for Sellmeijer calculation [m]
VISCOSITY = 0.00000133  # Kinematic viscosity to determine intrinsic permeability of sand (at 10 degree celcius) [m2/s]
GAMMA_P_SUB = 16.19  # submerged weight of sand grains [kN/m3]
CRITICAL_HEAVE_GRADIENT = 0.3


class SellmeijerDataFrameColumns(Enum):
    """Enum for the column names of the Sellmeijer intermediate results DataFrame.
    Order matters here as this is the order of the columns in the downloadable excel sheets."""

    EXIT_POINT = "Uittredepunt"
    AQUIFER = "aquifer"
    DITCH = "Sloot"
    M_P = "m_p [-]"
    WHITE_COEFFICIENT = "CoefficientvanWhite [-]"
    THETA = "Theta [-]"
    D_70_REF = "d70_ref [mm]"
    R_C = "R_c"
    COVER_LAYER_THICKNESS = "DeklaagDikte [m]"
    AQUIFER_THICKNESS = "AquiferDikte [m]"
    AQUIFER_PERMEABILITY = "AquiferDarcyDoorlatenheid [m/d]"
    AQUIFER_INTR_PERMEABILITY = "AquiferIntrinsiekDoorlatenkeid [m/s]"
    AQUIFER_D_70 = "d70_m [mm]"
    PHREATIC_LEVEL = "FreatischNiveauUittredepunt [m NAP]"
    RIVER_LEVEL = "RivierPeil [m NAP]"
    F_1 = "f_1 [-]"
    F_2 = "f_2 [-]"
    F_3 = "f_3 [-]"
    SEEPAGE_LENGTH = "KwelwegLengte [m]"
    CRITICAL_HEAD_DIFFERENCE_SELLMEIJER = "KritiekVervalPipingSellmeijer [m]"
    REDUCED_HEAD_DIFFERENCE = "GereduceerdOptredendVerval [m]"
    SELLMEIJER_UNITY_CHECK = UNITY_CHECK = "uc_sellmeijer"


class UpliftDataFrameColumns(Enum):
    """Enum for the column names of the uplift intermediate results DataFrame.

    Order matters here as this is the order of the columns in the downloadable excel sheets."""

    EXIT_POINT = "Uittredepunt"
    AQUIFER = "aquifer"
    DITCH = "Sloot"
    DITCH_SMALL_B = "Sloot_b"
    DITCH_LARGE_B = "Sloot_B"
    GROUND_LEVEL = "Maaiveld [m NAP]"
    RIVER_LEVEL = "RivierPeil [m NAP]"
    COVER_LAYER_THICKNESS = "DeklaagDikte [m]"
    POTENTIAL_UPLIFT = "KritiekStijghoogteVerschilOpbarsten [m]"  # WSRL: d_pot_c_u
    AQUIFER_HYDRAULIC_HEAD = "StijghoogteWaterVoerendPakketBijUittredepunt [m NAP]"  # WSRL: pot_exit
    WATER_LEVEL_EXIT_POINT = "FreatischNiveauUittredepunt [m NAP]"  # WSRL: h_exit
    UPLIFT_UNITY_CHECK = "uc_opbarsten"
    UPLIFT_LIMIT_STATE_SCORE = "z opbarsten"


class HeaveDataFrameColumns(Enum):
    """Enum for the column names of the heave intermediate results DataFrame.

    Order matters here as this is the order of the columns in the downloadable excel sheets."""

    EXIT_POINT = "Uittredepunt"
    AQUIFER = "aquifer"
    DITCH = "Sloot"
    GROUND_LEVEL = "Maaiveld [m NAP]"
    CRITICAL_HEAVE_GRADIENT = "KritiekeGradientHeave"  # WSRL: i_c_h
    COVER_LAYER_THICKNESS = "DeklaagDikte [m]"
    POTENTIAL_UPLIFT = "KritiekStijghoogteVerschilOpbarsten [m]"  # WSRL: d_pot_c_u
    AQUIFER_HYDRAULIC_HEAD = "StijghoogteWaterVoerendPakketBijUittredepunt [m NAP]"  # WSRL: pot_exit
    HEAVE_UNITY_CHECK = "uc_heave"
    HEAVE_LIMIT_STATE_SCORE = "z heave"


class PipingDataFrameColumns(Enum):
    """Enum for the column names of all the piping calculation
    Order does not matter here as the dataframe is not directly returned
    """

    SCENARIO = "scenario"
    EXIT_POINT = "Uittredepunt"
    AQUIFER = "aquifer"
    DITCH = "Sloot"
    DITCH_SMALL_B = "Sloot_b"
    DITCH_LARGE_B = "Sloot_B"

    GROUND_LEVEL = "Maaiveld [m NAP]"
    RIVER_LEVEL = "RivierPeil [m NAP]"
    PHREATIC_LEVEL = "FreatischNiveauUittredepunt [m NAP]"
    COVER_LAYER_THICKNESS = "DeklaagDikte [m]"
    AQUIFER_HYDRAULIC_HEAD = "StijghoogteWaterVoerendPakketBijUittredepunt [m NAP]"  # WSRL: pot_exit
    WATER_LEVEL_EXIT_POINT = "FreatischNiveauUittredepunt [m NAP]"  # WSRL: h_exit
    M_P = "m_p [-]"
    WHITE_COEFFICIENT = "CoefficientvanWhite [-]"
    THETA = "Theta [-]"
    D_70_REF = "d70_ref [mm]"
    R_C = "R_c"

    POTENTIAL_UPLIFT = "KritiekStijghoogteVerschilOpbarsten [m]"  # WSRL: d_pot_c_u
    CRITICAL_HEAVE_GRADIENT = "KritiekeGradientHeave"  # WSRL: i_c_h
    AQUIFER_THICKNESS = "AquiferDikte [m]"
    AQUIFER_PERMEABILITY = "AquiferDarcyDoorlatenheid [m/d]"
    AQUIFER_INTR_PERMEABILITY = "AquiferIntrinsiekDoorlatenkeid [m/s]"
    AQUIFER_D_70 = "d70_m [mm]"
    F_1 = "f_1 [-]"
    F_2 = "f_2 [-]"
    F_3 = "f_3 [-]"
    SEEPAGE_LENGTH = "KwelwegLengte [m]"
    CRITICAL_HEAD_DIFFERENCE_SELLMEIJER = "KritiekVervalPipingSellmeijer [m]"
    REDUCED_HEAD_DIFFERENCE = "GereduceerdOptredendVerval [m]"

    UPLIFT_UNITY_CHECK = "uc_opbarsten"
    HEAVE_UNITY_CHECK = "uc_heave"
    SELLMEIJER_UNITY_CHECK = UNITY_CHECK = "uc_sellmeijer"
    UPLIFT_LIMIT_STATE_SCORE = "z opbarsten"
    HEAVE_LIMIT_STATE_SCORE = "z heave"
    SELLMEIJER_LIMIT_STATE_SCORE = "z Sellmeijer"
