import os
import re
import aiohttp
import googleapiclient.discovery
from azlyrics.azlyrics import lyrics
from youtube_title_parse import get_artist_title
from ytmusicapi import YTMusic


async def yt_search(**kwargs):
    api_service_name = "youtube"
    api_version = "v3"
    developer_key = os.environ['YOUTUBE']

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=developer_key)

    keyword = kwargs.get('keyword')
    if keyword:
        keyword = '+'.join(keyword.split())
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.youtube.com/results?search_query="+keyword) as resp:
                html = await resp.text()
        video_id = re.search(r"watch\?v=(\S{11})", html)
        if not video_id:
            return None, None
        video_id = video_id.group()[-11:]
        song_title = youtube.videos().list(
            part="snippet",
            id=video_id
        ).execute()['items'][0]['snippet']['title']
        return {'titles': [song_title], 'watch_urls': ["https://www.youtube.com/watch?v="+video_id]}, None

    pl_id = kwargs.get('pl_id')
    pl_name = youtube.playlists().list(
        part="snippet",
        id=pl_id
        ).execute()['items'][0]['snippet']['title']

    response = youtube.playlistItems().list(
        part="snippet",
        maxResults="50",
        playlistId=pl_id
    ).execute()

    items = response['items']
    next_page_token = response.get('nextPageToken')

    while next_page_token:
        response = youtube.playlistItems().list(
            part="snippet",
            maxResults="50",
            playlistId=pl_id,
            pageToken=next_page_token
        ).execute()
        items.extend(response['items'])
        next_page_token = response.get('nextPageToken')

    song_titles = []
    watch_urls = []
    for song in items:
        song_titles.append(song['snippet']['title'])
        watch_urls.append('https://youtube.com/watch?v='+song['snippet']['resourceId']['videoId'])

    return {'titles': song_titles, 'watch_urls': watch_urls}, pl_name

def lyrics_search(keyword):
        ytmusic = YTMusic('headers_auth.json')
        search_results = ytmusic.search(keyword)[0]
        song_title = search_results['title']
        song_artist = search_results['artists'][0]['name']

        song_artist, song_title = get_artist_title(song_artist+' - '+ song_title)
        print(song_title, 'by', song_artist)

        song_lyrics= lyrics(song_artist, song_title)
        # special case, azlyrics doesnt like The Weeknd :(
        if 'Error' in song_lyrics:
            print("Lyrics not found! Trying again")
            song_lyrics= lyrics(song_artist.lstrip('The '), song_title)
        if 'Error' in song_lyrics:
            print("Lyrics not found!")
            return None, None, None
            
        return song_title, song_artist, song_lyrics[0].strip()