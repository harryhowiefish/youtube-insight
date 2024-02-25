from src.core import YoutubeAPI, DB_Connection
import pandas as pd
import logging
logging.basicConfig(level=logging.INFO)


def main():
    '''
    This scripts uses youtube API to query the latest stats
    for the channels with active status in database.
    '''
    # setup connections

    db = DB_Connection()
    youtube = YoutubeAPI()

    # get channel_ids
    result = db.query('SELECT channel_id FROM channel')
    channel_ids = [item[0] for item in result]

    # youtube API call
    results = youtube.multiple_channels_stat(channel_ids)

    # format it to dataframe
    stat_df = pd.DataFrame(results)
    print(stat_df.columns)
    stat_df = stat_df.astype({'view_count': 'int', 'video_count': 'int',
                              'sub_count': 'int'})
    stat_df.to_csv('channel_stats.csv', index=False)

    # SQL INSERT
    # TODO: check if this might cause SQL injection.
    insert_stmt = f"""
    INSERT INTO channel_log ({','.join(stat_df.columns)})
    VALUES (%s, %s, %s, %s)
    """
    db.insert_df(insert_stmt, stat_df)


if __name__ == '__main__':
    main()
