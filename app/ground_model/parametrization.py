from viktor.parametrization import GeoPolygonField
from viktor.parametrization import HiddenField
from viktor.parametrization import Parametrization
from viktor.parametrization import Section


class GroundModelParametrization(Parametrization):
    ground_model = Section("Sectie naam")
    ground_model.data = HiddenField("Model", name="data")
    ground_model.convex_hull = GeoPolygonField("Model gebied", name="convex_hull")
    ground_model.chainage_length = HiddenField("Data kilometrering", name="chainage_length")
