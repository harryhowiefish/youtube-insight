import googleapiclient.discovery
import logging
from src import utils
import os


class YoutubeAPI():
    def __init__(self, env_path: str | None = None
                 ) -> None:
        self.youtube = self._api_key_from_env(env_path)
        pass

    def get_channel_info(self,
                         channel_id: str) -> dict:
        '''
        get channel information including customUrl, publish date,
        thumbnail link, description, country,
        keyword, topic

        Parameters
        ----------

        Returns
        -------
        '''
        request = self.youtube.channels().list(
            part="id,snippet,brandingSettings,topicDetails",
            id=channel_id)
        response = request.execute()
        if not response['items']:  # check if it's empty
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

    def get_channel_stat(self,
                         channel_id: str) -> dict:
        '''
        get the most recent channel stats
        including total view, sub count and video count

        Parameters
        ----------
        youtube: googleapiclient.discovery.Resource

        Returns
        -------
        '''
        request = self.youtube.channels().list(
            part="id, statistics",
            id=channel_id)
        response = request.execute()
        if not response['items']:  # check if it's empty
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

    def get_video_info(self,
                       video_id: str) -> dict:
        '''
        get information on single video including
        publish date, description, thumbnail link,
        tags, categoryId, duration, dimension

        Parameters
        ----------

        Returns
        -------
        '''
        request = self.youtube.videos().list(
            part="contentDetails,id,snippet,status,topicDetails",
            id=video_id)
        response = request.execute()
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

    def get_video_stat(self,
                       video_id: str) -> dict:
        '''
        get the most recent video stats
        including view, sub, and comment count

        Parameters
        ----------

        Returns
        -------
        '''
        request = self.youtube.videos().list(
            part="id, statistics",
            id=video_id)
        response = request.execute()
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

    def ids_to_data(self, video_lists: dict) -> list[dict]:
        video_data = []

        # loop through crawled data to call youtube API
        for video_type, video_ids in video_lists.items():
            if not video_ids:  # if there's no video crawled
                continue
            for video_id in video_ids:
                single_video = {'video_type': video_type}
                single_video.update(self.get_video_info(video_id))
                video_data.append(single_video)
        return video_data

    def _api_key_from_env(self, path: str | None
                          ) -> googleapiclient.discovery.Resource:
        '''

        Parameters
        ----------

        Returns
        -------
        '''
        api_service_name = "youtube"
        api_version = "v3"
        utils.load_env(path)
        DEVELOPER_KEY = os.environ['YOUTUBE_API']

        return googleapiclient.discovery.build(
            api_service_name, api_version, developerKey=DEVELOPER_KEY)
