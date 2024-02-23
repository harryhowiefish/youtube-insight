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
        Remote driver is required for crawler to be used along with airflow.
        '''
        # ToBeAdded: switch driver type
        driver = webdriver.Remote('remote_chromedriver:4444/wd/hub',
                                  options=self.options)
        # driver = webdriver.Chrome(options=self.options)

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

        Parameters
        ----------
        driver: selenium.WebDriver

        an instance of the driver object.

        url: str

        youtube link to crawl.
        It can be any page with video link / thumbnails.

        limit: int. Default 20

        Limit the number of elements to crawl.
        This is set to prevent issue with selenium.

        Returns:
        -------
        id_list: list

        List of video ids.
        Length likely be shorter than the limit due to missing href.

        -------
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
        Search for youtube channel id using keyword via youtube search.
        Matches are ordered base on the result given on the search page.
        Result can be None if no channel is suggested by youtube.

        Parameters
        ----------
        keyword: str

        Channel keyword.

        Returns:
        -------
        channel_list: list

        Return a list of tuples containing channel id and channel name.
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
        Look for the most recent video posting from a specified channel.
        Both video and shorts page will be query.
        An empty dictionary will be return in the rare case the channel
        has no video listing on the two pages.

        Parameters
        ----------
        channel_id: str

        Youtube channel_id (CHAR 24).
        Does not support youtube channel handles.

        Returns
        -------
        video_listing: dict

        Dictionary containing "videos" and/or "shorts" key.
        Each contain a list of video ids.
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
        if 'Shorts' in tabs:
            with self._start_driver() as driver:
                driver.implicitly_wait(5)
                url = f'https://www.youtube.com/channel/{channel_id}/shorts'
                result['short'] = self._single_page_video_listng(driver, url)  # noqa
        return result
