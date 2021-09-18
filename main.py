import discord
import re
import youtube_dl
import time
import random
import asyncio

from discord.ext import commands
from ytsearch import yt_search


play_status = 0  # 0 - stopped/no song, 1 - playing, 2 - paused
to_reply = False

play_list = []
now_playing = ''

client = commands.Bot(command_prefix='`')


def song_done(ctx):
    coro = test(ctx)
    fut = asyncio.run_coroutine_threadsafe(coro, client.loop)
    try:
        fut.result()
    except:
        print('nag error')
        raise


async def test(ctx):
    print('tapos na po')
    await play(ctx, autoplay=True)


@client.command(name="Play", brief="`p or `play  |  Plays a song or adds to queue", aliases=['p', 'P', "play"])
async def play(ctx, *args, autoplay=False):
    global play_status
    if args:
        check = await queue(ctx, *args)
        if check == -1 or play_status == 1:
            return
    else:  # works like pause/resume when used on its own, e.g., 'play or 'p
        if play_status and not autoplay:
            if play_status == 1:
                print('pause via play')
                await pause(ctx)
            elif play_status == 2:
                print('resume via play')
                await resume(ctx)
            return

    if ctx.author.voice is None:
        await ctx.send('bruh join ka muna voice channel lol')
        return
    voice_channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        await voice_channel.connect()
    else:
        await ctx.voice_client.move_to(voice_channel)
    voice = ctx.voice_client

    ffmpeg_opts = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    # Allow ffmpeg to reconnect

    play_status = 1

    global now_playing
    try:
        now_playing, song_url = play_list.pop(0)
    except IndexError:
        now_playing = ''
        return

    try:
        embed = discord.Embed(title=f'Now Playing:    {now_playing}')
        await ctx.send(embed=embed)
        voice.play(await discord.FFmpegOpusAudio.from_probe(song_url, **ffmpeg_opts), after=lambda _: song_done(ctx))
    except discord.errors.ClientException:
        pass


@client.command()
async def leave(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice:
        await voice.disconnect()
        await ctx.send("kbye")


@client.command()
async def pause(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    try:
        if voice.is_playing():
            voice.pause()
            global play_status
        play_status = 2
    except discord.ext.commands.errors.CommandInvokeError:
        await ctx.send("nothing's playing")
        return


@client.command()
async def resume(ctx):
    global play_status
    if play_status == 0:
        await ctx.send("ano man ireresume mo")
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_paused():
        voice.resume()
        play_status = 1
    else:
        if not play_status:
            await ctx.send("no song to play")
        else:
            await ctx.send("audio is not paused")


@client.command()
async def stop(ctx):
    global play_status
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    voice.stop()
    play_status = 0


@client.command(aliases=['q'])
async def queue(ctx, *args):
    """
    Previews song queue (only yt links for now)
    """
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

    start = time.time()
    try:
        video_url = await yt_search(keywords)
    except AttributeError:
        await ctx.send("sowi di ko mahanap 😢")
        return -1
    with youtube_dl.YoutubeDL({"source_address": "0.0.0.0"}) as ydl:  # forces ipv4
        inf = ydl.extract_info(video_url, download=False)
        song_url = inf['formats'][0]['url']
        song_title = inf['title']
    print(time.time() - start)
    print(video_url, '\n', song_title)

    # add try except, if except, add to queue
    await ctx.send(video_url)

    embed = discord.Embed(title=f"Added {song_title} to queue")
    await ctx.send(embed=embed)
    play_list.append([song_title, song_url])
    return song_url


async def auto_reply(ctx, msg):
    ka_man = re.search(r'hi|hello|hai|hoy|pota|hayop|cute|makanos|test', msg)
    global to_reply
    if ka_man is not None:
        await ctx.send(ka_man[0] + " ka man")
        to_reply = False
    if to_reply:
        await ctx.send(random.choice(["ge", "bala ka", "oks", ".", "👍"]))
        to_reply = False


@client.event
async def on_message(message):
    msg = message.content.lower()
    if message.author == client.user:
        print("chat:    replied: "+msg)
        return
    global to_reply
    print('chat:    '+str(message.author)[:-5]+': '+msg)  # debugging purposes
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
    await client.process_commands(message)

print("Bot Live")
client.run('ODg4MzYzNDE5NjQ2OTg0MjIy.YURm6A.ajqhThM9Tm05f5ni718vrS9LauA')
