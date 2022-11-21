# shut opencv errors up
import os

from db import Database
os.environ["OPENCV_LOG_LEVEL"]="SILENT"

import cv2
import glob
from api import *
from functions import *
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from shapely.geometry import LineString

import sys

def testDir(path):
  '''Test on a directory of images'''
  images = [cv2.imread(image) for image in glob.glob(f"testdata/{path}/*.jpg")]

  scoreAPI = ScoreAPI()

  for image in images:
    print("---")
    print(scoreAPI.basicOutput(image))

def testImage(path):
  '''Test on a single image'''
  image = cv2.imread(path)

  scoreAPI = ScoreAPI(draw=True)
  song, res = scoreAPI.getSongInfo(image)

  print("---")
  print(songInfoToStr(song))

  plt.imshow(cv2.cvtColor(res, cv2.COLOR_BGR2RGB))
  plt.show()


# testDir('live')
testImage(f'{sys.path[0]} + /../testdata/Screenshot_20221121-004050_BanG Dream!.png')