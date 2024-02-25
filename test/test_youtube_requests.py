from src import youtube_requests
import pytest


@pytest.fixture
def channel():
    channel_id = 'UCLW_SzI9txZvtOFTPDswxqg'  # 木曜
    c = youtube_requests.Channel(channel_id)
    yield c
    del c


class TestSinglePageVideoListing():
    @staticmethod
    def test_basic_success(channel: youtube_requests.Channel):
        url = f'https://www.youtube.com/channel/{channel.channel_id}/videos'
        result = channel._single_page_video_listing(url, 10)
        assert isinstance(result, list)


class TestGetChannelTabs():
    @staticmethod
    def test_type(channel: youtube_requests.Channel):
        result = channel.get_channel_tabs()
        assert isinstance(result, list)


class TestGetVideoLists():
    @staticmethod
    def test_basic_success(channel: youtube_requests.Channel):
        result = channel.get_video_lists(20)
        assert isinstance(result, dict)
        assert isinstance(result, dict)
        assert len(result) in [0, 1, 2]


class TestKeywordSearch():

    @staticmethod
    def test_type_list():
        result = youtube_requests.keyword_search('Mrbeast')
        assert isinstance(result, list)
