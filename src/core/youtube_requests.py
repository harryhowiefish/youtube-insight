'''
Includes the Channel class that to parse HTML result for
information from youtube channel pages.

'''
import re
import requests
import json
import logging

BASIC_HEADER = {"User-Agent": "Mozilla/5.0",
                "accept-language": "en-US,en"}


class Channel():
    '''
    A class to crawl infromation from a youtube channel.
    Initialize with the channel_id CHAR(24)
    '''

    def __init__(self, channel_id: str) -> None:
        self.headers: dict = BASIC_HEADER
        self.yt_api_key: str | None = None
        self.channel_id: str = channel_id

    @property
    def tabs(self):
        return self.get_channel_tabs()

    def get_channel_tabs(self) -> list[str]:
        '''
        Query the channel to see what tabs are avaliable for the channel.
        "Home" tab is added manual due to differ in class name in HTML

        Parameters
        ----------
        None

        Returns:
        -------
        tabs list[str]

        list of tabs (likely to include home, videos, shorts,
        playlists, community)
        '''
        resp = requests.get(
            f'https://www.youtube.com/channel/{self.channel_id}/',
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

    def get_video_lists(self,
                        limit: int = 20) -> dict[str, list | None]:
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
        Set the number of video to crawl.

        Returns
        -------
        video_listing: dict

        Dictionary containing "videos" and/or "shorts" key.
        Each contain a list of video ids.
        '''
        result = {}

        if 'Videos' in self.tabs:
            url = f'https://www.youtube.com/channel/{self.channel_id}/videos'
            result['video'] = self._single_page_video_listing(url, limit)
        if 'Shorts' in self.tabs:
            url = f'https://www.youtube.com/channel/{self.channel_id}/shorts'
            result['short'] = self._single_page_video_listing(url, limit)
        return result

    def _single_page_video_listing(self, url: str, limit: int = float('inf')
                                   ) -> list:
        '''
        Helper function to crawl the video listing on a single page.
        By default, it will crawl all the video listing on that page.

        Parameters
        ----------
        url: str

        Youtube link to crawl.
        It should be the shorts or videos tab for channels.

        limit: int. Default inf

        Limit the number of elements to crawl.
        This is set to prevent issue with selenium.

        Returns:
        -------
        id_list: list

        List of video ids.
        '''
        all_vids = []
        resp = requests.get(
            url,
            headers=self.headers)
        video_ids = re.findall(
            'Endpoint":{"videoId":"(.*?)",', resp.text)
        all_vids.extend(video_ids)
        try:
            token = re.findall('"continuationCommand":{"token":"(.*?)",',
                               resp.text)[0]
        except IndexError:
            logging.warning(f'Missing continuation in {url}')
            return all_vids[:min(len(all_vids), limit)]

        while len(all_vids) < limit:
            video_ids, token = self._continous_video_listing(token)
            all_vids.extend(video_ids)
            if not video_ids or not token:
                break

        logging.info(f'Recieved {min(len(all_vids),limit)} video from {url}')
        return all_vids[:min(len(all_vids), limit)]

    def _continous_video_listing(self, token: str) -> tuple[list[str], str]:
        '''
        Helper function to get the video listing on the next page.
        This is needed if number of video crawled exceeds the preload amount.

        Parameters
        ----------

        token : str
        Continuation token from the previous page.
        Used to query new videos using innertube post request.


        Returns:
        -------
        video_ids : list[str]
        list of video_ids on the current page/token.

        next_token : str

        Token for the next set of videos.
        An empty string will be return in no more video to load.

        '''
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

    def _create_innertube_post_data(self, token: str
                                    ) -> tuple[str, dict[str, str], str]:
        '''
        Helper function to create the required object
        for innertube's post request.

        Parameters
        ----------
        token: str
        Continuation token from the previous page.

        Returns:
        -------
        load_more_url : str

        Url used for post request to innertube (youtubei)

        headers : dict

        extended header from self.headers to meet innertube
        requirements.

        data : str

        Serialized data in json format.
        '''
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

    def _raw_html(self, url: str) -> str:
        '''
        Helper function to return the HTML of the url.
        Only used for debug / developing purpose.

        Parameters
        ----------

        url : str

        Returns:
        -------
        text : str

        raw html text
        '''
        resp = requests.get(
            url,
            headers=self.headers)
        return resp.text


def keyword_search(keyword: str) -> list:
    '''
    Search for youtube channel id using keyword via youtube search.
    Matches' order are based on the result given on the search page.
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
        f'https://www.youtube.com/results?search_query={keyword}',
        headers=BASIC_HEADER)
    result = re.findall('"channelId":"(.*?)",' +
                        '"title":{"simpleText":"(.*?)"}',
                        resp.text)
    return result
