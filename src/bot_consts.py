from consts import *

commandAliases = {
  'newScores': ['new', 'ns', 'add'],
  'getScores': ['get', 'getScore', 'getSong', 'getSongs', 'g'],
  'editScore': ['edit', 'editSong', 'e'],
  'deleteScore': ['delete', 'deleteSong', 'd'],
  'manualInput': ['input', 'mi'],
  'getBest': ['highest', 'best', 'b'],
  'listSongs': ['list', 'songs', 'ls', 'listScores'],
  'getSongStats': ['stats', 'songStats', 's'],
  'getRecent': ['recent', 'recentScores', 'r'],
  'compare': ['c'],
  'tagScore': ['tag', 't'],
  'bestdoriGet': ['bestdori', 'bd', 'bdGet'],
  'aboutTP': ['TP']
}
commandParams = {
  'newScores': {
    'defaultTag': {
      'type': str,
      'default': tags[0],
      'allowed': tags,
      'required': False,
      'help': 'The tag to apply to the song(s).'
    },
    'compare': {
      'type': bool,
      'default': True,
      'required': False,
      'help': 'Whether to compare the added score with the best existing one.'
    },
  },
  'getScores': {
    'query': {
      'type': str,
      'required': True,
      'help': 'The name of the song to search for. This searches for the database representation of the name.'
    },
  },
  'editScore': {
    'id': {
      'type': str,
      'required': True,
      'help': 'The ID of the score to edit.'
    }
  },
  'deleteScore': {
    'id': {
      'type': str,
      'required': True,
      'help': 'The ID of the score to delete.'
    }
  },
  'manualInput': {
    'defaultTag': {
      'type': str,
      'default': tags[0],
      'allowed': tags,
      'required': False,
      'help': 'The tag to apply to the song.'
    }
  },
  'getBest': {
    'songName': {
      'type': str,
      'required': False,
      'help': 'The name of the song to list the best scores for. This searches for the database representation of the name. Quotes are required if the name contains spaces.'
    },
    'difficulty': {
      'type': str,
      'allowed': difficulties,
      'required': False,
      'help': 'The difficulty to list the best scores for. Lists for all difficulties if not provided.'
    },
    'tag': {
      'type': str,
      'allowed': tags,
      'required': False,
      'help': 'The tag to list the best scores for. Lists for all tags if not provided.'
    },
    'query': {
      'type': str,
      'required': False,
      'allowed': bestDict.keys(),
      'help': f'The query to get the best for. This allows you to get the best for a specific query instead of all of the available values. By default, the following are all listed: {[h[0] for h in bestDict.values()]}'
    }
  },
  'listSongs': {
    'difficulty': {
      'type': str,
      'allowed': difficulties,
      'required': False,
      'help': 'The difficulty to list the songs for. Lists all difficulties if not provided.'
    },
    'tag': {
      'type': str,
      'allowed': tags,
      'required': False,
      'help': 'The tag to list the songs for. Lists all tags if not provided.'
    },
    'band': {
      'type': str,
      'allowed': bandEmojis.values(),
      'required': False,
      'help': 'The band to list the songs for. Lists all bands if not provided.'
    },
    'asFile': {
      'type': bool,
      'default': False,
      'required': False,
      'help': 'Whether to send the song list as a file instead of as discord messages'
    },
    'allPerfect': {
      'type': bool,
      'default': False,
      'required': False,
      'help': 'Whether to show whether songs have all perfect scores'
    }
  },
  'getSongStats': {
    'songName': {
      'type': str,
      'required': False,
      'help': 'The name of the song to get the stats for. This searches for the database representation of the name. Quotes are required if the name contains spaces. If left blank, this will fetch all of your songs.'
    },
    'difficulty': {
      'type': str,
      'allowed': difficulties,
      'required': False,
      'help': 'The difficulty to get the stats for. Lists all difficulties if not provided.'
    },
    'tag': {
      'type': str,
      'allowed': tags,
      'required': False,
      'help': 'The tag to get the stats for. Lists all tags if not provided.'
    },
    'matchExact': {
      'type': bool,
      'default': False,
      'required': False,
      'help': 'Whether to match the exact song name'
    },
    'showMaxCombo': {
      'type': bool,
      'default': True,
      'help': 'Whether to show the max combo for each song in the notes chart'
    },
    'showSongNames': {
      'type': bool,
      'default': False,
      'help': 'Whether to show the song names in the score and TP chart'
    },
    'interpolate': {
      'type': bool,
      'default': False,
      'help': 'Whether to interpolate missing song scores from high score entries of each score. No notes or TP data will be shown for interpolated scores.'
    }
  },
  'getRecent': {
    'limit': {
      'type': int,
      'default': 1,
      'required': False,
      'help': 'The number of recent scores to get'
    },
    'tag': {
      'type': str,
      'allowed': tags,
      'required': False,
      'help': 'The tag to get the recent scores for. Lists all tags if not provided.'
    },
  },
  'compare': {
    'query': {
      'id': str,
      'required': False,
      'help': 'The ID of the score to compare to. If left blank, this will compare the last score added to the database.'
    },
  },
  'tagScore': {
    'id': {
      'type': str,
      'required': True,
      'help': 'The ID of the score to tag.'
    },
    'tag': {
      'type': str,
      'allowed': tags,
      'required': False,
      'help': 'The tag to apply to the score. If left blank, this will prompt you for a tag.'
    }
  },
  'bestdoriGet': {
    'query': {
      'type': str,
      'required': True,
      'help': 'The query to search for. This searches for the name found on Bestdori.'
    },
  },
  'help': {
    'command': {
      'type': str,
      'required': False,
      'help': 'The command to get help for. If left blank, this will list all commands.'
    }
  },
  'aboutTP': {
  }
}
commandHelp = {
  'newScores': {
    'description': 'Adds a new score to the database.',
    'help': 'Adds a new score to your database given a screenshot of a score. Multiple scores can be added by having multiple images in the message.'
  },
  'getScores': {
    'description': 'Gets the scores for a song.',
    'help': 'Gets the scores under your database given a query. The query is everything following the command, and no quotes are required. This searches for the database representation of the name.'
  },
  'editScore': {
    'description': 'Edits a score in your database.',
    'help': 'Edits a score given the ID of a score. The ID can be found by using the getScores command.'
  },
  'deleteScore': {
    'description': 'Deletes a score from your database.',
    'help': 'Deletes a score given the ID of a score. The ID can be found by using the getScores command.'
  },
  'manualInput': {
    'description': 'Manually adds a score to your database.',
    'help': 'Manually inputs a score. This is useful if you want to add a score that is not in the database and that you do not have a screenshot for.'
  },
  'getBest': {
    'description': 'Gets the best scores',
    'help': f'Gets your best scores of the following criteria: {[h[0] for h in bestDict.values()]}.'
  },
  'listSongs': {
    'description': 'Lists all of the songs in your database.',
    'help': 'Lists all of the songs in your database. This can be filtered by difficulty and tag.'
  },
  'getSongStats': {
    'description': 'Gets the stats for a song.',
    'help': 'Gets charts displaying your scores, note numbers, and TP plotted on the graph.'
  },
  'getRecent': {
    'description': 'Gets your recent scores.',
    'help': 'Gets the most recent scores you added to the database'
  },
  'compare': {
    'description': 'Compares a score to the best existing one.',
    'help': 'Compares a score to the best existing one. The ID of the score can be found by using the getScores command.'
  },
  'tagScore': {
    'description': 'Tags a score.',
    'help': 'Tags a score given the ID of a score. The ID can be found by using the getScores command.'
  },
  'bestdoriGet': {
    'description': 'Gets Bestdori data on a song.',
    'help': 'Gets the Bestdori data of a song name. This searches for the name found on Bestdori.'
  },
  'aboutTP': {
    'description': 'Shows information on Technical points (TP).',
    'help': 'Shows information on Technical points (TP).'
  }
}