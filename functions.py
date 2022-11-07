
import numpy as np
import cv2
from discord.ext import commands
import asyncio
from consts import *
import json

class SongInfo:
  def __init__(self, songName="", difficulty="", rank="", score=-1, highScore=-1, maxCombo=-1, notes={}):
    self.songName = songName
    self.difficulty = difficulty
    self.rank = rank
    self.score = score
    self.highScore = highScore
    self.maxCombo = maxCombo
    self.notes = notes

  def __str__(self):
    return f"{self.songName} - {self.difficulty}\nRank: {self.rank}, Score: {self.score}, High Score: {self.highScore}, Max Combo: {self.maxCombo}\n{self.notes}"

  def __repr__(self):
    return self.__str__()

  def toDict(self):
    return {
      "songName": self.songName,
      "difficulty": self.difficulty,
      "rank": self.rank,
      "score": self.score,
      "highScore": self.highScore,
      "maxCombo": self.maxCombo,
      "notes": self.notes
    }
  
  def toJSON(self):
    return json.dumps(self.toDict())

  @staticmethod
  def fromDict(dict):
    return SongInfo(dict["songName"], dict["difficulty"], dict["rank"], dict["score"], dict["highScore"], dict["maxCombo"], dict["notes"])

  @staticmethod
  def fromJSON(json):
    return SongInfo.fromDict(json.loads(json))

# Function to fetch the templates for the different ranks
def fetchRanks(path):
  # List of ranks
  imgs = []
  for rank in ranks:
    ext = "png" if path == 'direct' else "jpg"
    template = cv2.imread(f'assets/{path}/rank/{rank}.{ext}')
    # If the template exists, add it to the list
    if not template is None:
      imgs.append(( template, rank ))
  return imgs

# Function to fetch the templates for the different note types
# Returns the name of the note type as well as variables for OCR ROI positioning
def fetchNoteTypes(path):
  # List of note types and variables for OCR matching
  ratios = [2.1, 2.75, 2.8, 4.3, 3.8]
  tolerances = [(0, 0), (1, 0), (0, 0), (0, 3), (2, 5)] # The top and bottom tolerances of the note type bounding box
  imgs = []
  for i in range(len(types)):
    ext = "png" if path == 'direct' else "jpg"
    template = cv2.imread(f'assets/{path}/score/{types[i]}.{ext}')
    if not template is None:
      # If the template exists, add it to the list
      imgs.append(( template, types[i], ratios[i], tolerances[i] ))
  return imgs

# Function to fetch the templates for the different difficulties
# This will not work with 'direct' mode
def fetchDifficulties(path):
  imgs = []
  for difficulty in difficulties:
    ext = "png" if path == 'direct' else "jpg"
    template = cv2.imread(f'assets/{path}/difficulty/{difficulty}.{ext}')
    if not template is None:
      # If the template exists, add it to the list
      imgs.append(( template, difficulty ))
  return imgs

# Fetch score icon
def fetchScoreIcon(path):
  ext = "png" if path == 'direct' else "jpg"
  return cv2.imread(f'assets/{path}/ScoreIcon.{ext}')

# Fetch Max combo reference image
def fetchMaxCombo(path):
  ext = "png" if path == 'direct' else "jpg"
  return cv2.imread(f'assets/{path}/Max combo.{ext}')

# Confirm a song info object to a formatted string
def songInfoToStr(song: SongInfo):
  songStr = f"({song.difficulty}) {song.songName}\n"
  songStr += f"Rank: {song.rank}\n"
  songStr += f"Score: {song.score if song.score >= 0 else '?'}\n"
  songStr += f"High Score: {song.highScore if song.highScore >= 0 else '?'}\n"
  songStr += f"Max Combo: {song.maxCombo if song.maxCombo >= 0 else '?'}\n"
  songStr += f"Note scores:\n"
  for key in song.notes:
    songStr += f"- {key}: {song.notes[key] if song.notes[key] >= 0 else '?'}\n"
  return songStr

# Converts a string to a song info object
def strToSongInfo(song: str):
  songInfo = SongInfo()
  lines = song.splitlines()
  # Get song name and difficulty
  songName, difficulty = lines[0].split(') ', 1)[1], lines[0].split(') ', 1)[0][1:]
  songInfo.songName =  songName
  if not difficulty in difficulties:
    return None, f"Invalid difficulty: {difficulty}. Must be in one of {difficulties}"
  songInfo.difficulty = difficulty
  # Get rank
  rank = lines[1].split(': ', 1)[1]
  if not rank in ranks:
    return None, f"Invalid rank: {rank}. Must be in one of {ranks}"
  songInfo.rank = rank
  # Get score
  score = lines[2].split(': ')[1]
  songInfo.score = int(score) if score.isdecimal() else -1
  # Get high score
  highScore = lines[3].split(': ')[1]
  songInfo.highScore = int(highScore) if highScore.isdecimal() else -1
  # Get max combo
  maxCombo = lines[4].split(': ')[1]
  songInfo.maxCombo = int(maxCombo) if maxCombo.isdecimal() else -1
  # Get note scores
  notes = {}
  for i in range(6, len(lines)):
    note = lines[i].split(': ')[0][2:]
    if note not in types:
      return None, f"Invalid note type: {note}. Must be in one of {types}"
    score = lines[i].split(': ')[1]
    notes[note] = int(score) if score.isdecimal() else -1
  
  # If any of the note types are missing, throw error
  if not all(note in notes for note in types):
    return None, f"Missing note types. Must have all of {types}"
  songInfo.notes = notes

  return songInfo, None

# Confirm the song info and allow the user to edit the info if incorrect
async def confirmSongInfo(bot: commands.Bot, ctx: commands.Context, oldSong: SongInfo):
  # Send template for user to edit
  await ctx.send('Does this not look correct? Edit the song by copying the next message and sending it back:')
  await ctx.send(f'```{songInfoToStr(oldSong)}```')

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

  return newSong

async def promptTag(bot: commands.Bot, ctx: commands.Context):
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