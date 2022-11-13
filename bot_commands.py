# Functions for the bot commands

from io import BytesIO
import discord
from discord.ext import commands
import asyncio

from dotenv import load_dotenv
import os

import cv2
import numpy as np

from api import ScoreAPI
from functions import songInfoToStr
from bot_util_functions import *
from db import Database
from consts import tags

async def newScores(
  scoreAPI: ScoreAPI, 
  bot: commands.Bot, 
  db: Database, ctx: 
  commands.Context, 
  compare: bool, 
  defaultTag: str = ""
):
  '''Adds a new score to the database from screenshots given in the user's message'''
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
    tag = defaultTag if defaultTag in tags else tags[0]

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
        output, wantTag = await confirmSongInfo(bot, ctx, output, askTag=True)
        if wantTag:
          tag = await promptTag(bot, ctx)
        pass
      elif str(reaction.emoji) == '❌':
        # Ignore
        output = None
        await ctx.send('Score discarded')
        pass

    if not output is None:
      if compare:
        compareRes = compareSongWithHighest(ctx, db, output.toDict())
      res = db.create_song(str(user.id), output, tag)
      if res and res != -1:
        id = res.get('_id', '')
        msgText = f'({output.difficulty}) {output.songName} with a score of {output.score} added to database with tag `{tag}`'
        msgText += f'\nid: `{id}`'
        await ctx.send(msgText)
      elif res == -1:
        await ctx.send('Song score already exists in database')
      else:
        await ctx.send('Error adding song to database')

  await ctx.send(f'Done processing scores of {len(files)} song(s)!')
  if compareRes:
    await printSongCompare(ctx, compareRes)


async def getScores(db: Database, ctx: commands.Context, query: str = ""):
  '''Gets the scores from the database given a query by the user'''
  user = ctx.message.author
  if not query:
    scores = db.get_songs(str(user.id))
  else:
    try:
      scores = db.get_song(str(user.id), query.strip())
    except Exception as e:
      print(e)
      scores = db.get_scores_of_song(str(user.id), query)

  if len(scores) == 0:
    await ctx.send(f'No scores found for "{query}"')
    return
  if isinstance(scores, dict):
    scores = [scores]
  await ctx.send(f'Found {len(scores)} score(s) for "{query}"')
  for score in scores:
    await ctx.send(db.songInfoMsg(score))


async def editScore(bot: commands.Bot, db: Database, ctx: commands.Context, id: str):
  '''Edits a score in the database given an id'''
  user = ctx.message.author

  # Fetch song info of id
  score = db.get_song(str(user.id), id)
  if not score:
    await ctx.send(f'No score found with id `{id}`')
    return


  song = SongInfo.fromDict(score)
  newSong, _ = await confirmSongInfo(bot, ctx, song)
  if newSong:
    # Update the song
    db.update_song(str(user.id), id, newSong)
  else:
    await ctx.send('No changes made')

async def deleteScore(bot: commands.Bot, db: Database, ctx: commands.Context, id: str):
  '''Deletes a score from the database given an id'''
  user = ctx.message.author

  # Fetch song info of id
  score = db.get_song(str(user.id), id)
  msgText = 'Are you sure you want to delete this score?\n'
  msgText += db.songInfoMsg(score)
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


async def manualInput(bot: commands.Bot, db: Database, ctx: commands.Context, defaultTag: str = ""):
  '''Manually input a song score'''
  user = ctx.message.author

  # Confirm if user really wants to manually input a song
  msgText = '**This is an advanced feature.** Are you sure you want to manually input a song?\n'
  msgText += 'React with ✅ to confirm\n'
  msgText += 'React with ❌ to cancel\n'

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
      # request song info
      tag = defaultTag if defaultTag in tags else tags[0]

      song, wantTag = await confirmSongInfo(bot, ctx, askTag=True)
      if song:
        if wantTag:
          tag = await promptTag(bot, ctx)
        res = db.create_song(str(user.id), song, tag)
        if res and res != -1:
          id = res.get('_id', '')
          msgText = f'({song.difficulty}) {song.songName} with a score of {song.score} added to database with tag `{tag}`'
          msgText += f'\nid: `{id}`'
          await ctx.send(msgText)
        elif res == -1:
          await ctx.send('Song score already exists in database')
        else:
          await ctx.send('Error adding song to database')
    elif str(reaction.emoji) == '❌':
      # Ignore
      await ctx.send('Cancelled manual input')


async def getHighest(db: Database, ctx: commands.Context, songName: str, difficulty: str, query: str = ""):
  if not songName or difficulty not in difficulties or (query and query not in [x[0] for x in highest]):
    await ctx.send(f'Invalid query: "{query}" for song {songName} and difficulty {difficulty}.\nQuery must be one of: {[x[0] for x in highest]}')
    return
  user = ctx.message.author
  scores = db.get_song_with_highest(str(user.id), songName, difficulty, query)[0] if query else db.get_highest_songs(str(user.id), songName, difficulty) 
  if len(scores) == 0:
    await ctx.send(f'No highest {query} entry for "{songName}" ({difficulty})')
    return
  if isinstance(scores, dict):
    await ctx.send(f'Found the highest {query} entry for "{songName}" ({difficulty})')
    await ctx.send(db.songInfoMsg(scores))
  elif isinstance(scores, list):
    for x, category in enumerate(highest):
      await ctx.send(f'The highest {category[1]} entry for "{songName}" ({difficulty}): \n{db.songInfoMsg(scores[x])}')