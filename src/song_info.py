import json
from bestdori import BestdoriAPI
from consts import *

class SongInfo:
  '''Object representing a song's info'''
  def __init__(self, songName="", difficulty="", rank="", score=-1, highScore=-1, maxCombo=-1, notes={'Perfect': -1, 'Great': -1, 'Good': -1, 'Bad': -1, 'Miss': -1}):
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
      "difficulty": difficulties.index(self.difficulty),
      "rank": ranks.index(self.rank),
      "score": self.score,
      "highScore": self.highScore,
      "maxCombo": self.maxCombo,
      "notes": self.notes,
      "TP": self.calculateTP()
    }
  
  def toJSON(self):
    return json.dumps(self.toDict())

  @staticmethod
  def fromDict(dict):
    return SongInfo(dict["songName"], difficulties[dict["difficulty"]], ranks[dict["rank"]], dict["score"], dict["highScore"], dict["maxCombo"], dict["notes"])

  @staticmethod
  def fromJSON(json):
    return SongInfo.fromDict(json.loads(json))

  def totalNotes(self):
    '''Returns the total number of notes in the song'''
    return sum(self.notes.values())

  def calculateTP(self):
    '''Calculates the Technical Points of the song based on note weighting'''
    tp = 0
    for noteType in self.notes:
      if self.notes[noteType] != -1:
        tp += self.notes[noteType] * noteWeights[noteType]
    return tp / self.totalNotes()

  def getSongData(self, bd: BestdoriAPI):
    _, song, _ = bd.getSong(self.songName)
    return song

  def getSongName(self, bd: BestdoriAPI):
    name = bd.closestSongName(self.songName)
    return name if name else self.songName

  def getBandName(self, bd: BestdoriAPI):
    return bd.getSongBand(self.songName)
