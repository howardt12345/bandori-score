import urllib.request, json 
from difflib import get_close_matches

SONGS_URL = 'https://bestdori.com/api/songs/'
SONGS_ALL = 'all.5.json'
BANDS_URL = 'https://bestdori.com/api/bands/all.1.json'
def headers(path: str): 
  return {
    'authority': 'bestdori.com',
    'method': 'GET',
    'path': path,
    'scheme': 'https',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.42'
  }

def getSongs():
  return getJson(SONGS_URL + SONGS_ALL, (SONGS_URL + SONGS_ALL).split('.com/')[1])

def getSong(songId: str):
  return getJson(f'{SONGS_URL}{songId}.json', f'{SONGS_URL}{songId}.json'.split('.com/')[1])
    
def getBands():
  return getJson(BANDS_URL, BANDS_URL.split('.com/')[1])

def getJson(url: str, path: str):
  request = urllib.request.Request(url, headers=headers(path))
  with urllib.request.urlopen(request) as response:
    data = json.loads(response.read())
    return data

class BestdoriAPI:
  def __init__(self, server=1):
    self.server = server
    self.songs = getSongs()
    self.bands = getBands()
  
  def closestSongName(self, songName):
    matches = get_close_matches(songName, self.getSongNames(), n=1, cutoff=0.4)
    return matches[0] if len(matches) > 0 else None
  
  def getBandName(self, bandId: int):
    bandName = self.bands[str(bandId)]['bandName'][self.server]
    fallbackBandName = next(band for band in self.bands[str(bandId)]['bandName'] if band is not None)
    return bandName if bandName is not None else fallbackBandName

  def getSongNames(self):
    songNames = []
    for song in self.songs:
      title = self.songs[song]['musicTitle'][self.server]
      fallbackTitle = next(song for song in self.songs[song]['musicTitle'] if song is not None)
      songNames.append(title if title is not None else fallbackTitle)
    return songNames

  def getSong(self, songName, songInfo=True):
    name = self.closestSongName(songName)
    song, info = None, None
    key = ""
    for s in self.songs:
      title = self.songs[s]['musicTitle'][self.server]
      fallbackTitle = next(song for song in self.songs[s]['musicTitle'] if song is not None)
      if title == name or fallbackTitle == name:
        key = s
        song = self.songs[s]
        break
    if songInfo and key:
      info = getSong(key)
    return key, song, info

  def getSongBand(self, songName):
    _, song, _ = self.getSong(songName)
    return self.getBandName(song['bandId'])

  def getSongName(self, song):
    title = song['musicTitle'][self.server]
    fallbackTitle = next(song for song in song['musicTitle'] if song is not None)
    return title if title is not None else fallbackTitle

  def getDifficulty(self, song: dict | str, difficulty: int):
    if type(song) is dict:
      return song['difficulty'][str(difficulty)]['playLevel']
    elif type(song) is str:
      _, s, _ = self.getSong(song)
      return s['difficulty'][str(difficulty)]['playLevel']

  def getDifficultyFromSongName(self, songName, difficulty: int):
    song = self.getSong(songName)
    return self.getDifficulty(song, difficulty)