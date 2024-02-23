from src.youtube_requests import Crawler


class TestSinglePageVideoListing():

    @staticmethod
    def test_basic_success():
        url = 'https://www.youtube.com/@MrBeast/video'
        result = Crawler().get_channel_tabs(url)
        assert isinstance(result, list)


class TestKeywordSearch():

    @staticmethod
    def test_type_list():
        result = Crawler().keyword_search('Mrbeast')
        assert isinstance(result, list)


class TestGetChannelTabs():
    @staticmethod
    def test_type():
        channel_id = 'UCLW_SzI9txZvtOFTPDswxqg'  # 木曜
        result = Crawler().get_channel_tabs(channel_id)
        assert isinstance(result, list)


class TestGetVideoLists():

    @staticmethod
    def test_type_list():
        result = Crawler().get_video_lists(
            'UCvw1LiGdyulhnGksJlGWB6g')
        assert isinstance(result, dict)
        assert len(result) in [0, 1, 2]
