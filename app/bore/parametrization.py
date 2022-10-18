from viktor.parametrization import LineBreak
from viktor.parametrization import NumberField
from viktor.parametrization import Parametrization
from viktor.parametrization import Section
from viktor.parametrization import Tab
from viktor.parametrization import TableInput
from viktor.parametrization import TextField


class BoreParametrization(Parametrization):
    gef = Tab("GEF")
    gef.bore_data = Section("Eigenschappen en bodemopbouw")
    gef.bore_data.x_rd = NumberField("X-coordinaat", suffix="m", name="x_rd")
    gef.bore_data.y_rd = NumberField("Y-coordinaat", suffix="m", name="y_rd")
    gef.bore_data.z = NumberField("Z-coordinaat", suffix="m", name="z")
    gef.bore_data.test_id = TextField("Test id", name="test_id")

    gef.bore_data.lb1 = LineBreak()
    gef.bore_data.soil_table = TableInput("Bodemopbouw", name="soil_table", visible=False)
    gef.bore_data.soil_table.top_nap = NumberField("Bovenkant NAP[m]", num_decimals=2)
    gef.bore_data.soil_table.bottom_nap = NumberField("Onderkand NAP[m]", num_decimals=2)
    gef.bore_data.soil_table.soil_code = TextField("Grond Code")
    gef.bore_data.soil_table.gravel_component = NumberField("Grind component", num_decimals=2)
    gef.bore_data.soil_table.sand_component = NumberField("Zand component", num_decimals=2)
    gef.bore_data.soil_table.clay_component = NumberField("Klei component", num_decimals=2)
    gef.bore_data.soil_table.loam_component = NumberField("Leem component", num_decimals=2)
    gef.bore_data.soil_table.peat_component = NumberField("Veen component", num_decimals=2)
