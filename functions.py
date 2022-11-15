
import numpy as np
import cv2
from io import BytesIO
from bestdori import BestdoriAPI
from consts import *
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

from song_info import SongInfo

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
  songInfo.songName = songName
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

def songCountGraph(songs: list[SongInfo], bd: BestdoriAPI, songName: str, difficulty: str = None, tag: str = "", showMaxCombo = False, userName: str = None, showSongNames = False, interpolate = False):
  scores = [song.score for song in songs]

  if interpolate:
    highScores = list(filter(lambda hs: hs > 0, [song.highScore for song in songs]))
    scoresSet = set(scores + highScores)
    newSongs = songs.copy()
    for song in songs:
      if song.highScore in scoresSet and song.highScore not in scores:
        newSongs.append(SongInfo(songName=song.songName, difficulty=song.difficulty, score=song.highScore, rank=song.rank))
    
    songs = sorted(newSongs, key=lambda song: song.score)
  
  scores = [song.score for song in songs]

  perfects = [song.notes['Perfect'] for song in songs]
  greats = [song.notes['Great'] for song in songs]
  goods = [song.notes['Good'] for song in songs]
  bads = [song.notes['Bad'] for song in songs]
  misses = [song.notes['Miss'] for song in songs]
  if showMaxCombo:
    maxCombos = [song.maxCombo for song in songs]
  TP = [song.calculateTP() for song in songs]

  figure, axis = plt.subplots(3, 1, figsize=(6 if len(songs) < 12 else len(songs)/2, 9))

  def format_number(data_value, indx):
    if data_value >= 1_000_000:
      formatter = '{:1.2f}M'.format(data_value*0.000_001)
    else:
      formatter = '{:1.2f}K'.format(data_value*0.001)
    return formatter
  
  def plotDot(x, y, a, v, h):
    axis[a].plot(x, y, 'o', color=difficultyColors[songs[x].difficulty])
    axis[a].annotate(f"{v}\n{'(Interpolated)' if songs[x].totalNotes() <= 0 else ''}".strip(), xy=(x, y), xytext=(0, 5*(1 if y > h else -1)), textcoords='offset points', ha='center', va='bottom' if y > h else 'top', fontsize=8)
    if showSongNames:
      axis[a].annotate(f'{songs[x].getSongName(bd)}\n{songs[x].getBandName(bd)}', xy=(x, y), xytext=(0, 10*(1 if y < h else -1)), textcoords='offset points', ha='left' if y < h else 'right', va='bottom' if y < h else 'top', fontsize=6, rotation=90)

  axis[0].plot(scores, color='silver')
  for i, v in enumerate(scores):
    plotDot(i, v, 0, v, min(scores) + (max(scores) - min(scores)) / 2)

  axis[0].set_title("Scores")
  axis[0].axes.get_xaxis().set_visible(False)
  axis[0].axes.get_yaxis().set_major_formatter(format_number)

  axis[0].grid(True)

  min_offset, max_offset = 1, 3
  min_notes, max_notes = 0, max(perfects if not showMaxCombo else [max(perfects), max(maxCombos)]) + max_offset
  distance = max_notes - min_notes

  perfect_transformed = [float(perfect + min_offset)/distance for perfect in perfects]
  great_transformed = [float(great + min_offset)/distance for great in greats]
  good_transformed = [float(good + min_offset)/distance for good in goods]
  bad_transformed = [float(bad + min_offset)/distance for bad in bads]
  miss_transformed = [float(miss + min_offset)/distance for miss in misses]
  axis[1].plot(perfect_transformed, label="Perfect", color='aquamarine', marker='o')
  axis[1].plot(great_transformed, label="Great", color='deeppink', marker='o')
  axis[1].plot(good_transformed, label="Good", color='greenyellow', marker='o')
  axis[1].plot(bad_transformed, label="Bad", color='mediumblue', marker='o')
  axis[1].plot(miss_transformed, label="Miss", color='slategray', marker='o')

  for i, v in enumerate(perfect_transformed):
    axis[1].annotate(perfects[i], xy=(i, v), xytext=(0, 5), textcoords='offset points', ha='center', va='bottom')
  for i, v in enumerate(great_transformed):
    axis[1].annotate(greats[i], xy=(i, v), xytext=(0, 5), textcoords='offset points', ha='center', va='bottom')
  for i, v in enumerate(good_transformed):
    axis[1].annotate(goods[i], xy=(i, v), xytext=(0, 5), textcoords='offset points', ha='center', va='bottom')
  for i, v in enumerate(bad_transformed):
    axis[1].annotate(bads[i], xy=(i, v), xytext=(0, 5), textcoords='offset points', ha='center', va='bottom')
  for i, v in enumerate(miss_transformed):
    axis[1].annotate(misses[i], xy=(i, v), xytext=(0, 5), textcoords='offset points', ha='center', va='bottom')
  
  if showMaxCombo:
    maxCombo_transformed = [float(maxCombo + min_offset)/distance for maxCombo in maxCombos]
    axis[1].plot(maxCombo_transformed, label="Max Combo", marker='o', color='lightgray')
    for i, v in enumerate(maxCombo_transformed):
      axis[1].annotate(maxCombos[i], xy=(i, v), xytext=(0, 5), textcoords='offset points', ha='center', va='bottom')

  axis[1].ticklabel_format(style='plain', axis='both', useOffset=False)
  axis[1].set_title("Notes")
  axis[1].legend(loc='center right', prop={'size': 8})
  axis[1].axes.get_xaxis().set_visible(False)
  axis[1].set_yscale('logit', one_half="1/2", use_overline=True)

  amount, step = 7, 1
  rangeList = [y ** 2 for y in range(min_notes, min_notes+amount*step, step)]
  ticks = [float(x+min_offset)/distance for x in rangeList] + [0.5] + [float(max_notes-x-(max_offset-1))/distance for x in reversed(rangeList)]
  minorTicks = rangeList + [(max_notes-min_notes)/2] + [max_notes-x-max_offset for x in reversed(rangeList)]

  axis[1].set_yticks(ticks, minorTicks)
  axis[1].grid(True)

  min_tp = min(filter(lambda tp: tp > 0.01, TP))
  xs = np.arange(len(TP))
  tp_y = np.array([tp if tp > 0 else None for tp in TP])
  tp_mask = [True if tp > 0 else False for tp in TP]
 
  axis[2].plot(xs[tp_mask], tp_y[tp_mask], color='silver')
  axis[2].set_title("Technical Points")
  axis[2].set_ylim([min_tp-(1.0-min_tp)*0.25, 1.0])
  axis[2].grid(True)
  axis[2].axes.get_xaxis().set_visible(False)
  axis[2].axes.get_yaxis().set_major_formatter(PercentFormatter(1))

  for i, v in enumerate(TP):
    plotDot(i, v, 2, '{:,.2%}'.format(v), min_tp + (max(TP) - min_tp) / 2)

  figure.suptitle(f"{f'{userName}: ' if userName else ''}{f'({difficulty}) ' if difficulty else ' '}{bd.closestSongName(songName)}{f' with tag {tag}' if tag else ''}", fontsize=16)
  figure.tight_layout()
  plt.gcf().set_size_inches(7 if len(songs) < 7 else len(songs), 21)
  buf = BytesIO()
  plt.savefig(buf, format='png')
  buf.seek(0)
  plt.close()
  return buf

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