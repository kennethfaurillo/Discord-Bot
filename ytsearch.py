import re
import aiohttp


async def yt_search(keyword):
    """
    Asynchronous YT keyword search

    keyword - str single or multiple search keywords

    Returns a tuple containing the URL and title of the first result
    """
    keyword = '+'.join(keyword.split())
    async with aiohttp.ClientSession() as session:
        async with session.get("https://www.youtube.com/results?search_query="+keyword) as resp:
            html = await resp.text()
    video_id = re.search(r"watch\?v=(\S{11})", html)
    if not video_id:
        return None
    url_first_result = "https://www.youtube.com/watch?v="+video_id.group()[-11:]
    return url_first_result  
