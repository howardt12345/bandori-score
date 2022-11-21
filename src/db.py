
import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT, errors
from dotenv import load_dotenv
import os
import re
from bson.objectid import ObjectId

from song_info import SongInfo
from bestdori import BestdoriAPI
from functions import songInfoToStr
from consts import *

class Database:
  def __init__(self):
    load_dotenv()
    self.client = MongoClient(os.getenv('ATLAS_URI'))
    self.db = self.client[os.getenv('DB_NAME')]
    print("Connected to the MongoDB database!")
    self.bestdori = BestdoriAPI()


  def create_song(self, userId: str, song: SongInfo, tag: str):
    self.db[userId]['songs'].create_index([
      ('songName', TEXT), 
      ('tag', ASCENDING),
      ('difficulty', DESCENDING), 
      ('rank', ASCENDING), 
      ('score', DESCENDING), 
      ('highScore', DESCENDING),
      ('maxCombo', DESCENDING),
      ('notes.Perfect', DESCENDING),
      ('notes.Great', ASCENDING),
      ('notes.Good', ASCENDING),
      ('notes.Bad', ASCENDING),
      ('notes.Miss', ASCENDING),
      ('TP', DESCENDING),
      ('fast', ASCENDING),
      ('slow', ASCENDING),
    ], unique=True, name="Ensure unique")

    songDict = song.toDict()
    songDict['tag'] = tags.index(tag)

    try:
      new_song = self.db[userId]['songs'].insert_one(songDict)
      created_song = self.db[userId]['songs'].find_one(
        {"_id": new_song.inserted_id}
      )
      self.log(userId, f"POST: User {userId} created: \n{song}", songId=created_song.get('_id', ''))
      return created_song
    except errors.DuplicateKeyError:
      self.log(userId, f"POST: User {userId} tried to create a duplicate song: \n{song}")
      return -1
    except Exception as e:
      self.log(userId, f"POST: User {userId} tried to create a song but failed: \n{song}")
      return None


  def get_songs(self, userId: str):
    songs = self.db[userId]['songs'].find()
    self.log(userId, f"GET: User {userId} got all songs")
    return list(songs)


  def get_song(self, userId: str, songId: str):
    try: 
      song = self.db[userId]['songs'].find_one({'_id': ObjectId(songId)})
      self.log(userId, f"GET: User {userId} got song with ID {songId}")
      return song
    except Exception as e:
      self.log(userId, f"GET: User {userId} tried to get song with ID {songId} but failed")
      raise e


  def get_scores_of_song(self, userId: str, songName: str, difficulty: str = "", tag: str = "", matchExact=False):
    q = {
      'songName': re.compile('^' + re.escape(songName) + '$' if matchExact else re.escape(songName), re.IGNORECASE)
    }
    if difficulty and difficulty in difficulties:
      q['difficulty'] = difficulties.index(difficulty)
    if tag and tag in tags:
      q['tag'] = tags.index(tag)
    scores = self.db[userId]['songs'].find(q).sort('score', ASCENDING) 
    self.log(userId, f'GET: User {userId} got scores with query text "{songName}"')
    return list(scores)


  def get_song_with_highest(self, userId: str, songName: str, difficulty: str, tag: str, query: str, order: str):
    q = {}
    if songName:
      q['songName'] = re.compile('^' + re.escape(songName) + '$', re.IGNORECASE)
    if difficulty and difficulty in difficulties:
      q['difficulty'] = difficulties.index(difficulty)
    if tag and tag in tags:
      q['tag'] = tags.index(tag)

    if query == 'fastSlow':
      songs = self.get_fast_slow(userId, q)
    else: 
      songs = self.db[userId]['songs'].find(q).sort(query, DESCENDING if order == 'DESC' else ASCENDING).limit(1)
    self.log(userId, f'GET: User {userId} got highest {query} score with query text "{songName}"')
    lst = list(songs)
    return lst if len(lst) > 0 else None

  def get_highest_songs(self, userId: str, songName: str, difficulty: str, tag: str):
    q = {}
    if songName:
      q['songName'] = re.compile('^' + re.escape(songName) + '$', re.IGNORECASE)
    if difficulty and difficulty in difficulties:
      q['difficulty'] = difficulties.index(difficulty)
    if tag and tag in tags:
      q['tag'] = tags.index(tag)

    res = []
    for _, (key, value) in enumerate(highestDict.items()):
      if key == 'fastSlow':
        songs = self.get_fast_slow(userId, q)
        lst = list(songs)
        res.extend(lst if len(lst) > 0 else [None])
      else:
        songs = self.db[userId]['songs'].find(q).sort(key, DESCENDING if value[1] == 'DESC' else ASCENDING).limit(1)
        res.extend(list(songs))

    self.log(userId, f'GET: User {userId} got highest scores with query text "{songName}"')
    return res

  def update_song(self, userId: str, songId: str, song: SongInfo, tag: str = ""):
    songDict = song.toDict()
    if tag and tag in tags:
      songDict['tag'] = tags.index(tag)
    self.db[userId]['songs'].update_one(
      {"_id": ObjectId(songId)},
      {"$set": songDict}
    )

    updated_song = self.db[userId]['songs'].find_one({"_id": ObjectId(songId)})
    self.log(userId, f"PUT: User {userId} updated song with ID {songId}: \n{updated_song}")
    return updated_song


  def delete_song(self, userId: str, songId: str):
    self.db[userId]['songs'].delete_one({"_id": ObjectId(songId)})
    self.log(userId, f"DELETE: User {userId} deleted song with ID {songId}")


  def get_song_counts(self, userId: str, difficulty: str, tag: str):
    q = {}
    if difficulty and difficulty in difficulties:
      q['difficulty'] = difficulties.index(difficulty)
    if tag and tag in tags:
      q['tag'] = tags.index(tag)
    song_counts = self.db[userId]['songs'].aggregate([
      {"$match": q},
      {
        "$group": {
          "_id": "$songName",
          "count": {"$sum": 1}
        }
      },
    ])
    self.log(userId, f"GET: User {userId} got song counts")
    return list(song_counts)

  
  def get_recent_songs(self, userId: str, limit: int, tag: str = ""):
    q = {}
    if tag and tag in tags:
      q['tag'] = tags.index(tag)
    recent_songs = self.db[userId]['songs'].find(q).sort('_id', DESCENDING).limit(limit)
    self.log(userId, f"GET: User {userId} got recent songs")
    return list(recent_songs)

  
  def get_fast_slow(self, userId: str, q: dict):
    q1 = q.copy()
    q1['fast'] = {'$exists': True}
    q1['slow'] = {'$exists': True}
    return self.db[userId]['songs'].aggregate([
      {'$match': q1},
      {'$project': {
        'songName': 1,
        'difficulty': 1,
        'tag': 1,
        'rank': 1,
        'score': 1,
        'highScore': 1,
        'maxCombo': 1,
        'notes': 1,
        'TP': 1,
        'fast': 1, 
        'slow': 1, 
        'fastSlow': {'$add': ['$fast', '$slow'] }
      }},
      {'$group': {
        '_id': '$_id',
        'songName': {'$first': '$songName'},
        'difficulty': {'$first': '$difficulty'},
        'tag': {'$first': '$tag'},
        'rank': {'$first': '$rank'},
        'score': {'$first': '$score'},
        'highScore': {'$first': '$highScore'},
        'maxCombo': {'$first': '$maxCombo'},
        'notes': {'$first': '$notes'},
        'TP': {'$first': '$TP'},
        'fast': {'$first': '$fast'},
        'slow': {'$first': '$slow'},
        'fastSlow': {'$first': '$fastSlow'},
      }},
      {'$sort': {'fastSlow': ASCENDING}},
      {'$limit': 1}
    ])

  def log(self, userId: str, message: str, songId: str = ""):
    self.db[userId]['log'].insert_one({
      "message": message, 
      "timestamp": datetime.datetime.now(),
      "songId": songId,
      "userId": userId
    })
    print(message)


  @staticmethod
  def songInfoMsg(song: dict):
    msg = ''
    msg += f"id: `{song.get('_id', '')}`\n"
    msg += f"tag: `{tags[song.get('tag', '')]}`\n"
    msg += f"```{songInfoToStr(SongInfo().fromDict(song))}```"
    return msg