# The functions for getting song information from an image
import numpy as np
import cv2
import pytesseract

from functions import SongInfo, fetchRanks, fetchNoteTypes, fetchDifficulties, fetchScoreIcon, fetchMaxCombo
from consts import ranks

# ScoreAPI class so that templates only need to be initialized once
class ScoreAPI:
  def __init__(self,  mode='cropped', draw=False):
    self.mode = mode
    self.draw = draw
    self.templates = {
      'ranks': fetchRanks(mode),
      'noteTypes': fetchNoteTypes(mode),
      'difficulties': fetchDifficulties(mode),
      'scoreIcon': fetchScoreIcon(mode),
      'maxCombo': fetchMaxCombo(mode)
    }

  # Function to get the rank of the image result
  def getRank(self, image):
    # Try all the ranks and get the best match
    results = [(cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED), rank) for template, rank in self.templates['ranks']]
    # Get the rank of the best match
    result, rank = max(results, key=lambda x: x[0].max())

    # Draw the rectangle of the bounding box if draw is enabled
    if self.draw:
      h, w, _ = self.templates['ranks'][ranks.index(rank)][0].shape
      y, x = np.unravel_index(np.argmax(result), result.shape)
      cv2.rectangle(image, (x, y), (x+w, y+h), (0, 0, 255), 1)

    return rank

  # Function to get the different note counts of the image result
  def getNotes(self, image):
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
        cv2.rectangle(image, (tl_x, tl_y), (br_x, br_y), (0, 0, 255), 1)

      # Make image black and white for OCR
      image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
      (_, blackAndWhiteImage) = cv2.threshold(image_gray, 117, 255, cv2.THRESH_BINARY)

      # Read the score of the note type from the image
      ROI = blackAndWhiteImage[tl_y:br_y, tl_x:br_x]
      data = pytesseract.image_to_string(ROI, config="--psm 6 digits")
      noteScores[type] = int(data.strip()) if data.strip().isdecimal() else -1
    
    # Return the note type scores in a map
    return noteScores

  # Function to get the score and high score of the image result
  def getScore(self, image):
    # Get the location of the score icon
    result = cv2.matchTemplate(image, self.templates['scoreIcon'], cv2.TM_CCOEFF_NORMED)
    h, w, _ = self.templates['scoreIcon'].shape
    y, x = np.unravel_index(np.argmax(result), result.shape)

    # Use location of line separator to get the bounding box of the score
    tl_x, tl_y = x+w+5, y-10
    br_x, br_y = x+w+625, y+h+60

    # Draw the rectangle of the bounding box if draw is enabled
    if self.draw:
      cv2.rectangle(image, (tl_x, tl_y), (br_x, br_y), (0, 0, 255), 1)

    # Make image black and white for OCR
    image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    (_, blackAndWhiteImage) = cv2.threshold(image_gray, 188, 255, cv2.THRESH_BINARY)

    # Read the score text from the image
    ROI = blackAndWhiteImage[tl_y:br_y, tl_x:br_x]
    data = pytesseract.image_to_string(ROI)
    lines = data.strip().splitlines()

    # If there are no scores, return a negative result
    if len(lines) == 0:
      return (-1, -1)
    
    # Get the score and high score
    score = lines[0].split(" ")[-1].strip()
    highScore = lines[1].split(" ")[-1].strip() if len(lines) > 1 else "0"

    # Return integer values of the scores, defaulting to 0 if the score is not a number
    return (int(score) if score.isdecimal() else 0, int(highScore) if highScore.isdecimal() else 0)

  # Function to get the song and difficulty level of the image result
  def getSong(self, image):
    # Try all the ranks and get the best match
    results = [(cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED), difficulty) for template, difficulty in self.templates['difficulties']]
    # Get the result and difficulty of the best match
    result, difficulty = max(results, key=lambda x: x[0].max())

    # Get the location of the difficulty
    h, w, _ = self.templates['difficulties'][0][0].shape
    y, x = np.unravel_index(np.argmax(result), result.shape)

    # Make a bounding box right of the difficulty for the song name
    tl_x, tl_y = x+w+10, y
    br_x, br_y = x+w+750, y+h

    # Draw the rectangle of the bounding box if draw is enabled
    if self.draw:
      cv2.rectangle(image, (tl_x, tl_y), (br_x, br_y), (0, 0, 255), 1)

    # Make image black and white for OCR
    image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    (_, blackAndWhiteImage) = cv2.threshold(image_gray, 188, 255, cv2.THRESH_BINARY)

    # Read the song name from the image
    ROI = blackAndWhiteImage[tl_y:br_y, tl_x:br_x]
    data = pytesseract.image_to_string(ROI, config='--psm 6')

    # Return the song name and difficulty
    return (data.strip(), difficulty)

  # Function to get the max combo of the image result
  def getMaxCombo(self, image):
    # Get the location of the max combo icon
    result = cv2.matchTemplate(image, self.templates['maxCombo'], cv2.TM_CCOEFF_NORMED)
    h, w, _ = self.templates['maxCombo'].shape
    y, x = np.unravel_index(np.argmax(result), result.shape)

    # Get the bounding box where the max combo is
    tl_x, tl_y = x+5, y+h+10
    br_x, br_y = x+w-5, y+h+65

    # Draw the rectangle of the bounding box if draw is enabled
    if self.draw:
      cv2.rectangle(image, (tl_x, tl_y), (br_x, br_y), (0, 0, 255), 1)

    # Make image black and white for OCR
    image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    (_, blackAndWhiteImage) = cv2.threshold(image_gray, 150, 255, cv2.THRESH_BINARY)

    # Read the max combo score from the image
    ROI = blackAndWhiteImage[tl_y:br_y, tl_x:br_x]
    data = pytesseract.image_to_string(ROI, config="--psm 6 digits")
    data = data.strip()

    # Return the max combo score, defaulting to 0 if the score is not a number
    return int(data) if data.isdecimal() else 0

  def getSongInfo(self, image):
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

      songInfo = SongInfo(song, difficulty, rank, score, highScore, maxCombo, notes)
      return songInfo

  def basicOutput(self, image):
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

    # Return the results in a formatted string
    return f"({difficulty}) {song}\nRank: {rank}, Score: {score}, High Score: {highScore}, Max Combo: {maxCombo}\n{notes}"

  def jsonOutput(self, image):
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