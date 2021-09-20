import os
import discord
import re
import random
import asyncio

from pytube import YouTube
from discord.ext import commands
from ytsearch import yt_search


play_status = 0  # 0 - stopped/no song, 1 - playing, 2 - paused
to_reply = False

ffmpeg_opts = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 3', 'options': '-vn'}
play_list = []
now_playing = ''
server = ''


client = commands.Bot(command_prefix='`')


def song_done_check(ctx):
    coro = song_done(ctx)
    fut = asyncio.run_coroutine_threadsafe(coro, client.loop)
    try:
        fut.result()
    except:
        print('nag error')
        leave(ctx)


async def song_done(ctx):
    print('tapos na po')
    if play_list:
        await play(ctx, autoplay=True)
    else:
        print("playlist done")
        global play_status
        play_status = 0


@client.command(name="Join", brief="    -    `join", aliases=['join'])
async def join(ctx):
    if ctx.author.voice is None:
        await ctx.send('bruh join ka muna voice channel lol')
        return

    voice_channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        await voice_channel.connect()
    else:
        await ctx.voice_client.move_to(voice_channel)
    voice = ctx.voice_client
    return voice


@client.command(name="Play", brief="    -    `p | `play", aliases=["play", 'p', 'P'])
async def play(ctx, *args, autoplay=False):
    if ctx.author.voice is None:
        await ctx.send('bruh join ka muna voice channel lol')
        return

    global play_status
    global now_playing
    if args:
        if not play_list and not now_playing:
            check = await queue(ctx, *args, no_message=True)
        else:
            check = await queue(ctx, *args, no_message=False)
        if check == -1 or play_status == 1:
            return
    else:
        if not play_list and not now_playing:
            await ctx.send("ano man ipplay ko")
            return
        if play_status and not autoplay:
            if play_status == 2:
                print('resume via play')
                await resume(ctx)
            return

    voice = await join(ctx)

    # Allow ffmpeg to reconnect

    play_status = 1

    try:
        now_playing, song_url = play_list.pop(0)
    except IndexError:
        now_playing = ''
        play_status = 0
        print('ubos na playlist')
        return

    try:
        embed = discord.Embed(title=f'Now Playing:    {now_playing}')
        await ctx.send(embed=embed)
        voice.play(await discord.FFmpegOpusAudio.from_probe(song_url, **ffmpeg_opts), after=lambda _: song_done_check(ctx))
    except discord.errors.ClientException:
        pass


@client.command(name='Queue', brief="    -    `q | `queue ", aliases=['queue', 'q'])
async def queue(ctx, *args, no_message=False):
    """
    Previews song queue (only yt links for now)
    """
    global server
    server = ctx.guild
    keywords = ' '.join(args)
    if not keywords.strip(' '):
        songs = ''
        for idx, x in enumerate(play_list):
            songs += (str(idx+1) + ':    ' + x[0] + '\n')
        songs = songs or "uda na kanta"
        if play_status:
            title = f"Now Playing:    {now_playing}"
            embed = discord.Embed(title=title, description=songs)
        else:
            embed = discord.Embed(description=songs)
        await ctx.send(embed=embed)
        return

    try:
        video_url = await yt_search(keywords)
    except AttributeError:
        await ctx.send("sowi di ko mahanap 😢")
        return -1

    yt = YouTube(video_url)
    song_url = yt.streaming_data.get('hlsManifestUrl') or yt.streams.get_audio_only().url
    song_title = yt.title
    print(video_url, '\n', song_title)
    print(song_url)

    await ctx.send(video_url, delete_after=7.5)

    embed = discord.Embed(title=f"Added:    {song_title} to queue")
    if not no_message:
        await ctx.send(embed=embed)
    play_list.append([song_title, song_url])
    return song_url


@client.command(name='Leave', brief="    -    `leave | `disconnect", aliases=['leave', 'disconnect'])
async def leave(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice:
        global play_list, play_status, server, now_playing
        play_list = []
        play_status = 0
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
        global play_status
        play_status = 2
        embed = discord.Embed(title=f"Paused:    {now_playing}")
        await ctx.send(embed=embed)


@client.command(name='Resume', brief="    -    `resume | `res ", aliases=['resume', 'res'])
async def resume(ctx):
    global play_status
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if not voice:
        await ctx.send("ano man ireresume ko")
    if voice.is_paused():
        voice.resume()
        play_status = 1
        await nowplaying(ctx)
    elif voice.is_playing():
        await ctx.send("nag pplay na baga")
    else:
        print('bug')


@client.command(name='Skip', brief="    -    `skip | `s", aliases=['skip', 's'])
async def skip(ctx, *args, message=True):
    if args:
        await jump(ctx, *args)
        return
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    global now_playing
    if voice and (voice.is_playing() or voice.is_paused()):
        if message:
            embed = discord.Embed(title=f"Skipping {now_playing}")
            await ctx.send(embed=embed)
        voice.stop()
        now_playing = ''
        # play_status = 2 # changed
    else:
        await ctx.send("ano isskip ko")


@client.command(name='Jump', brief="    -    `j | `jump | `goto", aliases=['jump', 'goto', 'j'])
async def jump(ctx, song_index=''):
    global play_list
    if song_index == '':
        await ctx.send("gib number plx")
        return
    try:
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

        # song_removed = play_list.pop(int(song_index)-1)[0]
        play_list = play_list[int(song_index)-1:]
        embed = discord.Embed(title="Skipping to "+play_list[0][0])
        await ctx.send(embed=embed)
        if voice:
            await skip(ctx, message=False)
    except IndexError:
        await ctx.send("uda man "+song_index)
    # if jump 1, just send to skip (same behavior maybe no message, maybe include it)


@client.command(name="Now Playing", brief="    -    `np | `NP  ", aliases=['np', 'NP'])
async def nowplaying(ctx):
    embed = discord.Embed(title=f'Now Playing:    {now_playing}')
    await ctx.send(embed=embed, delete_after=7.5)


@client.command(name="Remove", brief="    -    `remove | `r  ", aliases=['remove', 'r', 'R'])
async def remove(ctx, song_index=''):
    if song_index == '':
        await ctx.send("???")
    try:
        song_removed = play_list.pop(int(song_index)-1)[0]
        embed = discord.Embed(title="Removed "+song_removed)
        await ctx.send(embed=embed)
    except IndexError:
        await ctx.send("uda man "+song_index)


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
    print(str(client.user)+" Live")


@client.event
async def on_message(message):
    # Server check
    print('chat:    '+str(message.author)[:-5]+': '+message.content)  # debugging purposes

    if message.content.startswith('`'):
        if server and message.guild != server:
            await message.channel.send("bc aq")
        else:
            await client.process_commands(message)
        return

    msg = message.content.lower()
    if message.author == client.user:
        print("chat:    replied: "+msg)
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
                reply += ' ' + "<@"+str(message.author.id)+">"
            to_reply = True
        else:
            reply = 'oks'
        await message.channel.send(reply)
        return
    await auto_reply(await client.get_context(message), msg)

client.run(os.getenv("TOKEN"))
