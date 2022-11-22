
from matplotlib.axes import Axes
import numpy as np
from io import BytesIO
from bestdori import BestdoriAPI
from consts import *
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import matplotlib.font_manager as fm

from bestdori import BestdoriAPI
from functions import songInfoToStr
from song_info import SongInfo

fprop = fm.FontProperties(fname='NotoSansJP-Regular.otf')
min_offset, max_offset = 1, 3

def plotDot(axes, x, y, v, h, song: SongInfo, bd: BestdoriAPI, showSongNames: bool = False):
  '''Plots a dot on the graph, adds a song label if specified'''
  axes.plot(x, y, 'o', color=difficultyColors[song.difficulty])
  axes.annotate(
    f"{v}\n{'(int.)' if song.totalNotes() <= 0 else ''}".strip(), 
    xy=(x, y), 
    xytext=(0, 5*(1 if y > h else -1)), 
    textcoords='offset points', 
    ha='center', 
    va='bottom' if y > h else 'top', 
    fontsize=8
  )
  if showSongNames:
    axes.annotate(
      f'{song.getSongName(bd)}\n{song.getBandName(bd)}', 
      xy=(x, y), 
      xytext=(0, 10*(1 if y < h else -1)), 
      textcoords='offset points', 
      ha='left' if y < h else 'right', 
      va='bottom' if y < h else 'top', 
      fontsize=6, 
      rotation=90, 
      fontproperties=fprop
    )


def format_number(data_value, _):
  '''Formats the y scale number for thousands and millions'''
  if data_value >= 1_000_000:
    formatter = '{:1.2f}M'.format(data_value*0.000_001)
  else:
    formatter = '{:1.2f}K'.format(data_value*0.001)
  return formatter


def scoreGraph(axes: Axes, scores, songs, bd: BestdoriAPI, showSongNames: bool = False):
  '''Plots a graph of the scores'''
  axes.plot(scores, color='silver')
  for i, v in enumerate(scores):
    plotDot(axes, i, v, v, min(scores) + (max(scores) - min(scores)) / 2, songs[i], bd, showSongNames)

  axes.set_title("Scores")
  axes.axes.get_xaxis().set_visible(False)
  axes.axes.get_yaxis().set_major_formatter(format_number)

  axes.grid(True)


def notesGraph(axes: Axes, songs, showMaxCombo: bool = False):
  '''Plots the perfect, great, good, bad, miss, and max combo counts on a graph. The graph shows more difference between notes on the top and bottom of the graph'''
  perfects = [song.notes['Perfect'] for song in songs]
  greats = [song.notes['Great'] for song in songs]
  goods = [song.notes['Good'] for song in songs]
  bads = [song.notes['Bad'] for song in songs]
  misses = [song.notes['Miss'] for song in songs]
  if showMaxCombo:
    maxCombos = [song.maxCombo for song in songs]

  min_notes, max_notes = 0, max(perfects if not showMaxCombo else [max(perfects), max(maxCombos)]) + max_offset
  distance = max_notes - min_notes

  perfect_transformed = [float(perfect + min_offset)/distance for perfect in perfects]
  great_transformed = [float(great + min_offset)/distance for great in greats]
  good_transformed = [float(good + min_offset)/distance for good in goods]
  bad_transformed = [float(bad + min_offset)/distance for bad in bads]
  miss_transformed = [float(miss + min_offset)/distance for miss in misses]
  axes.plot(perfect_transformed, label="Perfect", color='aquamarine', marker='o')
  axes.plot(great_transformed, label="Great", color='deeppink', marker='o')
  axes.plot(good_transformed, label="Good", color='greenyellow', marker='o')
  axes.plot(bad_transformed, label="Bad", color='mediumblue', marker='o')
  axes.plot(miss_transformed, label="Miss", color='slategray', marker='o')

  for i, v in enumerate(perfect_transformed):
    axes.annotate(perfects[i], xy=(i, v), xytext=(0, 5), textcoords='offset points', ha='center', va='bottom')
  for i, v in enumerate(great_transformed):
    axes.annotate(greats[i], xy=(i, v), xytext=(0, 5), textcoords='offset points', ha='center', va='bottom')
  for i, v in enumerate(good_transformed):
    axes.annotate(goods[i], xy=(i, v), xytext=(0, 5), textcoords='offset points', ha='center', va='bottom')
  for i, v in enumerate(bad_transformed):
    axes.annotate(bads[i], xy=(i, v), xytext=(0, 5), textcoords='offset points', ha='center', va='bottom')
  for i, v in enumerate(miss_transformed):
    axes.annotate(misses[i], xy=(i, v), xytext=(0, 5), textcoords='offset points', ha='center', va='bottom')
  
  if showMaxCombo:
    maxCombo_transformed = [float(maxCombo + min_offset)/distance for maxCombo in maxCombos]
    axes.plot(maxCombo_transformed, label="Max Combo", marker='o', color='lightgray')
    for i, v in enumerate(maxCombo_transformed):
      axes.annotate(maxCombos[i], xy=(i, v), xytext=(0, 5), textcoords='offset points', ha='center', va='bottom')

  axes.ticklabel_format(style='plain', axis='both', useOffset=False)
  axes.set_title("Notes")
  axes.legend(loc='center right', prop={'size': 8})
  axes.axes.get_xaxis().set_visible(False)
  axes.set_yscale('logit', one_half="1/2", use_overline=True)

  amount, step = 7, 1
  rangeList = [y ** 2 for y in range(min_notes, min_notes+amount*step, step)]
  ticks = [float(x+min_offset)/distance for x in rangeList] + [0.5] + [float(max_notes-x-(max_offset-1))/distance for x in reversed(rangeList)]
  minorTicks = rangeList + [(max_notes-min_notes)/2] + [max_notes-x-max_offset for x in reversed(rangeList)]

  axes.set_yticks(ticks, minorTicks)
  axes.grid(True)

def TPgraph(axes: Axes, songs, bd: BestdoriAPI, showSongNames: bool = False):
  '''Plots the TP score calculated from each song'''
  TP = [song.calculateTP() for song in songs]
  min_tp = min(filter(lambda tp: tp > 0.01, TP))
  xs = np.arange(len(TP))
  tp_y = np.array([tp if tp > 0 else None for tp in TP])
  tp_mask = [True if tp > 0 else False for tp in TP]
 
  axes.plot(xs[tp_mask], tp_y[tp_mask], color='silver')
  axes.set_title("Technical Points")
  axes.set_ylim([min_tp-(1.0-min_tp)*0.25, 1.0])
  axes.grid(True)
  axes.get_xaxis().set_visible(False)
  axes.get_yaxis().set_major_formatter(PercentFormatter(1))
  
  for i, v in enumerate(TP):
    plotDot(axes, i, v, '{:,.2%}'.format(v), min_tp + (max(TP) - min_tp) / 2, songs[i], bd, showSongNames)

def fastSlowGraph(axes: Axes, songs):
  fast = [song['fast'] for song in songs]
  slow = [song['slow'] for song in songs]

  min_notes, max_notes = 0, max([max(fast), max(slow)]) + max_offset
  distance = max_notes - min_notes

  fast_transformed = [float(fast + min_offset)/distance for fast in fast]
  slow_transformed = [float(slow + min_offset)/distance for slow in slow]
  axes.plot(fast_transformed, label="Perfect", color='blue', marker='o')
  axes.plot(slow_transformed, label="Great", color='orange', marker='o')

  for i, v in enumerate(fast_transformed):
    axes.annotate(fast[i], xy=(i, v), xytext=(0, 5), textcoords='offset points', ha='center', va='bottom')
  for i, v in enumerate(slow_transformed):
    axes.annotate(slow[i], xy=(i, v), xytext=(0, 5), textcoords='offset points', ha='center', va='bottom')

  axes.ticklabel_format(style='plain', axis='both', useOffset=False)
  axes.set_title("Notes")
  axes.legend(loc='center right', prop={'size': 8})
  axes.axes.get_xaxis().set_visible(False)
  axes.set_yscale('logit', one_half="1/2", use_overline=True)

  amount, step = 7, 1
  rangeList = [y ** 2 for y in range(min_notes, min_notes+amount*step, step)]
  ticks = [float(x+min_offset)/distance for x in rangeList] + [0.5] + [float(max_notes-x-(max_offset-1))/distance for x in reversed(rangeList)]
  minorTicks = rangeList + [(max_notes-min_notes)/2] + [max_notes-x-max_offset for x in reversed(rangeList)]

  axes.set_yticks(ticks, minorTicks)
  axes.grid(True)

def songCountGraph(
  songs: list[songInfoToStr], 
  bd: BestdoriAPI, 
  songName: str, 
  difficulty: str = None, 
  tag: str = "", 
  showMaxCombo = False, 
  userName: str = None, 
  showSongNames = False, 
  interpolate = False
):
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

  fprop = fm.FontProperties(fname='NotoSansJP-Regular.otf')
  chartWidth = max(len(songs)/1.5, 10)
  chartHeight = 9

  figure, axis = plt.subplots(3, 1, figsize=(chartWidth, chartHeight))

  scoreGraph(axis[0], scores, songs, bd, showSongNames)
  notesGraph(axis[1], songs, showMaxCombo)
  TPgraph(axis[2], songs, bd, showSongNames)

  closestSongName = bd.closestSongName(songName)
  figure.suptitle(f"{f'{userName}: ' if userName else ''}{f'({difficulty}) ' if difficulty else ' '}{closestSongName if closestSongName else songName}{f' with tag {tag}' if tag else ''}", fontsize=16, fontproperties=fprop)
  figure.tight_layout()
  plt.gcf().set_size_inches(chartWidth, (chartHeight-2)*3)
  buf = BytesIO()
  plt.savefig(buf, format='png')
  buf.seek(0)
  plt.close()
  return buf