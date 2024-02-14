# Youtube Insights

 
<!-- ## Introduction -->
Want to gain insight on youtube channels? This is the tool for you! 

This repo include tools to pull stats from youtube via youtube data API and custom crawler. Along with some common visualization notebooks to help you gain insight to the channels you're following

![channel distribution](images/channel_distribution.png)
![duration view relation](images/duration_view_relation.png)
![view-sub ratio](images/view_sub_ratio.png)



## Tools used

- Python packages - Selenium, psycopg2, Plotly
- Database - Postgres
- Orchestration/container - Docker

## Usage

### Setup

Follow sample.json to create your secrets.json file.
Please follow instructions [here](https://developers.google.com/youtube/v3/getting-started) to set up Youtube API key.

### Run Postgres docker
```
docker build -t youtube_db .
docker run --name youtube_db -v mydbdata:/var/lib/postgresql/data -p 5432:5432 -d my_youtube_db
```

### Select channels to track

option 1: search with channel keyword
```
python3 search_channel_id.py <keyword>

>> Is this channel <keyword> correct? 
>> 1 for Yes, 2 for No: 1

>> The channel id is: <channel id>
>> Do you want to add data to db?
>> 1 for Yes, 2 for No: 1
```

option 2: add with channel ids (txt file)
```
# channel_id.txt
UCvw1LiGdyulhnGksJlGWB6g,UCGbshtvS9t-8CW11W7TooQg
```
```
python3 add_channel_listing.py channel_id.txt
```

<!-- ### Run Airflow server -->

### Crawl data daily (Airflow support to be added)
```
python3 crawl_new_videos.py
python3 update_channel_stat.py 
python3 update_video_stat.py
```
### Visualize result
use the notebooks in the visualization folder to explore insights into your selected channels.

## Priority
- add testing
- add github action
- change name

## Working progress
- airflow automation
- add method to update channel active status
- add method to update video status 30 days and can't find
- 30 minute crawl for the first 24 hours
- 6 hour crawl for the first 7 days
- 1 day crawl for the 30 days
- interactive plotly
- dashboard with dash
- count video and shorts during daily insert

## Issues
- if get new video failed to insert, don't update status
- bash script if catch exceptions


## Resources
[youtube data API documentation](https://developers.google.com/youtube/v3/docs)