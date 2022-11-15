import urllib.request, json 
from difflib import get_close_matches

SONGS_URL = 'https://bestdori.com/api/songs/all.5.json'
BANDS_URL = 'https://bestdori.com/api/bands/all.1.json'
headers = {
  'authority': 'bestdori.com',
  'method': 'GET',
  'path': '/api/songs/all.5.json',
  'scheme': 'https',
  'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.42'
}

def getSongs():
  return getJson(SONGS_URL)
    
def getBands():
  return getJson(BANDS_URL)

def getJson(url: str):
  request = urllib.request.Request(url, headers=headers)
  with urllib.request.urlopen(request) as response:
    data = json.loads(response.read())
    return data

class BestdoriAPI:
  def __init__(self, server=1):
    self.songs = getSongs()
    self.bands = getBands()
    self.server = server
  
  def closestSongName(self, songName):
    matches = get_close_matches(songName, self.getSongNames(), n=1, cutoff=0.8)
    return matches[0] if len(matches) > 0 else None
  
  def getBandName(self, bandId: int):
    bandName = self.bands[str(bandId)]['bandName'][self.server]
    ballbackBandName = next(band for band in self.bands[str(bandId)]['bandName'] if band is not None)
    return bandName if bandName is not None else ballbackBandName

  def getSongNames(self):
    songNames = []
    for song in self.songs:
      title = self.songs[song]['musicTitle'][self.server]
      fallbackTitle = next(song for song in self.songs[song]['musicTitle'] if song is not None)
      songNames.append(title if title is not None else fallbackTitle)
    return songNames

  def getSong(self, songName):
    name = self.closestSongName(songName)
    for song in self.songs:
      title = self.songs[song]['musicTitle'][self.server]
      fallbackTitle = next(song for song in self.songs[song]['musicTitle'] if song is not None)
      if title == name or fallbackTitle == name:
        return self.songs[song]
    return None

  def getSongBand(self, songName):
    song = self.getSong(songName)
    return self.getBandName(song['bandId'])

  def getDifficulty(self, song, difficulty: int):
    return song['difficulty'][str(difficulty)]['playLevel']

  def getDifficultyFromSongName(self, songName, difficulty: int):
    song = self.findSongFromSongName(songName)
    return self.getDifficulty(song, difficulty)