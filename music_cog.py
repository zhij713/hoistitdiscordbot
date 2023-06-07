from ast import alias
import discord
from discord.ext import commands
#from youtube_dl import YoutubeDL
from yt_dlp import YoutubeDL
from googleapiclient.discovery import build
import os

yt_key = os.getenv('YT_KEY')

class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_playing = False
        self.is_paused = False

        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        self.is_looping = False


        self.vc = None
    
    def format_time(self, duration):
        minutes, seconds = divmod(duration, 60)
        return f"{minutes}:{seconds:02d}"


    def query_yt(self, query):
        youtube_api_key = yt_key
        youtube = build('youtube', 'v3', developerKey=youtube_api_key)

        search_response = youtube.search().list(
            part='id',
            q=query,
            type='video',
            maxResults=1,
            fields='items(id(videoId))'
        ).execute()
        

        if 'items' in search_response and search_response['items']:
            video_id = search_response['items'][0]['id']['videoId']
            video_url = f'https://www.youtube.com/watch?v={video_id}'
            return video_url

        return None

    def search_yt(self, item):

        if not item.startswith("https://"):
            item = self.query_yt(item)
        
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            song_info = ydl.extract_info(item, download=False)
            if 'url' not in song_info:
                return False
        #print(f"DUration: {song_info['duration']}")
            return {'source': song_info['url'], 'title':song_info['title'], 'duration': song_info['duration']}
    
    def play_next(self):
        if not self.music_queue:
            self.is_playing = False
            return
        
        if not self.is_looping:
            self.music_queue.pop(0)

        if self.music_queue:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    async def play_music(self, ctx):
        if not self.music_queue:
            self.is_playing = True
            return
        
        self.is_playing = True
        title, duration, source, channel = self.music_queue[0][0]['title'], self.music_queue[0][0]['duration'], self.music_queue[0][0]['source'], self.music_queue[0][1]

        if not self.vc or not self.vc.is_connected():
            self.vc = await self.music_queue[0][1].connect()

            if not self.vc:
                await ctx.send("Could not connect to voice channel")
                self.is_playing = False
                return
        else:
            await self.vc.move_to(channel)

        await ctx.send(f"Now playing {title} - {self.format_time(duration)}")

        while True:
            self.vc.play(discord.FFmpegPCMAudio(source, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
            await asyncio.sleep(duration)

            if not self.is_looping:
                break


    @commands.command(name="play",aliases=["p","playing"], help="Play the selected song from Youtube")
    async def play(self, ctx, *args):
        query = " ".join(args)

        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            await ctx.send("Connect to a voice channel")
        elif self.is_paused:
            self.vc.resume()
        else:
            song = self.search_yt(query)
            if type(song) == type(True):
                await ctx.send("Couldn't get song!")
            else:
                await ctx.send(f"{song['title']} - {self.format_time(song['duration'])} added to queue")
                #await ctx.send("Song added to queue")
                self.music_queue.append([song, voice_channel])

                if self.is_playing == False:
                    await self.play_music(ctx)

    @commands.command(name="pause", help="Pauses the current song")
    async def pause(self, ctx, *args):   
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()

        elif self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()
    
    @commands.command(name="resume", aliases = ["r"],help="Resumes the current song")
    async def resume(self, ctx, *args):  
        if self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()
    
    @commands.command(name="skip",aliases=["s"], help="Skips the current song")
    async def skip(self, ctx, *args):
        if self.vc != None and self.vc:
            self.vc.stop()
        if len(self.music_queue) > 0:
            self.music_queue.pop(0)
        await self.play_music(ctx)

    @commands.command(name="queue",aliases=["q"], help="Displays all songs in queue")
    async def queue(self, ctx):
        retval = ""
        for i in range(0, len(self.music_queue)):
            if i > 4: break
            retval += self.music_queue[i][0]['title'] + '\n'

        if retval != "":
            await ctx.send(retval)
        else:
            await ctx.send("No music in queue")

    @commands.command(name="clear",aliases=["c"], help="Stops song and clears queue")
    async def clear(self, ctx, *args):
        if self.vc != None and self.is_playing:
            self.vc.stop()
        self.music_queue = []
        await ctx.send("Music queue cleared")
    
    @commands.command(name="leave",aliases=["l","disconnect"], help="Kicks bot from VC")
    async def leave(self, ctx):
        self.is_playing = False
        self.is_paused = False
        await self.vc.disconnect()
    
    @commands.command(name="loop", help="Toggle loop mode (usage: *loop or *loop off)")
    async def loop(self, ctx, *args):
        if len(args) > 0 and args[0] == "off":
            self.is_looping = False
            await ctx.send("Looping turned off")
        elif self.is_looping:
            await ctx.send("Looping already turned on")
        else:
            self.is_looping = True
            await ctx.send("Looping turned on")
