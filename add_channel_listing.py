import sys
import logging
from src import get_data, db_connection

logging.basicConfig(level=logging.INFO)


def main():

    # crawl channel listing on search page using selenium
    path = sys.argv[1]
    



    # get channel information using youtube API
    youtube = get_data.start_youtube_connection('config/secrets.json')
    result = get_data.get_channel_info(youtube, result[idx][0])

    # adding final result to DB
    db = db_connection.DB_Connection()
    db.conn_string_from_path('config/secrets.json')
    insert_stmt = f"""
    INSERT INTO channel ({','.join(result.keys())})
    VALUES ({", ".join(['%s']*len(result))})
    """
    db.insert_one(insert_stmt, tuple(result.values()))


if __name__ == '__main__':
    main()
