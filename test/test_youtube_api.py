import pytest
from unittest.mock import patch, MagicMock
from src.core import youtube_api

# Sample data to mock the API response
mock_channel_response = {
    'items': [{
        'id': 'test_channel_id',
        'snippet': {
            'title': 'Test Channel',
            'customUrl': 'testchannel',
            'publishedAt': '2020-01-01T00:00:00Z',
            'thumbnails': {
                'high': {
                    'url': 'http://example.com/thumbnail.jpg'
                }
            }
        },
        'brandingSettings': {
            'channel': {
                'description': 'Test Description',
                'country': 'Test Country'
            }
        }
    }]
}


@pytest.fixture
def youtube_client():
    with patch('src.core.youtube_api.YoutubeAPI._api_key_from_env') as mock_build:  # noqa
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        yield mock_youtube


@pytest.fixture
def API_object(youtube_client):
    API = youtube_api.YoutubeAPI()
    yield API
    del API


def test_start(API_object, youtube_client):
    assert API_object.youtube == youtube_client


def test_get_channel_info_success(API_object, youtube_client):
    # Mock the channels().list().execute() method chain
    youtube_client.channels().list().execute.return_value = mock_channel_response  # noqa

    # Call the function with a mock channel ID
    channel_info = API_object.get_channel_info(
        'test_channel_id')

    # Assertions to validate the expected outcomes
    assert channel_info is not None
    assert channel_info['channel_id'] == 'test_channel_id'
    assert channel_info['name'] == 'Test Channel'
    assert channel_info['customUrl'] == 'testchannel'
    assert channel_info['published_date'] == '2020-01-01T00:00:00Z'
    assert channel_info['thumbnail_url'] == 'http://example.com/thumbnail.jpg'
    assert channel_info['description'] == 'Test Description'
    assert channel_info['country'] == 'Test Country'


def test_get_channel_info_not_found(API_object, youtube_client):
    # Mock the API response for a non-existent channel
    youtube_client.channels().list().execute.return_value = {
        'something_else': 'foo'}

    # Call the function with a mock channel ID that does not exist
    channel_info = API_object.get_channel_info('non_existent_channel_id')

    # Assert that the function handles non-existent channels gracefully
    assert channel_info is None
