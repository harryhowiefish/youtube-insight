from src.airflow_scripts import update_channel_stat
import logging
import pytest
import os


class Mock_Youtube:
    def __init__(self) -> None:
        pass

    def multiple_channels_stat(self, ids: list):
        return [{'view_count': 111,
                 'video_count': 2,
                 'sub_count': 5}]


class Mock_DB:
    def __init__(self) -> None:
        pass

    def query(self, stmt):
        return [['id'],]

    def insert_df(self, stmt, df):
        logging.info(f'Insert transaction complete. inserted {len(df)} rows.')


@pytest.fixture(autouse=True)
def patch_modules(monkeypatch):
    monkeypatch.setattr('src.core.youtube_api.YoutubeAPI',
                        lambda: Mock_Youtube())
    monkeypatch.setattr(
        'src.core.db_connection.DB_Connection', lambda: Mock_DB())


def test_main_success(monkeypatch, caplog, tmp_path):
    caplog.clear()
    caplog.set_level(level='INFO')
    monkeypatch.chdir(tmp_path)

    update_channel_stat.main()
    # check logging
    assert "['view_count', 'video_count', 'sub_count']" in caplog.text

    # check export csv
    assert os.path.exists(tmp_path / 'channel_stats.csv')

    # check insert df
    expected_log = 'Insert transaction complete. inserted 1 rows.'
    assert expected_log in caplog.text
