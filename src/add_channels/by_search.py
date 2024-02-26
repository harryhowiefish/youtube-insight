import sys
import logging
from src.core import DB_Connection, YoutubeAPI, youtube_requests

logging.basicConfig(level=logging.INFO)


def main():

    # crawl channel listing on search page using selenium
    keyword = sys.argv[1]
    result = youtube_requests.keyword_search(keyword)

    # result can include more than one channel. Loop through to check.
    idx = 0
    while idx < len(result):
        if input(f'Is this channel {result[idx][1]} correct? ' +
                 '1 for Yes, 2 for No: ') == '1':
            print(f'The channel id is {result[idx][0]}')
            break
        idx += 1
    if idx == len(result):
        print('Can not find any/other channel. Try another keyword.')
        return
    # prompting user to decide whether to add this channel to DB.
    if input('Do you want to add data to db? ' +
             '1 for Yes, 2 for No: ') == '2':
        print('No data added.')
        return

    # get channel information using youtube API
    youtube = YoutubeAPI()
    result = youtube.get_channel_info(youtube, result[idx][0])
    # adding final result to DB
    db = DB_Connection()
    db.conn_string_from_path('config/secrets.json')
    insert_stmt = f"""
    INSERT INTO channel ({','.join(result.keys())})
    VALUES ({", ".join(['%s']*len(result))})
    """
    db.insert_one(insert_stmt, tuple(result.values()))


if __name__ == '__main__':
    main()
