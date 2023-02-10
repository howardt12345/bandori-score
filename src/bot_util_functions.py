import numpy as np
import cv2
from discord.ext import commands
import asyncio
import logging

from consts import *
from db import Database
from functions import songInfoToStr, songTemplateFormat, strToSongInfo, validateSong
from song_info import SongInfo

def msgLog(ctx: commands.Context):
  logging.info(f'--- {ctx.message.author} ({ctx.message.guild} in #{ctx.message.channel}) {ctx.message.content}')

async def confirmSongInfo(bot: commands.Bot, db: Database, ctx: commands.Context, oldSong: SongInfo = None, currentTag: str = ""):
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
  tag = currentTag if currentTag in tags else tags[0]

  # Wait for user to send edited song
  def check(m):
    return m.author == ctx.author and m.channel == ctx.channel
  try:
    ns = None
    while ns is None:
      # Get the message from the user and store it in song info
      msg = await bot.wait_for('message', check=check, timeout=TIMEOUT)
      ns, error = strToSongInfo(msg.content)
      if error:
        await ctx.send(error)
      
      # Check if the score is valid, if not, ask user to edit again
      try:
        key, song, info = db.bestdori.getSong(ns.songName)
      except:
        info = None
      songValid, validationErrors = validateSong(ns, info)
      if not songValid:
        msgText = f"❌ Invalid song score: {', '.join(key for key, value in validationErrors.items() if not value)}.\n"
        msgText += "React with 🔁 to try again\n"
        msgText += "React with ⚠️ to ignore the errors and save the song anyway\n"
        msgText += "React with ❌ to cancel this operation\n"
        reply_msg = await ctx.send(msgText)
        await reply_msg.add_reaction('🔁')
        await reply_msg.add_reaction('⚠️')
        await reply_msg.add_reaction('❌')

        def check1(reaction, user):
          return user == ctx.author and reaction.message.id == reply_msg.id and str(reaction.emoji) in ['🔁', '⚠️', '❌']

        # Wait for user to react
        try:
          reaction, _ = await bot.wait_for('reaction_add', timeout=TIMEOUT, check=check1)
        except asyncio.TimeoutError:
          await ctx.send('Timed out')
        else:
          # If user confirms, save new song and return
          if str(reaction.emoji) == '⚠️':
            break
          # If user cancels, return nothing
          elif str(reaction.emoji) == '❌':
            # Ignore
            await ctx.send('Cancelled operation')
            return None, None
          else:
            # Ignore
            await ctx.send('Please try again')
            ns = None
            continue

    # Give user a double check prompt before deciding whether to save
    msgText = f'Double check if this is what you want the song information to be:\n```{songInfoToStr(ns)}```'
    msgText += f'Detected Song:\n{db.bestdori.getUrl(key)}\n'
    msgText += "✅ Valid song score" if songValid else f"⚠️ Invalid song score: {', '.join(key for key, value in validationErrors.items() if not value)}"
    if ns.songName != db.bestdori.getSongName(song):
      msgText += f'\n‼️ Song name will be stored as `{db.bestdori.getSongName(song)}` on save'
    msgText += "\n---\n"
    # Display the possible message actions
    msgText += 'React with ✅ to save the song to the database\n'
    msgText += f'React with ☑️ to add a tag to the song before saving (`{tag}` by default)\n'
    msgText += 'React with ❌ to discard the song\n'

    reply_msg = await ctx.send(msgText)
    await reply_msg.add_reaction('✅')
    await reply_msg.add_reaction('☑️')
    await reply_msg.add_reaction('❌')

    def check(reaction, user):
      return user == ctx.author and reaction.message.id == reply_msg.id and str(reaction.emoji) in ['✅', '☑️', '❌']

    # Wait for user to react
    try:
      reaction, _ = await bot.wait_for('reaction_add', timeout=TIMEOUT, check=check)
    except asyncio.TimeoutError:
      await ctx.send('Timed out')
    else:
      # If user confirms, save new song and return
      if str(reaction.emoji) == '✅':
        # Add to database
        logging.info('confirmSongInfo: Confirming current song info')
        pass
      elif str(reaction.emoji) == '☑️':
        logging.info('confirmSongInfo: Prompting for tag')
        tag = await promptTag(bot, ctx)
        pass
      # If user cancels, return nothing
      elif str(reaction.emoji) == '❌':
        # Ignore
        await ctx.send('Cancelled saving this song')
        return None, tag
  except asyncio.TimeoutError:
    await ctx.send('Timed out.')
  else:
    await ctx.send('Thanks for confirming the song!')

  ns.songName = db.bestdori.getSongName(song)
  newSong = ns

  return newSong, tag

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
    return user == ctx.author and reaction.message.id == reply_msg.id and str(reaction.emoji) in tagIcons
  try:
    reaction, _ = await bot.wait_for('reaction_add', timeout=TIMEOUT, check=check)
    tag = tags[tagIcons.index(reaction.emoji)]
  except asyncio.TimeoutError:
    await ctx.send('Timed out.')
  else:
    await ctx.send('Thanks for confirming the tag!')

  return tag

async def compareSongWithBest(ctx: commands.Context, db: Database, song: SongInfo, tag: str):
  '''Compare the song with the best rated songs in the database'''
  res = {}
  user = ctx.message.author
  bestScores = await db.get_best_songs(str(user.id), song.songName, song.difficulty, tag)
  for x, (id, value) in enumerate(bestDict.items()):
    _, op, _ = value
    if id == "notes.Perfect":
      score = song.notes['Perfect']
      bestScore = bestScores[x]['notes']['Perfect'] if len(bestScores) > 0 and bestScores[x] else 0
      better = score >= bestScore if op == 'DESC' else score <= bestScore if bestScore >= 0 else True
      res[id] = (score, bestScore, better)
      continue

    if id == "fastSlow":
      if not song.hasFastSlow():
        continue

      if (bestScores[x]):
        score = (song.fast, song.slow)
        bestScore = (bestScores[x]['fast'], bestScores[x]['slow']) if len(bestScores) > 0 and bestScores[x] else (-1, -1)
        better = sum(score) >= sum(bestScore) if op == 'DESC' else sum(score) <= sum(bestScore) 
        res[id] = (score, bestScore, better)
      else:
        res[id] = ((song.fast, song.slow), (-1, -1), True)
      continue

    if id == "fullCombo" or id == "allPerfect":
      if id == "allPerfect":
        score = song.isAllPerfect()
      else:
        score = song.isFullCombo()
      bestScore = bestScores[x] if len(bestScores) > 0 and bestScores[x] else False
      better = score
      res[id] = (score, bestScore, better)
      continue

    score = song.toDict()[id]
    bestScore = bestScores[x][id] if len(bestScores) > 0 and bestScores[x] else 0 if op == 'DESC' else -1
    better = score >= bestScore if op == 'DESC' else score <= bestScore if bestScore >= 0 else True
    res[id] = (score, bestScore, better)
  return res

async def printSongCompare(ctx: commands.Context, bestScores: dict):
  '''logging.info the comparison of the song with the best rated songs in the database'''
  if bestScores is None:
    await ctx.send('Failed to compare song with other entries')
    return

  def format(category, score):
    if category == 'TP':
      return f'{score*100:.5f}%'
    elif category == 'rank':
      return f'{ranks[score]}'
    else:
      return score
  
  msg = 'Score analysis:\n'
  for _, (id, value) in enumerate(bestDict.items()):
    name, _, _ = value
    if not id in bestScores:
      continue

    if id == "fullCombo" or id == "allPerfect":
      score, bestScore, better = bestScores[id]
      fscore, fbestScore = format(id, score), format(id, bestScore)
      if better:
        msg += f'✅ {name}! ({f"✅had {name.lower()} before" if fbestScore else f"❌no existing {name.lower()}"})\n'
      else:
        msg += f'❌ Not {name.lower()} ({f"✅had {name.lower()} before" if fbestScore else f"❌no existing {name.lower()}"})\n'
      continue

    score, bestScore, better = bestScores[id]
    fscore, fbestScore = format(id, score), format(id, bestScore)
    if better:
      msg += f'✅ {name} >= best ({fscore} >= {fbestScore})\n'
    else:
      msg += f'❌ {name} < best ({fscore} < {fbestScore})\n'
  await ctx.send(msg)

def getBandEmoji(id: int):
  '''Get the emoji for the band'''
  try:
    return bandEmojis[id]
  except:
    return '◼️'

def idFromBandEmoji(emoji: str):
  '''Get the band id from the emoji'''
  try:
    return [k for k, v in bandEmojis.items() if v == emoji][0]
  except:
    return -1