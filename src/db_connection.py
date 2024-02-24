import psycopg2
from psycopg2.extras import execute_batch
import logging
from contextlib import contextmanager
import pandas as pd
from dotenv import load_dotenv
import os


class DB_Connection():
    '''
    Include methods to help with DB manipulation.
    '''

    def __init__(self, env_path: str | None = None):
        self.conn_string = self._conn_string_from_env(env_path)
        pass

    def _conn_string_from_env(self, path: str | None = None) -> None:
        '''

        Parameters
        ----------
        path : str

        provide config data to create conn_string.
        self.conn_string added to class.

        Returns
        -------
        None
        '''
        load_dotenv(path)

        HOST = os.environ['pg_host']
        USER = os.environ['pg_user']
        DBNAME = os.environ['pg_dbname']
        PASSWORD = os.environ['pg_password']

        return f"host={HOST} user={USER} " + \
            f"dbname={DBNAME} password={PASSWORD} sslmode=allow"

    @contextmanager
    def _start_cursor(self):
        '''
        Create a contextmanager for db connection to shuts down after use.
        '''
        conn = psycopg2.connect(self.conn_string)
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

        Parameters
        ----------
        insert_stmt : str

        Returns
        -------
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

        Parameters
        ----------

        Returns
        -------
        '''
        with self._start_cursor() as cur:
            try:
                # Execute the INSERT statement for each row in the DataFrame
                cur.execute(insert_stmt, data)
                # Commit the transaction
                logging.info('insert transaction complete')
                return cur.rowcount
            except Exception as e:
                logging.error(f"An error occurred here: {e}")

    def query(self, query_stmt: str) -> list:
        '''

        Parameters
        ----------

        Returns
        -------
        '''
        with self._start_cursor() as cur:
            try:
                # Execute the INSERT statement for each row in the DataFrame
                cur.execute(query_stmt)
                result = cur.fetchall()
                return result
            except Exception as e:
                logging.error(f"An error occurred here: {e}")
                return

    def update(self, query_stmt: str) -> None:
        '''

        Parameters
        ----------

        Returns
        -------
        '''
        with self._start_cursor() as cur:
            try:
                # Execute the INSERT statement for each row in the DataFrame
                cur.execute(query_stmt)
                return cur.rowcount
            except Exception as e:
                logging.error(f"An error occurred here: {e}")
                return

    def export_csv(self, query: str, path: str) -> None:
        '''

        Parameters
        ----------

        Returns
        -------
        '''
        with self._start_cursor() as cur:
            outputquery = "COPY ({0}) TO STDOUT WITH CSV HEADER".format(query)
            with open(path, 'w') as f:
                cur.copy_expert(outputquery, f)
