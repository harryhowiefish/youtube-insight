import pytest
from src.core import youtube_api
import json
import os
# Sample data to mock the API response
with open('test/test_data/channel_sample.json') as f:
    mock_channel_response = json.load(f)
with open('test/test_data/video_sample.json') as f:
    mock_video_response = json.load(f)


class Mock_API:
    def __init__(self, s, v, developerKey) -> None:
        self.api_service_name = s
        self.api_version = v
        self.developerKey = developerKey
        pass

    def channels(self):
        return self.item('channel')

    def videos(self):
        return self.item('video')

    class item():
        def __init__(self, type) -> None:
            self.type = type

        def list(self, part, id):
            return Mock_request(self.type)


class Mock_request:
    def __init__(self, type) -> None:
        self.type = type

    def execute(self):
        pass

    def execute_success(self):
        if self.type == 'channel':
            return mock_channel_response
        if self.type == 'video':
            return mock_video_response

    def execute_missing_data(self):
        if self.type == 'channel':
            return {}
        if self.type == 'video':
            return {"items": []}


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    mock_path = 'test/test_data'
    monkeypatch.setattr('os.getcwd', lambda: mock_path)
    monkeypatch.setattr('googleapiclient.discovery.build',
                        lambda s, v, developerKey: Mock_API(
                            s, v, developerKey))


@pytest.fixture
def yt():
    yt = youtube_api.YoutubeAPI()
    yield yt
    del yt


def test_start(yt):
    assert isinstance(yt, youtube_api.YoutubeAPI)


class TestGetChannelInfo():

    @staticmethod
    def test_get_channel_info_success(yt, monkeypatch):
        # Mock the channels().list().execute() method chain
        monkeypatch.setattr(Mock_request, "execute",
                            Mock_request.execute_success)
        # Call the function with a mock channel ID
        channel_info = yt.get_channel_info(
            'UCdEpz2A4DzV__4C1x2quKLw')

        # # Assertions to validate the expected outcomes
        assert channel_info is not None
        assert channel_info['channel_id'] == 'UCdEpz2A4DzV__4C1x2quKLw'
        assert channel_info['name'] == 'PAPAYA 電腦教室'
        assert channel_info['customUrl'] == '@papayaclass'
        assert channel_info['published_date'] == '2008-11-09T03:54:16Z'
        assert channel_info['thumbnail_url'] == 'https://yt3.ggpht.com/ytc/AIdro_m3nf14bpEjVkXq0hNJOp2UrcdcjnfeU97VktoAxg=s800-c-k-c0x00ffffff-no-rj'  # noqa
        assert channel_info['description'] == "PAPAYA 希望以最淺白易懂的方式，讓大家能夠輕鬆上手常用的電腦軟體。"  # noqa
        assert channel_info['country'] == 'TW'

    @staticmethod
    def test_get_channel_info_bad_id(yt, monkeypatch):
        # Mock the API response for a non-existent channel
        monkeypatch.setattr(Mock_request, "execute",
                            Mock_request.execute_missing_data)

        # Call the function with a mock channel ID that does not exist
        channel_info = yt.get_channel_info('bad_id')

        # Assert that the function handles non-existent channels gracefully
        assert channel_info is None


class TestSingleAndMultiChannelStat():
    @staticmethod
    def test_single_channel_stat_success(yt, monkeypatch):
        monkeypatch.setattr(Mock_request, "execute",
                            Mock_request.execute_success)
        channel_stat = yt.get_channel_stat('UCdEpz2A4DzV__4C1x2quKLw')
        assert channel_stat is not None
        assert isinstance(channel_stat, dict)
        assert channel_stat['channel_id'] == "UCdEpz2A4DzV__4C1x2quKLw"
        assert channel_stat['view_count'] == "115815042"
        assert channel_stat['sub_count'] == "1420000"
        assert channel_stat['video_count'] == "494"

    @staticmethod
    def test_single_channel_stat_missing(yt, monkeypatch):
        monkeypatch.setattr(Mock_request, "execute",
                            Mock_request.execute_missing_data)
        channel_stat = yt.get_channel_stat('bad_id')
        assert channel_stat is None

    @staticmethod
    def test_multi_channel_stat_success(yt, monkeypatch):
        monkeypatch.setattr(Mock_request, "execute",
                            Mock_request.execute_success)
        channel_list = ['channel1', 'channel2']
        result = yt.multiple_channels_stat(channel_list)
        assert isinstance(result, list)
        assert isinstance(result[0], dict)
        assert len(result) == len(channel_list)
        assert result[0] == yt.get_channel_stat(channel_list[0])

    @staticmethod
    def test_multi_channel_stat_fail(yt, monkeypatch):
        monkeypatch.setattr(Mock_request, "execute",
                            Mock_request.execute_missing_data)
        channel_list = ['channel1', 'channel2']
        result = yt.multiple_channels_stat(channel_list)
        assert isinstance(result, list)
        assert result == []


class TestSingleAndMultiVideoInfo():
    @staticmethod
    def test_single_video_info_success(yt, monkeypatch):
        monkeypatch.setattr(Mock_request, "execute",
                            Mock_request.execute_success)
        video_id = 'liOtZ0vldBU'
        video_info = yt.get_video_info(video_id)
        assert video_info is not None

    @staticmethod
    def test_single_video_info_fail(yt, monkeypatch):
        monkeypatch.setattr(Mock_request, "execute",
                            Mock_request.execute_missing_data)
        video_id = 'liOtZ0vldBU'
        video_info = yt.get_video_info(video_id)
        assert video_info is None

    @staticmethod
    def test_multi_video_info_success(yt, monkeypatch):
        monkeypatch.setattr(Mock_request, "execute",
                            Mock_request.execute_success)
        video_lists = {'video': ['video1', 'video2'],
                       'short': ['short1', 'short2']}
        video_info = yt.multiple_videos_info(video_lists)
        assert isinstance(video_info, list)

    @staticmethod
    def test_multi_video_info_fail(yt, monkeypatch):
        monkeypatch.setattr(Mock_request, "execute",
                            Mock_request.execute_missing_data)
        video_lists = {'video': ['video1', 'video2'],
                       'short': ['short1', 'short2']}
        video_info = yt.multiple_videos_info(video_lists)
        assert isinstance(video_info, list)
        assert video_info == []


class TestSingleAndMultiVideoStat():

    @staticmethod
    def test_single_video_stat_success(yt, monkeypatch):
        monkeypatch.setattr(Mock_request, "execute",
                            Mock_request.execute_success)
        video_id = 'liOtZ0vldBU'
        video_info = yt.get_video_stat(video_id)
        assert video_info is not None

    @staticmethod
    def test_single_video_stat_fail(yt, monkeypatch):
        monkeypatch.setattr(Mock_request, "execute",
                            Mock_request.execute_missing_data)
        video_id = 'liOtZ0vldBU'
        video_info = yt.get_video_stat(video_id)
        assert video_info is None

    @staticmethod
    def test_multi_video_stat_success(yt, monkeypatch):
        monkeypatch.setattr(Mock_request, "execute",
                            Mock_request.execute_success)
        video_lists = {'video': ['video1', 'video2'],
                       'short': ['short1', 'short2']}
        video_info = yt.multiple_videos_stat(video_lists)
        assert isinstance(video_info, list)

    @staticmethod
    def test_multi_video_stat_fail(yt, monkeypatch):
        monkeypatch.setattr(Mock_request, "execute",
                            Mock_request.execute_missing_data)
        video_lists = {'video': ['video1', 'video2'],
                       'short': ['short1', 'short2']}
        video_info = yt.multiple_videos_stat(video_lists)
        assert isinstance(video_info, list)
        assert video_info == []


def test_api_key_from_env(yt, monkeypatch):
    result = yt._api_key_from_env()
    assert isinstance(result, Mock_API)
    assert result.api_service_name == 'youtube'
    assert result.api_version == 'v3'
    assert result.developerKey == os.environ['YOUTUBE_API']
