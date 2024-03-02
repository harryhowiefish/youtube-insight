from src.airflow_scripts import crawl_new_videos
import pandas as pd
import datetime
import pytz
import pytest
import logging
import os


class Mock_DB:
    def __init__(self) -> None:
        pass

    def query(self, stmt):
        return [['id1'], ['id2']]

    def insert_df(self, stmt, df):
        logging.info(f'Insert transaction complete. inserted {len(df)} rows.')

    def update(self, stmt, data=None):
        logging.info('Number of row updated: some_number')


class Mock_Youtube:
    def __init__(self) -> None:
        pass

    def multiple_channels_stat(self, ids: list):
        return [{'view_count': 111,
                 'video_count': 2,
                 'sub_count': 5}]

    def multiple_videos_info(self, video_lists):
        return [{'video_type': 'video',
                'video_id': '1YD30z7yXG4',
                 'title': 'How to Draw a River in the Forest',
                 'published_date': '2024-02-20T15:00:01Z',
                 'description': "Jay Lee is a painting youtuber.",
                 'thumbnail_url': 'hqdefault.jpg',
                 'duration': 'PT11M6S',
                 'categoryId': '27'}]


class Mock_Channel():
    def __init__(self, channel_id) -> None:
        self.channel_id: str = channel_id

    def get_video_lists(self, limit=None):
        videos_data = ['video1', 'video2', 'video3'][:limit]
        shorts_data = ['short1', 'short2', 'short3'][:limit]
        return {'video': videos_data, 'short': shorts_data}


@pytest.fixture(autouse=True)
def replace_modules(monkeypatch):
    monkeypatch.setattr('src.core.youtube_api.YoutubeAPI',
                        lambda: Mock_Youtube())
    monkeypatch.setattr(
        'src.core.db_connection.DB_Connection', lambda: Mock_DB())
    monkeypatch.setattr('src.core.youtube_requests.Channel',
                        lambda channel_id: Mock_Channel(channel_id))


class TestScrapeVideoByChannelId:
    @staticmethod
    def test_no_count():
        result = crawl_new_videos.scrape_video_by_channel_id(
            channel_id='channel_id')
        expected = {'video': ['video1', 'video2', 'video3'],
                    'short': ['short1', 'short2', 'short3']}
        assert result == expected

    @staticmethod
    def test_with_count():
        result = crawl_new_videos.scrape_video_by_channel_id(
            channel_id='channel_id', count=2)
        expected = {'video': ['video1', 'video2'],
                    'short': ['short1', 'short2']}
        assert result == expected

    @staticmethod
    def test_get_empty_dict(monkeypatch):
        monkeypatch.setattr(Mock_Channel, 'get_video_lists', lambda _: {})
        result = crawl_new_videos.scrape_video_by_channel_id(
            channel_id='channel_id')
        assert result is None

    @staticmethod
    def test_get_dict_with_empty_item(monkeypatch):
        monkeypatch.setattr(Mock_Channel, 'get_video_lists',
                            lambda _: {'video': [], 'short': []})
        result = crawl_new_videos.scrape_video_by_channel_id(
            channel_id='channel_id')
        assert result is None


class TestChannelVids:

    @staticmethod
    def test_success():
        result = crawl_new_videos.channel_vids('channel_id')
        expected = {'video': ['id1', 'id2'],
                    'short': ['id1', 'id2']}
        assert result == expected


class TestFilterVideos:
    @staticmethod
    def test_no_existing():
        new_videos = {'video': ['id1', 'id2'],
                      'short': ['id1', 'id2']}
        existing_videos = {'video': [], 'short': []}
        result = crawl_new_videos.filter_videos(new_videos, existing_videos)
        assert result == new_videos

    @staticmethod
    def test_all_existing():
        new_videos = {'video': ['id1', 'id2'],
                      'short': ['id1', 'id2']}
        existing_videos = {'video': ['id1', 'id2'],
                           'short': ['id1', 'id2']}
        result = crawl_new_videos.filter_videos(new_videos, existing_videos)
        assert result == {'video': [], 'short': []}


class TestDataToDf:

    @staticmethod
    def test_good_data():
        data = {'video_type': 'video',
                'video_id': '1YD30z7yXG4',
                'title': 'How to Draw a River in the Forest',
                'published_date': '2024-02-20T15:00:01Z',
                'description': "Jay Lee is a painting youtuber.",
                'thumbnail_url': 'hqdefault.jpg',
                'duration': 'PT11M6S',
                'categoryId': '27'}
        channel_id = 'UCHm9SiOLG8UoBT8STWY5mVA'
        result = crawl_new_videos.data_to_df([data], channel_id)
        tz = pytz.timezone('Asia/Taipei')
        timestamp = datetime.datetime(
            2024, 2, 20, 23, 0, 1, tzinfo=tz)
        time = timestamp.time()
        date = timestamp.date()
        expected = pd.DataFrame(
            {
                'video_id': [data['video_id']],
                'video_type': [data['video_type']],
                'title': [data['title']],
                'published_date': [date],
                'description': [data['description']],
                'thumbnail_url': [data['thumbnail_url']],
                'duration': [datetime.timedelta(seconds=666)],
                'categoryId': [data['categoryId']],
                'channel_id': [channel_id],
                'published_timestamp': [timestamp],
                'published_time': [time],
            }
        )
        assert result['channel_id'].equals(expected['channel_id'])

    @staticmethod
    def test_duplicated_data():
        data = {'video_type': 'video',
                'video_id': '1YD30z7yXG4',
                'title': 'How to Draw a River in the Forest',
                'published_date': '2024-02-20T15:00:01Z',
                'description': "Jay Lee is a painting youtuber.",
                'thumbnail_url': 'hqdefault.jpg',
                'duration': 'PT11M6S',
                'categoryId': '27'}
        channel_id = 'UCHm9SiOLG8UoBT8STWY5mVA'
        result = crawl_new_videos.data_to_df([data, data], channel_id)
        tz = pytz.timezone('Asia/Taipei')
        timestamp = datetime.datetime(
            2024, 2, 20, 23, 0, 1, tzinfo=tz)
        time = timestamp.time()
        date = timestamp.date()
        expected = pd.DataFrame(
            {
                'video_id': [data['video_id']],
                'video_type': [data['video_type']],
                'title': [data['title']],
                'published_date': [date],
                'description': [data['description']],
                'thumbnail_url': [data['thumbnail_url']],
                'duration': [datetime.timedelta(seconds=666)],
                'categoryId': [data['categoryId']],
                'channel_id': [channel_id],
                'published_timestamp': [timestamp],
                'published_time': [time],
            }
        )
        assert result['channel_id'].equals(expected['channel_id'])


class TestDeactiveChannel:
    @staticmethod
    def test_new_tag_true(caplog):
        caplog.clear()
        caplog.set_level(level='INFO')
        crawl_new_videos.deactive_channel('channel_id', new_tag=True)
        assert len(caplog.records) == 2
        assert 'Number of row updated: some_number' == caplog.records[0].msg
        assert 'channel_id video updated' == caplog.records[1].msg

    @staticmethod
    def test_new_tag_false(caplog):
        caplog.clear()
        caplog.set_level(level='INFO')
        crawl_new_videos.deactive_channel('channel_id', new_tag=False)
        assert len(caplog.records) == 2
        assert 'Number of row updated: some_number' == caplog.records[0].msg
        assert 'channel_id has no video to update' == caplog.records[1].msg


def test_main(monkeypatch, tmp_path, caplog):
    caplog.clear()
    caplog.set_level(level='INFO')
    monkeypatch.chdir(tmp_path)
    crawl_new_videos.main()
    assert os.path.exists(tmp_path / 'id1_videos.csv')
    assert os.path.exists(tmp_path / 'id2_videos.csv')
    expected_log = 'New video loading complete.' + \
        'Total of 2 videos were added.'
    assert expected_log == caplog.records[-1].msg
