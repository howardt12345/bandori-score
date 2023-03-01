TIMEOUT = 180.0
ENABLE_LOGGING = True
ranks = ['SS', 'S', 'A', 'B', 'C', 'D']
types = ['Perfect', 'Great', 'Good', 'Bad', 'Miss']

noteTypes = {
  'Perfect': {
    'type': 'Perfect',
    'ratio': 2.115,
    'tolerance': (2, 0),
    'ext': 'jpg',
  },
  'Great': {
    'type': 'Great',
    'ratio': 2.78,
    'tolerance': (0, 0),
    'ext': 'jpg',
  },
  'Good': {
    'type': 'Good',
    'ratio': 2.85,
    'tolerance': (-1, 0),
    'ext': 'jpg',
  },
  'Bad': {
    'type': 'Bad',
    'ratio': 4.37,
    'tolerance': (2, 3),
    'ext': 'jpg',
  },
  'Miss': {
    'type': 'Miss',
    'ratio': 3.9,
    'tolerance': (-1, 5),
    'ext': 'jpg',
  },
}
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
# [key]: (display_name, sort_order, hidden (not shown when getBest))
bestDict = {
  'score': ('Score', 'DESC', False),
  'rank': ('Rank', 'ASC', True),
  'maxCombo': ('Max Combo', 'DESC', False),
  'notes.Perfect': ('Number of Perfects', 'DESC', False),
  'TP': ('Technical Points', 'DESC', False),
  'fastSlow': ('Fast/Slow', 'ASC', False),
  'fullCombo': ('Full Combo', 'DESC', True),
  'allPerfect': ('All Perfect', 'DESC', True),
}
difficultyColors = {
  'Easy': '#3376f7',
  'Normal': '#58ef40',
  'Hard': '#f9c234',
  'Expert': '#ff2d31',
  'Special': '#f0209e',
}
bandEmojis = {
  1: '<:PopipaLogo:1054792560360566884>',
  2: '<:AfterglowLogo:1054792554769551511>',
  3: '<:HHWLogo:1054792556665393263>',
  4: '<:PasupareLogo:1054792558930313347>',
  5: '<:RoseliaLogo:1054792563112022186>',
  6: '<:GlitterGreenLogo:1054792555969122374>',
  18: '<:RASLogo:1054792561585307700>',
  21: '<:MorfonicaLogo:1054792557823008879>',
}