import sys
import logging
import pandas as pd
from src.core import DB_Connection, YoutubeAPI

logging.basicConfig(level=logging.INFO)


def main():

    # crawl channel listing on search page using selenium
    path = sys.argv[1]
    with open(path) as f:
        txt = f.read()
    channels = txt.replace(' ', '').split(',')
    youtube = YoutubeAPI()
    db = DB_Connection()

    # get channel information using youtube API
    channel_info = []
    for channel in channels:
        channel_info.append(youtube.get_channel_info(channel))
    channel_df = pd.DataFrame(channel_info)

    # adding final result to DB
    insert_stmt = f"""
    INSERT INTO channel ({','.join(channel_df.columns)})
    VALUES ({", ".join(['%s']*channel_df.shape[1])})
    """
    db.insert_df(insert_stmt, channel_df)


if __name__ == '__main__':
    main()
