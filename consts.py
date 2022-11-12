ranks = ['SS', 'S', 'A', 'B', 'C', 'D']
types = ['Perfect', 'Great', 'Good', 'Bad', 'Miss']
ratios = [2.115, 2.78, 2.85, 4.37, 3.9]
tolerances = [(0, 0), (1, 0), (0, 0), (0, 3), (2, 5)] # The top and bottom tolerances of the note type bounding box
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