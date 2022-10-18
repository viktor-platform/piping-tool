# pylint: disable-all
from io import BytesIO
from pathlib import Path
from unittest import TestCase
from unittest import skip
from unittest.mock import MagicMock

from app.dyke.controller import Controller as DykeController
from app.dyke.dykeAPI import DykeAPI
from app.ground_model.tno_model import TNOGroundModel
from app.lib.shapely_helper_functions import convert_shapely_linestring_to_shapefile
from tests.fixtures.mocked_files import DYKES_ENTITIES
from tests.fixtures.mocked_files import SEGMENT_ENTITIES
from tests.fixtures.mocked_files import STE_GROUND_MODEL_ENTITY
from tests.fixtures.mocked_files import STE_GROUND_MODEL_FILE
from viktor import File
from viktor.result import DownloadResult
from viktor.views import MapResult
from viktor.views import PlotlyResult


class TestSegmentController(TestCase):
    """This class tests the Controller of the Segment entity type"""

    controller_type = DykeController
    default_entity = DYKES_ENTITIES[0]

    def setUp(self) -> None:
        """This setup function is automatically called before every test.

        It will set-up the default params and controller with default mocked functions
        """
        # Load relevant test data
        self.params = self.default_entity.last_saved_params
        self.entity_id = 1
        tno_entity = STE_GROUND_MODEL_ENTITY
        tno_file = File.from_data(STE_GROUND_MODEL_FILE)
        tno_model = TNOGroundModel(tno_entity.last_saved_params, tno_file)
        self.params.downloads.segment_select = SEGMENT_ENTITIES[0]

        # Mock API calls
        api = DykeAPI(self.entity_id, self.params)
        api.get_tno_entity = MagicMock(return_value=tno_entity)
        api.get_ground_model = MagicMock(return_value=tno_model)

        self.controller = self.controller_type(params=self.params)
        self.controller.get_api = MagicMock(return_value=api)

    def tearDown(self) -> None:
        """This setup function is automatically called after every test.

        It will the previously set-up variable to ensure that no state is stored
        """
        self.params = None
        self.controller = None

    @skip("")
    def test_visualize_map_returns_MapResult(self, *args):
        """Test that the visualize_map function returns a MapResult"""
        # Act
        result = self.controller.visualize_map(self.controller, self.params, self.entity_id)

        # Assert
        self.assertIsInstance(result, MapResult)

    def test_visualize_ground_model_along_dyke_returns_PlotlyResult(self):
        """Test that the visualize_ground_model_along_dyke function returns a PlotlyResult"""
        # Act
        result = self.controller.visualize_ground_model_along_dyke(self.controller, self.params, self.entity_id)

        # Assert
        self.assertIsInstance(result, PlotlyResult)

    @skip("Comparing bytes not feasible, possibly try later")
    def test_convert_shapely_linestring_to_shapefile(self):
        """Test that the shapely linestring conversion returns shapefiles"""
        # Act
        segment_entity = SEGMENT_ENTITIES[0]
        segment_polygon = segment_entity.last_saved_params.segment_polygon
        result = convert_shapely_linestring_to_shapefile(self.params, segment_polygon, segment_entity.name)
        dbf = result[f"{segment_entity.name}_trajectory.dbf"]
        shp = result[f"{segment_entity.name}_trajectory.shp"]
        shx = result[f"{segment_entity.name}_trajectory.shx"]

        dbf_path = Path(__file__).parent.parent / f"fixtures/segment_trajectory/Segment1_trajectory.dbf"
        with open(dbf_path, "rb") as fh:
            dbf_fixture = BytesIO(fh.read())
        shp_path = Path(__file__).parent.parent / f"fixtures/segment_trajectory/Segment1_trajectory.shp"
        with open(shp_path, "rb") as fh:
            shp_fixture = BytesIO(fh.read())
        shx_path = Path(__file__).parent.parent / f"fixtures/segment_trajectory/Segment1_trajectory.shx"
        with open(shx_path, "rb") as fh:
            shx_fixture = BytesIO(fh.read())

        # Assert
        assert dbf.getvalue() == dbf_fixture.getvalue()
        assert shp.getvalue() == shp_fixture.getvalue()
        assert shx.getvalue() == shx_fixture.getvalue()

    def test_get_segment_trajectories_returns_DownloadResult(self):
        """Test that the get_segment_trajectories function returns a DownloadResult"""
        # Act
        result = self.controller.get_segment_trajectories(self.params)

        # Assert
        self.assertIsInstance(result, DownloadResult)
