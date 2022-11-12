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
  image = cv2.imread(path)

  scoreAPI = ScoreAPI()
  song = scoreAPI.getSongInfo(image)

  print("---")
  print(song.toJSON())  
  print(song.totalNotes())
  print(song.calculateTP())


# testDir('live')
testImage('testdata/test3.jpg')
