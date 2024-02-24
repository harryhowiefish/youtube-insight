import re
import requests
import json
import logging


class Crawler():
    '''
    '''

    def __init__(self) -> None:
        self.headers = {"User-Agent": "Mozilla/5.0",
                        "accept-language": "en-US,en"}
        self.yt_api_key = None

    def _single_page_video_listng(self, url: str, limit: int
                                  ) -> list:
        '''
        Helper function to crawl the video listing on a single page.
        If continuation is set, use post method to get the next page.

        Parameters
        ----------
        url: str

        youtube link to crawl.
        It can be any page with video link / thumbnails.

        continuation: str. Default = None
        continuation token from the previous loading page.

        limit: int. Default 20

        Limit the number of elements to crawl.
        This is set to prevent issue with selenium.

        Returns:
        -------
        id_list: list

        List of video ids.

        -------
        '''
        all_vids = []
        resp = requests.get(
            url,
            headers=self.headers)
        video_ids = re.findall(
            '"watchEndpoint":{"videoId":"(.*?)",', resp.text)

        token = re.findall('"continuationCommand":{"token":"(.*?)",',
                           resp.text)[0]
        all_vids.extend(video_ids)
        while len(all_vids) < limit:
            video_ids, token = self._continous_video_listing(token)
            all_vids.extend(video_ids)
            if not video_ids or not token:
                break

        logging.info(f'Recieved {min(len(all_vids),limit)} video from {url}')
        return all_vids[:limit]

    def _continous_video_listing(self, token: str):
        url, headers, data = self._create_innertube_post_data(token)
        resp = requests.post(url, headers=headers, data=data)
        text = resp.text.replace(' ', '').replace('\n', '')
        video_ids = re.findall('"videoRenderer":{"videoId":"(.*?)",', text)
        try:
            next_token = re.findall(
                '"continuationCommand":{"token":"(.*?)",', text)[0]
        except IndexError:
            return video_ids, ''
        return video_ids, next_token

    def _create_innertube_post_data(self, token):
        load_more_url = "https://www.youtube.com/youtubei/v1/browse?key=" + \
            f"{self.yt_api_key}"
        headers = {
            "X-YouTube-Client-Name": "1",
            "X-YouTube-Client-Version": "2.20200720.00.02",
            "Content-Type": "application/json"
        }
        headers.update(self.headers)
        data_dict = {
            "continuation": token,
            "context": {
                "client": {
                    "clientName": "WEB",
                    "clientVersion": "2.20200720.00.02"
                }
            }
        }
        data = json.dumps(data_dict)
        return load_more_url, headers, data

    def keyword_search(self, keyword: str) -> list:
        '''
        Search for youtube channel id using keyword via youtube search.
        Matches are ordered base on the result given on the search page.
        Result can be None if no channel is suggested by youtube.

        Parameters
        ----------
        keyword: str

        Channel keyword.

        Returns:
        -------
        channel_list: list

        Return a list of tuples containing channel id and channel name.
        '''
        resp = requests.get(
            f'https://www.youtube.com/results?search_query={keyword}')
        result = re.findall('"channelId":"(.*?)",' +
                            '"title":{"simpleText":"(.*?)"}',
                            resp.text)
        return result

    def get_channel_tabs(self, channel_id: str) -> list[str]:
        resp = requests.get(
            f'https://www.youtube.com/channel/{channel_id}/',
            headers=self.headers)
        tabs = re.findall('{"tabRenderer":(.*?}}.*?}}.*?})}',
                          resp.text)
        self.yt_api_key = re.findall(
            '"INNERTUBE_API_KEY":"(.*?)",', resp.text)[0]
        # First tab is always home. And can not be json load properly.
        tabs = [json.loads(item) for item in tabs[1:]]
        tabs = [item['title'] for item in tabs]
        tabs.insert(0, 'Home')
        return tabs

    def get_video_lists(self, channel_id: str,
                        limit: int = 100) -> dict[str, list]:
        '''
        Look for the most recent video posting from a specified channel.
        Both video and shorts page will be query.
        An empty dictionary will be return in the rare case the channel
        has no video listing on the two pages.

        Parameters
        ----------
        channel_id: str

        Youtube channel_id (CHAR 24).
        Does not support youtube channel handles.

        limit: int. Default None
        set the number of video to crawl

        Returns
        -------
        video_listing: dict

        Dictionary containing "videos" and/or "shorts" key.
        Each contain a list of video ids.
        '''
        result = {}
        tabs = ""

        tabs = self.get_channel_tabs(channel_id)

        if 'Videos' in tabs:
            url = f'https://www.youtube.com/channel/{channel_id}/videos'
            result['video'] = self._single_page_video_listng(url, limit)
        if 'Shorts' in tabs:
            url = f'https://www.youtube.com/channel/{channel_id}/shorts'
            result['short'] = self._single_page_video_listng(url, limit)
        return result
