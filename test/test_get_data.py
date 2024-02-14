import pytest
from unittest.mock import patch, MagicMock
from src import get_data

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
    with patch('googleapiclient.discovery.build') as mock_build:
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        yield mock_youtube


def test_get_channel_info_success(youtube_client):
    # Mock the channels().list().execute() method chain
    youtube_client.channels().list().execute.return_value = mock_channel_response  # noqa

    # Call the function with a mock channel ID
    channel_info = get_data.get_channel_info(youtube_client, 'test_channel_id')

    # Assertions to validate the expected outcomes
    assert channel_info is not None
    assert channel_info['channel_id'] == 'test_channel_id'
    assert channel_info['name'] == 'Test Channel'
    assert channel_info['customUrl'] == 'testchannel'
    assert channel_info['published_date'] == '2020-01-01T00:00:00Z'
    assert channel_info['thumbnail_url'] == 'http://example.com/thumbnail.jpg'
    assert channel_info['description'] == 'Test Description'
    assert channel_info['country'] == 'Test Country'


def test_get_channel_info_not_found(youtube_client):
    # Mock the API response for a non-existent channel
    youtube_client.channels().list().execute.return_value = {'items': []}

    # Call the function with a mock channel ID that does not exist
    channel_info = get_data.get_channel_info(youtube_client,
                                             'non_existent_channel_id')

    # Assert that the function handles non-existent channels gracefully
    assert channel_info is None
