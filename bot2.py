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

# Get token from .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Create bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='$', intents=intents)

# Create API
scoreAPI = ScoreAPI()

# Confirm a song info object to a formatted string
def songInfoToStr(song: SongInfo):
  songStr = f"({song.difficulty}) {song.songName}\n"
  songStr += f"Rank: {song.rank}\nScore: {song.score}\nHigh Score: {song.highScore}\nMax Combo: {song.maxCombo}\n"
  songStr += f"Note scores:\n"
  for key in song.notes:
    songStr += f"- {key}: {song.notes[key] if len(song.notes[key]) > 0 else '?'}\n"
  return songStr

# Converts a string to a song info object
def strToSongInfo(song: str):
  songInfo = SongInfo()
  lines = song.splitlines()
  # Get song name and difficulty
  songInfo.songName = lines[0].split(') ', 1)[1]
  songInfo.difficulty = lines[0].split(') ', 1)[0][1:]
  # Get rank
  songInfo.rank = lines[1].split(': ')[1]
  # Get score
  songInfo.score = lines[2].split(': ')[1]
  # Get high score
  songInfo.highScore = lines[3].split(': ')[1]
  # Get max combo
  songInfo.maxCombo = lines[4].split(': ')[1]
  # Get note scores
  for i in range(6, len(lines)):
    note = lines[i].split(': ')[0][2:]
    score = lines[i].split(': ')[1]
    songInfo.notes[note] = score
  return songInfo

# Confirm the song info and allow the user to edit the info if incorrect
async def confirmSongInfo(ctx: commands.Context, oldSong: SongInfo):
  # Send template for user to edit
  await ctx.send('Does this not look correct? Edit the song by copying the next message and sending it back:')
  await ctx.send(f'```{songInfoToStr(oldSong)}```')

  # New song to return
  newSong = None

  # Wait for user to send edited song
  def check(m):
    return m.author == ctx.author and m.channel == ctx.channel
  try:
    # Get the message from the user and store it in song info
    msg = await bot.wait_for('message', check=check, timeout=60.0)
    ns = strToSongInfo(msg.content)

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
  except:
    await ctx.send('Timed out.')
  else:
    await ctx.send('Thanks for the confirmation!')

  return newSong

@bot.command()
async def newScore(ctx: commands.Context):
  user = ctx.message.author

  # Get all the attachments
  files = ctx.message.attachments

  await ctx.send(f'Processing scores of {len(files)} songs...')

  for x, file in enumerate(files):
    await ctx.send(f'Song {x+1}/{len(files)}')
    # Get the file
    fp = BytesIO()
    await file.save(fp)
    # Get a file that the API can use
    image_np = np.frombuffer(fp.read(), np.uint8)
    img = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

    # Get the song info
    output = scoreAPI.getSongInfo(img)

    # Display the song info to the user and wait for a response
    fp.seek(0)
    message = await ctx.send(f"Song {x+1}/{len(files)}\n```{songInfoToStr(output)}```", file=discord.File(fp, filename=file.filename, spoiler=file.is_spoiler()))

    await message.add_reaction('✅')
    await message.add_reaction('❓')
    await message.add_reaction('❌')

    def check(reaction, user):
      return user == ctx.author and str(reaction.emoji) in ['✅', '❓', '❌']

    # Wait for user to react
    try:
      reaction, _ = await bot.wait_for('reaction_add', timeout=60.0, check=check)
    except asyncio.TimeoutError:
      await ctx.send('Timed out')
    else:
      if str(reaction.emoji) == '✅':
        # Add to database
        await ctx.send(f'({output.difficulty}) {output.songName} with a score of {output.score} added to database')
        pass
      elif str(reaction.emoji) == '❓':
        # Have user confirm song info
        output = await confirmSongInfo(ctx, output)
        pass
      elif str(reaction.emoji) == '❌':
        # Ignore
        output = None
        await ctx.send('Ignoring')
        pass

    print(output)

  await ctx.send(f'Done processing scores of {len(files)} songs!')

bot.run(TOKEN)