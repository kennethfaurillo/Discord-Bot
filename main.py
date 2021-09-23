import os
import discord
import re
import random
from discord.ext import commands

client = commands.Bot(command_prefix="`")
guild_tracker = {'id': {}}


async def auto_reply(ctx, msg):
    ka_man = re.search(r'\bhi|hello|hai|hoy|pota|hayop|cute|magayon|pogi|gwapo|makanos|chaka|test|patal\b', msg)
    if ka_man is not None:
        await ctx.send(ka_man[0] + " ka man")
        guild_tracker[ctx.guild.id]['to_reply'] = False
    if guild_tracker[ctx.guild.id]['to_reply']:
        await ctx.send(random.choice(["ge", "bala ka", "oks", ".", "👍"]))
        guild_tracker[ctx.guild.id]['to_reply'] = False


@client.event
async def on_ready():
    for guild in client.guilds:
        guild_tracker[guild.id] = {'to_reply': False}
    print(str(client.user) + " Live")


@client.event
async def on_message(message):
    print('chat:    ' + str(message.author)[:-5] + ': ' + message.content)  # debugging purposes

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

client.load_extension(f"cogs.{'music_player'}")

client.run(os.getenv("TOKEN"))
