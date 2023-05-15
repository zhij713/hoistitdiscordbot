import discord
from discord.ext import commands

class help_cog(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.help_message = """
        ```
        *play: Adds music to queue (must be YT link)\n
        *pause: Pauses music (or resumes if already paused)\n
        *resume: Resumes current song\n
        *skip: Skips current song\n
        *queue: Shows all songs in queue\n
        *clear: Stops song and clears queue\n
        *leave: Kicks bot out out VC
        ```
        """
        self.text_channel_text = []

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                self.text_channel_text.append(channel)
        
        await self.send_to_all(self.help_message)

    async def send_to_all(self, msg):
        for text_channel in self.text_channel_text:
            await text_channel.send(msg)
    
    @commands.command(name="help",help="DIsplays all avail commands")
    async def help(self, ctx):
        await ctx.send(self.help_message)