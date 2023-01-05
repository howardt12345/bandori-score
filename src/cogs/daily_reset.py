import datetime
from discord.ext import commands, tasks
import logging
from bot import db

utc = datetime.timezone.utc
times = [
  datetime.time(hour=1, minute=1, tzinfo=utc),
]

class MyCog(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.my_task.start()

  def cog_unload(self):
    self.my_task.cancel()

  @tasks.loop(time=times)
  async def my_task(self):
    logging.info("Updating database")
    db.initBestdori()

async def setup(bot):
  await bot.add_cog(MyCog(bot))