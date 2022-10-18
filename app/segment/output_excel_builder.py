from pathlib import Path
from typing import Dict
from typing import List
from typing import Union

from munch import Munch
from numpy import inf
from numpy import nan
from pandas import DataFrame

from app.piping_tool.constants import HeaveDataFrameColumns
from app.piping_tool.constants import PipingDataFrameColumns
from app.piping_tool.constants import SellmeijerDataFrameColumns
from app.piping_tool.constants import UpliftDataFrameColumns
from app.segment.param_parser_functions import Scenario
from app.segment.param_parser_functions import get_representative_soil_layouts
from viktor import File
from viktor.external.spreadsheet import DirectInputCell
from viktor.external.spreadsheet import InputCellRange
from viktor.external.spreadsheet import NamedInputCell
from viktor.external.spreadsheet import render_spreadsheet


class PipingExcelBuilder:
    def __init__(self, results: List[Dict], params: Munch, scenario: Scenario):
        self.template_file_path = Path(__file__).parent.parent / "templates" / "piping_results.xlsx"

        self.params = params
        self.scenario = scenario

        # Add exit point name to dataframe
        def add_exit_point_name(row):
            return row.name

        self.sellmeijer_df = DataFrame.from_records(results, columns=[col.value for col in SellmeijerDataFrameColumns])
        self.sellmeijer_df[PipingDataFrameColumns.EXIT_POINT.value] = self.sellmeijer_df[
            PipingDataFrameColumns.EXIT_POINT.value
        ].apply(add_exit_point_name)
        self.sellmeijer_df = self.sellmeijer_df.replace(nan, "Nan")
        self.sellmeijer_df = self.sellmeijer_df.replace(inf, "Nan")

        self.uplift_df = DataFrame.from_records(results, columns=[col.value for col in UpliftDataFrameColumns])
        self.uplift_df[PipingDataFrameColumns.EXIT_POINT.value] = self.uplift_df[
            PipingDataFrameColumns.EXIT_POINT.value
        ].apply(add_exit_point_name)
        self.uplift_df = self.uplift_df.replace(nan, "Nan")
        self.uplift_df = self.uplift_df.replace(inf, "Nan")

        self.heave_df = DataFrame.from_records(results, columns=[col.value for col in HeaveDataFrameColumns])
        self.heave_df[PipingDataFrameColumns.EXIT_POINT.value] = self.heave_df[
            PipingDataFrameColumns.EXIT_POINT.value
        ].apply(add_exit_point_name)
        self.heave_df = self.heave_df.replace(nan, "Nan")
        self.heave_df = self.heave_df.replace(inf, "Nan")

    def get_input_cells(
        self,
    ) -> List[Union[InputCellRange, DirectInputCell, NamedInputCell]]:
        """This method should return a list of InputCell objects for the SpreadsheetTemplate"""
        headers_cells = [
            InputCellRange("Opbarsten", "A", 1, data=[[name.value for name in UpliftDataFrameColumns]]),
            InputCellRange("Heave", "A", 1, data=[[name.value for name in HeaveDataFrameColumns]]),
            InputCellRange("Sellmeijer", "A", 1, data=[[name.value for name in SellmeijerDataFrameColumns]]),
        ]

        sellmeijer_cells = self.get_sellmeijer_table()
        uplift_cells = self.get_uplift_table()
        heave_cells = self.get_heave_table()
        metadata_cells = self.get_metadata_cells()

        return headers_cells + sellmeijer_cells + uplift_cells + heave_cells + metadata_cells

    def get_metadata_cells(self) -> List[Union[InputCellRange, DirectInputCell, NamedInputCell]]:
        """Returns the cells for the sheet Metadata"""
        cells = []
        _, rep_soil_layout = get_representative_soil_layouts(self.params, self.scenario)
        for index, layer in enumerate(rep_soil_layout.serialize().get("layers"), 1):
            cells.append(DirectInputCell("Metadata", "A", row=1 + index, value=layer["soil"].get("name")))
            cells.append(DirectInputCell("Metadata", "B", row=1 + index, value=layer.get("top_of_layer")))
            cells.append(DirectInputCell("Metadata", "C", row=1 + index, value=layer.get("bottom_of_layer")))
        return cells

    def get_sellmeijer_table(self) -> List[InputCellRange]:
        """Fill the spreadsheet with the Sellmeijer results"""
        data = self.get_piping_data(calculation_type="sellmeijer")
        table = []
        for index, row in enumerate(data):
            table.append(InputCellRange("Sellmeijer", "A", index + 2, data=[row]))
        return table

    def get_uplift_table(self) -> List[InputCellRange]:
        """Fill the spreadsheet with the Uplift results"""
        data = self.get_piping_data(calculation_type="uplift")
        table = []
        for index, row in enumerate(data):
            table.append(InputCellRange("Opbarsten", "A", index + 2, data=[row]))
        return table

    def get_heave_table(self) -> List[InputCellRange]:
        """Fill the spreadsheet with the Heave results"""
        data = self.get_piping_data(calculation_type="heave")
        table = []
        for index, row in enumerate(data):
            table.append(InputCellRange("Heave", "A", index + 2, data=[row]))
        return table

    def get_piping_data(self, calculation_type: str) -> List[List]:
        """Return the data of the piping results to be used in the Excel Template. It's a rectangular list of lists
        :param calculation_type: one of ['sellmeijer', 'uplift', 'heave']
        """
        if calculation_type == "sellmeijer":
            column_names = SellmeijerDataFrameColumns
            df = self.sellmeijer_df
        elif calculation_type == "uplift":
            column_names = UpliftDataFrameColumns
            df = self.uplift_df
        elif calculation_type == "heave":
            column_names = HeaveDataFrameColumns
            df = self.heave_df
        else:
            raise ValueError("Missing calculation type")

        data = []
        for _, row in df.iterrows():
            data.append([row[name.value] for name in column_names])

        return data

    def get_rendered_file(self) -> File:
        """Returns the rendered template spreadsheet and the corresponding file_name"""

        with open(self.template_file_path, "rb") as template:
            template = render_spreadsheet(template, self.get_input_cells())

        return template
