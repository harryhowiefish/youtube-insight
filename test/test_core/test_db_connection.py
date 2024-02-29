from src.core import DB_Connection
import pytest
from dotenv.main import dotenv_values
import pandas as pd
import logging
import os


# Mock connection that returns either a success or exception cursor

class MockCursor:
    def __init__(self):
        pass

    def execute(self, insert_stmt, data=None):
        if data:
            self.rowcount = len(data)
        pass

    def fetchall(self):
        return ['item1', 'item2']

    def mogrify(self, stmt, data):
        self.rowcount = len(data)
        return b'data'

    def close(self):
        pass

    def copy_expert(stmt, file):
        pass


class MockConnection:
    def __init__(self, dsn):
        pass

    def cursor(self):
        return MockCursor()

    def rollback(self):
        pass

    def commit(self):
        pass

    def close(self):
        pass


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    mock_path = 'test/test_data/'
    monkeypatch.setattr('os.getcwd', lambda: mock_path)
    monkeypatch.setattr("psycopg2.connect",
                        lambda dsn: MockConnection(dsn))


@pytest.fixture
def db_conn():
    db_conn = DB_Connection()
    yield db_conn
    del db_conn


class TestSetupAndContextManager():

    @staticmethod
    def test_init(db_conn):
        isinstance(db_conn, DB_Connection)

    @staticmethod
    def test_conn_string():
        var = dotenv_values('test/test_data/.ENV')
        expected = f"host={var['pg_host']} user={var['pg_user']} " + \
            f"dbname={var['pg_dbname']} password={var['pg_password']} " + \
            f"sslmode={var['pg_sslmode']}"
        result = DB_Connection()._conn_string_from_env()
        assert expected == result

    @staticmethod
    def test_start_cursor(db_conn):
        with db_conn._start_cursor() as cursor:
            assert cursor == MockConnection.MockCursor


class TestTwoInsertMethods():

    @staticmethod
    def test_insert_df(db_conn, caplog):
        caplog.clear()
        data = {'col1': [1, 2], 'col2': [3, 4]}
        df = pd.DataFrame(data)
        with caplog.at_level(logging.INFO):
            db_conn.insert_df('insert_stmt', df)
        expected_log = f'Insert transaction complete. inserted {len(df)} rows.'
        assert expected_log in caplog.text

    @staticmethod
    def test_insert_one(db_conn, caplog):
        caplog.clear()
        data = ['item1', 'item2']
        with caplog.at_level(logging.INFO):
            result = db_conn.insert_one('insert_stmt', data)
        assert result == len(data)
        assert 'Insert transaction completed.' in caplog.text


class TestQueryAndUpdate():

    @staticmethod
    def test_query(db_conn):
        result = db_conn.query('query_stmt')
        assert result == ['item1', 'item2']

    @staticmethod
    def test_update(db_conn):
        result = db_conn.update('update_stmt')
        assert result is None


class TestExportCsv():

    @staticmethod
    def test_file_exist(db_conn, tmp_path):
        path = tmp_path / 'test.csv'
        db_conn.export_csv('stmt', path)
        assert os.path.exists(path)
