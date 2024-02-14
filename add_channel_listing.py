import sys
import logging
import pandas as pd
from src import get_data, db_connection

logging.basicConfig(level=logging.INFO)


def main():

    # crawl channel listing on search page using selenium
    path = sys.argv[1]
    with open(path) as f:
        txt = f.read()
    channels = txt.replace(' ', '').split(',')
    youtube = get_data.start_youtube_connection('config/secrets.json')
    db = db_connection.DB_Connection()
    db.conn_string_from_path('config/secrets.json')

    # get channel information using youtube API
    channel_info = []
    for channel in channels:
        channel_info.append(get_data.get_channel_info(youtube, channel))
    channel_df = pd.DataFrame(channel_info)

    # adding final result to DB
    insert_stmt = f"""
    INSERT INTO channel ({','.join(channel_df.columns)})
    VALUES ({", ".join(['%s']*channel_df.shape[1])})
    """
    db.insert_df(insert_stmt, channel_df)


if __name__ == '__main__':
    main()
