from selenium import webdriver
import re
from selenium.webdriver.chrome.options import Options
import sys
import src.get_data as get_data
import src.db_connection as db_connection
import logging
logging.basicConfig(level=logging.INFO)


def main():
    keyword = sys.argv[1]
    options = Options()
    options.add_argument('--headless=new')
    driver = webdriver.Chrome(options=options)
    driver.get(f'https://www.youtube.com/results?search_query={keyword}')
    result = re.findall('"channelId":"(.*?)","title":{"simpleText":"(.*?)"}',
                        driver.page_source)
    idx = 0
    while idx < len(result):
        if input(f'Is this channel {result[idx][1]} correct? ' +
                 '1 for Yes, 2 for No: ') == '1':
            break
        idx += 1
    if idx == len(result):
        print('Can not find any/other channel. Try another keyword.')
        return
    elif input('Do you want to add data to db? ' +
               '1 for Yes, 2 for No: ') == '2':
        print('No data added.')
        return
    youtube = get_data.start_youtube_connection('config/secrets.json')
    result = get_data.get_channel_info(youtube, result[idx][0])
    db = db_connection.DB_Connection()
    db.conn_string_from_path('config/secrets.json')
    insert_stmt = f"""
    INSERT INTO channel ({','.join(result.keys())})
    VALUES ({", ".join(['%s']*len(result))})
    """
    db.insert_one(insert_stmt, tuple(result.values()))


if __name__ == '__main__':
    main()
