import os
import re
import random
import asyncio
import discord
import logging
from dotenv import load_dotenv
from discord.ext import commands
from datetime import datetime
import time    
epoch_time = int(time.time())
import music_player

load_dotenv()

intents = discord.Intents.all()
client = commands.Bot(command_prefix="`", activity=discord.Game(name="dead"), intents=intents)
guild_tracker = {'id': {}}
handler = logging.FileHandler(filename=r'logs/discord'+str(int(time.time()))+'.log', encoding='utf-8', mode='w')
discord.utils.setup_logging(handler=handler, level=logging.DEBUG)

async def auto_reply(ctx, msg):
    ka_man = re.search(r'\b(hi|hello|hai|hoy|pota|hayop|cute|magayon|pogi|gwapo|makanos|chaka|test|patal|bahala|bala)\b', msg)
    if ka_man is not None:
        await ctx.send(ka_man[0] + " ka man")
        guild_tracker[ctx.guild.id]['to_reply'] = False
    if guild_tracker[ctx.guild.id]['to_reply']:
        await ctx.send(random.choice(["ge", "bala ka", "oks", ".", "👍"]))
        guild_tracker[ctx.guild.id]['to_reply'] = False

def guild_check():
    for guild in client.guilds:
      guild_tracker[guild.id] = {'to_reply': False}


@client.event
async def on_ready():
    for guild in client.guilds:
        guild_tracker[guild.id] = {'to_reply': False}
    print(str(client.user) + " Live")


@client.event
async def on_message(message):
    print(datetime.now().strftime(r"%I:%M %p"))
    print(str(message.author.guild) + ': ' + str(message.author)[:-5] + ': ' + message.content)  # debugging purposes
    guild_check()
    msg = message.content.lower()
    if message.author == client.user:
        return
    if msg.startswith('<@!888363419646984222>'):
        if re.search(r'delete', msg):
            await message.channel.purge(limit=2)
            return
        if msg.endswith('<@!888363419646984222>'):
            reply = random.choice(["ano", "op", "yo", "?", "nukaman", "👋"])
            if str(message.author) == "kennethfau#9316":
                reply = "ano po boss"
            else:
                reply += ' ' + "<@" + str(message.author.id) + ">"
            guild_tracker[message.author.guild.id]['to_reply'] = True
        else:
            reply = random.choice(['oks', 'ge', 'ah'])
        await message.channel.send(reply)
        return
    await auto_reply(await client.get_context(message), msg)
    await client.process_commands(message)


async def start_bot():
    async with client:
        await client.add_cog(music_player.MusicPlayer(client))
        await client.start(os.getenv("TOKEN"))

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(start_bot())