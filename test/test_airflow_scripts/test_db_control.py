from src.airflow_scripts import db_control
import pytest
from argparse import Namespace


class Mock_client:
    def __init__(self) -> None:
        self.info = {'DBInstanceStatus': 'FILLER'}

    def describe_db_instances(self, DBInstanceIdentifier):
        return {'DBInstances': [self.info]}

    def start_db_instance(self, DBInstanceIdentifier):
        return

    def stop_db_instance(self, DBInstanceIdentifier):
        return


@pytest.fixture(autouse=True)
def replace_client(monkeypatch):
    monkeypatch.setattr('boto3.client', lambda _: Mock_client())


def test_get_db_status(monkeypatch):
    client = Mock_client()
    result = db_control.get_db_status(client, 'name')
    assert result == 'FILLER'

    monkeypatch.setitem(client.info, 'DBInstanceStatus', 'stopped')
    result = db_control.get_db_status(client, 'name')
    assert result == 'stopped'


def test_db_polling(monkeypatch, caplog):
    caplog.clear()
    caplog.set_level(level='INFO')
    client = Mock_client()
    status_values = ['initial_status', 'expected_status']

    def mock_get_db_status(client, db_name):
        return status_values.pop(0)

    # Replace the actual get_db_status with the mock version
    monkeypatch.setattr(db_control, 'get_db_status', mock_get_db_status)

    # Mock time.sleep to avoid delays during the test
    monkeypatch.setattr("time.sleep", lambda s: None)

    # Call the db_polling function
    db_control.db_polling(client, 'db_name', 'expected_status')

    assert len(caplog.records) == 2
    assert caplog.records[0].msg == 'DB is changing status...'
    assert caplog.records[1].msg == 'DB expected_status.'


class TestParseArgs:
    @staticmethod
    def test_set_status_on():
        args = db_control.parse_args(['--set_status', 'on'])
        assert args.set_status == 'on'

    @staticmethod
    def test_set_status_off():
        args = db_control.parse_args(['--set_status', 'off'])
        assert args.set_status == 'off'

    @staticmethod
    def test_check_status():
        args = db_control.parse_args(['--check_status'])
        assert args.check_status is True

    @staticmethod
    def test_no_args():
        args = db_control.parse_args([])
        assert args.set_status is None
        assert args.check_status is False

    @staticmethod
    def test_invalid_set_status():
        with pytest.raises(SystemExit):
            db_control.parse_args(['--set_status', 'invalid'])


class TestMain():

    @staticmethod
    def test_no_args(monkeypatch, caplog):
        caplog.clear()
        caplog.set_level(level='INFO')
        monkeypatch.setattr(db_control, 'parse_args',
                            lambda: Namespace(**{
                            }))
        db_control.main()
        expected_log = 'Please provide arguments, or check --help for info.'
        assert expected_log == caplog.records[0].msg

    @staticmethod
    def test_arg_check(monkeypatch, caplog):
        caplog.clear()
        caplog.set_level(level='INFO')
        monkeypatch.setattr(db_control, 'parse_args',
                            lambda: Namespace(**{
                                'check_status': True
                            }))
        db_control.main()
        assert "DB status is: FILLER" == caplog.records[0].msg

    @staticmethod
    def test_arg_set_on_status_on(monkeypatch, caplog):

        caplog.clear()
        caplog.set_level(level='INFO')
        status_values = ['available']

        def mock_get_db_status(client, db_name):
            return status_values.pop(0)

        monkeypatch.setattr(db_control, 'get_db_status', mock_get_db_status)
        monkeypatch.setattr(db_control, 'parse_args',
                            lambda: Namespace(**{
                                'set_status': 'on',
                                'check_status': False
                            }))
        db_control.main()
        assert "DB already running" == caplog.records[0].msg

    @staticmethod
    def test_arg_set_on_bad_status(monkeypatch, caplog):

        caplog.clear()
        caplog.set_level(level='INFO')
        status_values = ['bad_status']

        def mock_get_db_status(client, db_name):
            return status_values.pop(0)

        monkeypatch.setattr(db_control, 'get_db_status', mock_get_db_status)
        monkeypatch.setattr(db_control, 'parse_args',
                            lambda: Namespace(**{
                                'set_status': 'on',
                                'check_status': False
                            }))
        with pytest.raises(ConnectionError):
            db_control.main()
        expected_log = """Cannot interact with DB.
                  Current status is bad_status"""
        assert expected_log == caplog.records[0].msg

    @staticmethod
    def test_arg_set_on_status_off(monkeypatch, caplog):

        caplog.clear()
        caplog.set_level(level='INFO')
        status_values = ['stopped', 'running', 'available']

        def mock_get_db_status(client, db_name):
            return status_values.pop(0)

        monkeypatch.setattr(db_control, 'get_db_status', mock_get_db_status)
        monkeypatch.setattr(db_control, 'parse_args',
                            lambda: Namespace(**{
                                'set_status': 'on',
                                'check_status': False
                            }))
        monkeypatch.setattr("time.sleep", lambda s: None)
        db_control.main()
        assert 'DB is changing status...' == caplog.records[0].msg
        assert 'DB available.' == caplog.records[1].msg

    @staticmethod
    def test_arg_set_off_status_off(monkeypatch, caplog):

        caplog.clear()
        caplog.set_level(level='INFO')
        status_values = ['stopped']

        def mock_get_db_status(client, db_name):
            return status_values.pop(0)

        monkeypatch.setattr(db_control, 'get_db_status', mock_get_db_status)
        monkeypatch.setattr(db_control, 'parse_args',
                            lambda: Namespace(**{
                                'set_status': 'off',
                                'check_status': False
                            }))
        db_control.main()
        assert 'DB already stopped.' == caplog.records[0].msg

    @staticmethod
    def test_arg_set_off_status_on(monkeypatch, caplog):

        caplog.clear()
        caplog.set_level(level='INFO')
        status_values = ['available', 'shutting down', 'stopped']

        def mock_get_db_status(client, db_name):
            return status_values.pop(0)

        monkeypatch.setattr(db_control, 'get_db_status', mock_get_db_status)
        monkeypatch.setattr(db_control, 'parse_args',
                            lambda: Namespace(**{
                                'set_status': 'off',
                                'check_status': False
                            }))
        monkeypatch.setattr("time.sleep", lambda s: None)
        db_control.main()
        assert 'DB is changing status...' == caplog.records[0].msg
        assert 'DB stopped.' == caplog.records[1].msg
