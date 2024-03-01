from src.add_channels import by_search
import logging
import pytest


class TestUserConfirmation:
    @staticmethod
    def test_reject_two(monkeypatch, caplog):
        caplog.clear()
        caplog.set_level(level='INFO')
        inputs = iter(['2', '2'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))
        result = by_search.user_confirmation([['a_id', 'a_name'],
                                              ['b_id', 'b_name']])
        assert result is None
        expected_log = 'Can not find any/other channel. Try another keyword.'
        assert expected_log in caplog.text

    @staticmethod
    def test_accept_second_but_dont_add(monkeypatch, caplog):
        caplog.clear()
        caplog.set_level(level='INFO')
        inputs = iter(['2', '1', '2'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))
        result = by_search.user_confirmation([['a_id', 'a_name'],
                                              ['b_id', 'b_name']])
        assert result is None
        expected_log = 'No data added.'
        assert expected_log in caplog.text
        expected_log = 'The channel id is b_id'
        assert expected_log in caplog.text

    @staticmethod
    def test_accept_second_and_add(monkeypatch, caplog):
        caplog.clear()
        caplog.set_level(level='INFO')
        inputs = iter(['2', '1', '1'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))
        result = by_search.user_confirmation([['a_id', 'a_name'],
                                              ['b_id', 'b_name']])
        expected_log = 'The channel id is b_id'
        assert expected_log in caplog.text
        assert result == 'b_id'


class Mock_Youtube:
    def __init__(self) -> None:
        pass

    def get_channel_info(self, id):
        return {'key': 'value'}


class Mock_DB:
    def __init__(self) -> None:
        pass

    def insert_one(self, stmt, data):
        logging.info('Insert transaction completed.')


@pytest.fixture(autouse=True)
def patch_modules(monkeypatch):
    monkeypatch.setattr('src.core.youtube_api.YoutubeAPI',
                        lambda: Mock_Youtube())
    monkeypatch.setattr(
        'src.core.db_connection.DB_Connection', lambda: Mock_DB())


class TestBySearch:
    @staticmethod
    def test_missing_arg(monkeypatch, caplog):
        caplog.clear()
        monkeypatch.setattr('sys.argv', ['filename'])
        by_search.main()
        expected_log = 'Please provide keyword to search for channel...'
        assert expected_log in caplog.text

    @staticmethod
    def test_success(monkeypatch, caplog):
        caplog.clear
        caplog.set_level(level='INFO')
        monkeypatch.setattr(by_search, 'user_confirmation', lambda _: 'id')
        monkeypatch.setattr('src.core.youtube_requests.keyword_search',
                            lambda _: [])
        monkeypatch.setattr('sys.argv', ['filename', 'mrbeast'])
        by_search.main()
        assert 'Insert transaction completed.' in caplog.text
