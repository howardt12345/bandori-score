
import numpy as np
import cv2
import pytesseract
import json

class SongInfo:
  def __init__(self, songName, difficulty, rank, score, highScore, maxCombo, notes):
    self.songName = songName
    self.difficulty = difficulty
    self.rank = rank
    self.score = score
    self.highScore = highScore
    self.maxCombo = maxCombo
    self.notes = notes

  def __str__(self):
    return f"{self.songName} - {self.difficulty}\nRank: {self.rank}, Score: {self.score}, High Score: {self.highScore}, Max Combo: {self.maxCombo}\n{self.notes}"

  def __repr__(self):
    return self.__str__()

  def toDict(self):
    return {
      "songName": self.songName,
      "difficulty": self.difficulty,
      "rank": self.rank,
      "score": self.score,
      "highScore": self.highScore,
      "maxCombo": self.maxCombo,
      "notes": self.notes
    }
  
  def toJSON(self):
    return json.dumps(self.toDict())

# Function to fetch the templates for the different ranks
def fetchRanks(path):
  # List of ranks
  ranks = ['SS', 'S', 'A', 'B', 'C', 'D']
  imgs = []
  for rank in ranks:
    ext = "png" if path == 'direct' else "jpg"
    template = cv2.imread(f'assets/{path}/rank/{rank}.{ext}')
    # If the template exists, add it to the list
    if not template is None:
      imgs.append(( template, rank ))
  return imgs


# Function to fetch the templates for the different note types
# Returns the name of the note type as well as variables for OCR ROI positioning
def fetchNoteTypes(path):
  # List of note types and variables for OCR matching
  types = ['Perfect', 'Great', 'Good', 'Bad', 'Miss']
  ratios = [2.1, 2.75, 2.8, 4.3, 3.8]
  tolerances = [(0, 0), (1, 0), (0, 0), (0, 3), (2, 5)] # The top and bottom tolerances of the note type bounding box
  imgs = []
  for i in range(len(types)):
    ext = "png" if path == 'direct' else "jpg"
    template = cv2.imread(f'assets/{path}/score/{types[i]}.{ext}')
    if not template is None:
      # If the template exists, add it to the list
      imgs.append(( template, types[i], ratios[i], tolerances[i] ))
  return imgs


# Function to fetch the templates for the different difficulties
# This will not work with 'direct' mode
def fetchDifficulties(path):
  difficulties = ['Easy', 'Normal', 'Hard', 'Expert', 'Special']
  imgs = []
  for difficulty in difficulties:
    ext = "png" if path == 'direct' else "jpg"
    template = cv2.imread(f'assets/{path}/difficulty/{difficulty}.{ext}')
    if not template is None:
      # If the template exists, add it to the list
      imgs.append(( template, difficulty ))
  return imgs


# Fetch score icon
def fetchScoreIcon(path):
  ext = "png" if path == 'direct' else "jpg"
  return cv2.imread(f'assets/{path}/ScoreIcon.{ext}')


# Fetch Max combo reference image
def fetchMaxCombo(path):
  ext = "png" if path == 'direct' else "jpg"
  return cv2.imread(f'assets/{path}/Max combo.{ext}')


# Function to get the rank of the image result
def getRank(image, mode='cropped'):
  templates = fetchRanks(mode)

  # Try all the ranks and get the best match
  results = [(cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED), rank) for template, rank in templates]
  # Get the rank of the best match
  _, rank = max(results, key=lambda x: x[0].max())

  return rank

# Function to get the different note counts of the image result
def getNotes(image, mode='cropped'):
  templates = fetchNoteTypes(mode)

  noteScores = {}

  for template in templates:
    tmp, type, ratio, tolerance = template

    # Get the location of the note type row
    result = cv2.matchTemplate(image, tmp, cv2.TM_CCOEFF_NORMED)
    h, w, _ = tmp.shape
    y, x = np.unravel_index(np.argmax(result), result.shape)

    # Get the bounding box where the score of the note type is
    tl_x, tl_y = x+w+20, y-6+tolerance[0]
    br_x, br_y = x+int(w*ratio), y+h+tolerance[1]

    # Make image black and white for OCR
    image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    (_, blackAndWhiteImage) = cv2.threshold(image_gray, 117, 255, cv2.THRESH_BINARY)

    # Read the score of the note type from the image
    ROI = blackAndWhiteImage[tl_y:br_y, tl_x:br_x]
    data = pytesseract.image_to_string(ROI, config="--psm 6 digits")
    noteScores[type] = data.strip()
  
  # Return the note type scores in a map
  return noteScores


# Function to get the score and high score of the image result
def getScore(image, mode='cropped'):
  # Get the location of the line separator
  template = fetchScoreIcon(mode)
  result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
  h, w, _ = template.shape
  y, x = np.unravel_index(np.argmax(result), result.shape)

  # Use location of line separator to get the bounding box of the score
  tl_x, tl_y = x+w+5, y-10
  br_x, br_y = x+w+650, y+h+60

  # Make image black and white for OCR
  image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
  (_, blackAndWhiteImage) = cv2.threshold(image_gray, 188, 255, cv2.THRESH_BINARY)

  # Read the score text from the image
  ROI = blackAndWhiteImage[tl_y:br_y, tl_x:br_x]
  data = pytesseract.image_to_string(ROI)
  lines = data.strip().splitlines()

  if len(lines) == 0:
    return (-1,-1)
  
  # Get the score and high score
  score = lines[0].split(" ")[-1].strip()
  highScore = lines[1].split(" ")[-1].strip() if len(lines) > 1 else "0"

  # Return integer values of the scores, defaulting to 0 if the score is not a number
  return (int(score) if score.isdecimal() else 0, int(highScore) if highScore.isdecimal() else 0)

# Function to get the song and difficulty level of the image result
def getSong(image, mode='cropped'):
  templates = fetchDifficulties(mode)

  # Try all the ranks and get the best match
  results = [(cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED), difficulty) for template, difficulty in templates]
  # Get the result and difficulty of the best match
  result, difficulty = max(results, key=lambda x: x[0].max())

  # Get the location of the difficulty
  h, w, _ = templates[0][0].shape
  y, x = np.unravel_index(np.argmax(result), result.shape)

  # Make a bounding box right of the difficulty for the song name
  tl_x, tl_y = x+w, y
  br_x, br_y = x+w+750, y+h

  # Make image black and white for OCR
  image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
  (_, blackAndWhiteImage) = cv2.threshold(image_gray, 188, 255, cv2.THRESH_BINARY)

  # Read the song name from the image
  ROI = blackAndWhiteImage[tl_y:br_y, tl_x:br_x]
  data = pytesseract.image_to_string(ROI, config='--psm 6')

  # Return the song name and difficulty
  return (data.strip(), difficulty)


# Function to get the max combo of the image result
def getMaxCombo(image, mode='cropped'):
  # Get the location of the max combo text
  template = fetchMaxCombo(mode)
  result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)

  # USe the location of the max combo text to create bounding box for the max combo score
  h, w, _ = template.shape
  y, x = np.unravel_index(np.argmax(result), result.shape)
  tl_x, tl_y = x+5, y+h+10
  br_x, br_y = x+w-5, y+h+65

  # Make image black and white for OCR
  image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
  (_, blackAndWhiteImage) = cv2.threshold(image_gray, 150, 255, cv2.THRESH_BINARY)

  # Read the max combo score from the image
  ROI = blackAndWhiteImage[tl_y:br_y, tl_x:br_x]
  data = pytesseract.image_to_string(ROI, config="--psm 6 digits")
  data = data.strip()

  # Return the max combo score, defaulting to 0 if the score is not a number
  return int(data) if data.isdecimal() else 0


# A basic string output from an image
def basicOutput(image):
  # Get the song name and difficulty
  song, difficulty = getSong(image)
  # Get the score rank
  rank = getRank(image)
  # Get the score and high score
  score, highScore = getScore(image)
  # Get the max combo
  maxCombo = getMaxCombo(image)
  # Get the note type scores
  notes = getNotes(image)

  # Return the results in a formatted string
  return f"({difficulty}) {song}\nRank: {rank}, Score: {score}, High Score: {highScore}, Max Combo: {maxCombo}\n{notes}"