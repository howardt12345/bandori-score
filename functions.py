
import numpy as np
import cv2
from discord.ext import commands
import asyncio
from consts import *
import json

class SongInfo:
  '''Object representing a song's info'''
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

  def totalNotes(self):
    '''Returns the total number of notes in the song'''
    return sum(self.notes.values())

  def calculateTP(self):
    '''Calculates the total percentage of the song based on note weighting'''
    tp = 0
    for noteType in self.notes:
      tp += self.notes[noteType] * noteWeights[noteType]
    return tp / self.totalNotes()

def fetchRanks(path):
  '''Fetches the templates of the different ranks'''
  # List of ranks
  imgs = []
  for rank in ranks:
    ext = "png" if path == 'direct' else "jpg"
    template = cv2.imread(f'assets/{path}/rank/{rank}.{ext}')
    # If the template exists, add it to the list
    if not template is None:
      imgs.append(( template, rank ))
  return imgs

def fetchNoteTypes(path):
  '''Fetches the templates for the different note types
  \nReturns the name of the note type as well as variables for OCR ROI positioning'''
  # List of note types and variables for OCR matching
  imgs = []
  for x, type in enumerate(types):
    ext = "png" if path == 'direct' else "jpg"
    template = cv2.imread(f'assets/{path}/score/{type}.{ext}')
    if not template is None:
      # If the template exists, add it to the list
      imgs.append(( template, type, ratios[x], tolerances[x] ))
  return imgs

def fetchDifficulties(path):
  '''Fetches the templates for the different difficulties
  \nThis will not work with the 'direct' path assets'''
  imgs = []
  for difficulty in difficulties:
    ext = "png" if path == 'direct' else "jpg"
    template = cv2.imread(f'assets/{path}/difficulty/{difficulty}.{ext}')
    if not template is None:
      # If the template exists, add it to the list
      imgs.append(( template, difficulty ))
  return imgs

def fetchScoreIcon(path):
  '''Fetches the score icon'''
  ext = "png" if path == 'direct' else "jpg"
  return cv2.imread(f'assets/{path}/ScoreIcon.{ext}')

def fetchMaxCombo(path):
  '''Fetches the max combo template'''
  ext = "png" if path == 'direct' else "jpg"
  return cv2.imread(f'assets/{path}/Max combo.{ext}')

def songInfoToStr(song: SongInfo):
  '''Converts a SongInfo object to a formatted string'''
  songStr = f"({song.difficulty}) {song.songName}\n"
  songStr += f"Rank: {song.rank}\n"
  songStr += f"Score: {song.score if song.score >= 0 else '?'}\n"
  songStr += f"High Score: {song.highScore if song.highScore >= 0 else '?'}\n"
  songStr += f"Max Combo: {song.maxCombo if song.maxCombo >= 0 else '?'}\n"
  songStr += f"Note scores:\n"
  for key in song.notes:
    songStr += f"- {key}: {song.notes[key] if song.notes[key] >= 0 else '?'}\n"
  return songStr

def strToSongInfo(song: str):
  '''Converts a formatted string to a SongInfo object'''
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

def songTemplateFormat():
  '''Returns a formatted string of the song template'''
  songStr = f"({'|'.join(difficulties)}) song_name\n"
  songStr += f"Rank: {'|'.join(ranks)}\n"
  songStr += f"Score: score\n"
  songStr += f"High Score: high_score\n"
  songStr += f"Max Combo: max_combo\n"
  songStr += f"Note scores:\n"
  for key in types:
    songStr += f"- {key}: {key.lower()}_count\n"
  return songStr

def emptyTemplate():
  '''Returns an empty song template'''
  songStr = f"({'|'.join(difficulties)}) \n"
  songStr += f"Rank: {'|'.join(ranks)}\n"
  songStr += f"Score: \n"
  songStr += f"High Score: \n"
  songStr += f"Max Combo: \n"
  songStr += f"Note scores:\n"
  for key in types:
    songStr += f"- {key}: \n"
  return songStr