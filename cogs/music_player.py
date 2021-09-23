import asyncio
import discord
import random
from discord.ext import commands
from youtube_dl import YoutubeDL
from cogs.ytsearch import yt_search


class MusicPlayer(commands.Cog):
    ffmpeg_opts = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 3', 'options': '-vn'}
    guild_tracker = {}  # 'guild_id': {'name': '', 'pl': []}}
    queue_chunk_size = 20

    def __init__(self, client):
        self.client = client

    def song_done_check(self, ctx):
        coro = self.song_done(ctx)
        fut = asyncio.run_coroutine_threadsafe(coro, self.client.loop)
        try:
            fut.result()
        except:
            print('nag error')

    async def song_done(self, ctx):
        print('tapos na po')
        await self.play(ctx, autoplay=True)

    @commands.command(name="Join", brief="    -    `join", aliases=['join'])
    async def join(self, ctx):
        if ctx.author.voice is None:
            await ctx.send('bruh join ka muna voice channel lol')
            return None

        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await voice_channel.connect()
        else:
            await ctx.voice_client.move_to(voice_channel)
        return ctx.voice_client

    def add_to_tracker(self, ctx):
        if ctx.guild.id not in self.guild_tracker:
            print("adding", ctx.guild.id, 'to tracker')
            self.guild_tracker[ctx.guild.id] = {'name': str(ctx.guild), 'pl': [], 'np': ''}
        else:
            print(self.guild_tracker[ctx.guild.id]['name'], 'already in tracker')
            pass

    async def play_helper(self, ctx, watch_url):
        voice = ctx.voice_client
        try:
            song_url = YoutubeDL().extract_info(watch_url, download=False)['formats'][0]['url']
            voice.play(await discord.FFmpegOpusAudio.from_probe(song_url, **self.ffmpeg_opts),
                       after=lambda _: self.song_done_check(ctx))
            embed = discord.Embed(title=f'Now Playing:    {self.guild_tracker[ctx.guild.id]["np"]}')
            await ctx.send(embed=embed)
        except discord.errors.ClientException:
            await ctx.send('wait lang')
            pass

    @commands.command(name="Play", brief="    -    `p | `play", aliases=["play", 'p', 'P'])
    async def play(self, ctx, *args, autoplay=False):
        self.add_to_tracker(ctx)
        voice = await self.join(ctx)
        if not voice:
            return
        if not autoplay:
            if args:  # Song keyword/link given
                if not self.guild_tracker[ctx.guild.id]['pl'] and not self.guild_tracker[ctx.guild.id]['np']:
                    queue_check = await self.queue(ctx, *args, no_message=True, from_play=True)
                else:
                    queue_check = await self.queue(ctx, *args, no_message=False, from_play=True)
                if not queue_check or voice.is_playing():  # possible bug
                    return
            else:  # just `play
                if not self.guild_tracker[ctx.guild.id]['pl'] and not self.guild_tracker[ctx.guild.id]['np']:
                    await ctx.send("ano man ipplay ko")
                    return
                if not autoplay:  # possible bug
                    if voice.is_paused():
                        print('resume via play')
                        await self.resume(ctx)
                        return
                    elif voice.is_playing():
                        await ctx.send("nagpplay na baga")
                        return

        # Allow ffmpeg to reconnect
        try:
            self.guild_tracker[ctx.guild.id]['np'], song_url = self.guild_tracker[ctx.guild.id]['pl'].pop(0)
        except IndexError:
            self.guild_tracker[ctx.guild.id]['np'] = ''
            print('ubos na playlist')
            await self.timeout(ctx, 30)
            return
        await self.play_helper(ctx, song_url)

    async def queue_helper(self, ctx, to_queue, no_message, pl_name=None, from_play=False):
        is_playlist = bool(pl_name)
        if is_playlist:
            embed = discord.Embed(title=f"Added {len(to_queue['titles'])} songs to queue from {pl_name} playlist")
            await ctx.send(embed=embed)
        for idx, (song_title, watch_url) in enumerate(zip(to_queue['titles'], to_queue['watch_urls'])):
            if pl_name and not idx:
                if ctx.voice_client and from_play:
                    self.guild_tracker[ctx.guild.id]['np'] = song_title
                    await self.play_helper(ctx, watch_url)
                    continue
            self.guild_tracker[ctx.guild.id]['pl'].append([song_title, watch_url])
            if not is_playlist:
                await ctx.send(watch_url, delete_after=7.5)
            if not is_playlist and not no_message:
                embed = discord.Embed(title=f"Added:    {song_title} to queue")
                await ctx.send(embed=embed)

    @commands.command(name='Queue', brief="    -    `q | `queue ", aliases=['queue', 'q'])
    async def queue(self, ctx, *args, no_message=False, from_play=False):
        self.add_to_tracker(ctx)
        keywords = ' '.join(args)
        voice = ctx.voice_client
        if not keywords.strip():  # Show the queue
            pl_size = len(self.guild_tracker[ctx.guild.id]['pl'])
            queue_chunks_temp = divmod(pl_size, self.queue_chunk_size)
            queue_chunks_count = queue_chunks_temp[0] + bool(queue_chunks_temp[1])*1
            embeds = []
            for queue_chunk in range(queue_chunks_count):
                start = queue_chunk * self.queue_chunk_size
                end = start + self.queue_chunk_size
                songs = ''
                for idx, x in enumerate(self.guild_tracker[ctx.guild.id]['pl'][start: end]):
                    songs += (str(start + idx + 1) + ':    ' + x[0] + '\n')
                if voice and (voice.is_playing() or voice.is_paused()):
                    title = f"Now Playing:    {self.guild_tracker[ctx.guild.id]['np']}"
                    embeds.append(discord.Embed(title=title, description=songs))
                else:
                    embeds.append(discord.Embed(description=songs))
                if queue_chunk == range(queue_chunks_count)[-1]:
                    break
            else:
                await ctx.send(embed=discord.Embed(title="uda na kanta"))

            for embed in embeds:
                await ctx.send(embed=embed)

            return
        else:  # Add to queue
            if 'youtube.com/playlist?' in keywords:     # Playlist
                keywords_check = keywords.split()
                search_args = {'pl_id': keywords_check[0][-34:]}
            else:
                search_args = {'keyword': keywords}
            to_queue, pl_name = await yt_search(**search_args)
            if not to_queue:
                await ctx.send("sowi di ko mahanap 😢")
                return False
            print(to_queue)
            await self.queue_helper(ctx, to_queue, no_message, pl_name, from_play)
            return True

    def keyword_to_index(self, keyword, ctx):
        lower_case_titles = [x[0].lower() for x in self.guild_tracker[ctx.guild.id]['pl']]
        keyword = keyword.lower()
        for idx, lower_case_title in enumerate(lower_case_titles):
            if keyword in lower_case_title:
                return idx + 1
        else:
            return keyword

    @commands.command(name='Move', brief="    -    `mv | `move", aliases=['move', 'mv'])
    async def move(self, ctx, source_index, dest_index):
        if not source_index.isdigit():  # keyword is given
            source_index = self.keyword_to_index(source_index, ctx)
            if not type(source_index) == int:
                await ctx.send(f"uda man {source_index}")
                return
        if not dest_index.isdigit():  # keyword is given
            dest_index = self.keyword_to_index(dest_index, ctx)
            if not type(dest_index) == int:
                await ctx.send(f"uda man {dest_index}")
                return
        source_index, dest_index = int(source_index), int(dest_index)
        if source_index == dest_index or (max(int(source_index), int(dest_index)) > len(self.guild_tracker[ctx.guild.id]['pl'])):
            await ctx.send("???")
            return
        try:
            song_to_move = self.guild_tracker[ctx.guild.id]['pl'].pop(int(source_index)-1)
            self.guild_tracker[ctx.guild.id]['pl'].insert(int(dest_index)-1, song_to_move)
            embed = discord.Embed(title=f"Moved {song_to_move[0]} to {dest_index}")
            await ctx.send(embed=embed)
        except IndexError:
            await ctx.send("bug")

    async def timeout(self, ctx, secs=30):
        await asyncio.sleep(secs)
        voice = ctx.voice_client
        if not voice.is_paused() and not voice.is_playing():
            try:
                self.guild_tracker.pop(ctx.guild.id)
            except KeyError:
                raise
            await self.leave(ctx)

    @commands.command(name='Leave', brief="    -    `leave | `disconnect", aliases=['leave', 'disconnect'])
    async def leave(self, ctx):
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if voice:
            self.guild_tracker[ctx.guild.id]['pl'] = []
            self.guild_tracker[ctx.guild.id]['np'] = ''
            await voice.disconnect()
            await ctx.send("kbye")

    @commands.command(name='Pause', brief="    -    `pause ", aliases=['pause'])
    async def pause(self, ctx):
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if not voice:
            await ctx.send("ano man ipapause ko")
        if voice.is_paused():
            await ctx.send("naka pause na baga")
            return
        elif voice.is_playing():
            voice.pause()
            embed = discord.Embed(title=f"Paused:    {self.guild_tracker[ctx.guild.id]['np']}")
            await ctx.send(embed=embed)

    @commands.command(name='Resume', brief="    -    `resume | `res ", aliases=['resume', 'res'])
    async def resume(self, ctx):
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if not voice:
            await ctx.send("ano man ireresume ko")
        if voice.is_paused():
            voice.resume()
            await self.nowplaying(ctx)
        elif voice.is_playing():
            await ctx.send("nag pplay na baga")
        else:
            print('bug')

    @commands.command(name='Skip', brief="    -    `skip | `s", aliases=['skip', 's'])
    async def skip(self, ctx, *args, message=True):
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if voice and (voice.is_playing() or voice.is_paused()):
            if message:
                embed = discord.Embed(title=f"Skipping {self.guild_tracker[ctx.guild.id]['np']}")
                await ctx.send(embed=embed)
            voice.stop()
        else:
            await ctx.send("ano isskip ko")

    @commands.command(name='Jump', brief="    -    `j | `jump | `goto", aliases=['jump', 'goto', 'j'])
    async def jump(self, ctx, song_index=''):
        if song_index == '':
            await ctx.send("gib number plx")
            return
        try:
            if not song_index.isdigit():                            # keyword is given
                lower_case_titles = [x[0].lower() for x in self.guild_tracker[ctx.guild.id]['pl']]
                song_index = song_index.lower()
                for idx, lower_case_title in enumerate(lower_case_titles):
                    if song_index in lower_case_title:
                        song_index = idx + 1
                        break
            voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
            self.guild_tracker[ctx.guild.id]['pl'] = self.guild_tracker[ctx.guild.id]['pl'][int(song_index) - 1:]
            embed = discord.Embed(title="Skipping to " + self.guild_tracker[ctx.guild.id]['pl'][0][0])
            await ctx.send(embed=embed)
            if voice:
                await self.skip(ctx, False)
        except IndexError:
            await ctx.send("uda man " + song_index)

    @commands.command(name="Now Playing", brief="    -    `np | `NP  ", aliases=['np', 'NP'])
    async def nowplaying(self, ctx):
        embed = discord.Embed(title=f"Now Playing:    {self.guild_tracker[ctx.guild.id]['np']}")
        await ctx.send(embed=embed, delete_after=7.5)

    @commands.command(name="Remove", brief="    -    `remove | `r  ", aliases=['remove', 'r', 'R'])
    async def remove(self, ctx, song_index=''):
        if song_index == '':
            await ctx.send("???")
        try:
            if not song_index.isdigit():  # keyword is given
                if song_index.lower() in self.guild_tracker[ctx.guild.id]['np'].lower():
                    await ctx.send("cannot remove nagpplay, baka skip?")
                    return
                song_index = self.keyword_to_index(song_index, ctx)
            song_removed = self.guild_tracker[ctx.guild.id]['pl'].pop(int(song_index) - 1)[0]
            embed = discord.Embed(title="Removed " + song_removed)
            await ctx.send(embed=embed)
        except (ValueError, IndexError):
            await ctx.send("uda man " + song_index)

    @commands.command(name="Clear", brief="    -    `clear", aliases=['clear'])
    async def clear(self, ctx):
        self.guild_tracker[ctx.guild.id]['pl'].clear()
        embed = discord.Embed(title="Cleared queue")
        await ctx.send(embed=embed)

    @commands.command(name="Shuffle", brief="    -    `shuffle", aliases=['shuffle'])
    async def shuffle(self, ctx):
        if not self.guild_tracker[ctx.guild.id]['pl']:
            await ctx.send("uda man play list")
        random.shuffle(self.guild_tracker[ctx.guild.id]['pl'])
        embed = discord.Embed(title="Queue shuffled")
        await ctx.send(embed=embed)

    @commands.command(name="Commands", brief="    -    Shows this message", aliases=['commands'])
    async def _commands(self, ctx):
        await ctx.send_help()

    @commands.command(name="Servers", brief="    -    Shows the servers the bot is currently playing for", aliases=['servers'])
    async def _servers(self, ctx):
        if not len(self.guild_tracker):
            await ctx.send(embed=discord.Embed(title="wala"))
        else:
            servers = ''
            for server in self.guild_tracker.values():
                servers += server['name'] + '\n'
            await ctx.send(embed=discord.Embed(description=servers))

    @commands.Cog
    async def on_ready(self):
        print(str(self.client.user) + " Live")


def setup(client):
    client.add_cog(MusicPlayer(client))
