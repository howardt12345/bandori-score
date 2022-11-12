
import datetime
from pymongo import MongoClient, DESCENDING, TEXT, errors
from dotenv import load_dotenv
import os
import re
from bson.objectid import ObjectId


from api import SongInfo
from functions import songInfoToStr

class Database:
  def __init__(self):
    load_dotenv()
    self.client = MongoClient(os.getenv('ATLAS_URI'))
    self.db = self.client[os.getenv('DB_NAME')]
    print("Connected to the MongoDB database!")

  def create_song(self, userId: str, song: SongInfo, tag: str):
    self.db[userId]['songs'].create_index([
      ('songName', TEXT), 
      ('difficulty', TEXT), 
      ('rank', TEXT), 
      ('tag', TEXT),
      ('score', DESCENDING), 
      ('highScore', DESCENDING),
      ('maxCombo', DESCENDING),
      ('notes.Perfect', DESCENDING),
      ('notes.Great', DESCENDING),
      ('notes.Good', DESCENDING),
      ('notes.Bad', DESCENDING),
      ('notes.Miss', DESCENDING),
    ], unique=True)

    songDict = song.toDict()
    songDict['tag'] = tag

    try:
      new_song = self.db[userId]['songs'].insert_one(songDict)
      created_song = self.db[userId]['songs'].find_one(
        {"_id": new_song.inserted_id}
      )
      self.log(userId, created_song.get('_id', ''), f"User {userId} created: \n{song}")
      return created_song
    except errors.DuplicateKeyError:
      return -1
    except Exception as e:
      print(e)
      return None

  def get_songs(self, userId: str):
    songs = self.db[userId]['songs'].find()
    return list(songs)

  def get_song(self, userId: str, songId: str):
    song = self.db[userId]['songs'].find_one({"_id": ObjectId(songId)})
    return song

  def get_scores_of_song(self, userId: str, songName: str):
    scores = self.db[userId]['songs'].find({'songName': re.compile('^' + re.escape(songName) + '$', re.IGNORECASE)})
    return list(scores)

  def update_song(self, userId: str, songId: int, song: SongInfo):
    self.db[userId]['songs'].update_one(
      {"_id": songId},
      {"$set": song.toDict()}
    )

    updated_song = self.db[userId]['songs'].find_one({"_id": songId})
    return updated_song

  def delete_song(self, userId: str, songId: str):
    self.db[userId]['songs'].delete_one({"_id": ObjectId(songId)})


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
    msg += f"tag: `{song.get('tag', '')}`\n"
    msg += f"```{songInfoToStr(SongInfo().fromDict(song))}```"
    return msg