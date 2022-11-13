
import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT, errors
from dotenv import load_dotenv
import os
import re
from bson.objectid import ObjectId

from api import SongInfo
from functions import songInfoToStr
from consts import *

class Database:
  def __init__(self):
    load_dotenv()
    self.client = MongoClient(os.getenv('ATLAS_URI'))
    self.db = self.client[os.getenv('DB_NAME')]
    print("Connected to the MongoDB database!")


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
    song = self.db[userId]['songs'].find_one({'_id': ObjectId(songId)})
    self.log(userId, f"GET: User {userId} got song with ID {songId}")
    return song


  def get_scores_of_song(self, userId: str, songName: str):
    scores = self.db[userId]['songs'].find({"$text": {"$search": songName, "$caseSensitive": False}}).sort('score', ASCENDING) 
    self.log(userId, f'GET: User {userId} got scores with query text "{songName}"')
    return list(scores)


  def get_song_with_highest(self, userId: str, songName: str, difficulty: str, query: str):
    songs = self.db[userId]['songs'].find({
      "$text": {"$search": songName, "$caseSensitive": False},
      "difficulty": difficulties.index(difficulty),
    }).sort(query, DESCENDING).limit(1)
    self.log(userId, f'GET: User {userId} got highest {query} score with query text "{songName}"')
    return list(songs)

  def get_highest_songs(self, userId: str, songName: str, difficulty: str):
    res = []
    for category in highest:
      songs = self.db[userId]['songs'].find({
        "$text": {"$search": songName, "$caseSensitive": False},
        "difficulty": difficulties.index(difficulty),
      }).sort(category[0], DESCENDING if category[2] == 'DESC' else ASCENDING).limit(1)
      res.extend(list(songs))

    self.log(userId, f'GET: User {userId} got highest scores with query text "{songName}"')
    return res

  def update_song(self, userId: str, songId: str, song: SongInfo):
    self.db[userId]['songs'].update_one(
      {"_id": ObjectId(songId)},
      {"$set": song.toDict()}
    )

    updated_song = self.db[userId]['songs'].find_one({"_id": ObjectId(songId)})
    self.log(userId, f"PUT: User {userId} updated song with ID {songId}: \n{updated_song}")
    return updated_song


  def delete_song(self, userId: str, songId: str):
    self.db[userId]['songs'].delete_one({"_id": ObjectId(songId)})
    self.log(userId, f"DELETE: User {userId} deleted song with ID {songId}")


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