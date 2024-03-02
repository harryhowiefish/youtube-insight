'''
Includes a YoutubeAPI class to process the data from youtube data api v3
Set API_KEY in ENV is required.
'''

import googleapiclient.discovery
import logging
from src import utils
import os
from googleapiclient.errors import HttpError


class YoutubeAPI():
    '''
    Class contain methods to retrieve data from youtube api.
    Initialize class with env path.
    Path will default to .env in working directory.
    '''

    def __init__(self, env_path: str | None = None
                 ) -> None:
        self.youtube = self._api_key_from_env(env_path)
        pass

    def get_channel_info(self,
                         channel_id: str) -> dict[str, any]:
        '''
        get channel information including customUrl, publish date,
        thumbnail link, description, country,
        keyword, topic.

        Parameters
        ----------
        channel_id : str

        CHAR(24)

        Returns
        -------
        data : dict

        channel_id, name, customUrl, published_date, thumbnail_url,
        description, country, keywords, topic
        '''
        request = self.youtube.channels().list(
            part="id,snippet,brandingSettings,topicDetails",
            id=channel_id)
        try:
            response = request.execute()
        except HttpError as e:
            logging.error(e)
            return
        if 'items' not in response:  # check if it's empty
            logging.error(f"Can't find channel with id {channel_id}")
            # raise ValueError("Cannot find channel using channel id")
            return
        info = response['items'][0]
        result = {}
        result['channel_id'] = info['id']
        result['name'] = info['snippet']['title']
        if 'customUrl' in info['snippet']:
            result['customUrl'] = info['snippet']['customUrl']
        result['published_date'] = info['snippet']['publishedAt']
        result['thumbnail_url'] = info['snippet']['thumbnails']['high']['url']
        result['description'] = info['brandingSettings']['channel']['description']  # noqa
        if 'country' in info['brandingSettings']['channel']:
            result['country'] = info['brandingSettings']['channel']['country']
        if 'keywords' in info['brandingSettings']['channel']:
            result['keywords'] = info['brandingSettings']['channel']['keywords']  # noqa
        if 'topicDetails' in info:
            if 'topicCategories' in info['topicDetails']:
                result['topic'] = info['topicDetails']['topicCategories']
                result['topic'] = ', '.join([item.split('/')[-1] for item in result['topic']])  # noqa
        return result

    def multiple_channels_stat(self,
                               channel_list: list[str]) -> list[dict]:
        '''
        Run channel_stat for multiple channel id.

        Parameters
        -----------
        channel_list : list[str]

        A list containing all the channel id to query.

        Return
        -----------
        data : list[dict]

        Each item in list correspond to the data for each channel.

        '''
        results = []
        for channel_id in channel_list:
            result = self.get_channel_stat(channel_id)
            if result:
                results.append(result)
        return results

    def get_channel_stat(self,
                         channel_id: str) -> dict:
        '''
        Get the most recent channel stats by channel id.
        Including total view, sub count and video count

        Parameters
        ----------
        channel_id : str

        CHAR(24)

        Returns
        -------
        data : dict
        channel_id, view_count, sub_count, video_count
        '''
        request = self.youtube.channels().list(
            part="id, statistics",
            id=channel_id)
        try:
            response = request.execute()
        except HttpError as e:
            logging.error(e)
            return
        if 'items' not in response:  # check if it's empty
            logging.error(f"Can't find channel with id {channel_id}")
            # raise ValueError("Cannot find channel using channel id")
            return
        info = response['items'][0]
        result = {}
        result['channel_id'] = info['id']
        result['view_count'] = info['statistics']['viewCount']
        result['sub_count'] = info['statistics']['subscriberCount']
        result['video_count'] = info['statistics']['videoCount']
        return result

    def multiple_videos_info(self, video_lists: dict[str, list]) -> list[dict]:
        video_data = []
        '''
        Run video_info for multiple video id.

        Parameters
        -----------
        video_lists : dict[str, list]

        Expecting a dictionary wtih 'video' and 'short' keys.
        Each containing a list of video id.

        Return
        -----------
        data : list[dict]

        Each item in list correspond to the data for each video.
        '''
        # loop through crawled data to call youtube API
        for video_type, video_ids in video_lists.items():
            if not video_ids:  # if there's no video crawled
                continue
            for video_id in video_ids:
                single_video = {'video_type': video_type}
                info = self.get_video_info(video_id)
                if info:
                    single_video.update(info)
                    video_data.append(single_video)
        return video_data

    def get_video_info(self,
                       video_id: str) -> dict:
        '''
        Get information on single video by video id.

        Parameters
        ----------
        video_id : str

        CHAR(11)

        Returns
        -------
        data : dict

        video_id, title, published_date, thumbnail_url,
        description, duration, tags, categoryId
        '''
        request = self.youtube.videos().list(
            part="contentDetails,id,snippet,status,topicDetails",
            id=video_id)
        try:
            response = request.execute()
        except HttpError as e:
            logging.error(e)
            return
        if not response['items']:  # check if it's empty
            logging.error(f"Can't find video with id {video_id}")
            # raise ValueError("Cannot find video using video id")
            return
        info = response['items'][0]
        result = {}
        result['video_id'] = info['id']
        result['title'] = info['snippet']['title']
        result['published_date'] = info['snippet']['publishedAt']
        result['description'] = info['snippet']['description']
        result['thumbnail_url'] = info['snippet']['thumbnails']['high']['url']
        result['duration'] = info['contentDetails']['duration']
        if 'tag' in info['snippet']:
            result['tags'] = info['snippet']['tags']
        if 'categoryId' in info['snippet']:
            result['categoryId'] = info['snippet']['categoryId']
        return result

    def multiple_videos_stat(self,
                             video_list: list[str]) -> list[dict]:
        '''
        Run video_stat for multiple video id.

        Parameters
        -----------
        video_list : list[str]

        A list containing all the video id to query.

        Return
        -----------
        data : list[dict]

        Each item in list correspond to the data for each video.
        '''
        results = []
        for id in video_list:
            result = self.get_video_stat(id)
            if result:
                results.append(result)
        return results

    def get_video_stat(self,
                       video_id: str) -> dict:
        '''
        get video stats from video_id
        including view, sub, and comment count

        Parameters
        ----------
        video_id : str

        CHAR(11)

        Returns
        -------
        data : dict
        video_id, view_count, like_count, comment_count
        '''
        request = self.youtube.videos().list(
            part="id, statistics",
            id=video_id)
        try:
            response = request.execute()
        except HttpError as e:
            logging.error(e)
            return
        if not response['items']:  # check if it's empty
            logging.warning(f"Can't find video with id {video_id}")
            # raise ValueError("Cannot find video using video id")
            return
        info = response['items'][0]
        result = {}
        result['video_id'] = info['id']
        if 'viewCount' in info['statistics']:
            result['view_count'] = info['statistics']['viewCount']
        if 'likeCount' in info['statistics']:
            result['like_count'] = info['statistics']['likeCount']
        if 'commentCount' in info['statistics']:
            result['comment_count'] = info['statistics']['commentCount']
        return result

    def _api_key_from_env(self, path: str | None = None
                          ) -> googleapiclient.discovery.Resource:
        '''
        helper function to get API key from .env

        Parameters
        ----------
        path : str

        Path to env file.
        Default path to working directory.

        Returns
        -------
        youtube :  googleapiclient.discovery.Resource

        Youtube Client.
        '''
        api_service_name = "youtube"
        api_version = "v3"
        utils.load_env(path)
        DEVELOPER_KEY = os.environ['YOUTUBE_API']

        return googleapiclient.discovery.build(
            api_service_name, api_version, developerKey=DEVELOPER_KEY)
