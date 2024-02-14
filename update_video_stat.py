import src.get_data as get_data
import src.db_connection as db_connection
import pandas as pd
import numpy as np
import logging
logging.basicConfig(level=logging.INFO)


def main():
    youtube = get_data.start_youtube_connection('config/secrets.json')
    db = db_connection.DB_Connection()
    db.conn_string_from_path('config/secrets.json')

    result = db.query('SELECT video_id FROM video where active = True')
    video_ids = [item[0] for item in result]
    results = []
    for id in video_ids:
        result = get_data.get_video_stat(youtube, id)
        if result:
            results.append(result)
    stat_df = pd.DataFrame(results)
    stat_df = stat_df.replace([np.nan], [None])

    stat_df.to_csv('video_stats.csv', index=False)

    insert_stmt = f"""
    INSERT INTO video_log ({','.join(stat_df.columns)})
    VALUES (%s, %s, %s, %s)
    """
    db.insert_df(insert_stmt, stat_df)


if __name__ == '__main__':
    main()
