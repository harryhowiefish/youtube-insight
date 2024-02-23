import src.get_data as get_data
import src.db_connection as db_connection
import pandas as pd
import logging
logging.basicConfig(level=logging.INFO)


def main():
    '''
    This scripts uses youtube API to query the latest stats
    for the channels with active status in database.
    '''
    youtube = get_data.start_youtube_connection('config/secrets.json')
    db = db_connection.DB_Connection()
    db.conn_string_from_path('config/secrets.json')
    result = db.query('SELECT channel_id FROM channel WHERE active=True')
    channel_ids = [item[0] for item in result]
    results = []
    for id in channel_ids:
        result = get_data.get_channel_stat(youtube, id)
        if result:
            results.append(result)
    stat_df = pd.DataFrame(results)
    stat_df = stat_df.astype({'view_count': 'int', 'video_count': 'int',
                              'sub_count': 'int'})
    stat_df.to_csv('channel_stats.csv', index=False)

    insert_stmt = f"""
    INSERT INTO channel_log ({','.join(stat_df.columns)})
    VALUES (%s, %s, %s, %s)
    """
    db.insert_df(insert_stmt, stat_df)


if __name__ == '__main__':
    main()
