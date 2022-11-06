# shut opencv errors up
import os
os.environ["OPENCV_LOG_LEVEL"]="SILENT"

import cv2
import glob
from api import *


# Test on directory of images
mode = 'cropped'
path = 'live'

images = [cv2.imread(image) for image in glob.glob(f"testdata/{path}/*.jpg")]

for image in images:
  print("---")
  songName, difficulty = getSong(image, mode)
  rank = getRank(image, mode)
  score, highScore = getScore(image, mode)
  maxCombo = getMaxCombo(image, mode)
  notes = getNotes(image, mode)
  print(f"{songName} - {difficulty}")
  print(f"Rank: {rank}, Score: {score}, High Score: {highScore}, Max Combo: {maxCombo}")
  print(notes)