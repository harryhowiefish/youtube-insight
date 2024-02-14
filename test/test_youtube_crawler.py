import pytest
from selenium.webdriver.chrome.webdriver import WebDriver
from src.youtube_crawler import Crawler
import logging

LOGGER = logging.getLogger(__name__)


@pytest.fixture
def crawler():
    # Setup code before each test
    crawler_instance = Crawler()
    yield crawler_instance
    # Teardown code after each test
    del crawler_instance


def test_init(crawler):
    assert isinstance(crawler, Crawler), "Crawler instance should be created"


def test_start_driver_context_manager(crawler):
    with crawler._start_driver() as driver:
        assert isinstance(driver, WebDriver
                          ), "Should return a WebDriver instance"


class TestSinglePageVideoListing():

    @staticmethod
    def test_basic_success(crawler):
        url = 'https://www.youtube.com/@MrBeast'
        with crawler._start_driver() as driver:
            result = crawler._single_page_video_listng(driver, url)
        assert isinstance(result, list)

    @staticmethod
    def test_bad_url(crawler, caplog):
        url = 'random_string'
        with crawler._start_driver() as driver:
            crawler._single_page_video_listng(driver, url)
        assert "Invalid argument. Likely bad url." in caplog.text


class TestKeywordSearch():

    @staticmethod
    def test_type_list(crawler):
        result = crawler.keyword_search('Mrbeast')
        assert isinstance(result, list)


class TestGetVideoLists():

    @staticmethod
    def test_type_list(crawler):
        result = crawler.get_video_lists(
            'UCvw1LiGdyulhnGksJlGWB6g')
        assert isinstance(result, dict)
        assert len(result) in [0, 1, 2]

    @staticmethod
    def test_bad_channel_id(crawler, caplog):
        crawler.get_video_lists('123')
        assert "Can't find element. Likely bad url." in caplog.text
