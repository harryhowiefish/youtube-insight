import logging
import pandas as pd
import isodate
from src import get_data, db_connection, youtube_crawler
logging.basicConfig(level=logging.INFO)


def main():
    youtube = get_data.start_youtube_connection('config/secrets.json')
    db = db_connection.DB_Connection()
    db.conn_string_from_path('config/secrets.json')
    crawler = youtube_crawler.Crawler()
    result = db.query('SELECT channel_id FROM channel where active=True')
    channel_ids = [item[0] for item in result]

    for channel_id in channel_ids:
        v_ids = crawler.get_video_lists(channel_id)
        video_data = []
        for video_type, video_ids in v_ids.items():
            if not video_ids:  # if there's no video crawled
                continue
            for video_id in video_ids:
                single_video = {'video_type': video_type}
                single_video.update(get_data.get_video_info(youtube, video_id))
                video_data.append(single_video)
        if not video_data:  # if there's no video crawled
            continue
        video_df = pd.DataFrame(video_data)
        video_df['channel_id'] = channel_id
        video_df['published_date'] = pd.to_datetime(video_df['published_date']).dt.tz_convert(tz='Asia/Shanghai')  # noqa
        video_df['published_time'] = video_df['published_date'].dt.timetz
        video_df['published_date'] = video_df['published_date'].dt.date
        video_df['duration'] = video_df['duration'].apply(isodate.parse_duration)  # noqa
        insert_stmt = f"""
        INSERT INTO video ({','.join(video_df.columns)})
        VALUES ({','.join(['%s']*video_df.shape[1])})
        """
        db.insert_df(insert_stmt, video_df)


if __name__ == '__main__':
    main()
