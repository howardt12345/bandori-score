
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import re

from api import SongInfo

class Database:
  def __init__(self):
    load_dotenv()
    self.client = MongoClient(os.getenv('ATLAS_URI'))
    self.db = self.client[os.getenv('DB_NAME')]
    print("Connected to the MongoDB database!")

  def create_song(self, userId: str, song: SongInfo):
    new_song = self.db[userId]['songs'].insert_one(song.toDict())
    created_song = self.db[userId]['songs'].find_one(
      {"_id": new_song.inserted_id}
    )

    return created_song

  def get_songs(self, userId: str):
    songs = self.db[userId]['songs'].find()
    return list(songs)

  def get_song(self, userId: str, songId: int):
    song = self.db[userId]['songs'].find_one({"_id": songId})
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

  def delete_song(self, userId: str, songId: int):
    self.db[userId]['songs'].delete_one({"_id": songId})


  def log(self, userId: str, message: str):
    self.db[userId]['log'].insert_one({"message": message})