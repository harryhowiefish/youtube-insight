from airflow_scripts import crawl_new_videos
import pandas as pd
import datetime
import pytz


class TestDataToDf():

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
                'video_type': [data['video_type']],
                'video_id': [data['video_id']],
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
