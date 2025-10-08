import unittest
from unittest.mock import patch, MagicMock
import os
import shutil
import pandas as pd
from  src.data_manager.myfoodrepo_data_manager import (
    insert_user_meal_data_to_db, process_user_data, load_data_from_csv,
    download_csv, update_database, MyFoodRepoService, ExportCohortAnnotationsService
)
from ..src.db_session import session_scope
from ..src.utils.csv_utils import read_csv_to_dataframe
from ..src.utils.pandas_utils import delete_empty_rows
from ..src.utils.date_utils import convert_to_local_time
from ..src.data_manager.models import Meal, User

class TestMyFoodRepoDataManager(unittest.TestCase):

    @patch('src.db_session.session_scope')
    @patch('your_module.get_json_from_df_row')
    def test_insert_user_meal_data_to_db(self, mock_get_json, mock_session_scope):
        # Setup mock session
        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        
        # Prepare DataFrame for the test
        df = pd.DataFrame({
            'food_name': ['Meal1', 'Meal2'],
            'local_time': [pd.Timestamp('2023-03-01 12:00'), pd.Timestamp('2023-03-01 13:00')],
            'participation_key': ['key1', 'key1']
        })

        # Mock the user retrieval
        mock_user = MagicMock()
        mock_user.id = 1
        mock_session.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Mock the get_json_from_df_row to return some dummy data
        mock_get_json.return_value = {"nutrients": "dummy_data"}

        # Call the function
        insert_user_meal_data_to_db(df, 'key1')

        # Verify database operations
        mock_session.query.assert_called()
        mock_session.add.assert_called()

    @patch('your_module.group_by_intakeid')
    @patch('your_module.aggregate_by_time_window')
    @patch('your_module.insert_user_meal_data_to_db')
    def test_process_user_data(self, mock_insert, mock_aggregate, mock_group):
        # Prepare the DataFrame and mock methods
        df = pd.DataFrame({
            'food_name': ['Meal1', 'Meal2'],
            'local_time': [pd.Timestamp('2023-03-01 12:00'), pd.Timestamp('2023-03-01 13:00')],
            'participation_key': ['key1', 'key1']
        })
        
        mock_group.return_value = df
        mock_aggregate.return_value = df

        # Call the function
        process_user_data(df, 'key1')

        # Check that insert_user_meal_data_to_db was called
        mock_insert.assert_called_with(df, 'key1')

    @patch('your_module.read_csv_to_dataframe')
    def test_load_data_from_csv(self, mock_read_csv):
        # Prepare a mock DataFrame
        mock_df = pd.DataFrame({'col1': [1, 2], 'col2': ['A', 'B']})
        mock_read_csv.return_value = mock_df

        # Call the function
        df = load_data_from_csv()

        # Assert that DataFrame is returned correctly
        self.assertEqual(df.shape, (2, 2))
        mock_read_csv.assert_called_once_with(os.path.join('data', 'cohort_annotations.csv'))

    @patch('your_module.MyFoodRepoService')
    @patch('your_module.ExportCohortAnnotationsService')
    @patch('shutil.copyfile')
    @patch('os.remove')
    def test_download_csv(self, mock_remove, mock_copy, mock_export, mock_service):
        # Mock environment variables
        os.environ['MFR_ENV_KEY'] = 'staging'
        os.environ['MFR_COHORT_ID_KEY'] = '123'

        # Mocking the MyFoodRepoService and ExportCohortAnnotationsService
        mock_service_instance = MagicMock()
        mock_service.return_value = mock_service_instance
        mock_export_service = MagicMock()
        mock_export.return_value = mock_export_service
        
        # Mock the file paths
        mock_copy.return_value = None
        mock_remove.return_value = None

        # Call the function
        download_csv()

        # Assert that the download process works as expected
        mock_service.assert_called_once()
        mock_export_service.call.assert_called_once()
        mock_copy.assert_called_once()
        mock_remove.assert_called_once()

    @patch('your_module.download_csv')
    @patch('your_module.load_data_from_csv')
    @patch('your_module.process_user_data')
    def test_update_database(self, mock_process, mock_load, mock_download):
        # Prepare the mock data
        mock_download.return_value = None
        mock_df = pd.DataFrame({
            'participation_key': ['key1', 'key2'],
            'food_name': ['Meal1', 'Meal2'],
            'local_time': [pd.Timestamp('2023-03-01 12:00'), pd.Timestamp('2023-03-01 13:00')]
        })
        mock_load.return_value = mock_df
        
        # Mock the processing
        mock_process.return_value = None

        # Call the function
        update_database()

        # Assert that all the steps are executed
        mock_download.assert_called_once()
        mock_load.assert_called_once()
        mock_process.assert_called()

if __name__ == '__main__':
    unittest.main()
