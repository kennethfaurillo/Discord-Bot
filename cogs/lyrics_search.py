import aiohttp
import asyncio
import re
import os
from googleapiclient.discovery import build
from azlyrics.azlyrics import lyrics as get_lyrics
my_api_key = os.getenv("GOOGLE_API_KEY")
my_cse_id = os.getenv("CSE_ID")

def google_search(search_term, api_key, cse_id, **kwargs):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().siterestrict().list(q=search_term, cx=cse_id, **kwargs).execute()
    return res['items'][0]['link']

async def lyrics_search(keyword):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5)\
        AppleWebKit/537.36 (KHTML, like Gecko) Cafari/537.36'}
    if keyword:
        azlyrics_url = google_search(keyword, my_api_key, my_cse_id)
        print(azlyrics_url)
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(azlyrics_url) as resp:
                html = await resp.text(encoding='utf-8')
        regex = re.match(r"https://www.azlyrics.com/lyrics\/(.*)\/(.*)\.ht", azlyrics_url).groups()
        artist = regex[0]
        song = regex[1]
        lyrics = get_lyrics(artist, song)[0]
        print(song + " by " + artist)
        if "Error" in lyrics:
            print("No lyrics found!")
            return None
        print(lyrics)
        lyrics = lyrics.replace('<br>','')
        return lyrics

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(lyrics_search(keyword="less than zero weeknd"))
