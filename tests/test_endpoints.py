import pytest
from unittest.mock import patch, MagicMock
from src.config.config import create_app

@pytest.fixture()
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@patch('src.data_manager.user.get_all_users', return_value=[])
def test_index(mock_get_all_users, client):
    """Testing the app's home page."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'users_count' in response.data
    mock_get_all_users.assert_called_once()  # Checks if the user count is present
    #TODO : Adding other useful things to assert


@patch('src.data_manager.user.add_user', return_value="User Added Successfully")
def test_add_user(mock_add_user, client):
    """Test adding a user."""
    response = client.post('/add_user', data={'phone_number': '1234567890'})
    assert response.status_code == 200
    assert b"User Added Successfully" in response.data
    mock_add_user.assert_called_once_with('1234567890', None)
    #TODO : Adding other useful things to assert


@patch('src.data_manager.user.get_all_users', return_value=[
        MagicMock(to_dict=lambda: {"phone_number": "+1234567890"})
        ])
def test_get_users(mock_get_all_users, client):
    """Test fetching all users."""
    response = client.get('/get_users')
    assert response.status_code == 200
    assert response.json == [{"phone_number": "+1234567890"}]
    mock_get_all_users.assert_called_once()


