
import numpy as np
import cv2
from shapely.geometry import LineString

import sys

from consts import *
from song_info import SongInfo

ASSETS_DIR = f'{sys.path[0]} + /../assets'

def getDifficulty(d: str):
  try:
    return next(i for i,v in enumerate(difficulties) if v.lower() == d.lower())
  except:
    return None

def hasDifficulty(d: str):
  try:
    return d.lower() in (x.lower() for x in difficulties)
  except:
    return False

def getTag(t: str):
  try:
    return next(i for i,v in enumerate(tags) if v.lower() == t.lower())
  except:
    return None

def hasTag(t: str):
  try:
    return t.lower() in (x.lower() for x in tags)
  except:
    return False

def fetchRanks(path):
  '''Fetches the templates of the different ranks'''
  # List of ranks
  imgs = []
  for rank in ranks:
    ext = "png" if path == 'direct' else "jpg"
    template = cv2.imread(f'{ASSETS_DIR}/{path}/rank/{rank}.{ext}')
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
    template = cv2.imread(f'{ASSETS_DIR}/{path}/score/{type}.{ext}')
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
    template = cv2.imread(f'{ASSETS_DIR}/{path}/difficulty/{difficulty}.{ext}')
    if not template is None:
      # If the template exists, add it to the list
      imgs.append(( template, difficulty ))
  return imgs

def fetchScoreIcon(path):
  '''Fetches the score icon'''
  ext = "png" if path == 'direct' else "jpg"
  return cv2.imread(f'{ASSETS_DIR}/{path}/ScoreIcon.{ext}')

def fetchMaxCombo(path):
  '''Fetches the max combo template'''
  ext = "png" if path == 'direct' else "jpg"
  return cv2.imread(f'{ASSETS_DIR}/{path}/Max combo.{ext}'), cv2.imread(f'{ASSETS_DIR}/{path}/Max combo small.{ext}')

def fetchFastSlow(path):
  '''Fetches the fast and slow templates'''
  ext = "png" if path == 'direct' else "jpg"
  return cv2.imread(f'{ASSETS_DIR}/{path}/fast.{ext}'), cv2.imread(f'{ASSETS_DIR}/{path}/slow.{ext}')

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
  if song.hasFastSlow():
    songStr += f"Fast: {song.fast}\n"
    songStr += f"Slow: {song.slow}\n"
  return songStr

def strToSongInfo(song: str):
  '''Converts a formatted string to a SongInfo object'''
  try:
    songInfo = SongInfo()
    lines = song.splitlines()
    # Get song name and difficulty
    songName, difficulty = lines[0].split(') ', 1)[1], lines[0].split(') ', 1)[0][1:]
    songInfo.songName = songName
    if not hasDifficulty(difficulty):
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
    for i in range(6, 6 + len(types)):
      note = lines[i].split(': ')[0][2:]
      if note not in types:
        return None, f"Invalid note type: {note}. Must be in one of {types}"
      score = lines[i].split(': ')[1]
      notes[note] = int(score) if score.isdecimal() else -1
    
    # If any of the note types are missing, throw error
    if not all(note in notes for note in types):
      return None, f"Missing note types. Must have all of {types}"
    songInfo.notes = notes
    # Get fast and slow
    if len(lines) > 6 + len(types):
      fast = lines[6 + len(types)].split(': ')[1]
      songInfo.fast = int(fast) if fast.isdecimal() else -1
      slow = lines[7 + len(types)].split(': ')[1]
      songInfo.slow = int(slow) if slow.isdecimal() else -1

    return songInfo, None
  except:
    return None, 'Invalid input.'

def calculateImgDimensions(width, height):
  if width / height < 16 / 9:
    w = width
    h = int(w * 9 / 16)
  else:
    w = width
    h = height

  x = np.arange(450, 3000, 1)
  y = 248.515 * np.log(0.413359 * x - 179.201) - 581.131
  y2 = h/w * x

  line1 = LineString(np.column_stack((x, y)))
  line2 = LineString(np.column_stack((x, y2)))
  intersection = line1.intersection(line2)

  # get the second intersection point
  p = list(intersection.geoms)[1]
  return (int(p.x), int(p.x * (height / width)))

def rescaleImage(img):
  w = int(img.shape[1])
  h = int(img.shape[0])
  dim = calculateImgDimensions(w, h)
  return cv2.resize(img, dim, interpolation=cv2.INTER_AREA)

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

def getAboutTP():
  msg = "Technical points (TP) is a Cytus term for the measure of the overall accuracy of an individual play. It is calculated based on note timing and describes how far on average a player deviates from hitting the note at its exact timing."
  msg += "\n\nThe TP calculated by this program is calculated by giving each note type the following weighting:"
  for note in noteWeights:
    msg += f"\n  - {note}: {int(noteWeights[note]*100)}%"
  return msg

def validateSong(songInfo: SongInfo, songData: dict):
  '''Validates a song against the song data'''
  songDataNotes = songData['notes'][str(getDifficulty(songInfo.difficulty))]
  # If there are no fast/slow notes, then the fast/slow counts must be 0. 
  # If there are fast/slow notes, then the sum of fast/slow must equal the total number of great, good, and bad notes
  fastSlow = not songInfo.hasFastSlow() or ((songInfo.fast + songInfo.slow) == (songInfo.notes['Great'] + songInfo.notes['Good'] + songInfo.notes['Bad']))
  # If any of the note counts are negative, then the song is invalid
  noteScores = all(songInfo.notes[note] >= 0 for note in types)
  # If the sum of the note counts is not equal to the total number of notes for the song, then the song is invalid
  totalNotes = songInfo.totalNotes() == songDataNotes
  # If the score is less than the score required for the detected rank, then the song is invalid
  rank = songInfo.score >= songData['difficulty'][str(getDifficulty(songInfo.difficulty))][f'score{songInfo.rank}']
  # If the score is greater than 10 million, assume it's impossible
  impossibleScore = songInfo.score < 10000000

  return fastSlow and noteScores and totalNotes and rank and impossibleScore, {
    'fastSlow': fastSlow,
    'noteScores': noteScores,
    'totalNotes': totalNotes,
    'rank': rank,
    'impossibleScore': impossibleScore
  }