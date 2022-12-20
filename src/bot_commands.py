# Functions for the bot commands

from io import BytesIO, StringIO
import discord
from discord.ext import commands
import asyncio
import logging

from dotenv import load_dotenv
import os

import cv2
import numpy as np

from api import ScoreAPI
from chart import songCountGraph
from functions import getDifficulty, hasDifficulty, hasTag, songInfoToStr, getAboutTP, validateSong
from bot_util_functions import confirmSongInfo, promptTag, compareSongWithBest, printSongCompare
from song_info import SongInfo
from db import Database
from consts import tags, bestDict, TIMEOUT
from bot_help import getCommandHelp

async def newScores(
  scoreAPI: ScoreAPI, 
  bot: commands.Bot, 
  db: Database, 
  ctx: commands.Context, 
  compare: bool, 
  defaultTag: str = ""
):
  '''Adds a new score to the database from screenshots given in the user's message'''
  user = ctx.message.author

  # Get all the attachments
  files = ctx.message.attachments

  compareRes = None

  logging.info(f'newScores: Processing scores of {len(files)} song(s)')
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
    key, song, info = db.bestdori.getSong(output.songName)
    songValid, validationErrors = validateSong(output, info)

    # Display the song info to the user and wait for a response
    fp.seek(0)
    logging.info('newScores: Initial song read: ')
    logging.info(output)

    msgText = f'Song {x+1}/{len(files)}:\n'
    msgText += f'```{songInfoToStr(output)}```'
    msgText += f'Detected Song:\n{db.bestdori.getUrl(key)}\n'
    msgText += "✅ Valid song score" if songValid else f"⚠️ Invalid song score: {', '.join(key for key, value in validationErrors.items() if not value)}"
    if output.songName != db.bestdori.getSongName(song):
      msgText += f'\n‼️ Song name will be stored as `{db.bestdori.getSongName(song)}` on save'
    msgText += '\n---\nReact with ✅ to save the song to the database\n'
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
      reaction, _ = await bot.wait_for('reaction_add', timeout=TIMEOUT, check=check)
    except asyncio.TimeoutError:
      output = None
      await ctx.send('Timed out')
    else:
      if str(reaction.emoji) == '✅':
        # Add to database
        logging.info('newScores: Adding score to database')
        pass
      elif str(reaction.emoji) == '☑️':
        # Add tag
        logging.info('newScores: Prompting for tag')
        tag = await promptTag(bot, ctx)
        pass
      elif str(reaction.emoji) == '📝':
        # Have user confirm song info
        logging.info('newScores: User deemed song info inaccurate and is editing song info')
        output, wantTag = await confirmSongInfo(bot, db, ctx, output, askTag=True, currentTag=tag)
        if wantTag:
          tag = await promptTag(bot, ctx)
        pass
      elif str(reaction.emoji) == '❌':
        # Ignore
        output = None
        logging.info('newScores: Score add operation canceled')
        await ctx.send('Score discarded')
        pass

    if not output is None:
      output.songName = db.bestdori.getSongName(song)
      if compare:
        compareRes = await compareSongWithBest(ctx, db, output, tag)
      res = await db.create_song(str(user.id), output, tag)
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

    if not output is None and compareRes:
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
      scores = await db.get_song(str(user.id), query.strip())
    except Exception as e:
      logging.info(e)
      scores = await db.get_scores_of_song(str(user.id), db.bestdori.closestSongName(query.strip()))

  if not scores or len(scores) == 0:
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
  score = await db.get_song(str(user.id), id)
  if not score:
    await ctx.send(f'No score found with id `{id}`')
    return


  song = SongInfo.fromDict(score)
  newSong, wantTag = await confirmSongInfo(bot, db, ctx, song, askTag=True, currentTag=tags[score['tag']])
  if wantTag:
    tag = await promptTag(bot, ctx)
  else:
    tag = None
  if newSong:
    # Update the song
    await db.update_song(str(user.id), id, newSong, tag)
    await ctx.send(f'Score with id `{id}` updated')
  else:
    await ctx.send('No changes made')

async def deleteScore(bot: commands.Bot, db: Database, ctx: commands.Context, id: str):
  '''Deletes a score from the database given an id'''
  user = ctx.message.author

  # Fetch song info of id
  score = await db.get_song(str(user.id), id)
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
    reaction, _ = await bot.wait_for('reaction_add', timeout=TIMEOUT, check=check)
  except asyncio.TimeoutError:
    await ctx.send('Timed out')
  else:
    if str(reaction.emoji) == '✅':
      # Delete
      await db.delete_song(str(user.id), id)
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
    reaction, _ = await bot.wait_for('reaction_add', timeout=TIMEOUT, check=check)
  except asyncio.TimeoutError:
    await ctx.send('Timed out')
  else:
    if str(reaction.emoji) == '✅':
      # request song info
      tag = defaultTag if defaultTag in tags else tags[0]

      song, wantTag = await confirmSongInfo(bot, db, ctx, askTag=True)
      if song:
        if wantTag:
          tag = await promptTag(bot, ctx)
        res = await db.create_song(str(user.id), song, tag)
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


async def getBest(db: Database, ctx: commands.Context, songName: str, difficulty: str, tag: str = "", query: str = ""):
  '''Gets the best score of a song given a song nam, difficulty, and tag'''

  if (query and query not in bestDict.keys()):
    await ctx.send(f'''Invalid query: "{query}" for song {songName} and difficulty {difficulty}.
    \nSong name and difficulty must be provided and query must be one of: {bestDict.keys()}''')
    return
  user = ctx.message.author
  res = await db.get_song_with_best(str(user.id), songName, difficulty, tag, query, bestDict[query][1]) if query else await db.get_best_songs(str(user.id), songName, difficulty, tag)
  scores = res[0] if res and query else res
  if not scores or len(scores) == 0:
    await ctx.send(f'No best {query} entry for "{songName}" {f"({difficulty})" if difficulty else ""}')
    return
  if isinstance(scores, dict):
    await ctx.send(f'Found the best {query} entry for "{songName}" {f"({difficulty})" if difficulty else ""}')
    await ctx.send(db.songInfoMsg(scores))
  elif isinstance(scores, list):
    for x, (_, value) in enumerate(bestDict.items()):
      if value[2]:
        continue
      if scores[x]:
        await ctx.send(f"The best {value[0]} entry{f' for {songName}' if songName else ''}{f' in {difficulty}' if difficulty else ''}: \n{db.songInfoMsg(scores[x])}")
      else:
        await ctx.send(f"No best {value[0]} entry{f' for {songName}' if songName else ''}{f' in {difficulty}' if difficulty else ''}")


async def listSongs(db: Database, ctx: commands.Context, difficulty: str, tag: str = "", asFile=False, allPerfect=False):
  '''Gets the number of songs in the database'''
  user = ctx.message.author
  counts = await db.list_songs(str(user.id), difficulty, tag)
  counts.sort(key=lambda x: x['_id'].lower())
  totalCount = sum([x['count'] for x in counts])
  totalFC = sum([x['fullCombo'] for x in counts])
  if allPerfect: totalAP = sum([x['allPerfect'] for x in counts])
  # counts.sort(key=lambda x: x['count'], reverse=True)
  # counts.sort(key=lambda x: db.bestdori.getDifficulty(x['_id'], getDifficulty(difficulty) if hasDifficulty(difficulty) else 3))
  msgText = f"You have the following{f' {difficulty}' if difficulty else ''} song scores stored{f' with a tag of {tag}' if tag else ''} ({len(counts)} songs, {totalCount} scores):\n"
  for count in counts:
    dbName = count['_id']
    _, song, _ = db.bestdori.getSong(dbName, songInfo=False)
    name = db.bestdori.getSongName(song)
    d = db.bestdori.getDifficulty(song, getDifficulty(difficulty) if hasDifficulty(difficulty) else 3)
    msgText += f'`{d}`'
    msgText += f'{"✅" if count["fullCombo"] else "❌"} '
    if allPerfect: msgText += f'{"☑️" if count["allPerfect"] else "❌"}'
    msgText += f'{name if name else dbName}{f" (`{dbName}`)" if name != dbName else ""}: {count["count"]}'
    msgText += "\n"

  msgText += f'\nSongs that have a full combo entry in {difficulty if difficulty else "Expert"}: {totalFC}'
  if allPerfect: msgText += f'\nSongs that have an all perfect entry: {totalAP}'

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


async def getSongStats(db: Database, ctx: commands.Context, songName: str = "", difficulty: str = None, tag: str = "", matchExact = False, showMaxCombo = False, showSongNames = False, interpolate = False):
  '''Gets the stats of a song given a song name and difficulty'''
  user = ctx.message.author
  await ctx.send(f"Getting stats for{f' ({difficulty}) ' if difficulty else ' '}{songName}{f' with tag {tag}' if tag else ''}...")
  stats = await db.get_scores_of_song(str(user.id), songName, difficulty, tag, matchExact)
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
  songs = await db.get_recent_songs(str(user.id), limit, tag)
  if len(songs) == 0:
    await ctx.send(f'No recent songs found')
    return
  await ctx.send(f"Your {limit} most recent song(s){f' with tag {tag}' if tag else ''}:")
  for song in songs:
    await ctx.send(db.songInfoMsg(song))

async def compare(db: Database, ctx: commands.Context, id: str):
  '''Compares the user's scores to the user's best score of the song'''
  user = ctx.message.author

  # Fetch song info of id
  score = await db.get_song(str(user.id), id)
  if not score:
    await ctx.send(f'No score found with id `{id}`')
    return

  res = await compareSongWithBest(ctx, db, SongInfo.fromDict(score), score['tag'])
  await printSongCompare(ctx, res)


async def tagScore(bot: commands.Bot, db: Database, ctx: commands.Context, id: str, tag: str = ""):
  '''Tags a score with a given tag'''
  user = ctx.message.author

  # Fetch song info of id
  score = await db.get_song(str(user.id), id)
  if not score:
    await ctx.send(f'No score found with id `{id}`')
    return

  song = SongInfo.fromDict(score)
  await ctx.send(f'{songInfoToStr(song)}')
  if not tag or not hasTag(tag):
    tag = await promptTag(bot, ctx)

  await db.update_song(str(user.id), id, song, tag)
  await ctx.send(f'Changed the tag of the score with id `{id}` to `{tag}`')


async def bestdoriGet(db: Database,ctx: commands.Context, query: str):
  '''Gets the bestdori song info for a given query'''
  key, song, _ = db.bestdori.getSong(query)
  if song:
    await ctx.send(f'```json\n{song}```')
  if key: 
    await ctx.send(f'https://bestdori.com/info/songs/{key}')
  else:
    await ctx.send(f'No Bestdori song info found for query "{query}"')


async def help(ctx: commands.Context, command: str = ""):
  '''Gets the help message'''
  await ctx.send(getCommandHelp(command, ctx.prefix))


async def aboutTP(ctx: commands.Context):
  '''Gets the about message'''
  await ctx.send(getAboutTP())