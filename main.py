import discord
import re
import youtube_dl
import os
from discord import ClientException
from ytsearch import yt_search
import time
import random
from discord.ext import commands


play_status = 0 # 0 - stopped/no song, 1 - playing, 2 - paused
to_reply = False

# client = discord.Client()
client = commands.Bot(command_prefix='`')

@client.command()
async def play(ctx, *args):
    song_dir = os.path.abspath(os.getcwd()) + "\\songs"
    keyword = ' '.join(args)
    if not keyword.strip(' '):
        global play_status
        if play_status == 2:
            await resume(ctx)
            return
        await ctx.send("ha ano ipplay ko?")
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

    start = time.time()
    song_url = yt_search(keyword)
    print(time.time() - start)
    await ctx.send(song_url)

    print(song_url)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'songs/%(id)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        if os.path.isfile(song_dir+"\\"+song_url[-11:]+'.mp3'):
            print('local copy found!')
        else:
            await ctx.send('wait lang nag ddownload pa')
            ydl.download([song_url])
            await ctx.channel.purge(limit=1)
    play_status = 1
    # add try except, if except, add to queue
    voice.play(discord.FFmpegPCMAudio(song_dir+"\\"+song_url[-11:]+'.mp3'), after=print("tapos na po"))


@client.command()
async def leave(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice:
        await voice.disconnect()
        await ctx.send("kbye")


@client.command()
async def pause(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
        global play_status
        play_status = 2
    else:
        await ctx.send("nothing's playing")


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


@client.event
async def on_message(message):
    msg = message.content.lower()
    ctx = await client.get_context(message)
    if message.author == client.user:
        return
    global to_reply
    print('message',message.author, msg)  # debugging purposes
    if msg.startswith('<@!888363419646984222>'):
        if re.search(r'delete', msg):
            await message.channel.purge(limit=2)
            return
        if msg.endswith('<@!888363419646984222>'):
            reply = random.choice(["ano", "op", "yo", "?", "nukaman", "👋"])
            if str(message.author) == "kennethfau#9317":
                reply = "ano po boss"
            else:
                reply += ' ' + str(message.author)[:-5]
            to_reply = True
        else:
            reply = 'oks'
        await message.channel.send(reply)
        return

    # Auto replies lol
    ka_man = re.search(r'hi|hello|hai|hoy|pota|hayop|cute|makanos|test', msg)
    if ka_man is not None:
        print(ka_man[0] + " ka man")
        await message.channel.send(ka_man[0] + " ka man")
        to_reply = False
    if to_reply:
        await message.channel.send(random.choice(["ge", "bala ka", "oks", ".", "👍"]))
        to_reply = False
    await client.process_commands(message)


client.run('ODg4MzYzNDE5NjQ2OTg0MjIy.YURm6A.ajqhThM9Tm05f5ni718vrS9LauA')
