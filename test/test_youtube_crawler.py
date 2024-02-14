import pytest
from selenium.webdriver.chrome.webdriver import WebDriver
from src.youtube_crawler import Crawler


# Mocking Selenium WebDriver for unit tests
class MockWebDriver(WebDriver):
    def __init__(self, *args, **kwargs):
        pass

    def quit(self):
        pass  # Mock quit method to do nothing


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
        assert isinstance(driver, MockWebDriver), "Should return a WebDriver instance"
