
from pymongo import MongoClient
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
    songDict = song.toDict()
    songDict['tag'] = tag

    new_song = self.db[userId]['songs'].insert_one(songDict)
    created_song = self.db[userId]['songs'].find_one(
      {"_id": new_song.inserted_id}
    )

    return created_song

  def get_songs(self, userId: str):
    songs = self.db[userId]['songs'].find()
    return list(songs)

  def get_song(self, userId: str, songId: str):
    song = self.db[userId]['songs'].find_one({"_id": ObjectId(songId)})
    return song

  def get_scores_of_song(self, userId: str, songName: str):
    scores = self.db[userId]['songs'].find({'songName': re.compile('^' + songName + '$', re.IGNORECASE)})
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


  def log(self, userId: str, message: str):
    self.db[userId]['log'].insert_one({"message": message})


  @staticmethod
  def songInfoMsg(song: dict):
    msg = ''
    msg += f"id: `{song.get('_id', '')}`\n"
    msg += f"tag: `{song.get('tag', '')}`\n"
    msg += f"```{songInfoToStr(SongInfo().fromDict(song))}```"
    return msg