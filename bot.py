# Bot with chat commands

from io import BytesIO
import discord
from discord.ext import commands
import asyncio

from dotenv import load_dotenv
import os

import cv2
import numpy as np

from api import ScoreAPI
from db import Database
from consts import tags
import bot_commands
from bot_util_functions import msgLog

# Get token from .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Create bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='$', intents=intents)

# Create API
scoreAPI = ScoreAPI(draw=True)
db = Database()

@bot.command()
async def newScores(ctx: commands.Context, defaultTag: str = "", compare: bool = True):
  msgLog(ctx)
  await bot_commands.newScores(scoreAPI, bot, db, ctx, compare, defaultTag)

@bot.command()
async def getScores(ctx: commands.Context, *, query: str = ""):
  msgLog(ctx)
  await bot_commands.getScores(db, ctx, query)

@bot.command()
async def editScore(ctx: commands.Context, id: str):
  msgLog(ctx)
  await bot_commands.editScore(bot, db, ctx, id)

@bot.command()
async def deleteScore(ctx: commands.Context, id: str):
  msgLog(ctx)
  await bot_commands.deleteScore(bot, db, ctx, id)

@bot.command()
async def manualInput(ctx: commands.Context, defaultTag: str = ""):
  msgLog(ctx)
  await bot_commands.manualInput(bot, db, ctx, defaultTag)

@bot.command()
async def getHighest(ctx: commands.Context, songName: str = None, difficulty: str = None, tag: str = "", query: str = ""):
  msgLog(ctx)
  await bot_commands.getHighest(db, ctx, songName, difficulty, tag, query)

@bot.command()
async def getSongCounts(ctx: commands.Context, difficulty: str = None, tag: str = ""):
  msgLog(ctx)
  await bot_commands.getSongCounts(db, ctx, difficulty, tag)

@bot.command()
async def getSongStats(ctx: commands.Context, songName: str = None, difficulty: str = None, tag: str = ""):
  msgLog(ctx)
  await bot_commands.getSongStats(db, ctx, songName, difficulty, tag)

bot.run(TOKEN)
