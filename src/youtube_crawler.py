from selenium import webdriver
import re
from selenium.webdriver.chrome.options import Options
from contextlib import contextmanager
import logging


class Crawler():
    def __init__(self) -> None:
        self.options = Options()
        self.options.add_argument('--headless=new')

    @contextmanager
    def _start_driver(self):
        driver = webdriver.Chrome(options=self.options)
        try:
            yield driver
        except Exception as e:
            logging.error(f"An error occurred: {e}")
        finally:
            driver.quit()

    def keyword_search(self, keyword):
        with self._start_driver() as driver:
            driver.get(f'https://www.youtube.com/results?search_query={keyword}')  # noqa
            result = re.findall('"channelId":"(.*?)",' +
                                '"title":{"simpleText":"(.*?)"}',
                                driver.page_source)
            return result

    def get_video_lists(self, channel_id):
        result = {}
        tabs = ""
        with self._start_driver() as driver:
            driver.implicitly_wait(1000)
            url = f'https://www.youtube.com/channel/{channel_id}/videos'
            result['video'] = self._single_page_video_listng(driver, url)
            tabs = driver.find_element("xpath", '//*[@id="tabs"]').text
        if 'Shorts' in tabs:
            with self._start_driver() as driver:
                driver.implicitly_wait(1000)
                url = f'https://www.youtube.com/channel/{channel_id}/shorts'
                result['short'] = self._single_page_video_listng(driver, url)  # noqa
        return result

    def _single_page_video_listng(self, driver, url):

        driver.get(url)
        videos = driver.find_elements("xpath",
            '//*[@class="yt-simple-endpoint inline-block style-scope ytd-thumbnail"]')  # noqa
        videos = videos[:20]
        ids = [item.get_attribute('href')[-11:] for item in videos if item.get_attribute('href') is not None]  # noqa
        logging.info(f'Recieved {len(ids)} video from {url}')
        return ids
