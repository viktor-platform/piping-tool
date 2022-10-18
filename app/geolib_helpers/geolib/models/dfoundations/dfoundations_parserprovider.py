from typing import List
from typing import Tuple
from typing import Type

from geolib.models.dseries_parser import DSerieParser
from geolib.models.dseries_parser import DSeriesStructure
from geolib.models.parsers import BaseParserProvider
from pydantic import FilePath

from .internal import DFoundationsDumpfileOutputStructure
from .internal import DFoundationsDumpStructure
from .internal import DFoundationsInputStructure
from .internal import DFoundationsStructure


class DFoundationsInputParser(DSerieParser):
    """DFoundations parser of input files."""

    @property
    def suffix_list(self) -> List[str]:
        return [".foi"]

    @property
    def dserie_structure(self) -> Type[DFoundationsStructure]:
        return DFoundationsStructure


class DFoundationsOutputParser(DSerieParser):
    """DFoundations parser of input files."""

    @property
    def suffix_list(self) -> List[str]:
        return [".fod"]

    @property
    def dserie_structure(self) -> Type[DFoundationsDumpStructure]:
        return DFoundationsDumpStructure


class DFoundationsParserProvider(BaseParserProvider):

    __input_parsers = None
    __output_parsers = None

    @property
    def input_parsers(self) -> Tuple[DFoundationsInputParser]:
        if not self.__input_parsers:
            self.__input_parsers = (DFoundationsInputParser(),)
        return self.__input_parsers

    @property
    def output_parsers(self) -> Tuple[DFoundationsOutputParser]:
        if not self.__output_parsers:
            self.__output_parsers = (DFoundationsOutputParser(),)
        return self.__output_parsers

    @property
    def parser_name(self) -> str:
        return "DFoundations"
