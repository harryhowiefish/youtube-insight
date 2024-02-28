from src import utils
import os
import pytest


def test_default_path(monkeypatch):
    mock_path = 'test/test_data/'

    monkeypatch.setattr(os, 'getcwd', lambda: mock_path)
    result = utils.load_env()
    expected_keys = ['YOUTUBE_API', 'pg_host',
                     'pg_dbname', 'pg_user', 'pg_password',
                     'pg_sslmode']
    assert isinstance(result, dict)
    assert list(result.keys()) == expected_keys


def test_assigned_path():
    result = utils.load_env('test/test_data/.ENV')
    expected_keys = ['YOUTUBE_API', 'pg_host',
                     'pg_dbname', 'pg_user', 'pg_password',
                     'pg_sslmode']
    assert isinstance(result, dict)
    assert list(result.keys()) == expected_keys
    pass


def test_missing_file():
    with pytest.raises(FileExistsError):
        utils.load_env('wrong_path')
