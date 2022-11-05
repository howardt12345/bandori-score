# shut opencv errors up
import os
os.environ["OPENCV_LOG_LEVEL"]="SILENT"

import matplotlib.pyplot as plt
import numpy as np

import cv2
import pytesseract
import glob

def fetchRanks(path):
  ranks = ['SS', 'S', 'A', 'B', 'C', 'D']
  imgs = []
  for rank in ranks:
    ext = "png" if path == 'direct' else "jpg"
    template = cv2.imread(f'assets/{path}/rank/{rank}.{ext}')
    if not template is None:
      imgs.append(( template, rank ))
  return imgs

def fetchScores(path):
  scores = ['Perfect', 'Great', 'Good', 'Bad', 'Miss']
  ratios = [2.1, 2.75, 2.8, 4.3, 3.8]
  tolerances = [(0, 0), (1, 0), (0, 0), (0, 3), (2, 5)] # The top and bottom tolerances of the score bounding box
  imgs = []
  for i in range(len(scores)):
    ext = "png" if path == 'direct' else "jpg"
    template = cv2.imread(f'assets/{path}/score/{scores[i]}.{ext}')
    if not template is None:
      imgs.append(( template, scores[i], ratios[i], tolerances[i] ))
  return imgs

def getRank(image, mode):
  if mode == 'direct':
    templates = fetchRanks('direct')
  else:
    templates = fetchRanks('cropped')

  results = [(cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED), rank) for template, rank in templates]
  # Get the rank of the best match
  r_, rank = max(results, key=lambda x: x[0].max())

  return rank

def getScore(image, mode):
  if mode == 'direct':
    templates = fetchScores('direct')
  else:
    templates = fetchScores('cropped')

  for template in templates:
    tmp, score, ratio, tolerance = template

    result = cv2.matchTemplate(image, tmp, cv2.TM_CCOEFF_NORMED)
    h, w, _ = tmp.shape
    y, x = np.unravel_index(np.argmax(result), result.shape)

    tl_x, tl_y = x+w+5, y-6+tolerance[0]
    br_x, br_y = x+int(w*ratio), y+h+tolerance[1]
    cv2.rectangle(image, (tl_x-1, tl_y-1), (br_x+1, br_y+1), (0,0,255), 1)

    image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    (_, blackAndWhiteImage) = cv2.threshold(image_gray, 117, 255, cv2.THRESH_BINARY)

    plt.imshow(cv2.cvtColor(blackAndWhiteImage, cv2.COLOR_BGR2RGB))

    ROI = blackAndWhiteImage[tl_y:br_y, tl_x:br_x]
    data = pytesseract.image_to_string(ROI, config="--psm 6 digits")
    print(score, data)
  
  plt.show()


getScore(cv2.imread('testdata/test3.jpg'), 'cropped')

# Test on directory of images
# images = [cv2.imread(image) for image in glob.glob("testdata/live/*.jpg")]

# for image in images:
#   print(getRank(image, 'cropped'))