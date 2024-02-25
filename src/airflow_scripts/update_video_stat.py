from src.core import YoutubeAPI, DB_Connection
import pandas as pd
import numpy as np
import logging
logging.basicConfig(level=logging.INFO)


def main():
    '''
    This script queries active video from the database
    and get status on the videos via youtube API.
    '''

    # setup
    youtube = YoutubeAPI()
    db = DB_Connection()

    # query list of video to call API.
    result = db.query('SELECT video_id FROM video where active = True')
    video_ids = [item[0] for item in result]

    # youtube API call

    results = youtube.multiple_videos_stat(video_ids)

    # create dataframe and save
    stat_df = pd.DataFrame(results)
    stat_df = stat_df.replace([np.nan], [None])
    stat_df.to_csv('video_stats.csv', index=False)

    # insert all video stat into database
    insert_stmt = f"""
    INSERT INTO video_log ({','.join(stat_df.columns)})
    VALUES (%s, %s, %s, %s)
    """
    db.insert_df(insert_stmt, stat_df)


if __name__ == '__main__':
    main()
