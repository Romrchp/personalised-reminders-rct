import unittest
from unittest.mock import patch, MagicMock
import os
from ..src.data_manager.myfoodrepo_api_handler import create_myfoodrepo_service_instance, MyFoodRepoService

class TestMyFoodRepoService(unittest.TestCase):

    @patch.dict(os.environ, {'MFR_UID': 'dummy_uid', 'MFR_CLIENT': 'dummy_client', 'MFR_ACCESS_TOKEN': 'dummy_token'})
    def test_create_myfoodrepo_service_instance_valid_key(self):
        # Mocking the creation of MyFoodRepoService with 'staging'
        mfr_key = 'staging'
        cohort_id = 123

        # Mocking the service instance
        with patch('your_module.MyFoodRepoService') as MockMyFoodRepoService:
            service_instance = create_myfoodrepo_service_instance(mfr_key, cohort_id)

            # Check if MyFoodRepoService is initialized with the correct parameters
            MockMyFoodRepoService.assert_called_once_with(
                host=MockMyFoodRepoService.STAGING_HOST,
                uid='dummy_uid',
                client='dummy_client',
                access_token='dummy_token'
            )
            self.assertIsInstance(service_instance, MyFoodRepoService)

    @patch.dict(os.environ, {'MFR_UID': 'dummy_uid', 'MFR_CLIENT': 'dummy_client', 'MFR_ACCESS_TOKEN': 'dummy_token'})
    def test_create_myfoodrepo_service_instance_invalid_key(self):
        # Test invalid environment key
        with self.assertRaises(ValueError):
            create_myfoodrepo_service_instance('invalid_key')

    @patch.dict(os.environ, {'MFR_UID': 'dummy_uid', 'MFR_CLIENT': 'dummy_client', 'MFR_ACCESS_TOKEN': 'dummy_token'})
    @patch('requests.request')
    def test_participations(self, mock_request):
        # Prepare the mock response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'data': [{'id': 1, 'name': 'Test Participation'}],
            'meta': {'next': None}
        }
        mock_request.return_value = mock_response

        service = MyFoodRepoService(
            host="staging-v2.myfoodrepo.org",
            uid="dummy_uid",
            client="dummy_client",
            access_token="dummy_token"
        )

        # Test the method
        data, next_page = service.participations(cohort_id=123, page=1)

        # Verify the response and call
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Test Participation')
        self.assertIsNone(next_page)

        mock_request.assert_called_once_with(
            'get',
            'https://staging-v2.myfoodrepo.org/collab/api/v1/cohorts/123/participations',
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'uid': 'dummy_uid',
                'client': 'dummy_client',
                'access-token': 'dummy_token'
            },
            params={'page': 1, 'items': 100},
            verify=True
        )

    @patch.dict(os.environ, {'MFR_UID': 'dummy_uid', 'MFR_CLIENT': 'dummy_client', 'MFR_ACCESS_TOKEN': 'dummy_token'})
    @patch('requests.request')
    def test_nutrient_ids(self, mock_request):
        # Prepare the mock response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'data': [{'id': 1}, {'id': 2}],
            'meta': {'next': None}
        }
        mock_request.return_value = mock_response

        service = MyFoodRepoService(
            host="staging-v2.myfoodrepo.org",
            uid="dummy_uid",
            client="dummy_client",
            access_token="dummy_token"
        )

        # Test the method
        nutrient_ids = service.nutrient_ids()

        # Verify the response and call
        self.assertEqual(nutrient_ids, [1, 2])

        mock_request.assert_called_once_with(
            'get',
            'https://staging-v2.myfoodrepo.org/collab/api/v1/nutrients',
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'uid': 'dummy_uid',
                'client': 'dummy_client',
                'access-token': 'dummy_token'
            },
            params={'page': 1, 'items': 250},
            verify=True
        )

    @patch.dict(os.environ, {'MFR_UID': 'dummy_uid', 'MFR_CLIENT': 'dummy_client', 'MFR_ACCESS_TOKEN': 'dummy_token'})
    @patch('requests.request')
    def test_create_cohort_participation(self, mock_request):
        # Prepare the mock response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {'data': {'id': 1, 'name': 'New Participation'}}
        mock_request.return_value = mock_response

        service = MyFoodRepoService(
            host="staging-v2.myfoodrepo.org",
            uid="dummy_uid",
            client="dummy_client",
            access_token="dummy_token"
        )

        # Test the method
        participation = service.create_cohort_participation(cohort_id=123)

        # Verify the response and call
        self.assertEqual(participation['name'], 'New Participation')

        mock_request.assert_called_once_with(
            'post',
            'https://staging-v2.myfoodrepo.org/collab/api/v1/cohorts/123/participations',
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'uid': 'dummy_uid',
                'client': 'dummy_client',
                'access-token': 'dummy_token'
            },
            params={},
            verify=True
        )

if __name__ == '__main__':
    unittest.main()
