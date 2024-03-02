import boto3
import time
import os
import argparse
import logging
logging.basicConfig(level=logging.INFO)


def main():
    '''
    This script creates a faster way to switch on/off AWS RDS.
    .aws in root directory is required for this to work.
    '''
    args = parse_args()

    # AWS connection setup
    os.environ['AWS_PROFILE'] = "boto3"
    os.environ['AWS_DEFAULT_REGION'] = "ap-southeast-1"
    client = boto3.client('rds')
    db_name = 'youtube-db'

    # get db current status
    status = get_db_status(client, db_name)

    #  no args provided
    if not any(vars(args).values()):
        logging.info('Please provide arguments, or check --help for info.')
        return

    elif args.check_status:
        logging.info(f"DB status is: {status}")

    elif args.set_status == 'on':
        if status == 'available':
            logging.info('DB already running')
            return
        elif status != 'stopped':
            logging.info(f"""Cannot interact with DB.
                  Current status is {status}""")
            raise ConnectionError('DB failed to start')

        # start db processes
        client.start_db_instance(
            DBInstanceIdentifier='youtube-db')

        # wait until db launch complete
        db_polling(client, db_name, waiting_for='available')

    elif args.set_status == 'off':
        if status == 'stopped':
            logging.info('DB already stopped.')
            return
        # Start shutdown processes
        client.stop_db_instance(
            DBInstanceIdentifier='youtube-db')

        # wait until db shutdown complete
        db_polling(client, db_name, waiting_for='stopped')


def get_db_status(client, db_name: str) -> str:
    '''
    Parse status from describe_db_instances method's result.

    Parameters
    ----------
    client: boto3.client.RDS

    RDS client

    db_name : str

    DB name on AWS

    Returns:
    -------
    status : str
    '''
    info = client.describe_db_instances(
        DBInstanceIdentifier=db_name)['DBInstances'][0]
    return info['DBInstanceStatus']


def parse_args(args=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('-set', '--set_status', help='turn db on or off',
                        choices=['on', 'off'])
    parser.add_argument('-check', '--check_status',
                        help='return db current status',
                        action='store_true')
    return parser.parse_args(args)


def db_polling(client, db_name: str, waiting_for: str) -> None:
    '''
    Continously check in on status until change complete.

    Parameters
    ----------
    client: boto3.client.RDS

    RDS client

    db_name : str

    DB name on AWS

    waiting_for : str

    The status you expect to recieve.

    Returns:
    -------
    None
    '''
    while True:
        status = get_db_status(client, db_name)
        if status == waiting_for:
            logging.info(f'DB {waiting_for}.')
            return
        else:
            logging.info('DB is changing status...')
            time.sleep(30)


if __name__ == '__main__':
    main()
