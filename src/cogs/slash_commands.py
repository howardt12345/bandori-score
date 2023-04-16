import logging
from discord import app_commands
import discord
from discord.ext import commands

class Slash(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  # test command
  @app_commands.command(name="test", description="test command")
  async def test(self, interaction: discord.Interaction):
    await interaction.response.send_message("test")

async def setup(bot):
  await bot.add_cog(Slash(bot))