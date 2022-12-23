
import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT, errors
import motor.motor_asyncio as motor
from dotenv import load_dotenv
import os
import re
from bson.objectid import ObjectId
import logging

from song_info import SongInfo
from bestdori import BestdoriAPI
from functions import getDifficulty, hasDifficulty, getTag, hasTag, songInfoToStr
from consts import *

class Database:
  def __init__(self):
    load_dotenv()
    self.client = motor.AsyncIOMotorClient(os.getenv('ATLAS_URI'), serverSelectionTimeoutMS = 2000)
    self.db = self.client[os.getenv('DB_NAME')]
    logging.info("Connected to the MongoDB database!")
    self.bestdori = BestdoriAPI()


  async def create_song(self, userId: str, song: SongInfo, tag: str):
    await self.db[userId]['songs'].create_index([
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
    songDict['tag'] = getTag(tag)

    try:
      new_song = await self.db[userId]['songs'].insert_one(songDict)
      created_song = await self.db[userId]['songs'].find_one(
        {"_id": new_song.inserted_id}
      )
      await self.log(userId, f"POST: User {userId} created: \n{song}\n{created_song.get('_id', '')}", songId=created_song.get('_id', ''))
      return created_song
    except errors.DuplicateKeyError:
      await self.log(userId, f"POST: User {userId} tried to create a duplicate song: \n{song}")
      return -1
    except Exception as e:
      await self.log(userId, f"POST: User {userId} tried to create a song but failed: \n{song}")
      return None


  async def get_songs(self, userId: str):
    songs = self.db[userId]['songs'].find()
    await self.log(userId, f"GET: User {userId} got all songs")
    return await songs.to_list(length=None)


  async def get_song(self, userId: str, songId: str):
    try: 
      song = self.db[userId]['songs'].find_one({'_id': ObjectId(songId)})
      await self.log(userId, f"GET: User {userId} got song with ID {songId}")
      return await song
    except Exception as e:
      await self.log(userId, f"GET: User {userId} tried to get song with ID {songId} but failed")
      raise e


  async def get_scores_of_song(self, userId: str, songName: str, difficulty: str = "", tag: str = "", matchExact=False):
    q = {
      'songName': re.compile('^' + re.escape(songName) + '$' if matchExact else re.escape(songName), re.IGNORECASE)
    }
    if difficulty and hasDifficulty(difficulty):
      q['difficulty'] = getDifficulty(difficulty)
    if tag and hasTag(tag):
      q['tag'] = getTag(tag)
    scores = self.db[userId]['songs'].find(q).sort('score', ASCENDING) 
    await self.log(userId, f'GET: User {userId} got scores with query text "{songName}"')
    return await scores.to_list(length=None)


  async def get_song_with_best(self, userId: str, songName: str, difficulty: str, tag: str, query: str, order: str):
    q = {}
    if songName:
      q['songName'] = re.compile('^' + re.escape(songName) + '$', re.IGNORECASE)
    if difficulty and hasDifficulty(difficulty):
      q['difficulty'] = getDifficulty(difficulty)
    if tag and hasTag(tag):
      q['tag'] = getTag(tag)

    if query == 'fastSlow':
      songs = self.get_fast_slow(userId, q)
    else: 
      songs = self.db[userId]['songs'].find(q).sort(query, DESCENDING if order == 'DESC' else ASCENDING).limit(1)
    await self.log(userId, f'GET: User {userId} got best {query} score with query text "{songName}"')
    lst = await songs.to_list(length=None)
    return lst if len(lst) > 0 else None

  async def get_best_songs(self, userId: str, songName: str, difficulty: str, tag: str):
    q = {}
    if songName:
      q['songName'] = re.compile('^' + re.escape(songName) + '$', re.IGNORECASE)
    if difficulty and hasDifficulty(difficulty):
      q['difficulty'] = getDifficulty(difficulty)
    if tag and hasTag(tag):
      q['tag'] = getTag(tag)

    res = []
    for _, (key, value) in enumerate(bestDict.items()):
      if key == 'fastSlow':
        songs = self.get_fast_slow(userId, q)
        lst = await songs.to_list(length=None)
        res.extend(lst if len(lst) > 0 else [None])
      elif key == 'fullCombo' or key == 'allPerfect':
        if key == 'allPerfect':
          songs = self.get_all_perfect_songs(userId, q)
        else:
          songs = self.get_full_combo_songs(userId, q)
        lst = await songs.to_list(length=None)
        res.extend([len(lst) > 0])
      else:
        songs = self.db[userId]['songs'].find(q).sort(key, DESCENDING if value[1] == 'DESC' else ASCENDING).limit(1)
        lst = await songs.to_list(length=None)
        res.extend(lst if len(lst) > 0 else [None])

    await self.log(userId, f'GET: User {userId} got best scores with query text "{songName}"')
    return res

  async def update_song(self, userId: str, songId: str, song: SongInfo, tag: str = ""):
    songDict = song.toDict()
    if tag and hasTag(tag):
      songDict['tag'] = getTag(tag)
    self.db[userId]['songs'].update_one(
      {"_id": ObjectId(songId)},
      {"$set": songDict}
    )

    updated_song = await self.db[userId]['songs'].find_one({"_id": ObjectId(songId)})
    await self.log(userId, f"PUT: User {userId} updated song with ID {songId}", songId)
    return updated_song


  async def delete_song(self, userId: str, songId: str):
    await self.db[userId]['songs'].delete_one({"_id": ObjectId(songId)})
    await self.log(userId, f"DELETE: User {userId} deleted song with ID {songId}", songId)


  async def list_songs(self, userId: str, difficulty: str, tag: str):
    q = {}
    if difficulty and hasDifficulty(difficulty):
      q['difficulty'] = d = getDifficulty(difficulty)
    else:
      d = 3
    if tag and hasTag(tag):
      q['tag'] = getTag(tag)
    song_counts = self.db[userId]['songs'].aggregate([
      {"$match": q},
      { '$unwind': '$notes'},
      {'$project': {
        'songName': 1,
        'lowerSongName': {'$toLower': '$songName'},
        'difficulty': 1,
        'tag': 1,
        'rank': 1,
        'score': 1,
        'highScore': 1,
        'maxCombo': 1,
        'notes': 1,
        'TP': 1,
        'fullCombo': {
          '$cond': [
            {'$eq': ['$difficulty', d]},
            {'$eq': [{'$sum': ['$notes.Perfect', '$notes.Great']}, '$maxCombo']},
            False
          ],
        },
        'allPerfect': {'$eq': ['$notes.Perfect', '$maxCombo']},
      }},
      {
        "$group": {
          "_id": "$songName",
          "count": {"$sum": 1},
          "fullCombo": {'$max': '$fullCombo'},
          "allPerfect": {'$max': '$allPerfect'},
          "lowerSongName": {'$first': '$lowerSongName'},
        }
      },
      {'$sort': {'lowerSongName': ASCENDING}},
    ])
    await self.log(userId, f"GET: User {userId} got song counts")
    return await song_counts.to_list(length=None)

  
  async def get_recent_songs(self, userId: str, limit: int, tag: str = ""):
    q = {}
    if tag and hasTag(tag):
      q['tag'] = getTag(tag)
    recent_songs = self.db[userId]['songs'].find(q).sort('_id', DESCENDING).limit(limit)
    await self.log(userId, f"GET: User {userId} got recent songs")
    return await recent_songs.to_list(length=None)

  
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

  def get_full_combo_songs(self, userId: str, q: dict):
    q1 = q.copy()
    return self.db[userId]['songs'].aggregate([
      {'$match': q1},
      { '$unwind': '$notes'},
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
        'fullCombo': {'$sum': ['$notes.Perfect', '$notes.Great']}
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
        'fullCombo': {'$first': '$fullCombo'},
      }},
      {'$match': {'$expr': {'$eq': ['$fullCombo', '$maxCombo']}}},
      {'$sort': {'fullCombo': DESCENDING}}
    ])

  def get_all_perfect_songs(self, userId: str, q: dict):
    q1 = q.copy()
    return self.db[userId]['songs'].aggregate([
      {'$match': q1},
      { '$unwind': '$notes'},
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
      }},
      {'$match': {'$expr': {'$eq': ['$notes.Perfect', '$maxCombo']}}},
      {'$sort': {'score': DESCENDING}}
    ])

  async def log(self, userId: str, message: str, songId: str = ""):
    await self.db[userId]['log'].insert_one({
      "message": message, 
      "timestamp": datetime.datetime.now(),
      "songId": songId,
      "userId": userId
    })
    logging.info(message)
  
  async def ping_server(self):
    try:
      await self.client.server_info()
      return True
    except:
      return False


  @staticmethod
  def songInfoMsg(song: dict):
    msg = ''
    msg += f"id: `{song.get('_id', '')}`\n"
    msg += f"tag: `{tags[song.get('tag', '')]}`\n"
    msg += f"```{songInfoToStr(SongInfo().fromDict(song))}```"
    return msg