import logging
import pandas as pd
import isodate
from src.core import YoutubeAPI, DB_Connection, Channel
logging.basicConfig(level=logging.INFO)


def main():
    '''
    This script involve 5 steps to crawl new videos from youtube channels
    1. Query database to retrieve (active) youtube channels to crawl
    2. Use to crawl video id of the most recent 20 video and shorts
    3. Filter videos crawled, so that they do not exist in the database
    4. Use youtube API to crawl video info using id
    5. Add the new info to database.

    Channels in the database have active tags which are which are set as true
    at the start and set as false after they are crawled.
    This is designed to know where to restart if crawler failed.
    '''

    # setup connections (youtube API, db and crawler)
    youtube = YoutubeAPI()
    db = DB_Connection()

    # set all channels as active
    # TODO this is only temporarily used to catch errors
    # Can be deleted alongside all the deactivate calls
    db.update('UPDATE channel SET active=True')

    # get the channel ids from db
    result = db.query('SELECT channel_id FROM channel where active=True')
    channel_ids = [item[0] for item in result]
    total_vids = 0
    for channel_id in channel_ids:
        # use crawler the get video
        new_videos = scrape_video_by_channel_id(channel_id)
        if not new_videos:
            deactive_channel(channel_id, new_tag=False)
            continue

        exisiting_videos = channel_vids(channel_id)
        video_lists = filter_videos(new_videos, exisiting_videos)

        # check if both video and short has no new video
        if all([not item for item in video_lists.values()]):
            deactive_channel(channel_id, new_tag=False)
            continue

        video_data = youtube.multiple_videos_info(video_lists)
        video_df = data_to_df(video_data, channel_id)
        video_df.to_csv(f'{channel_id}_videos.csv', index=False)

        insert_stmt = f"""
        INSERT INTO video ({','.join(video_df.columns)})
        VALUES ({','.join(['%s']*video_df.shape[1])})
        """
        db.insert_df(insert_stmt, video_df)
        total_vids += len(video_df)
        deactive_channel(channel_id, new_tag=True)

    logging.info('New video loading complete.' +
                 f'Total of {total_vids} videos were added.')


def scrape_video_by_channel_id(channel_id: str,
                               count: int | None = None) -> dict[str, list]:
    '''

    Parameters
    ----------

    Returns:
    -------
    '''
    c = Channel(channel_id)
    if not count:
        video_lists = c.get_video_lists()
    else:
        video_lists = c.get_video_lists(count)
    if not video_lists or all([not item for item in video_lists.values()]):
        return None

    return video_lists


def channel_vids(channel_id: str) -> dict[str, list]:
    '''

    Parameters
    ----------

    Returns:
    -------
    '''
    existing_vids = {}
    db = DB_Connection()
    for video_type in ['video', 'short']:
        query_stmt = f"""
            select video_id
            from video
            where channel_id = '{channel_id}' and video_type='{video_type}'
            """
        result = db.query(query_stmt)
        existing_vids[video_type] = [item[0] for item in result]
    return existing_vids


def filter_videos(new_videos: dict, existing_videos: dict):
    '''

    Parameters
    ----------

    Returns:
    -------
    '''
    video_lists = {}
    for key, value in new_videos.items():
        video_lists[key] = []
        for id in value:
            if id not in existing_videos[key]:
                video_lists[key].append(id)
    return video_lists


def update_channel_status(channel_id):
    '''

    Parameters
    ----------

    Returns:
    -------
    '''
    db = DB_Connection()
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
    return


def data_to_df(video_data: list[dict], channel_id: str):
    '''

    Parameters
    ----------

    Returns:
    -------
    '''
    # organize into dataframe
    video_df = pd.DataFrame(video_data)
    video_df['channel_id'] = channel_id
    video_df['published_timestamp'] = pd.to_datetime(video_df['published_date']).dt.tz_convert(tz='Asia/Taipei')  # noqa
    video_df['published_time'] = video_df['published_timestamp'].dt.timetz
    video_df['published_date'] = video_df['published_timestamp'].dt.date
    video_df['duration'] = video_df['duration'].apply(isodate.parse_duration)  # noqa
    video_df.drop('published_timestamp', axis=1, inplace=True)
    video_df.drop_duplicates(subset='video_id', inplace=True)
    return video_df


def deactive_channel(channel_id: str, new_tag: bool) -> None:
    '''

    Parameters
    ----------

    Returns:
    -------
    '''
    db = DB_Connection()
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
            if new_tag:
                logging.info(f'{channel_id} video updated')
            else:
                logging.info(f"{channel_id} has no video to update")
        except Exception as e:
            logging.error(f"An error occurred here: {e}")


if __name__ == '__main__':
    main()
