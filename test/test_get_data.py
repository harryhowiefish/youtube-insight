import pytest
import json
import googleapiclient.discovery
import src.get_data as get_data


# function get_channel_id no longer in use
# class TestGetChannelId(object):

#     @pytest.fixture(autouse=True)
#     def _youtube_resource(self):
#         api_service_name = "youtube"
#         api_version = "v3"
#         with open('config/api.json') as f:
#             config = json.load(f)
#         DEVELOPER_KEY = config['YOUTUBE_API']

#         self.youtube = googleapiclient.discovery.build(
#             api_service_name, api_version, developerKey=DEVELOPER_KEY)

#     def test_correct_keyword(self):
#         actual = get_data.get_channel_id(self.youtube, '這群人')
#         expected = {'Name': '這群人TGOP',
#                     'Channel_id': 'UC6FcYHEm7SO1jpu5TKjNXEA'}
#         msg = f'expected {expected}, got {actual}'
#         assert actual == expected, msg

#     def test_bad_keyword(self):
#         with pytest.raises(ValueError) as excinfo:
#             get_data.get_channel_id(self.youtube, '百齡果')
#         assert str(excinfo.value) == 'Cannot find channel'
