import sys
import logging
from src.core import db_connection, youtube_api, youtube_requests

logging.basicConfig(level=logging.INFO)


def main():

    # crawl channel listing on search page using selenium
    if len(sys.argv) < 2:
        logging.error('Please provide keyword to search for channel...')
        return

    keyword = sys.argv[1]
    result = youtube_requests.keyword_search(keyword)

    # result can include more than one channel. Loop through to check.
    channel_id = user_confirmation(result)
    if channel_id is None:
        return

    # get channel information using youtube API
    youtube = youtube_api.YoutubeAPI()
    result = youtube.get_channel_info(channel_id)

    # adding final result to DB
    db = db_connection.DB_Connection()
    insert_stmt = f"""
    INSERT INTO channel ({','.join(result.keys())})
    VALUES ({", ".join(['%s']*len(result))})
    """
    db.insert_one(insert_stmt, tuple(result.values()))


def user_confirmation(result) -> int | None:
    idx = 0
    while idx < len(result):
        if input(f'Is this channel {result[idx][1]} correct? ' +
                 '1 for Yes, 2 for No: ') == '1':
            logging.info(f'The channel id is {result[idx][0]}')
            break
        idx += 1
        if idx == len(result):
            logging.info(
                'Can not find any/other channel. Try another keyword.')
            return None
    # prompting user to decide whether to add this channel to DB.
    if input('Do you want to add data to db? ' +
             '1 for Yes, 2 for No: ') == '2':
        logging.info('No data added.')
        return None
    return result[idx][0]


if __name__ == '__main__':
    main()
