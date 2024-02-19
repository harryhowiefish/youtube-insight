import boto3
import time
import os
import argparse


def main():

    # Parser setting
    parser = argparse.ArgumentParser()
    parser.add_argument('-set', '--set_status', help='turn db on or off')
    parser.add_argument('-check', '--check_status',
                        help='return db current status',
                        action='store_true')
    args = parser.parse_args()

    # AWS connection setup
    os.environ['AWS_PROFILE'] = "boto3"
    os.environ['AWS_DEFAULT_REGION'] = "ap-southeast-1"
    client = boto3.client('rds')

    # get db current status
    info = client.describe_db_instances(
        DBInstanceIdentifier='youtube-db')['DBInstances'][0]
    status = info['DBInstanceStatus']

    # if no args provided
    if not any(vars(args).values()):
        print('Please provide arguments, or check --help for info.')
        return

    elif args.check_status:
        print(f"DB status is: {status}")

    elif args.set_status == 'on':
        if status == 'available':
            print('DB already running')
            return
        elif status != 'stopped':
            print(f"""Cannot interact with DB.
                  Current status is {status}""")
            raise ConnectionError('DB failed to start')

        # start db processes
        client.start_db_instance(
            DBInstanceIdentifier='youtube-db')

        # wait until db launch complete
        while True:
            info = client.describe_db_instances(
                DBInstanceIdentifier='youtube-db')['DBInstances'][0]
            if info['DBInstanceStatus'] in ['starting',
                                            'Configuring-enhanced-monitoring',
                                            'configuring-enhanced-monitoring']:  # noqa
                print('DB is starting...')
                time.sleep(30)
            elif info['DBInstanceStatus'] == 'available':
                print('DB started successfully')
                return
            else:
                print('start process was not successful')
                print(f"status is {info['DBInstanceStatus']}")
                raise ConnectionError('DB failed to start')

    elif args.set_status == 'off':
        if status == 'stopped':
            print('DB already stopped.')
            return
        # Start shutdown processes
        client.stop_db_instance(
            DBInstanceIdentifier='youtube-db')

        # wait until db shutdown complete
        while True:
            info = client.describe_db_instances(
                DBInstanceIdentifier='youtube-db')['DBInstances'][0]
            if info['DBInstanceStatus'] == 'stopped':
                print('DB shutdown successfully')
                return
            else:
                print('DB is shutting down...')
                time.sleep(30)


if __name__ == '__main__':
    main()
