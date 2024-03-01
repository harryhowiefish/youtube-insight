from src.add_channels import by_file
import logging


def test_missing_arg(monkeypatch, caplog):
    caplog.clear()
    monkeypatch.setattr('sys.argv', ['filename'])
    by_file.main()
    assert 'Please provide txt file' in caplog.text


def test_bad_file_type(monkeypatch, caplog):
    caplog.clear()
    monkeypatch.setattr('sys.argv', ['filename', 'random_file'])
    by_file.main()
    assert 'Please provide file that ends with .txt' in caplog.text


def test_file_not_found(monkeypatch, caplog):
    caplog.clear()
    monkeypatch.setattr('sys.argv', ['filename', 'sample.txt'])
    monkeypatch.setattr('os.path.exists', lambda path: False)
    by_file.main()
    assert 'File sample.txt does not exist.' in caplog.text


class Mock_Youtube:
    def __init__(self) -> None:
        pass

    def get_channel_info(self, id):
        return


class Mock_DB:
    def __init__(self) -> None:
        pass

    def insert_df(self, stmt, df):
        logging.info(f'Insert transaction complete. inserted {len(df)} rows.')


def test_no_channel_id(monkeypatch, tmp_path, caplog):
    caplog.clear()
    data = 'just_some_random_text'
    file_path = tmp_path / 'sample.txt'
    file_path = file_path.as_posix()
    with open(file_path, 'w') as f:
        f.write(data)
    monkeypatch.setattr('sys.argv', ['filename', file_path])
    monkeypatch.setattr('src.core.youtube_api.YoutubeAPI',
                        lambda: Mock_Youtube())
    by_file.main()
    assert 'No valid channel_id provided.' in caplog.text


def test_success(monkeypatch, tmp_path, caplog):
    monkeypatch.setattr('src.core.youtube_api.YoutubeAPI',
                        lambda: Mock_Youtube())
    monkeypatch.setattr(
        'src.core.db_connection.DB_Connection', lambda: Mock_DB())
    caplog.clear()
    data = 'channel_id1, channel_id2'
    file_path = tmp_path / 'sample.txt'
    file_path = file_path.as_posix()
    with open(file_path, 'w') as f:
        f.write(data)
    monkeypatch.setattr('sys.argv', ['filename', file_path])
    monkeypatch.setattr(Mock_Youtube, 'get_channel_info',
                        lambda self, id: {'column': 'data'})
    caplog.set_level(level='INFO')
    by_file.main()
    assert 'Insert transaction complete. inserted 2 rows.' in caplog.text
