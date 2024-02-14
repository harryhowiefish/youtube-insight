import pytest  # noqa
from unittest.mock import patch, MagicMock  # noqa
from src.db_connection import DB_Connection


def test_start_cursor():
    db_conn = DB_Connection()
    db_conn.conn_string = "dummy_connection_string"

    with patch("psycopg2.connect") as mock_connect:
        mock_conn = mock_connect.return_value
        mock_cursor = mock_conn.cursor.return_value

        with db_conn._start_cursor() as cursor:
            assert cursor == mock_cursor

        # Check if the connection was opened and closed properly
        mock_connect.assert_called_once_with("dummy_connection_string")
        mock_conn.cursor.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

        # Check for commit
        mock_conn.commit.assert_called_once()
