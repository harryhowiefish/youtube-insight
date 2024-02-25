import sys
import os
import logging
import pandas as pd
from src.core import DB_Connection, YoutubeAPI

logging.basicConfig(level=logging.INFO)


def main():
    if len(sys.argv) < 2:
        logging.error('Please provide txt file')
        return
    # check path
    path = sys.argv[1]
    if path[-4:] != '.txt':
        logging.error('Please provide file that ends with .txt')
    if not os.path.exists(os.path.join(os.curdir, path)):
        logging.error(f'File {path} does not exist.')

    # load text to list
    with open(path) as f:
        txt = f.read()
    channels = txt.replace(' ', '').split(',')

    # create connections
    youtube = YoutubeAPI()
    db = DB_Connection()

    # get channel information using youtube API
    channel_info = []
    for channel in channels:
        data = youtube.get_channel_info(channel)
        if data:
            channel_info.append(data)
    if not channel_info:
        logging.warning('No valid channel_id provided')
        return
    channel_df = pd.DataFrame(channel_info)

    # adding final result to DB
    insert_stmt = f"""
    INSERT INTO channel ({','.join(channel_df.columns)})
    VALUES ({", ".join(['%s']*channel_df.shape[1])})
    """
    db.insert_df(insert_stmt, channel_df)


if __name__ == '__main__':
    main()
