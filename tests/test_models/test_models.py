# pylint: disable-all
from unittest import TestCase
from unittest.mock import MagicMock

from app.models.controller import Controller as ModelsController
from tests.fixtures.mocked_files import MODELS_FOLDER_ENTITIES
from tests.test_models.fixtures_models import CUT_CSV_MOCK
from viktor.result import DownloadResult
from viktor.views import MapResult


class TestModelsController(TestCase):
    """This class test the Controller of the Models entity"""

    controller = ModelsController
    default_entity = MODELS_FOLDER_ENTITIES[0]
    params = default_entity.last_saved_params
    entity_id = 1

    def test_map_visualization_returns_MapResult(self):
        """Test that the visualize_map function returns a MapResult"""
        # Act
        result = self.controller.visualization(self.controller, self.params, self.entity_id)

        # Assert
        self.assertIsInstance(result, MapResult)

    def test_csv_cutter_returns_DownloadResult(self):
        """Test that the csv_cutter function returns a DownloadResult"""
        # Mock
        self.controller.run_generic_worker_csv_cutter = MagicMock(return_value=CUT_CSV_MOCK)

        # Act
        result = self.controller.cut_csv(self.controller, self.params)

        # Assert
        self.assertIsInstance(result, DownloadResult)
