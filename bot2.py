# Bot with chat commands

from io import BytesIO
import discord
from discord.ext import commands

from dotenv import load_dotenv
import os

import cv2
import numpy as np

from api import ScoreAPI

# Get token from .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Create bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='$', intents=intents)

# Create API
scoreAPI = ScoreAPI()

@bot.command()
async def newScore(ctx: commands.Context):
  await ctx.send('Processing scores...')
  files = ctx.message.attachments
  for file in files:
    fp = BytesIO()
    await file.save(fp)

    image_np = np.frombuffer(fp.read(), np.uint8)
    img = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

    output = scoreAPI.basicOutput(img)
    await ctx.send(output)

bot.run(TOKEN)