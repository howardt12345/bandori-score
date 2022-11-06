# shut opencv errors up
import os
os.environ["OPENCV_LOG_LEVEL"]="SILENT"

import cv2
import glob
from api import *


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

  print("---")
  songName, difficulty = getSong(image, mode)
  rank = getRank(image, mode)
  score, highScore = getScore(image, mode)
  maxCombo = getMaxCombo(image, mode)
  notes = getNotes(image, mode)
  print(f"{songName} - {difficulty}")
  print(f"Rank: {rank}, Score: {score}, High Score: {highScore}, Max Combo: {maxCombo}")
  print(notes)


# Test on single image
def testImage2(path):
  mode = 'cropped'

  image = cv2.imread(path)

  scoreAPI = ScoreAPI()

  print("---")
  songName, difficulty = scoreAPI.getSong(image)
  rank = scoreAPI.getRank(image)
  score, highScore = scoreAPI.getScore(image)
  maxCombo = scoreAPI.getMaxCombo(image)
  notes = scoreAPI.getNotes(image)
  print(f"{songName} - {difficulty}")
  print(f"Rank: {rank}, Score: {score}, High Score: {highScore}, Max Combo: {maxCombo}")
  print(notes)

testDir('live')
# testImage('testdata/test.jpg')
# testImage2('testdata/test.jpg')
