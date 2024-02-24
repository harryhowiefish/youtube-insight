import logging
import pandas as pd
import isodate
from src import db_connection, youtube_api, youtube_requests
from googleapiclient.discovery import Resource as yt_resource
logging.basicConfig(level=logging.INFO)


def id_to_data(youtube: yt_resource, video_lists: dict) -> list[dict]:
    video_data = []

    # loop through crawled data to call youtube API
    for video_type, video_ids in video_lists.items():
        if not video_ids:  # if there's no video crawled
            continue
        for video_id in video_ids:
            single_video = {'video_type': video_type}
            single_video.update(youtube_api.get_video_info(youtube, video_id))
            video_data.append(single_video)
    return video_data


def data_to_df(video_data: list[dict], channel_id: str):
    # organize into dataframe
    video_df = pd.DataFrame(video_data)
    video_df['channel_id'] = channel_id
    video_df['published_timestamp'] = pd.to_datetime(video_df['published_date']).dt.tz_convert(tz='Asia/Taipei')  # noqa
    video_df['published_time'] = video_df['published_timestamp'].dt.timetz
    video_df['published_date'] = video_df['published_timestamp'].dt.date
    video_df['duration'] = video_df['duration'].apply(isodate.parse_duration)  # noqa
    return video_df


def main():
    '''
    This script involve 5 steps to crawl new videos from youtube channels
    1. Query database to retrieve (active) youtube channels to crawl
    2. Use selenium to crawl video id of the most recent ~20 video and shorts
    3. Use youtube API to crawl video info using id
    4. Filter videos crawled, so that they are newer than the 5 most recent
       videos datapoint in database
    5. Add the filtered list to database.

    Channels in the database have active tags which are which are set as true
    at the start and set as false after they are crawled.
    This is designed to know where to restart if crawler failed.
    '''

    # setup connections (youtube API, db and crawler)
    youtube = youtube_api.start_youtube_connection('config/secrets.json')
    db = db_connection.DB_Connection()
    db.conn_string_from_path('config/secrets.json')
    crawler = youtube_requests.Crawler()

    # set all channels as active
    # (Future work: this should be moved to a separate task in DAG)
    db.update('UPDATE channel SET active=True')

    # get the channel ids from db
    result = db.query('SELECT channel_id FROM channel where active=True')
    channel_ids = [item[0] for item in result]

    for channel_id in channel_ids:
        # use crawler the get video
        video_lists = crawler.get_video_lists(channel_id)
        if not video_lists:
            logging.info(f'{channel_id} has no video to updated.')
            continue
        video_data = id_to_data(video_lists, youtube)
        video_df = data_to_df(video_data, channel_id)

        new_df_list = []
        for video_type in ['video', 'short']:
            query_stmt = f"""
            select video_id
            from video
            where channel_id = '{channel_id}' and video_type='{video_type}'
            order by published_date + published_time desc
            limit 5
            """
            result = db.query(query_stmt)
            existing_v_ids = [item[0] for item in result]
            while existing_v_ids:
                if existing_v_ids[0] in video_df.index:
                    break
                existing_v_ids.pop(0)
            if existing_v_ids:
                new_df_list.append(
                    video_df[(video_df['published_timestamp'] >
                              video_df.at[existing_v_ids[0], 'published_timestamp']) &  # noqa
                             (video_df['video_type'] == video_type)])
            else:
                new_df_list.append(video_df[video_df['video_type'] == video_type])  # noqa
        new_vids_df = pd.concat(new_df_list)

        new_vids_df = new_vids_df.reset_index().drop('published_timestamp',
                                                     axis=1)
        new_vids_df.drop_duplicates(subset='video_id', inplace=True)

        insert_stmt = f"""
        INSERT INTO video ({','.join(new_vids_df.columns)})
        VALUES ({','.join(['%s']*new_vids_df.shape[1])})
        """
        db.insert_df(insert_stmt, new_vids_df)

        update_stmt = """
        update channel
        set active = false
        where channel_id = %s
        """
        with db._start_cursor() as cur:
            try:
                # Execute the INSERT statement for each row in the DataFrame
                cur.execute(update_stmt, (channel_id,))
                # Commit the transaction
                logging.info(f'{channel_id} video updated')
            except Exception as e:
                logging.error(f"An error occurred here: {e}")


if __name__ == '__main__':
    main()
