'''
Custom extension base on psycopg2.
The main functionality includes:
- Automatically close connection with context managing
- include logging with all SQL excecution
'''

import psycopg2
from psycopg2.extras import execute_batch
import logging
from contextlib import contextmanager
import pandas as pd
from src import utils
import os


class DB_Connection():
    '''
    Include methods to help with DB manipulation.
    '''

    def __init__(self, env_path: str | None = None
                 ) -> None:
        self.conn_string = self._conn_string_from_env(env_path)
        pass

    def _conn_string_from_env(self,
                              path: str | None = None) -> str:
        '''
        Create conn_string from env file.

        Parameters
        ----------
        path : str

        Path to env file.

        Returns
        -------
        None

        conn_string added to class as an attribute
        '''
        utils.load_env(path)
        HOST = os.environ['pg_host']
        USER = os.environ['pg_user']
        DBNAME = os.environ['pg_dbname']
        PASSWORD = os.environ['pg_password']
        SSLMODE = os.environ['pg_sslmode']

        return f"host={HOST} user={USER} " + \
            f"dbname={DBNAME} password={PASSWORD} sslmode={SSLMODE}"

    @contextmanager
    def _start_cursor(self):
        '''
        Create a contextmanager for db connection to shuts down after use.
        Autocommit sql transaction.
        '''
        conn = psycopg2.connect(self.conn_string, connect_timeout=30)
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception as e:
            conn.rollback()
            logging.error(f"An error occurred: {e}")
        finally:
            cur.close()
            conn.close()

    def insert_df(self, insert_stmt: str, df: pd.DataFrame) -> None:
        '''
        Insert pd.DataFrame into database.

        Parameters
        ----------
        insert_stmt : str

        The df.column order needs to match the order in the insert_stmt.

        df: pd.DataFrame

        Data to insert. data will be paginate into 100 row per page to insert.

        Returns
        -------
        None
        '''
        with self._start_cursor() as cur:
            try:
                # Execute the INSERT statement for each row in the DataFrame
                execute_batch(cur, insert_stmt, df.values)
                # Commit the transaction
                logging.info(f'Insert transaction complete. inserted {len(df)} rows.')  # noqa
            except Exception as e:
                logging.error(f"An error occurred here: {e}")

    def insert_one(self, insert_stmt: str, data: tuple) -> None:
        '''
        Single row insert statement.

        Parameters
        ----------
        insert_stmt : str

        The data order needs to match the order in the insert_stmt.

        data : tuple

        Returns
        -------
        None
        '''
        with self._start_cursor() as cur:
            try:
                # Execute the INSERT statement for each row in the DataFrame
                cur.execute(insert_stmt, data)
                # Commit the transaction
                logging.info('Insert transaction completed.')
                return cur.rowcount
            except Exception as e:
                logging.error(f"An error occurred here: {e}")

    def query(self, query_stmt: str) -> list[tuple] | None:
        '''
        For SQL SELECT statments

        Parameters
        ----------
        query_stmt : str

        Any Standard SQL SELECT statements

        Returns
        -------
        data : list[tuple]

        Items in list are always tuples even if select statement
        returns a single column.

        Returns none if error occurs.

        '''
        with self._start_cursor() as cur:
            try:
                cur.execute(query_stmt)
                result = cur.fetchall()
                logging.info(f"Queried {len(result)} rows from db.")
                return result
            except Exception as e:
                logging.error(f"An error occurred here: {e}")
                return

    def update(self, update_stmt: str,
               data: tuple | None = None
               ) -> int | None:
        '''
        For SQL UPDATE statments

        Parameters
        ----------
        query_stmt : str

        Any Standard SQL SELECT statements

        Returns
        -------
        row_count : int

        Number of row updated. Return none if error occurs.
        '''
        with self._start_cursor() as cur:
            try:
                # Execute the INSERT statement for each row in the DataFrame
                cur.execute(update_stmt, vars=data)
                logging.info(f'Number of row updated: {cur.rowcount}')
                return cur.rowcount
            except Exception as e:
                logging.error(f"An error occurred here: {e}")
                return

    def export_csv(self, query: str, path: str) -> None:
        '''
        Uses SQL COPY command to export data to csv.

        Parameters
        ----------
        query : str

        Standard SQL SELECT statement

        path : str

        Export path

        Returns
        -------
        None
        '''
        with self._start_cursor() as cur:
            try:
                outputquery = "COPY ({0}) TO STDOUT WITH CSV HEADER".format(
                    query)
            except Exception as e:
                logging.error(f"An error occurred here: {e}")
                return
            with open(path, 'w') as f:
                cur.copy_expert(outputquery, f)
            return
