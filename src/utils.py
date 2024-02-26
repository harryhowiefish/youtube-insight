from dotenv import load_dotenv
import os
import logging


def load_env(path: str | None) -> None:

    # check if path not provided use default
    if not path:
        path = os.path.join(os.getcwd(), '.ENV')

    # check if file exist
    if not os.path.exists(path):
        raise FileExistsError(f"Can't find .ENV file at {path}")
    load_dotenv(path)
    # check all info is there
    for item in ['YOUTUBE_API', 'pg_host', 'pg_host',
                 'pg_dbname', 'pg_user', 'pg_password', 'pg_password',
                 'pg_sslmode']:
        if item not in os.environ:
            logging.warning(
                f"Missing {item} in environment," +
                "some functions might not work properly.")
    return
