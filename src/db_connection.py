import json
import psycopg2
from psycopg2.extras import execute_batch
import logging
from contextlib import contextmanager
import pandas as pd


class DB_Connection():
    '''
    Include methods to help with DB manipulation.
    '''
    def __init__(self):
        pass

    def conn_string_from_path(self, path: str) -> None:
        '''

        Parameters
        ----------
        path : str


        Returns
        -------
        '''
        with open(path) as f:
            config = json.load(f)

        HOST = config['postgres']['host']
        USER = config['postgres']['user']
        DBNAME = config['postgres']['dbname']
        PASSWORD = config['postgres']['password']

        self.conn_string = f"host={HOST} user={USER} " + \
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
                return
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
