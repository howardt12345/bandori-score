
ranks = ['SS', 'S', 'A', 'B', 'C', 'D']
types = ['Perfect', 'Great', 'Good', 'Bad', 'Miss']
ratios = [2.115, 2.78, 2.85, 4.37, 3.9]
# The top and bottom tolerances of the note type bounding box
tolerances = [(0, -2), (0, 0), (0, 0), (0, 3), (2, 5)]
difficulties = ['Easy', 'Normal', 'Hard', 'Expert', 'Special']
tags = ['live', 'multilive', 'event']
tagIcons = ['🎵', '🎤', '🎉']
noteWeights = {
  'Perfect': 1,
  'Great': 0.75,
  'Good': 0.5,
  'Bad': 0.25,
  'Miss': 0
}
highest = [
  ('score', 'Score', 'DESC', False),
  ('rank', 'Rank', 'ASC', True),
  ('maxCombo', 'Max Combo', 'DESC', False),
  ('notes.Perfect', 'Number of Perfects', 'DESC', False),
  ('TP', 'Technical Points', 'DESC', False),
]
difficultyColors = {
  'Easy': '#3376f7',
  'Normal': '#58ef40',
  'Hard': '#f9c234',
  'Expert': '#ff2d31',
  'Special': '#F12499',
}
botAliases = {
  'newScores': ['new', 'ns', 'add'],
  'getScores': ['get', 'getScore', 'getSong', 'getSongs'],
  'editScore': ['edit', 'editSong'],
  'deleteScore': ['delete', 'deleteSong'],
  'manualInput': ['input'],
  'getHighest': ['highest', 'best'],
  'listSongs': ['list', 'songs', 'ls'],
  'getSongStats': ['stats', 'songStats'],
}