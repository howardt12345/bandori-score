# Functions for the bot commands

from io import BytesIO, StringIO
import discord
from discord.ext import commands
import asyncio

from dotenv import load_dotenv
import os

import cv2
import numpy as np

from api import ScoreAPI
from functions import songCountGraph, songInfoToStr
from bot_util_functions import confirmSongInfo, promptTag, compareSongWithHighest, printSongCompare
from song_info import SongInfo
from db import Database
from consts import tags, highest
from bot_help import getCommandHelp

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

  compareRes = None

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
    output, res = scoreAPI.getSongInfo(img)
    tag = defaultTag if defaultTag in tags else tags[0]

    # Display the song info to the user and wait for a response
    fp.seek(0)

    msgText = f'Song {x+1}/{len(files)}:\n'
    msgText += f'```{songInfoToStr(output)}```'
    msgText += 'React with ✅ to save the song to the database\n'
    msgText += f'React with ☑️ to add a tag to the song before saving (`{tag}` by default)\n'
    msgText += 'React with 📝 to edit the song info\n'
    msgText += 'React with ❌ to discard the song\n'
    message = await ctx.send(msgText, file=discord.File(BytesIO(cv2.imencode('.jpg', res)[1]), filename=file.filename, spoiler=file.is_spoiler()))

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
        compareRes = compareSongWithHighest(ctx, db, output.toDict(), tag)
      res = db.create_song(str(user.id), output, tag)
      if res and res != -1:
        id = res.get('_id', '')
        msgText = f'({output.difficulty}) {output.songName} with a score of {output.score} added to database with tag `{tag}`'
        msgText += f'\nid: `{id}`'
        await ctx.send(msgText)
        await ctx.send(f'{id}')
      elif res == -1:
        await ctx.send('Song score already exists in database')
      else:
        await ctx.send('Error adding song to database')

    if compareRes:
      await printSongCompare(ctx, compareRes)

  await ctx.send(f'Done processing scores of {len(files)} song(s)!')



async def getScores(db: Database, ctx: commands.Context, query: str = ""):
  '''Gets the scores from the database given a query by the user'''
  user = ctx.message.author
  if not query:
    await ctx.send('A query must be provided')
    return
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
  newSong, wantTag = await confirmSongInfo(bot, ctx, song, askTag=True)
  if wantTag:
    tag = await promptTag(bot, ctx)
  else:
    tag = None
  if newSong:
    # Update the song
    db.update_song(str(user.id), id, newSong, tag)
    await ctx.send(f'Score with id `{id}` updated')
  else:
    await ctx.send('No changes made')

async def deleteScore(bot: commands.Bot, db: Database, ctx: commands.Context, id: str):
  '''Deletes a score from the database given an id'''
  user = ctx.message.author

  # Fetch song info of id
  score = db.get_song(str(user.id), id)
  if not score:
    await ctx.send(f'No score found with id `{id}`')
    return
  msgText = 'Are you sure you want to delete this score?\n**THIS ACTION CANNOT BE UNDONE**\n'
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


async def getHighest(db: Database, ctx: commands.Context, songName: str, difficulty: str, tag: str = "", query: str = ""):
  '''Gets the highest score of a song given a song nam, difficulty, and tag'''

  if (query and query not in [x[0] for x in highest]):
    await ctx.send(f'''Invalid query: "{query}" for song {songName} and difficulty {difficulty}.
    \nSong name and difficulty must be provided and query must be one of: {[x[0] for x in highest]}''')
    return
  user = ctx.message.author
  scores = db.get_song_with_highest(str(user.id), songName, difficulty, tag, query)[0] if query else db.get_highest_songs(str(user.id), songName, difficulty, tag) 
  if len(scores) == 0:
    await ctx.send(f'No highest {query} entry for "{songName}" ({difficulty})')
    return
  if isinstance(scores, dict):
    await ctx.send(f'Found the highest {query} entry for "{songName}" ({difficulty})')
    await ctx.send(db.songInfoMsg(scores))
  elif isinstance(scores, list):
    for x, category in enumerate(highest):
      if category[3]:
        continue
      await ctx.send(f"The highest {category[1]} entry{f' for {songName}' if songName else ''}{f' in {difficulty}' if difficulty else ''}: \n{db.songInfoMsg(scores[x])}")


async def getSongCounts(db: Database, ctx: commands.Context, difficulty: str, tag: str = "", asFile=False):
  '''Gets the number of songs in the database'''
  user = ctx.message.author
  counts = db.get_song_counts(str(user.id), difficulty, tag)
  counts.sort(key=lambda x: x['_id'].lower())
  totalCount = sum([x['count'] for x in counts])
  # counts.sort(key=lambda x: x['count'], reverse=True)
  msgText = f"You have the following{f' {difficulty}' if difficulty else ''} song scores stored{f' with a tag of {tag}' if tag else ''} ({totalCount} total):\n"
  for count in counts:
    dbName = count['_id']
    name = db.bestdori.closestSongName(dbName)
    msgText += f'{name if name else dbName} {f"(`{dbName}` in database)" if name != dbName else ""}: {count["count"]}\n'

  if asFile:
    buf = StringIO(msgText)
    f = discord.File(buf, filename=f'{user.id}_songs.txt')
    await ctx.send(file=f)
  else:
    if len(msgText) > 2000:
      lines = msgText.splitlines()
      msgText = ''
      for line in lines:
        if len(msgText) + len(line) > 2000:
          await ctx.send(msgText)
          msgText = ''
        msgText += line + '\n'
    await ctx.send(msgText)


async def getSongStats(db: Database, ctx: commands.Context, songName: str, difficulty: str = None, tag: str = "", matchExact = False, showMaxCombo = False, showSongNames = False, interpolate = False):
  '''Gets the stats of a song given a song name and difficulty'''
  user = ctx.message.author
  await ctx.send(f"Getting stats for{f' ({difficulty}) ' if difficulty else ' '}{songName}{f' with tag {tag}' if tag else ''}...")
  stats = db.get_scores_of_song(str(user.id), songName, difficulty, tag, matchExact)
  if len(stats) == 0:
    await ctx.send(f'Can\'t get stats for "{songName}" ({difficulty})')
    return
  # Add difficulty level to stats
  songs = [SongInfo.fromDict(x) for x in stats]
  graphFile = songCountGraph(songs, db.bestdori, songName, difficulty, tag, userName=str(user), showMaxCombo=showMaxCombo, showSongNames=showSongNames, interpolate=interpolate)
  await ctx.send(f"Stats for{f' ({difficulty}) ' if difficulty else ' '}{songName}{f' with tag {tag}' if tag else ''}", file=discord.File(graphFile, filename=f'{user.id} {songName} {difficulty} {tag}.png'))
  

async def getRecent(db: Database, ctx: commands.Context, limit: int, tag: str = ""):
  '''Gets the most recent songs added to the database'''
  user = ctx.message.author
  songs = db.get_recent_songs(str(user.id), limit, tag)
  if len(songs) == 0:
    await ctx.send(f'No recent songs found')
    return
  await ctx.send(f"Your {limit} most recent song(s){f' with tag {tag}' if tag else ''}:")
  for song in songs:
    await ctx.send(db.songInfoMsg(song))


async def bestdoriGet(db: Database,ctx: commands.Context, query: str):
  '''Gets the bestdori song info for a given query'''
  song = db.bestdori.getSong(query)
  if song:
    await ctx.send(f'```json\n{song}```')
  else:
    await ctx.send(f'No Bestdori song info found for query "{query}"')


async def help(ctx: commands.Context, command: str = ""):
  '''Gets the help message'''
  await ctx.send(getCommandHelp(command, ctx.prefix))