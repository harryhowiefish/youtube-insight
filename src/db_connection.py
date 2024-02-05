import json
import psycopg2
from psycopg2.extras import execute_batch
import logging
from contextlib import contextmanager


class DB_Connection():

    def __init__(self):
        pass

    def conn_string_from_path(self, path):
        with open(path) as f:
            config = json.load(f)

        HOST = config['postgres']['host']
        USER = config['postgres']['user']
        DBNAME = config['postgres']['dbname']
        PASSWORD = config['postgres']['password']

        self.conn_string = f"host={HOST} user={USER} " + \
            f"dbname={DBNAME} password={PASSWORD} sslmode=allow"

    @contextmanager
    def _get_cursor(self):
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

    def insert_df(self, insert_stmt, df):
        with self._get_cursor() as cur:
            try:
                # Execute the INSERT statement for each row in the DataFrame
                execute_batch(cur, insert_stmt, df.values)
                # Commit the transaction
                logging.info('insert transaction complete')
            except Exception as e:
                logging.error(f"An error occurred here: {e}")

    def insert_one(self, insert_stmt, data):
        with self._get_cursor() as cur:
            try:
                # Execute the INSERT statement for each row in the DataFrame
                cur.execute(insert_stmt, data)
                # Commit the transaction
                logging.info('insert transaction complete')
            except Exception as e:
                logging.error(f"An error occurred here: {e}")

    def query(self, query_stmt):
        with self._get_cursor() as cur:
            try:
                # Execute the INSERT statement for each row in the DataFrame
                cur.execute(query_stmt)
                result = cur.fetchall()
                return result
            except Exception as e:
                logging.error(f"An error occurred here: {e}")
