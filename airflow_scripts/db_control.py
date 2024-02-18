import boto3
import sys
import time
import os


def main():
    os.environ['AWS_PROFILE'] = "boto3"
    os.environ['AWS_DEFAULT_REGION'] = "ap-southeast-1"
    client = boto3.client('rds')
    if len(sys.argv) == 1:
        print('missing arg. Input on or off.')
    mode = sys.argv[1]
    info = client.describe_db_instances(
        DBInstanceIdentifier='youtube-db')['DBInstances'][0]
    if info['DBInstanceStatus'] not in ['stopped', 'available']:
        print(f"""Cannot interact with DB.
              Current status is {info['DBInstanceStatus']}""")
        raise ConnectionError('DB failed to start')

    if mode == 'on':
        if info['DBInstanceStatus'] == 'available':
            print('DB already running')
            return
        client.start_db_instance(
            DBInstanceIdentifier='youtube-db')
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

    elif mode == 'off':
        if info['DBInstanceStatus'] == 'stopped':
            print('DB already stopped.')
            return
        client.stop_db_instance(
            DBInstanceIdentifier='youtube-db')
        while True:
            info = client.describe_db_instances(
                DBInstanceIdentifier='youtube-db')['DBInstances'][0]
            if info['DBInstanceStatus'] == 'stopped':
                print('DB shutdown successfully')
                return
            else:
                print('DB is shutting down...')
                time.sleep(30)
    else:
        print('incorrect mode. Input on or off.')


if __name__ == '__main__':
    main()
