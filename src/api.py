# The functions for getting song information from an image
import numpy as np
import cv2
import pytesseract

import sys
import datetime

from song_info import SongInfo
from functions import fetchRanks, fetchNoteTypes, fetchDifficulties, fetchScoreIcon, fetchMaxCombo, fetchFastSlow, rescaleImage
from consts import ranks, maxComboDim, ENABLE_LOGGING

def writeData(img, prefix, res='', path='data', ext='tif'):
  if ENABLE_LOGGING:
    path = f"{sys.path[0]} + /../testdata/{path}/{prefix}-{str(datetime.datetime.now()).split('.')[0].replace(':', '-')}"
    cv2.imwrite(f'{path}.{ext}', img)
    try:
      with open(f'{path}.gt.txt', 'w') as f:
        f.write(str(res))
    except:
      pass

class ScoreAPI:
  '''ScoreAPI class so that templates only need to be initialized once'''
  def __init__(self,  mode='cropped', draw=False):
    self.mode = mode
    self.draw = draw
    self.templates = {
      'ranks': fetchRanks(mode),
      'noteTypes': fetchNoteTypes(mode),
      'difficulties': fetchDifficulties(mode),
      'scoreIcon': fetchScoreIcon(mode),
      'maxCombo': fetchMaxCombo(mode),
      'fastSlow': fetchFastSlow(mode)
    }

  def getRank(self, image):
    '''Gets the rank of the image result'''
    # Try all the ranks and get the best match
    results = [(cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED), rank) for template, rank in self.templates['ranks']]
    # Get the rank of the best match
    result, rank = max(results, key=lambda x: x[0].max())

    # Draw the rectangle of the bounding box if draw is enabled
    if self.draw:
      h, w, _ = self.templates['ranks'][ranks.index(rank)][0].shape
      y, x = np.unravel_index(np.argmax(result), result.shape)
      cv2.rectangle(image, (x-1, y-1), (x+w+1, y+h+1), (0, 0, 255), 1)

    return rank

  def getNotes(self, image):
    '''Gets the different note counts of the image result'''
    noteScores = {}

    for template in self.templates['noteTypes']:
      tmp, type, ratio, tolerance = template

      # Get the location of the note type row
      result = cv2.matchTemplate(image, tmp, cv2.TM_CCOEFF_NORMED)
      h, w, _ = tmp.shape
      y, x = np.unravel_index(np.argmax(result), result.shape)

      # Get the bounding box where the score of the note type is
      tl_x, tl_y = x+w+20, y-6+tolerance[0]
      br_x, br_y = x+int(w*ratio), y+h+tolerance[1]

      # Draw the rectangle of the bounding box if draw is enabled
      if self.draw:
        cv2.rectangle(image, (tl_x-1, tl_y-1), (br_x+1, br_y+1), (0, 0, 255), 1)

      # Make image black and white for OCR
      crop = image[tl_y:br_y, tl_x:br_x]
      image_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
      blackAndWhiteImage = cv2.adaptiveThreshold(image_gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,\
            cv2.THRESH_BINARY, 9, 2)

      # Read the score of the note type from the image
      ROI = blackAndWhiteImage
      data = pytesseract.image_to_string(ROI, config="--psm 7 digits")
      res = int(data.strip()) if data.strip().isdecimal() else -1
      noteScores[type] = res

      # Write the data to testdata
      writeData(crop, f'Note-{type}', res)
    
    # Return the note type scores in a map
    return noteScores

  def getScore(self, image):
    '''Gets the score and high score of the image result'''
    # Get the location of the score icon
    result = cv2.matchTemplate(image, self.templates['scoreIcon'], cv2.TM_CCOEFF_NORMED)
    h, w, _ = self.templates['scoreIcon'].shape
    y, x = np.unravel_index(np.argmax(result), result.shape)

    # Use location of line separator to get the bounding box of the score
    tl_x, tl_y = x+w+5, y-10
    br_x, br_y = x+w+625, y+h+60

    # Draw the rectangle of the bounding box if draw is enabled
    if self.draw:
      cv2.rectangle(image, (tl_x-1, tl_y-1), (br_x+1, br_y+1), (0, 0, 255), 1)

    # Make image black and white for OCR
    crop = image[tl_y:br_y, tl_x:br_x]
    image_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    blackAndWhiteImage = cv2.adaptiveThreshold(image_gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,\
          cv2.THRESH_BINARY, 9, 2)

    # Read the score text from the image
    ROI = blackAndWhiteImage
    data = pytesseract.image_to_string(ROI, config="--psm 6")

    # Write the data to testdata
    writeData(crop, f'Score', data)

    lines = data.strip().splitlines()

    # If there are no scores, return a negative result
    if len(lines) == 0:
      return (-1, -1)
    
    # Get the score and high score
    score = lines[0].split(" ")[-1].strip()
    highScore = lines[1].split(" ")[-1].strip() if len(lines) > 1 else "0"

    # Return integer values of the scores, defaulting to 0 if the score is not a number
    return (int(score) if score.isdecimal() else 0, int(highScore) if highScore.isdecimal() else 0)

  def getSong(self, image):
    '''Gets the song and difficulty level of the image result'''
    # Try all the ranks and get the best match
    results = [(cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED), difficulty) for template, difficulty in self.templates['difficulties']]
    # Get the result and difficulty of the best match
    result, difficulty = max(results, key=lambda x: x[0].max())

    # Get the location of the difficulty
    h, w, _ = self.templates['difficulties'][0][0].shape
    y, x = np.unravel_index(np.argmax(result), result.shape)

    # Make a bounding box right of the difficulty for the song name
    tl_x, tl_y = x+w+10, y
    br_x, br_y = x+w+825, y+h

    # Draw the rectangle of the bounding box if draw is enabled
    if self.draw:
      cv2.rectangle(image, (tl_x-1, tl_y-1), (br_x+1, br_y+1), (0, 0, 255), 1)

    # Make image black and white for OCR
    crop = image[tl_y:br_y, tl_x:br_x]
    image_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    (_, blackAndWhiteImage) = cv2.threshold(image_gray, 150, 255, cv2.THRESH_BINARY)

    # Read the song name from the image
    ROI = blackAndWhiteImage
    data = pytesseract.image_to_string(ROI, config='--psm 7')

    # Write the data to testdata
    writeData(crop, f'Song', data)

    # Return the song name and difficulty
    return (data.strip(), difficulty)

  def getMaxCombo(self, image):
    '''Gets the max combo of the image result'''
    # Get the location of the max combo icon
    results = [(cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED), x) for x, template in enumerate(self.templates['maxCombo'])]
    result, index = max(results, key=lambda x: x[0].max())
    h, w, _ = self.templates['maxCombo'][index].shape
    y, x = np.unravel_index(np.argmax(result), result.shape)

    dim = maxComboDim[index]

    # Get the bounding box where the max combo is
    tl_x, tl_y = x+dim[0][0], y+h+dim[0][1]
    br_x, br_y = x+w+dim[1][0], y+h+dim[1][1]

    # Draw the rectangle of the bounding box if draw is enabled
    if self.draw:
      cv2.rectangle(image, (tl_x-1, tl_y-1), (br_x+1, br_y+1), (0, 0, 255), 1)

    # Make image black and white for OCR
    crop = image[tl_y:br_y, tl_x:br_x]
    image_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    (_, blackAndWhiteImage) = cv2.threshold(image_gray, 150, 255, cv2.THRESH_BINARY)

    # Read the max combo score from the image
    ROI = blackAndWhiteImage
    data = pytesseract.image_to_string(ROI, config="--psm 7 digits")
    data = data.strip()

    # Write the data to testdata
    writeData(crop, f'MaxCombo', data)

    # Return the max combo score, defaulting to 0 if the score is not a number
    return int(data) if data.isdecimal() else 0, index == 1

  def getFastSlow(self, image):
    '''Gets the fast and slow count of the image result'''
    # Iterates through the fast/slow tuple templates
    res = []
    results = [(cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED), x) for x, template in enumerate(self.templates['fastSlow'])]
    for result, x in results:
      h, w, _ = self.templates['fastSlow'][x].shape
      y, x = np.unravel_index(np.argmax(result), result.shape)

      # Get the bounding box where the fast/slow score is
      tl_x, tl_y = x+w, y-2
      br_x, br_y = x+(w*2), y+h

      # Draw the rectangle of the bounding box if draw is enabled
      if self.draw:
        cv2.rectangle(image, (tl_x-1, tl_y-1), (br_x+1, br_y+1), (0, 0, 255), 1)

      # Make image black and white for OCR
      crop = image[tl_y:br_y, tl_x:br_x]
      image_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
      blackAndWhiteImage = cv2.adaptiveThreshold(image_gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,\
          cv2.THRESH_BINARY, 9, 2)
      # Read the fast/slow score from the image
      ROI = blackAndWhiteImage
      data = pytesseract.image_to_string(ROI, config="--psm 7 digits")
      data = data.strip()

      # Write the data to testdata
      writeData(crop, f'FastSlow', data)

      res.append(int(data) if data.isdecimal() else -1)

    # Returns the result in a list. The list should be of the same length as the tuple of templates
    return res

  def getSongInfo(self, image):
    '''Gets the song information from an image'''
    # Rescale the image according to its aspect ratio
    img = rescaleImage(image)

    # Get the song name and difficulty
    song, difficulty = self.getSong(img)
    # Get the score rank
    rank = self.getRank(img)
    # Get the score and high score
    score, highScore = self.getScore(img)
    # Get the max combo
    maxCombo, fastSlow = self.getMaxCombo(img)
    if fastSlow:
      fast, slow = self.getFastSlow(img)
    else:
      fast, slow = -1, -1
    # Get the note type scores
    notes = self.getNotes(img)

    # Write the data to testdata
    writeData(img, f'SongInfo', path='songs', ext='png')

    songInfo = SongInfo(song, difficulty, rank, score, highScore, maxCombo, notes, fast, slow)
    return songInfo, img

  def jsonOutput(self, image):
    '''Returns the result of the song information in a json format'''
    # Get the song name and difficulty
    song, difficulty = self.getSong(image)
    # Get the score rank
    rank = self.getRank(image)
    # Get the score and high score
    score, highScore = self.getScore(image)
    # Get the max combo
    maxCombo = self.getMaxCombo(image)
    # Get the note type scores
    notes = self.getNotes(image)

    # Return the results in a json object
    return {
      "song": song,
      "difficulty": difficulty,
      "rank": rank,
      "score": score,
      "highScore": highScore,
      "maxCombo": maxCombo,
      "notes": notes
    }