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
  
  def closestSongName(self, songName):
    matches = get_close_matches(songName, self.getSongNames(), n=1, cutoff=0.5)
    return matches[0] if len(matches) > 0 else None
  
  def getBandName(self, bandId: int):
    bands = getBands()
    bandName = bands[str(bandId)]['bandName'][self.server]
    fallbackBandName = next(band for band in bands[str(bandId)]['bandName'] if band is not None)
    return bandName if bandName is not None else fallbackBandName

  def getSongNames(self):
    songs = getSongs()
    songNames = []
    for song in songs:
      title = songs[song]['musicTitle'][self.server]
      fallbackTitle = next(song for song in songs[song]['musicTitle'] if song is not None)
      songNames.append(title if title is not None else fallbackTitle)
    return songNames

  def getSong(self, songName, songInfo=True):
    songs = getSongs()
    name = self.closestSongName(songName)
    song, info = None, None
    key = ""
    for s in songs:
      title = songs[s]['musicTitle'][self.server]
      fallbackTitle = next(song for song in songs[s]['musicTitle'] if song is not None)
      if title == name or fallbackTitle == name:
        key = s
        song = songs[s]
        break
    if songInfo and key:
      info = getSong(key)
    return key, song, info

  def getSongBand(self, songName):
    song = self.getSong(songName)
    return self.getBandName(song['bandId'])

  def getDifficulty(self, song, difficulty: int):
    return song['difficulty'][str(difficulty)]['playLevel']

  def getDifficultyFromSongName(self, songName, difficulty: int):
    song = self.getSong(songName)
    return self.getDifficulty(song, difficulty)