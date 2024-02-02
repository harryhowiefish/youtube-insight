import googleapiclient.discovery
import sys
import json
import logging


def main():
    api_service_name = "youtube"
    api_version = "v3"
    with open('config/api.json') as f:
        config = json.load(f)
    DEVELOPER_KEY = config['YOUTUBE_API']

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=DEVELOPER_KEY)

    keyword = sys.argv[1]
    result = get_channel_id(youtube, keyword)
    print(result)


def get_channel_id(youtube: googleapiclient.discovery.Resource,
                   keyword: str) -> dict:
    '''
    get channel id from keyword search.
    '''
    request = youtube.search().list(
        part='snippet',
        q=keyword)
    response = request.execute()
    items = response['items']
    for item in items:
        if keyword.lower() in item['snippet']['channelTitle'].lower():
            return {'Name': item['snippet']['channelTitle'],
                    'Channel_id': item['snippet']['channelId']}
    logging.warning(f"Can't find channel with name {keyword}. " +
                    "Were you trying to find " +
                    f"{items[0]['snippet']['channelTitle']}")
    raise ValueError("Cannot find channel")


def get_channel_info(youtube: googleapiclient.discovery.Resource,
                   channel_id: str) -> dict:
    '''
    get channel information including customUrl, publish date,
    thumbnail link, description, country,
    view count, sub count, video count
    keyword, topic
    '''
    pass


def list_new_videos(youtube: googleapiclient.discovery.Resource,
                   keyword: str) -> dict:
    '''
    list video posted in the last 30 days
    '''
    pass


def get_video_info(
    youtube: googleapiclient.discovery.Resource,
                    video_id: str) -> dict:
    '''
    get information on single video including
    publish date, description, thumbnail link,
    tags, categoryId, duration, dimension,
    view count, like count, comment count,
    topic
    '''
    pass


if __name__ == '__main__':
    main()
