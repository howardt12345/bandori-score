# Bot with chat commands

import discord
from discord.ext import commands

from dotenv import load_dotenv
import os

from api import ScoreAPI
from db import Database
import bot_commands
from bot_util_functions import msgLog
from bot_help import *

import sys

# Get token from .env
load_dotenv()
TOKEN = os.getenv('TOKEN_DEV' if len(sys.argv) > 1 and sys.argv[1] == 'dev' else 'TOKEN')

# Create bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='$', intents=intents, help_command=None)

# Create API
scoreAPI = ScoreAPI(draw=True)
db = Database()

@bot.command(aliases=commandAliases['newScores'])
async def newScores(ctx: commands.Context, defaultTag: str = "", compare: bool = True):
  msgLog(ctx)
  await bot_commands.newScores(scoreAPI, bot, db, ctx, compare, defaultTag)

@bot.command(aliases=commandAliases['getScores'])
async def getScores(ctx: commands.Context, *, query: str = ""):
  msgLog(ctx)
  await bot_commands.getScores(db, ctx, query)

@bot.command(aliases=commandAliases['editScore'])
async def editScore(ctx: commands.Context, id: str):
  msgLog(ctx)
  await bot_commands.editScore(bot, db, ctx, id)

@bot.command(aliases=commandAliases['deleteScore'])
async def deleteScore(ctx: commands.Context, id: str):
  msgLog(ctx)
  await bot_commands.deleteScore(bot, db, ctx, id)

@bot.command(aliases=commandAliases['manualInput'])
async def manualInput(ctx: commands.Context, defaultTag: str = ""):
  msgLog(ctx)
  await bot_commands.manualInput(bot, db, ctx, defaultTag)

@bot.command(aliases=commandAliases['getHighest'])
async def getHighest(ctx: commands.Context, songName: str = None, difficulty: str = None, tag: str = "", query: str = ""):
  msgLog(ctx)
  await bot_commands.getHighest(db, ctx, songName, difficulty, tag, query)

@bot.command(aliases=commandAliases['listSongs'])
async def listSongs(ctx: commands.Context, difficulty: str = None, tag: str = "", asFile=False):
  msgLog(ctx)
  await bot_commands.getSongCounts(db, ctx, difficulty, tag, asFile)

@bot.command(aliases=commandAliases['getSongStats'])
async def getSongStats(ctx: commands.Context, songName: str = None, difficulty: str = None, tag: str = "", matchExact = False, showMaxCombo = True, showSongNames = False, interpolate = False):
  msgLog(ctx)
  await bot_commands.getSongStats(db, ctx, songName, difficulty, tag, matchExact, showMaxCombo, showSongNames, interpolate)

@bot.command(aliases=commandAliases['getRecent'])
async def getRecent(ctx: commands.Context, limit: int = 1, tag: str = ""):
  msgLog(ctx)
  await bot_commands.getRecent(db, ctx, limit, tag)

@bot.command(aliases=commandAliases['bestdoriGet'])
async def bestdoriGet(ctx: commands.Context, *, query: str = ""):
  msgLog(ctx)
  await bot_commands.bestdoriGet(db, ctx, query)

@bot.command()
async def help(ctx: commands.Context, command: str = ""):
  msgLog(ctx)
  await bot_commands.help(ctx, command)

bot.run(TOKEN)
