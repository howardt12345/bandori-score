# Bot with chat commands

import asyncio
import discord
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions

from dotenv import load_dotenv
import os

import datetime
import logging

from api import ScoreAPI
from db import Database
import bot_commands
import bot_commands_admin
from bot_util_functions import msgLog
from bot_help import *

import sys

# Get token from .env
load_dotenv()
dev = len(sys.argv) > 1 and sys.argv[1] == 'dev'
TOKEN = os.getenv('TOKEN_DEV' if dev else 'TOKEN')

filename = f"{str(datetime.datetime.now()).split('.')[0].replace(':', '-') + ('_dev' if dev else '')}.log"
path = f"{sys.path[0]} + /../logs/{filename}"
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.INFO, filename=path, filemode='a')
logging.getLogger().addHandler(logging.StreamHandler())

if not dev:
  sys.tracebacklimit = 0

# Create bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='$', intents=intents, help_command=None)

# Create API
scoreAPI: ScoreAPI = None
db: Database = None

async def dbCommand(ctx: commands.Context, cmd: any):
  status = await db.ping_server()
  if not status:
    await ctx.send("Unable to access the database")
    return
  else:
    await cmd

# Adds a new score to the user's scores in the database
@bot.command(aliases=commandAliases['newScores'])
async def newScores(ctx: commands.Context, defaultTag: str = "", compare: bool = True):
  msgLog(ctx)
  await dbCommand(ctx, bot_commands.newScores(scoreAPI, bot, db, ctx, compare, defaultTag))

# Gets the user's scores from the database given a query
@bot.command(aliases=commandAliases['getScores'])
async def getScores(ctx: commands.Context, *, query: str = ""):
  msgLog(ctx)
  await dbCommand(ctx, bot_commands.getScores(db, ctx, query))

# Edit a score in the database given an id
@bot.command(aliases=commandAliases['editScore'])
async def editScore(ctx: commands.Context, id: str):
  msgLog(ctx)
  await dbCommand(ctx, bot_commands.editScore(bot, db, ctx, id))

# Deletes a score in the database given an id
@bot.command(aliases=commandAliases['deleteScore'])
async def deleteScore(ctx: commands.Context, id: str):
  msgLog(ctx)
  await dbCommand(ctx, bot_commands.deleteScore(bot, db, ctx, id))

# Lets the user manually input a score
@bot.command(aliases=commandAliases['manualInput'])
async def manualInput(ctx: commands.Context, defaultTag: str = ""):
  msgLog(ctx)
  await dbCommand(ctx, bot_commands.manualInput(bot, db, ctx, defaultTag))

# Gets the user's best scores of categories defined in bestDict
@bot.command(aliases=commandAliases['getBest'])
async def getBest(ctx: commands.Context, songName: str = None, difficulty: str = None, tag: str = "", query: str = ""):
  msgLog(ctx)
  await dbCommand(ctx, bot_commands.getBest(db, ctx, songName, difficulty, tag, query))

# Lists all the songs of the user
@bot.command(aliases=commandAliases['listSongs'])
async def listSongs(ctx: commands.Context, difficulty: str = None, tag: str = "", band: str = "", asFile=False, allPerfect=False):
  msgLog(ctx)
  await dbCommand(ctx, bot_commands.listSongs(db, ctx, difficulty, tag, band, asFile, allPerfect))

# Generates a graph of the user's scores of a song
@bot.command(aliases=commandAliases['getSongStats'])
async def getSongStats(ctx: commands.Context, songName: str = "", difficulty: str = "", tag: str = "", matchExact = False, showMaxCombo = True, showSongNames = False, interpolate = False):
  msgLog(ctx)
  await dbCommand(ctx, bot_commands.getSongStats(db, ctx, songName, difficulty, tag, matchExact, showMaxCombo, showSongNames, interpolate))

# Get the user's most recent song(s)
@bot.command(aliases=commandAliases['getRecent'])
async def getRecent(ctx: commands.Context, limit: int = 1, tag: str = ""):
  msgLog(ctx)
  await dbCommand(ctx, bot_commands.getRecent(db, ctx, limit, tag))

# Compares the user's score to the user's best score of the song
@bot.command(aliases=commandAliases['compare'])
async def compare(ctx: commands.Context, id: str):
  msgLog(ctx)
  await dbCommand(ctx, bot_commands.compare(db, ctx, id))

# Edits the score's tag in the database given an id
@bot.command(aliases=commandAliases['tagScore'])
async def tagScore(ctx: commands.Context, id: str, tag: str = ""):
  msgLog(ctx)
  await dbCommand(ctx, bot_commands.tagScore(bot, db, ctx, id, tag))

# Gets a song's information from the Bestdori API
@bot.command(aliases=commandAliases['bestdoriGet'])
async def bestdoriGet(ctx: commands.Context, *, query: str = ""):
  db.initBestdori()
  msgLog(ctx)
  await bot_commands.bestdoriGet(db, ctx, query)

# Help command
@bot.command()
async def help(ctx: commands.Context, command: str = ""):
  msgLog(ctx)
  await bot_commands.help(ctx, command)

# About TP command
@bot.command(aliases=commandAliases['aboutTP'])
async def aboutTP(ctx: commands.Context):
  msgLog(ctx)
  await bot_commands.aboutTP(ctx)

# Admin commands

@bot.command()
@has_permissions(administrator=True)
async def version(ctx: commands.Context, version: str, ping: bool = False):
  msgLog(ctx)
  await bot_commands_admin.version(ctx, version, ping)

@bot.command()
@has_permissions(administrator=True)
async def announcements(ctx: commands.Context, ping: bool = False):
  msgLog(ctx)
  await bot_commands_admin.announcements(ctx, ping)

@bot.command()
@has_permissions(administrator=True)
async def ping(ctx: commands.Context):
  msgLog(ctx)
  await ctx.send("Pong!")
  dbStatus = await db.ping_server()
  await ctx.send(f"Database: {'Connected' if dbStatus else 'Disconnected'}")

async def main():
  logging.info("Starting bot")
  global scoreAPI
  scoreAPI = ScoreAPI(draw=True)
  global db
  db = Database()
  # For some reason the bot logs twice after loading extensions
  await bot.load_extension("cogs.daily_reset")
  await bot.start(TOKEN)

if __name__ == '__main__':
  asyncio.run(main())