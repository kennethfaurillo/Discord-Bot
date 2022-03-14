import os
import discord
import re
import random
from discord.ext import commands
from datetime import datetime
from keep_alive import keep_alive

client = commands.Bot(command_prefix="`", activity=discord.Game(name="dead"))
guild_tracker = {'id': {}}

async def auto_reply(ctx, msg):
    if msg.startswith("`say"): return
    ka_man = re.search(r'\b(hi|hello|hai|hoy|pota|hayop|cute|magayon|pogi|gwapo|makanos|chaka|test|patal|bahala|bala|madats)\b', msg)
    if ka_man is not None:
        await ctx.send(ka_man[0] + " ka man")
        guild_tracker[ctx.guild.id]['to_reply'] = False
    if guild_tracker[ctx.guild.id]['to_reply']:
        await ctx.send(random.choice(["ge", "bala ka", "oks", ".", "👍"]))
        guild_tracker[ctx.guild.id]['to_reply'] = False

def guild_check():
    for guild in client.guilds:
      guild_tracker[guild.id] = {'to_reply': False}

async def nikko_check(ctx, msg):
  if str(msg.author) == "Zoldyck#8583":
    await ctx.send("boto mo " + "<@" + str(msg.author.id) + ">")
    
def log(message):
  with open("log.txt", 'a') as f:
      f.write(message + '\n')

@client.event
async def on_ready():
    for guild in client.guilds:
        guild_tracker[guild.id] = {'to_reply': False}
    print(str(client.user) + " Live")
    log("\n" + str(client.user) + " Live\n")

@client.event
async def on_message(message):
    print(datetime.now().strftime(r"%I:%M %p"))
    print(str(message.author.guild) + ': ' + str(message.author)[:-5] + ': ' + message.content)  # debugging purposes
    guild_check()
    log(str(message.author.guild) + '@' + datetime.now().strftime(r"%I:%M %p") + ": " + str(message.author) + ': ' + message.content)
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
    # await nikko_check(await client.get_context(message), message)
    await client.process_commands(message)

      
client.load_extension(f"cogs.{'music_player'}")
keep_alive()
client.run(os.getenv("TOKEN"))
