import os
import re
import aiohttp
import googleapiclient.discovery


async def lyrics_search(**kwargs):
    keyword = kwargs.get('keyword')
    if keyword:
        keyword = '+'.join(keyword.split())
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.google.com/search?q=" + keyword) as resp:
                html = await resp.text()
        # video_id = re.search(r"watch\?v=(\S{11})", html)
        azlyrics_url = re.search(r"(https.*html)", html)
        async with aiohttp.ClientSession() as session:
            async with session.get(azlyrics_url) as resp:
                html = await resp.text()
        lyrics = re.search(r"\. -->\n\s*([\w\W]+?(?=\<\/))", html)
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

#https://www.google.com/search?q=