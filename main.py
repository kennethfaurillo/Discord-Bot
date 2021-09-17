import discord
import re
import youtube_dl
import os
from discord import ClientException

from ytsearch import yt_search
from discord.ext import commands

# client = discord.Client()
client = commands.Bot(command_prefix='`')


@client.command()
async def play(ctx, keyword=''):
    if not keyword.strip(' '):
        await ctx.send("ha ano ipplay ko?")
        return
    try:
        voice_channel = ctx.author.voice.channel
    except AttributeError:
        await ctx.send('bruh join ka muna voice channel lol')
        return
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    await ctx.channel.send(yt_search(keyword))  # message.channel.send("bruh")
    print(voice_channel)
    if not voice:
        await voice_channel.connect()
    # except ClientException:
    #     print('Already Connected!')
    print('oks')


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
    else:
        await ctx.send("nothing's playing")


@client.command()
async def resume(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_paused():
        voice.resume()
    else:
        await ctx.send("audio is not paused")

@client.command()
async def stop(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    voice.stop()

@client.event
async def on_message(message):
    msg = message.content.lower()
    ctx = await client.get_context(message)
    if message.author == client.user:
        return
    print('message',message.author, msg)  # debugging purposes
    if msg.startswith('<@!888363419646984222>'):
        if re.search(r'delete', msg):
            await message.channel.purge(limit=2)
            return
        if msg.endswith('<@!888363419646984222>'):
            reply = "ano "
            if str(message.author) == "kennethfau#9316":
                reply += "po boss"
            else:
                reply += str(message.author)[:-5]
            await message.channel.send(reply)
        msg = msg.split()
        # PLAY command start
        if msg[1] in ['p', 'play']:
            await play(ctx, ' '.join(msg[2:]))
        # PLAY command end
    await client.process_commands(message)




    # Auto replies lol
    ka_man = re.search(r'hi|hello|hai|hoy|pota|hayop|cute|makanos|test', msg)
    if ka_man is not None:
        print(ka_man[0] + " ka man")
        await message.channel.send(ka_man[0] + " ka man")


client.run('ODg4MzYzNDE5NjQ2OTg0MjIy.YURm6A.ajqhThM9Tm05f5ni718vrS9LauA')
