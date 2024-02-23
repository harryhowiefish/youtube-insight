import pytest
from src.youtube_crawler import Crawler
import logging
from unittest.mock import Mock, patch, MagicMock
from selenium.common import exceptions as sel_exceptions

LOGGER = logging.getLogger(__name__)


@pytest.fixture
def mock_webdriver():
    with patch('selenium.webdriver.Remote') as mock_build:
        mock_driver = MagicMock()
        mock_build.return_value = mock_driver
        yield mock_driver
        del mock_driver


@pytest.fixture
def crawler():
    # Setup code before each test
    crawler_instance = Crawler()
    yield crawler_instance
    # Teardown code after each test
    del crawler_instance


def test_init(crawler):
    assert isinstance(crawler, Crawler), "Crawler instance should be created"


def test_start_driver_context_manager(crawler, mock_webdriver):
    with crawler._start_driver() as driver:
        driver == mock_webdriver


class TestSinglePageVideoListing():

    @staticmethod
    def test_basic_success(crawler, mock_webdriver):
        url = 'https://www.youtube.com/@MrBeast'
        # item = MagicMock()
        # item.get_attribute.return_value = 'video_id'
        item = Mock()
        item.configure_mock(**{'get_attribute.return_value': 'video_id'})
        mock_webdriver.find_elements.return_value = [item, item]
        with crawler._start_driver() as driver:
            result = crawler._single_page_video_listng(driver, url)
        assert isinstance(result, list)

    @staticmethod
    def test_bad_url(crawler, mock_webdriver, caplog):
        url = 'bad_string'
        mock_webdriver.get.side_effect = sel_exceptions.InvalidArgumentException  # noqa
        with crawler._start_driver() as driver:
            crawler._single_page_video_listng(driver, url)
        assert "Invalid argument. Likely bad url." in caplog.text


class TestKeywordSearch():

    @staticmethod
    def test_type_list(crawler, mock_webdriver):
        mock_page = '''
        {"channelId":"UCX6OQ3DkcsbYNE6H8uQQuVA","title":{"simpleText":"MrBeast"}
        '''
        mock_webdriver.page_source = mock_page
        result = crawler.keyword_search('Mrbeast')
        assert isinstance(result, list)


class TestGetVideoLists():

    @staticmethod
    def test_type_list(crawler, mock_webdriver):
        tab_item = Mock()
        tab_item.configure_mock(text=['Videos'])
        # tab_item = MagicMock()
        # tab_item.text = ['Videos']
        mock_webdriver.find_element.return_value = tab_item
        result = crawler.get_video_lists(
            'UCvw1LiGdyulhnGksJlGWB6g')
        assert isinstance(result, dict)
        assert len(result) in [0, 1, 2]

    @staticmethod
    def test_bad_channel_id(crawler, mock_webdriver, caplog):
        mock_webdriver.get.side_effect = sel_exceptions.NoSuchElementException  # noqa
        crawler.get_video_lists('123')
        assert "Can't find element. Likely bad url." in caplog.text
