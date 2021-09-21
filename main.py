import os
import discord
import re
import random
import asyncio

from youtube_dl import YoutubeDL
from pytube import YouTube
from pytube import Playlist
from discord.ext import commands
from ytsearch import yt_search

to_reply = False

ffmpeg_opts = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 3', 'options': '-vn'}
play_list = []
now_playing = ''
server = ''

client = commands.Bot(command_prefix="`")


def song_done_check(ctx):
    coro = song_done(ctx)
    fut = asyncio.run_coroutine_threadsafe(coro, client.loop)
    try:
        fut.result()
    except:
        print('nag error')


# temp command
async def song_done(ctx):
    print('tapos na po')
    await play(ctx, autoplay=True)


@client.command(name="Join", brief="    -    `join", aliases=['join'])
async def join(ctx):
    if ctx.author.voice is None:
        await ctx.send('bruh join ka muna voice channel lol')
        return None

    voice_channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        await voice_channel.connect()
    else:
        await ctx.voice_client.move_to(voice_channel)
    return ctx.voice_client


async def play_helper(ctx, song_url):
    voice = ctx.voice_client
    try:
        voice.play(await discord.FFmpegOpusAudio.from_probe(song_url, **ffmpeg_opts),
                   after=lambda _: song_done_check(ctx))
        embed = discord.Embed(title=f'Now Playing:    {now_playing}')
        await ctx.send(embed=embed)
    except discord.errors.ClientException:
        await ctx.send('wait lang')
        pass


@client.command(name="Play", brief="    -    `p | `play", aliases=["play", 'p', 'P'])
async def play(ctx, *args, autoplay=False):
    global now_playing
    voice = await join(ctx)
    if not voice:
        return
    if not autoplay:
        if args:  # Song keyword/link given
            if not play_list and not now_playing:
                queue_check = await queue(ctx, *args, no_message=True, from_play=True)
            else:
                queue_check = await queue(ctx, *args, no_message=False, from_play=True)
            if not queue_check or voice.is_playing():  # possible bug
                return
        else:  # just `play
            if not play_list and not now_playing:
                await ctx.send("ano man ipplay ko")
                return
            if not autoplay:  # possible bug
                if voice.is_paused():
                    print('resume via play')
                    await resume(ctx)
                    return
                elif voice.is_playing():
                    await ctx.send("nagpplay na baga")
                    return

    # Allow ffmpeg to reconnect
    try:
        now_playing, song_url = play_list.pop(0)
    except IndexError:
        now_playing = ''
        print('ubos na playlist')
        await timeout(ctx, 30)
        return
    await play_helper(ctx, song_url)


async def queue_helper(ctx, url_list, no_message, pl_name=None, from_play=False):
    global now_playing
    is_playlist = bool(pl_name)
    if is_playlist:
        embed = discord.Embed(title=f"Added {len(url_list)} songs to queue from {pl_name} playlist")
        await ctx.send(embed=embed)

    for idx, yt in enumerate(url_list):
        song_url = YoutubeDL().extract_info(yt.watch_url, download=False)['formats'][0]['url']
        if pl_name and not idx:
            if ctx.voice_client and from_play:
                now_playing = yt.title
                await play_helper(ctx, song_url)
                continue
        song_title = yt.title
        if not is_playlist:
            await ctx.send(yt.watch_url, delete_after=7.5)
        if not is_playlist and not no_message:
            embed = discord.Embed(title=f"Added:    {song_title} to queue")
            await ctx.send(embed=embed)
        play_list.append([song_title, song_url])


@client.command(name='Queue', brief="    -    `q | `queue ", aliases=['queue', 'q'])
async def queue(ctx, *args, no_message=False, from_play=False):
    global server
    server = ctx.guild
    keywords = ' '.join(args)
    voice = ctx.voice_client
    if not keywords.strip():  # Show the queue
        songs = ''
        for idx, x in enumerate(play_list):
            songs += (str(idx + 1) + ':    ' + x[0] + '\n')
        songs = songs or "uda na kanta"
        if voice and (voice.is_playing() or voice.is_paused()):
            title = f"Now Playing:    {now_playing}"
            embed = discord.Embed(title=title, description=songs)
        else:
            embed = discord.Embed(description=songs)
        await ctx.send(embed=embed)
        return
    else:  # Add to queue
        pl_name = None
        if 'youtube.com/playlist?' in keywords:     # Playlist
            keywords_check = keywords.split()
            pl = Playlist(keywords_check[0])
            num_songs = len(pl)
            if len(keywords_check) > 1:             # number of songs to add given
                num_songs = int(keywords_check[-1])
            to_queue = list(pl.videos)[:num_songs]
            pl_name = pl.title
        else:
            video_url = await yt_search(keywords)   # Single (faster than ytdl)
            if not video_url:
                await ctx.send("sowi di ko mahanap 😢")
                return False
            to_queue = [YouTube(video_url)]
        await queue_helper(ctx, to_queue, no_message, pl_name, from_play)
        return True


def keyword_to_index(keyword):
    lower_case_titles = [x[0].lower() for x in play_list]
    keyword = keyword.lower()
    for idx, lower_case_title in enumerate(lower_case_titles):
        if keyword in lower_case_title:
            return idx + 1
    else:
        return keyword


@client.command(name='Move', brief="    -    `mv | `move", aliases=['move', 'mv'])
async def move(ctx, source_index, dest_index):
    if not source_index.isdigit():  # keyword is given
        source_index = keyword_to_index(source_index)
        if not type(source_index) == int:
            await ctx.send(f"uda man {source_index}")
            return
    if not dest_index.isdigit():  # keyword is given
        dest_index = keyword_to_index(dest_index)
        if not type(dest_index) == int:
            await ctx.send(f"uda man {dest_index}")
            return
    source_index, dest_index = int(source_index), int(dest_index)
    if source_index == dest_index or (max(int(source_index), int(dest_index)) > len(play_list)):
        await ctx.send("???")
        return
    try:
        song_to_move = play_list.pop(int(source_index)-1)
        play_list.insert(int(dest_index)-1, song_to_move)
        embed = discord.Embed(title=f"Moved {song_to_move[0]} to {dest_index}")
        await ctx.send(embed=embed)
    except IndexError:
        await ctx.send("bug")


async def timeout(ctx, secs=30):
    await asyncio.sleep(secs)
    voice = ctx.voice_client
    if not voice.is_paused() and not voice.is_playing():
        await leave(ctx)


@client.command(name='Leave', brief="    -    `leave | `disconnect", aliases=['leave', 'disconnect'])
async def leave(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice:
        global play_list, server, now_playing
        play_list = []
        server = ''
        now_playing = ''
        await voice.disconnect()
        await ctx.send("kbye")


@client.command(name='Pause', brief="    -    `pause ", aliases=['pause'])
async def pause(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if not voice:
        await ctx.send("ano man ipapause ko")
    if voice.is_paused():
        await ctx.send("naka pause na baga")
        return
    elif voice.is_playing():
        voice.pause()
        embed = discord.Embed(title=f"Paused:    {now_playing}")
        await ctx.send(embed=embed)


@client.command(name='Resume', brief="    -    `resume | `res ", aliases=['resume', 'res'])
async def resume(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if not voice:
        await ctx.send("ano man ireresume ko")
    if voice.is_paused():
        voice.resume()
        await nowplaying(ctx)
    elif voice.is_playing():
        await ctx.send("nag pplay na baga")
    else:
        print('bug')


@client.command(name='Skip', brief="    -    `skip | `s", aliases=['skip', 's'])
async def skip(ctx, *args, message=True):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    global now_playing
    if voice and (voice.is_playing() or voice.is_paused()):
        if message:
            embed = discord.Embed(title=f"Skipping {now_playing}")
            await ctx.send(embed=embed)
        voice.stop()
        # await play(ctx, autoplay=True)
    else:
        await ctx.send("ano isskip ko")


@client.command(name='Jump', brief="    -    `j | `jump | `goto", aliases=['jump', 'goto', 'j'])
async def jump(ctx, song_index=''):
    global play_list
    if song_index == '':
        await ctx.send("gib number plx")
        return
    try:
        if not song_index.isdigit():                            # keyword is given
            lower_case_titles = [x[0].lower() for x in play_list]
            song_index = song_index.lower()
            for idx, lower_case_title in enumerate(lower_case_titles):
                if song_index in lower_case_title:
                    song_index = idx + 1
                    break
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        play_list = play_list[int(song_index) - 1:]
        embed = discord.Embed(title="Skipping to " + play_list[0][0])
        await ctx.send(embed=embed)
        if voice:
            await skip(ctx, False)
    except IndexError:
        await ctx.send("uda man " + song_index)


@client.command(name="Now Playing", brief="    -    `np | `NP  ", aliases=['np', 'NP'])
async def nowplaying(ctx):
    embed = discord.Embed(title=f'Now Playing:    {now_playing}')
    await ctx.send(embed=embed, delete_after=7.5)


@client.command(name="Remove", brief="    -    `remove | `r  ", aliases=['remove', 'r', 'R'])
async def remove(ctx, song_index=''):
    if song_index == '':
        await ctx.send("???")
    try:
        if not song_index.isdigit():  # keyword is given
            if song_index.lower() in now_playing.lower():
                await ctx.send("cannot remove nagpplay, baka skip?")
                return
            song_index = keyword_to_index(song_index)
        song_removed = play_list.pop(int(song_index) - 1)[0]
        embed = discord.Embed(title="Removed " + song_removed)
        await ctx.send(embed=embed)
    except (ValueError, IndexError):
        await ctx.send("uda man " + song_index)


@client.command(name="Clear", brief="    -    `clear", aliases=['clear'])
async def clear(ctx):
    play_list.clear()
    embed = discord.Embed(title="Cleared queue")
    await ctx.send(embed=embed)


@client.command(name="Shuffle", brief="    -    `shuffle", aliases=['shuffle'])
async def shuffle(ctx):
    if not play_list:
        await ctx.send("uda man play list")
    random.shuffle(play_list)
    embed = discord.Embed(title="Queue shuffled")
    await ctx.send(embed=embed)


@client.command(name="Commands", brief="    -    Shows this message", aliases=['commands'])
async def _commands(ctx):
    await ctx.send_help()


@client.event
async def auto_reply(ctx, msg):
    ka_man = re.search(r'\bhi|hello|hai|hoy|pota|hayop|cute|magayon|pogi|gwapo|makanos|chaka|test|patal\b', msg)
    global to_reply
    if ka_man is not None:
        await ctx.send(ka_man[0] + " ka man")
        to_reply = False
    if to_reply:
        await ctx.send(random.choice(["ge", "bala ka", "oks", ".", "👍"]))
        to_reply = False


@client.event
async def on_ready():
    print(str(client.user) + " Live")


@client.event
async def on_message(message):
    # Server check
    print('chat:    ' + str(message.author)[:-5] + ': ' + message.content)  # debugging purposes

    if message.content.startswith('`'):
        if server and message.guild != server:
            await message.channel.send("bc aq")
        else:
            await client.process_commands(message)
        return

    msg = message.content.lower()
    if message.author == client.user:
        return

    global to_reply
    if msg.startswith('<@!888363419646984222>'):
        if re.search(r'delete', msg):
            await message.channel.purge(limit=2)
            return
        if msg.endswith('<@!888363419646984222>'):
            reply = random.choice(["ano", "op", "yo", "?", "nukaman", "👋"])
            if str(message.author) == "kennethfau#9317":
                reply = "ano po boss"
            else:
                reply += ' ' + "<@" + str(message.author.id) + ">"
            to_reply = True
        else:
            reply = 'oks'
        await message.channel.send(reply)
        return
    await auto_reply(await client.get_context(message), msg)


client.run(os.getenv("TOKEN"))
