# Bot with chat commands

from io import BytesIO
import discord
from discord.ext import commands
import asyncio

from dotenv import load_dotenv
import os

import cv2
import numpy as np

from api import ScoreAPI, SongInfo
from functions import songInfoToStr, confirmSongInfo, promptTag
from db import Database
from consts import tags

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
async def newScore(ctx: commands.Context):
  user = ctx.message.author

  # Get all the attachments
  files = ctx.message.attachments

  await ctx.send(f'Processing scores of {len(files)} song(s)...')

  for x, file in enumerate(files):
    await ctx.send(f'Starting song {x+1}/{len(files)}...')
    # Get the file
    fp = BytesIO()
    await file.save(fp)
    # Get a file that the API can use
    image_np = np.frombuffer(fp.read(), np.uint8)
    img = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

    # Get the song info
    output = scoreAPI.getSongInfo(img)
    tag = tags[0]

    # Display the song info to the user and wait for a response
    fp.seek(0)

    msgText = f'Song {x+1}/{len(files)}:\n'
    msgText += f'```{songInfoToStr(output)}```'
    msgText += 'React with ✅ to save the song to the database\n'
    msgText += f'React with ☑️ to add a tag to the song before saving (`{tag}` by default)\n'
    msgText += 'React with 📝 to edit the song info\n'
    msgText += 'React with ❌ to discard the song\n'
    message = await ctx.send(msgText, file=discord.File(BytesIO(cv2.imencode('.jpg', img)[1]), filename=file.filename, spoiler=file.is_spoiler()))

    await message.add_reaction('✅')
    await message.add_reaction('☑️')
    await message.add_reaction('📝')
    await message.add_reaction('❌')

    def check(reaction, user):
      return user == ctx.author and str(reaction.emoji) in ['✅', '☑️', '📝', '❌']

    # Wait for user to react
    try:
      reaction, _ = await bot.wait_for('reaction_add', timeout=60.0, check=check)
    except asyncio.TimeoutError:
      output = None
      await ctx.send('Timed out')
    else:
      if str(reaction.emoji) == '✅':
        # Add to database
        pass
      elif str(reaction.emoji) == '☑️':
        # Add tag
        tag = await promptTag(bot, ctx)
        pass
      elif str(reaction.emoji) == '📝':
        # Have user confirm song info
        output = await confirmSongInfo(bot, ctx, output)
        pass
      elif str(reaction.emoji) == '❌':
        # Ignore
        output = None
        await ctx.send('Discarded')
        pass

    if not output is None:
      db.create_song(str(user.id), output, tag)
      await ctx.send(f'({output.difficulty}) {output.songName} with a score of {output.score} added to database')
    print(output)

  await ctx.send(f'Done processing scores of {len(files)} song(s)!')


@bot.command()
async def getScores(ctx: commands.Context, *, query: str):
  user = ctx.message.author
  if not query:
    scores = db.get_songs(str(user.id))
  else:
    scores = db.get_scores_of_song(str(user.id), query)

  if len(scores) == 0:
    await ctx.send(f'No scores found for {query}')
    return
  await ctx.send(f'Found {len(scores)} score(s) for {query}')
  for score in scores:
    await ctx.send(f"```{songInfoToStr(SongInfo().fromDict(score))}```id: `{score.get('_id', '')}`\ntag: `{score.get('tag', '')}`")


@bot.command()
async def deleteScore(ctx: commands.Context, id: str):
  user = ctx.message.author

  # Fetch song info of id
  score = db.get_song(str(user.id), id)
  msgText = 'Are you sure you want to delete this score?\n'
  msgText += f"```{songInfoToStr(SongInfo().fromDict(score))}```"
  msgText += 'React with ✅ to confirm deletion\n'
  msgText += 'React with ❌ to cancel deletion\n'

  # Confirm deletion
  message = await ctx.send(msgText)
  await message.add_reaction('✅')
  await message.add_reaction('❌')

  def check(reaction, user):
    return user == ctx.author and str(reaction.emoji) in ['✅', '❌']

  # Wait for user to react
  try:
    reaction, _ = await bot.wait_for('reaction_add', timeout=60.0, check=check)
  except asyncio.TimeoutError:
    await ctx.send('Timed out')
  else:
    if str(reaction.emoji) == '✅':
      # Delete
      db.delete_song(str(user.id), id)
      await ctx.send(f'Deleted score `{id}`')
    elif str(reaction.emoji) == '❌':
      # Ignore
      await ctx.send('Cancelled deletion')

bot.run(TOKEN)
