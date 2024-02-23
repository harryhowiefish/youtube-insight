import re
import requests
import json
import logging


class Crawler():
    '''
    '''

    def __init__(self) -> None:
        self.header = {"User-Agent": "Mozilla/5.0",
                       "accept-language": "en-US,en"}
        self.yt_api_key = None

    def _single_page_video_listng(self, url: str,
                                  continuation: str = None) -> list:
        '''
        Helper function to crawl the video listing on a single page.
        If continuation is set, use post method to get the next page.

        Parameters
        ----------
        driver: selenium.WebDriver

        an instance of the driver object.

        url: str

        youtube link to crawl.
        It can be any page with video link / thumbnails.

        limit: int. Default 20

        Limit the number of elements to crawl.
        This is set to prevent issue with selenium.

        Returns:
        -------
        id_list: list

        List of video ids.
        Length likely be shorter than the limit due to missing href.

        -------
        '''
        if continuation:
            pass
        resp = requests.get(
            'https://www.youtube.com/channel/UCHm9SiOLG8UoBT8STWY5mVA/videos',
            headers=self.header)
        video_ids = re.findall(
            '"watchEndpoint":{"videoId":"(.*?)",', resp.text)

        logging.info(f'Recieved {len(video_ids)} video from {url}')
        return video_ids, continuation

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
            headers=self.header)
        tabs = re.findall('{"tabRenderer":(.*?}}.*?}}.*?})}',
                          resp.text)
        # First tab is always home. And can not be json load properly.
        tabs = [json.loads(item) for item in tabs[1:]]
        tabs = [item['title'] for item in tabs]
        tabs.insert(0, 'Home')
        return tabs

    def get_video_lists(self, channel_id: str,
                        limit: int | None = None) -> dict[str, list]:
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
            result['video'], _ = self._single_page_video_listng(url)
        if 'Shorts' in tabs:
            url = f'https://www.youtube.com/channel/{channel_id}/shorts'
            result['short'], _ = self._single_page_video_listng(url)
        return result
