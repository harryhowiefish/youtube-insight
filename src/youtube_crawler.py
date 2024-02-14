from selenium import webdriver
import re
from selenium.webdriver.chrome.options import Options
from contextlib import contextmanager
import logging
from selenium.common import exceptions as sel_exceptions


class Crawler():
    '''
    Using selenium to crawl informationf from youtube.
    selenium is set as headless to run in background.
    '''
    def __init__(self) -> None:
        self.options = Options()
        self.options.add_argument('--headless=new')

    @contextmanager
    def _start_driver(self):
        '''
        Create a contextmanager to make sure driver shuts down after every use.
        '''
        driver = webdriver.Chrome(options=self.options)
        try:
            yield driver
        except sel_exceptions.InvalidArgumentException:
            logging.error('Invalid argument. Likely bad url.')
        except sel_exceptions.NoSuchElementException:
            logging.error("Can't find element. Likely bad url.")
        except Exception as e:
            raise e
        finally:
            driver.quit()

    def _single_page_video_listng(self, driver, url: str,
                                  limit: int = 20) -> list:
        '''
        Helper function to crawl the video listing on a single page.
        limit 20 by default to prevent selenium error due to unloaded page.
        implicitly_wait time is arbiturarily set,
        future exploring might be required.
        '''
        driver.get(url)
        videos = driver.find_elements("xpath",
            '//*[@class="yt-simple-endpoint inline-block style-scope ytd-thumbnail"]')  # noqa
        videos = videos[:limit]
        ids = [item.get_attribute('href')[-11:] for item in videos if item.get_attribute('href') is not None]  # noqa
        logging.info(f'Recieved {len(ids)} video from {url}')
        return ids

    def keyword_search(self, keyword: str) -> list:
        '''

        Parameters
        ----------

        Returns
        -------
        '''
        with self._start_driver() as driver:
            driver.implicitly_wait(1000)
            driver.get(f'https://www.youtube.com/results?search_query={keyword}')  # noqa
            result = re.findall('"channelId":"(.*?)",' +
                                '"title":{"simpleText":"(.*?)"}',
                                driver.page_source)
            return result

    def get_video_lists(self, channel_id: str) -> dict:
        '''

        Parameters
        ----------

        Returns
        -------
        '''
        result = {}
        tabs = ""

        with self._start_driver() as driver:
            driver.implicitly_wait(5)
            url = f'https://www.youtube.com/channel/{channel_id}/videos'
            driver.get(url)
            tabs = driver.find_element("xpath", '//*[@id="tabs"]').text

        if 'Videos' in tabs:
            with self._start_driver() as driver:
                driver.implicitly_wait(5)
                url = f'https://www.youtube.com/channel/{channel_id}/videos'
                result['video'] = self._single_page_video_listng(driver, url)
        # with self._start_driver() as driver:
        #     driver.implicitly_wait(1000)
        #     url = f'https://www.youtube.com/channel/{channel_id}/videos'
        #     result['video'] = self._single_page_video_listng(driver, url)
        #     tabs = driver.find_element("xpath", '//*[@id="tabs"]').text
        if 'Shorts' in tabs:
            with self._start_driver() as driver:
                driver.implicitly_wait(5)
                url = f'https://www.youtube.com/channel/{channel_id}/shorts'
                result['short'] = self._single_page_video_listng(driver, url)  # noqa
        return result
