# shut opencv errors up
import os
os.environ["OPENCV_LOG_LEVEL"]="SILENT"

import matplotlib.pyplot as plt
import numpy as np

import cv2
import pytesseract
import glob

# Function to fetch the templates for the different ranks
def fetchRanks(path):
  ranks = ['SS', 'S', 'A', 'B', 'C', 'D']
  imgs = []
  for rank in ranks:
    ext = "png" if path == 'direct' else "jpg"
    template = cv2.imread(f'assets/{path}/rank/{rank}.{ext}')
    if not template is None:
      imgs.append(( template, rank ))
  return imgs

# Function to fetch the templates for the different note types
def fetchNoteTypes(path):
  types = ['Perfect', 'Great', 'Good', 'Bad', 'Miss']
  ratios = [2.1, 2.75, 2.8, 4.3, 3.8]
  tolerances = [(0, 0), (1, 0), (0, 0), (0, 3), (2, 5)] # The top and bottom tolerances of the note type bounding box
  imgs = []
  for i in range(len(types)):
    ext = "png" if path == 'direct' else "jpg"
    template = cv2.imread(f'assets/{path}/score/{types[i]}.{ext}')
    if not template is None:
      imgs.append(( template, types[i], ratios[i], tolerances[i] ))
  return imgs

# Function to fetch the templates for the different difficulties
def fetchDifficulties(path):
  difficulties = ['Easy', 'Normal', 'Hard', 'Expert', 'Special']
  imgs = []
  for difficulty in difficulties:
    ext = "png" if path == 'direct' else "jpg"
    template = cv2.imread(f'assets/{path}/difficulty/{difficulty}.{ext}')
    if not template is None:
      imgs.append(( template, difficulty ))
  return imgs

# Fetch Max combo reference image
def fetchMaxCombo(path):
  ext = "png" if path == 'direct' else "jpg"
  return cv2.imread(f'assets/{path}/Max combo.{ext}')

# Function to get the rank of the image result
def getRank(image, mode='cropped'):
  if mode == 'cropped':
    templates = fetchRanks('cropped')
  else:
    templates = fetchRanks('direct')

  results = [(cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED), rank) for template, rank in templates]
  # Get the rank of the best match
  r_, rank = max(results, key=lambda x: x[0].max())

  return rank

# Function to get the different note counts of the image result
def getNotes(image, mode='cropped'):
  if mode == 'cropped':
    templates = fetchNoteTypes('cropped')
  else:
    templates = fetchNoteTypes('direct')

  noteScores = {}

  for template in templates:
    tmp, type, ratio, tolerance = template

    result = cv2.matchTemplate(image, tmp, cv2.TM_CCOEFF_NORMED)
    h, w, _ = tmp.shape
    y, x = np.unravel_index(np.argmax(result), result.shape)

    tl_x, tl_y = x+w+20, y-6+tolerance[0]
    br_x, br_y = x+int(w*ratio), y+h+tolerance[1]

    image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    (_, blackAndWhiteImage) = cv2.threshold(image_gray, 117, 255, cv2.THRESH_BINARY)

    ROI = blackAndWhiteImage[tl_y:br_y, tl_x:br_x]
    data = pytesseract.image_to_string(ROI, config="--psm 6 digits")
    noteScores[type] = data.strip()
  
  return noteScores

# Function to get the score and high score of the image result
def getScore(image, mode='cropped'):
  line = cv2.matchTemplate(image, cv2.imread('assets/cropped/line.jpg'), cv2.TM_CCOEFF_NORMED)
  h, w, _ = cv2.imread('assets/cropped/line.jpg').shape
  y, x = np.unravel_index(np.argmax(line), line.shape)

  tl_x, tl_y = x+35, y-110
  br_x, br_y = x+w, y+h

  image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
  (_, blackAndWhiteImage) = cv2.threshold(image_gray, 188, 255, cv2.THRESH_BINARY)

  ROI = blackAndWhiteImage[tl_y:br_y, tl_x:br_x]
  data = pytesseract.image_to_string(ROI)
  lines = data.strip().splitlines()
  
  score = lines[0].split(" ")[-1].strip()
  highScore = lines[1].split(" ")[-1].strip() if len(lines) > 1 else "0"

  return (int(score) if score.isdecimal() else 0, int(highScore) if highScore.isdecimal() else 0)

# Function to get the song and difficulty level of the image result
def getSong(image, mode='cropped'):
  if mode == 'cropped':
    templates = fetchDifficulties('cropped')
  else:
    templates = fetchDifficulties('direct')

  results = [(cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED), difficulty) for template, difficulty in templates]
  # Get the result and difficulty of the best match
  result, difficulty = max(results, key=lambda x: x[0].max())
  h, w, _ = templates[0][0].shape
  y, x = np.unravel_index(np.argmax(result), result.shape)
  tl_x, tl_y = x+w, y
  br_x, br_y = x+w+750, y+h

  image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
  (_, blackAndWhiteImage) = cv2.threshold(image_gray, 188, 255, cv2.THRESH_BINARY)
  ROI = blackAndWhiteImage[tl_y:br_y, tl_x:br_x]
  data = pytesseract.image_to_string(ROI, config='--psm 6')

  return (data.strip(), difficulty)

def getMaxCombo(image, mode='cropped'):
  if mode == 'cropped':
    template = fetchMaxCombo('cropped')
  else:
    template = fetchMaxCombo('direct')

  result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
  h, w, _ = template.shape
  y, x = np.unravel_index(np.argmax(result), result.shape)
  tl_x, tl_y = x+5, y+h+10
  br_x, br_y = x+w-5, y+h+65

  image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
  (_, blackAndWhiteImage) = cv2.threshold(image_gray, 117, 255, cv2.THRESH_BINARY)

  ROI = blackAndWhiteImage[tl_y:br_y, tl_x:br_x]
  data = pytesseract.image_to_string(ROI, config="--psm 6 digits")

  return data.strip()


image = cv2.imread('testdata/test.jpg')
mode = 'cropped'

print(getRank(image, mode))
print(getNotes(image, mode))
print(getScore(image))
print(getSong(image))
print(getMaxCombo(image))

# Test on directory of images
test = True
if test:
  images = [cv2.imread(image) for image in glob.glob("testdata/multilive/*.jpg")]

  for image in images:
    print(getRank(image, mode))
    print(getNotes(image, mode))
    print(getScore(image))
    print(getSong(image, mode))
    print(getMaxCombo(image))