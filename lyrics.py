from azlyrics.azlyrics import lyrics
from youtube_title_parse import get_artist_title
from ytmusicapi import YTMusic

def fetch_lyrics(keyword):
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
        return song_title, song_artist, song_lyrics