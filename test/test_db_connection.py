import pytest  # noqa
from unittest.mock import patch, MagicMock  # noqa
from src.db_connection import DB_Connection
import os


def test_start_cursor():
    os.environ['pg_host'] = 'pytest'
    os.environ['pg_user'] = 'pytest'
    os.environ['pg_dbname'] = 'pytest'
    os.environ['pg_password'] = 'pytest'
    db_conn = DB_Connection()

    with patch("psycopg2.connect") as mock_connect:
        mock_conn = mock_connect.return_value
        mock_cursor = mock_conn.cursor.return_value

        with db_conn._start_cursor() as cursor:
            assert cursor == mock_cursor

        # Check if the connection was opened and closed properly
        mock_connect.assert_called_once_with(
            'host=pytest user=pytest dbname=pytest password=pytest sslmode=allow')  # noqa
        mock_conn.cursor.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

        # Check for commit
        mock_conn.commit.assert_called_once()
