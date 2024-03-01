from src.core import youtube_requests
import pytest
import json


@pytest.fixture()
def channel():
    channel_id = 'UCLW_SzI9txZvtOFTPDswxqg'  # 木曜
    c = youtube_requests.Channel(channel_id)
    yield c
    del c


@pytest.fixture(autouse=True)
def mocking_request(monkeypatch):
    monkeypatch.setattr("requests.get", lambda url, headers: Mock_resp())
    monkeypatch.setattr("requests.post", lambda url,
                        headers, data: Mock_resp())


class Mock_resp():

    @property
    def text(self):
        return "FILLER TEXT"


class TestInit():

    @staticmethod
    def test_init(channel):
        assert isinstance(channel, youtube_requests.Channel)

    @staticmethod
    def test_missing_id_fail():
        with pytest.raises(TypeError):
            youtube_requests.Channel()


class TestGetChannelTabs():

    @staticmethod
    def test_channel_tabs(channel: youtube_requests.Channel, monkeypatch):
        sample = '''
                {"tabRenderer":{"endpoint":{"":{"":{}},"":{}},"title":"Home"}},
                {"tabRenderer":{"endpoint":{"":{"":{}},"":{}},"title":"Videos"}},
                "INNERTUBE_API_KEY":"FAKE_KEY",
                 '''
        monkeypatch.setattr(Mock_resp, 'text', sample)
        result = channel.get_channel_tabs()
        assert result == ['Home', 'Videos']
        assert channel.yt_api_key == "FAKE_KEY"

    @staticmethod
    def test_property_tabs(channel: youtube_requests.Channel, monkeypatch):
        sample = '''
                {"tabRenderer":{"endpoint":{"":{"":{}},"":{}},"title":"Home"}},
                {"tabRenderer":{"endpoint":{"":{"":{}},"":{}},"title":"Videos"}},
                "INNERTUBE_API_KEY":"FAKE_KEY",
                 '''
        monkeypatch.setattr(Mock_resp, 'text', sample)
        assert channel.tabs == ['Home', 'Videos']
        assert channel.yt_api_key == "FAKE_KEY"


class TestSinglePageVideoListing():

    @staticmethod
    def test_missing_all_data(channel: youtube_requests.Channel,
                              monkeypatch: pytest.MonkeyPatch,
                              caplog):
        sample = ''
        monkeypatch.setattr(Mock_resp, 'text', sample)
        result = channel._single_page_video_listing('url', limit=1)
        assert result == []
        assert 'Missing continuation in url' in caplog.text

    @staticmethod
    def test_optional_limit(channel: youtube_requests.Channel,
                            monkeypatch: pytest.MonkeyPatch):
        sample = '''
        "Endpoint":{"videoId":"id1",
        "Endpoint":{"videoId":"id2",
        "Endpoint":{"videoId":"id3",
        "continuationCommand":{"token":"next_token",
        '''
        monkeypatch.setattr(Mock_resp, 'text', sample)
        result = channel._single_page_video_listing('url', limit=1)
        assert result == ['id1']
        result = channel._single_page_video_listing('url', limit=3)
        assert result == ['id1', 'id2', 'id3']

    @staticmethod
    def test_multi_page_infinite_loop(channel: youtube_requests.Channel,
                                      monkeypatch: pytest.MonkeyPatch):
        sample = '''
        "Endpoint":{"videoId":"id1",
        "Endpoint":{"videoId":"id2",
        "continuationCommand":{"token":"next_token",
        '''
        monkeypatch.setattr(Mock_resp, 'text', sample)
        monkeypatch.setattr(youtube_requests.Channel,
                            '_continous_video_listing',
                            lambda self, token: (['next_page_id3'],
                                                 'next_token'))
        result = channel._single_page_video_listing('url', 4)
        assert result == ['id1', 'id2', 'next_page_id3', 'next_page_id3']
        result = channel._single_page_video_listing('url', 5)
        assert result == ['id1', 'id2',
                          'next_page_id3', 'next_page_id3', 'next_page_id3']

    @staticmethod
    def test_multi_page_no_next_token(channel: youtube_requests.Channel,
                                      monkeypatch: pytest.MonkeyPatch):
        sample = '''
        "Endpoint":{"videoId":"id1",
        "Endpoint":{"videoId":"id2",
        "continuationCommand":{"token":"next_token",
        '''
        monkeypatch.setattr(Mock_resp, 'text', sample)
        monkeypatch.setattr(youtube_requests.Channel,
                            '_continous_video_listing',
                            lambda self, token: (['next_page_id3'],
                                                 ''))
        result = channel._single_page_video_listing('url')
        assert result == ['id1', 'id2', 'next_page_id3']

    @staticmethod
    def test_multi_page_no_more_video(channel: youtube_requests.Channel,
                                      monkeypatch: pytest.MonkeyPatch):
        sample = '''
        "Endpoint":{"videoId":"id1",
        "Endpoint":{"videoId":"id2",
        "continuationCommand":{"token":"next_token",
        '''
        monkeypatch.setattr(Mock_resp, 'text', sample)
        monkeypatch.setattr(youtube_requests.Channel,
                            '_continous_video_listing',
                            lambda self, token: ([],
                                                 'next_token'))
        result = channel._single_page_video_listing('url')
        assert result == ['id1', 'id2']


class Testhelperfunctions():

    @staticmethod
    def test_continous_listing_no_next_token(channel: youtube_requests.Channel,
                                             monkeypatch):
        sample = '''
        "videoRenderer":{"videoId":"video1",
        "videoRenderer":{"videoId":"video2",
        '''
        monkeypatch.setattr(Mock_resp, 'text', sample)
        video_ids, next_token = channel._continous_video_listing(
            'sample_token')
        assert video_ids == ['video1', 'video2']
        assert next_token == ''

    @staticmethod
    def test_continous_listing_with_token(channel: youtube_requests.Channel,
                                          monkeypatch):
        sample = '''
        "videoRenderer":{"videoId":"video1",
        "videoRenderer":{"videoId":"video2",
        "continuationCommand":{"token":"next_token",
        '''
        monkeypatch.setattr(Mock_resp, 'text', sample)
        video_ids, next_token = channel._continous_video_listing(
            'sample_token')
        assert video_ids == ['video1', 'video2']
        assert next_token == 'next_token'

    @staticmethod
    def test_continous_listing_empty_page(channel: youtube_requests.Channel,
                                          monkeypatch):
        sample = ''
        monkeypatch.setattr(Mock_resp, 'text', sample)
        video_ids, next_token = channel._continous_video_listing(
            'sample_token')
        assert video_ids == []
        assert next_token == ''

    @staticmethod
    def test_create_innertube_post_data(channel: youtube_requests.Channel):
        expected_url = "https://www.youtube.com/youtubei/v1/browse?key=None"
        expected_header = {
            "X-YouTube-Client-Name": "1",
            "X-YouTube-Client-Version": "2.20200720.00.02",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            "accept-language": "en-US,en"
        }
        expected_data = json.dumps({
            "continuation": 'sample_token',
            "context": {"client": {
                            "clientName": "WEB",
                            "clientVersion": "2.20200720.00.02"}
                        }})
        url, header, data = channel._create_innertube_post_data('sample_token')
        assert url == expected_url
        assert header == expected_header
        assert data == expected_data

    @staticmethod
    def test_raw_html(channel: youtube_requests.Channel, monkeypatch):
        sample = '''
                html_sample
                 '''
        monkeypatch.setattr(Mock_resp, 'text', sample)
        result = channel._raw_html('url')
        assert result == sample


class TestGetVideoLists():
    @staticmethod
    def test_only_video_tab(channel, monkeypatch):
        monkeypatch.setattr(youtube_requests.Channel,
                            'tabs', ['Videos'])
        monkeypatch.setattr(youtube_requests.Channel,
                            '_single_page_video_listing',
                            lambda self, url, limit: ['id1', 'id2'][:limit])
        result = channel.get_video_lists()
        assert isinstance(result, dict)
        assert result == {'video': ['id1', 'id2']}

    @staticmethod
    def test_all_tabs_with_limit(channel, monkeypatch):
        monkeypatch.setattr(youtube_requests.Channel,
                            'tabs', ['Videos', 'Shorts'])
        monkeypatch.setattr(youtube_requests.Channel,
                            '_single_page_video_listing',
                            lambda self, url, limit: ['id1', 'id2'][:limit])
        result = channel.get_video_lists(limit=1)
        assert isinstance(result, dict)
        assert result == {'video': ['id1'], 'short': ['id1']}
        result = channel.get_video_lists(limit=2)
        assert result == {'video': ['id1', 'id2'],
                          'short': ['id1', 'id2']}


class TestKeywordSearch():

    @staticmethod
    def test_type_list(monkeypatch):
        sample = '"channelId":"sample_id","title":{"simpleText":"sample_name"}'
        monkeypatch.setattr(Mock_resp, 'text', sample)
        result = youtube_requests.keyword_search('Mrbeast')
        assert isinstance(result, list)
        assert len(result) == 1
        assert result == [('sample_id', 'sample_name')]
