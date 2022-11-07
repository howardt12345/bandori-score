# shut opencv errors up
import os
os.environ["OPENCV_LOG_LEVEL"]="SILENT"

import cv2
import glob
from api import *
from functions import *

# Test on directory of images
def testDir(path):
  images = [cv2.imread(image) for image in glob.glob(f"testdata/{path}/*.jpg")]

  scoreAPI = ScoreAPI()

  for image in images:
    print("---")
    print(scoreAPI.basicOutput(image))

# Test on single image
def testImage(path):
  mode = 'cropped'

  image = cv2.imread(path)
  
  scoreAPI = ScoreAPI()
  song = scoreAPI.getSongInfo(image)

  print("---")
  songName, difficulty = song.getSong(image, mode)
  rank = song.getRank(image, mode)
  score, highScore = song.getScore(image, mode)
  maxCombo = song.getMaxCombo(image, mode)
  notes = song.getNotes(image, mode)
  print(f"{songName} - {difficulty}")
  print(f"Rank: {rank}, Score: {score}, High Score: {highScore}, Max Combo: {maxCombo}")
  print(notes)


# Test on single image
def testImage2(path):
  image = cv2.imread(path)

  scoreAPI = ScoreAPI()

  print("---")
  print(scoreAPI.getSongInfo(image).toJSON())

# testDir('live')
testImage('testdata/test.jpg')
testImage2('testdata/test.jpg')
