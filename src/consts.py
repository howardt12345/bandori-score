TIMEOUT = 180.0
ENABLE_LOGGING = True
ranks = ['SS', 'S', 'A', 'B', 'C', 'D']
types = ['Perfect', 'Great', 'Good', 'Bad', 'Miss']
ratios = [2.115, 2.78, 2.85, 4.37, 3.9]
# The top and bottom tolerances of the note type bounding box
tolerances = [(0, -2), (0, 0), (-1, 0), (1, 3), (-1, 5)]
maxComboDim = [((5, 10), (-5, 65)), ((0, 5), (0, 47))]
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
bestDict = {
  'score': ('Score', 'DESC', False),
  'rank': ('Rank', 'ASC', True),
  'maxCombo': ('Max Combo', 'DESC', False),
  'notes.Perfect': ('Number of Perfects', 'DESC', False),
  'TP': ('Technical Points', 'DESC', False),
  'fastSlow': ('Fast/Slow', 'ASC', False),
}
difficultyColors = {
  'Easy': '#3376f7',
  'Normal': '#58ef40',
  'Hard': '#f9c234',
  'Expert': '#ff2d31',
  'Special': '#f0209e',
}