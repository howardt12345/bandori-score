import numpy as np
import cv2
from discord.ext import commands
import asyncio
from consts import *
from db import Database

from functions import songInfoToStr, songTemplateFormat, strToSongInfo
from song_info import SongInfo

def msgLog(ctx: commands.Context):
  print(f'--- {ctx.message.author} ({ctx.message.guild}) {ctx.message.content}')

async def confirmSongInfo(bot: commands.Bot, ctx: commands.Context, oldSong: SongInfo = None, askTag=False):
  '''Confirm the song info and allow the user to edit the info if incorrect'''
  # Send template for user to edit
  if oldSong:
    await ctx.send('Does this score not look correct? Edit the song by copying the next message and sending it back:')
    await ctx.send(f'{songInfoToStr(oldSong)}')
  else:
    oldSong = SongInfo()
    await ctx.send('Please send the song info in the following format:')
    await ctx.send(f'{songTemplateFormat()}')

  # New song to return
  newSong = None

  # Wait for user to send edited song
  def check(m):
    return m.author == ctx.author and m.channel == ctx.channel
  try:
    ns = None
    while ns is None:
      # Get the message from the user and store it in song info
      msg = await bot.wait_for('message', check=check, timeout=180.0)
      ns, error = strToSongInfo(msg.content)
      if error:
        await ctx.send(error)

    # Give user a double check prompt before deciding whether to save
    reply_msg = await ctx.send(f'Double check if this is what you want the song information to be:\n```{songInfoToStr(ns)}```')
    await reply_msg.add_reaction('✅')
    await reply_msg.add_reaction('❌')

    def check(reaction, user):
      return user == ctx.author and str(reaction.emoji) in ['✅', '❌']

    # Wait for user to react
    try:
      reaction, _ = await bot.wait_for('reaction_add', timeout=60.0, check=check)
    except asyncio.TimeoutError:
      await ctx.send('Timed out')
    else:
      # If user confirms, save new song and return
      if str(reaction.emoji) == '✅':
        newSong = ns
        pass
      # If user cancels, return nothing
      elif str(reaction.emoji) == '❌':
        # Ignore
        await ctx.send('Ignoring this song')
        pass
  except asyncio.TimeoutError:
    await ctx.send('Timed out.')
  else:
    await ctx.send('Thanks for the confirmation!')

  # Ask if user wants to tag the song
  wantTag = False
  if askTag and newSong:
    reply_msg = await ctx.send(f'Do you want to tag this song?')
    await reply_msg.add_reaction('✅')
    await reply_msg.add_reaction('❌')

    def check(reaction, user):
      return user == ctx.author and str(reaction.emoji) in ['✅', '❌']

    # Wait for user to react
    try:
      reaction, _ = await bot.wait_for('reaction_add', timeout=60.0, check=check)
    except asyncio.TimeoutError:
      await ctx.send('Timed out')
    else:
      # If user confirms, save new song and return
      if str(reaction.emoji) == '✅':
        wantTag = True
        pass
      # If user cancels, return nothing
      elif str(reaction.emoji) == '❌':
        # Ignore
        await ctx.send('Using default tag')
        pass

  return newSong, wantTag

async def promptTag(bot: commands.Bot, ctx: commands.Context):
  '''Prompt the user to tag the song'''
  # Send template for user to edit
  msgText = ''
  for x, tag in enumerate(tags):
    msgText += f'React with {tagIcons[x]} to tag this song with `{tag}`\n'

  # Send message
  reply_msg = await ctx.send(msgText)
  for tagIcon in tagIcons:
    await reply_msg.add_reaction(tagIcon)
  # New song to return
  tag = None

  # Wait for user to send edited song
  def check(reaction, user):
    return user == ctx.author and str(reaction.emoji) in tagIcons
  try:
    reaction, _ = await bot.wait_for('reaction_add', timeout=60.0, check=check)
    tag = tags[tagIcons.index(reaction.emoji)]
  except asyncio.TimeoutError:
    await ctx.send('Timed out.')
  else:
    await ctx.send('Thanks for the confirmation!')

  return tag

def compareSongWithBest(ctx: commands.Context, db: Database, song: dict, tag: str):
  '''Compare the song with the best rated songs in the database'''
  res = {}
  user = ctx.message.author
  bestScores = db.get_best_songs(str(user.id), song['songName'], difficulties[song['difficulty']], tag)
  for x, (id, value) in enumerate(bestDict.items()):
    _, op, _ = value
    if id == "notes.Perfect":
      score = song['notes']['Perfect']
      bestScore = bestScores[x]['notes']['Perfect'] if len(bestScores) > 0 else 0
      better = score >= bestScore if op == 'DESC' else score <= bestScore if bestScore >= 0 else True
      res[id] = (score, bestScore, better)
    elif id == "fastSlow":
      if ('fast' in song and 'slow' in song):
        if (bestScores[x]):
          score = (song['fast'], song['slow'])
          bestScore = (bestScores[x]['fast'], bestScores[x]['slow']) if len(bestScores) > 0 else (-1, -1)
          better = score >= bestScore if op == 'DESC' else score <= bestScore
          res[id] = (score, bestScore, better)
        else:
          res[id] = ((song['fast'], song['slow']), (-1, -1), True)
    else:
      score = song[id]
      bestScore = bestScores[x][id] if len(bestScores) > 0 else 0 if op == 'DESC' else -1
      better = score >= bestScore if op == 'DESC' else score <= bestScore if bestScore >= 0 else True
      res[id] = (score, bestScore, better)
  return res

async def printSongCompare(ctx: commands.Context, bestScores: dict):
  '''Print the comparison of the song with the best rated songs in the database'''
  if bestScores is None:
    await ctx.send('Failed to compare song with other entries')
  else:
    def format(category, score):
      if category == 'TP':
        return f'{score*100:.4f}%'
      elif category == 'rank':
        return f'{ranks[score]}'
      else:
        return score
    msg = 'Score analysis:\n'
    for _, (id, value) in enumerate(bestDict.items()):
      name, _, _ = value
      if id in bestScores:
        score, bestScore, better = bestScores[id]
        fscore, fbestScore = format(id, score), format(id, bestScore)
        if better:
          msg += f'✅ {name} >= best ({fscore} >= {fbestScore})\n'
        else:
          msg += f'❌ {name} < best ({fscore} < {fbestScore})\n'
    await ctx.send(msg)
  