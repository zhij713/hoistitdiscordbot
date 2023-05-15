
import discord
from discord.ext import commands
import os

inty = discord.Intents.default()
inty.message_content = True

bot = commands.Bot(command_prefix="*",intents=inty)
bot.remove_command("help")
from help_cog import help_cog
from music_cog import music_cog

@bot.event
async def on_ready():
    await bot.add_cog(help_cog(bot))
    await bot.add_cog(music_cog(bot))

token = os.getenv('DISCORD_TOKEN')
bot.run(token)