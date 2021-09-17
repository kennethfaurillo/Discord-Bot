import discord
import re

client = discord.Client()


@client.event
async def on_message(message):
    msg = message.content.lower()
    if message.author == client.user:
        return
    print(message.author, msg) # debugging purposes
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

    # Auto replies lol
    ka_man = re.search(r'hi|hello|hoy|pota|hayop|cute|makanos|test|mama mo', msg)
    if ka_man is not None:
        print(ka_man[0] + " ka man")
        await message.channel.send(ka_man[0] + " ka man")


client.run('ODg4MzYzNDE5NjQ2OTg0MjIy.YURm6A.se-nXYyhTAxzM1r7dlXYQe_H2pM')
