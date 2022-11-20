from consts import *
from functools import reduce

commandAliases = {
  'newScores': ['new', 'ns', 'add'],
  'getScores': ['get', 'getScore', 'getSong', 'getSongs'],
  'editScore': ['edit', 'editSong'],
  'deleteScore': ['delete', 'deleteSong'],
  'manualInput': ['input'],
  'getHighest': ['highest', 'best'],
  'listSongs': ['list', 'songs', 'ls', 'listScores'],
  'getSongStats': ['stats', 'songStats'],
  'getRecent': ['recent', 'recentScores'],
  'bestdoriGet': ['bestdori', 'bd', 'bdGet']
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
  'getHighest': {
    'songName': {
      'type': str,
      'required': False,
      'help': 'The name of the song to list the highest scores for. This searches for the database representation of the name. Quotes are required if the name contains spaces.'
    },
    'difficulty': {
      'type': str,
      'allowed': difficulties,
      'required': False,
      'help': 'The difficulty to list the highest scores for. Lists for all difficulties if not provided.'
    },
    'tag': {
      'type': str,
      'allowed': tags,
      'required': False,
      'help': 'The tag to list the highest scores for. Lists for all tags if not provided.'
    },
    'query': {
      'type': str,
      'required': False,
      'allowed': [h[0] for h in highest],
      'help': f'The query to get the highest for. This allows you to get the highest for a specific query instead of all of the available values. By default, the following are all listed: {[h[1] for h in highest]}'
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
    'asFile': {
      'type': bool,
      'default': False,
      'required': False,
      'help': 'Whether to send the song list as a file instead of as discord messages'
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
  'getHighest': {
    'description': 'Gets the highest scores',
    'help': f'Gets your highest scores of the following criteria: {[h[1] for h in highest]}.'
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
  'bestdoriGet': {
    'description': 'Gets Bestdori data on a song.',
    'help': 'Gets the Bestdori data of a song name. This searches for the name found on Bestdori.'
  },
}

def getCommandHelp(command, prefix):
  if command == '':
    msg = 'Available commands: \n'
    for c in commandHelp:
      msg += f' - `{prefix}{c}` (aliases: `{"`, `".join(commandAliases[c])}`): {commandHelp[c]["description"]}\n'
    return msg + '\nUse `$help` command for more info on a command.'
  else:
    if command in commandHelp:
      msg = f'`{prefix}{"|".join([command] + commandAliases[command])}`\n\n{commandHelp[command]["help"]}\n\nArguments:'
      cmdParams = commandParams[command]
      for cmd in cmdParams:
        msg += f'\n`{cmd}`: {cmdParams[cmd]["type"].__name__}'
        msg += f'\n   {cmdParams[cmd]["help"]}'
        if 'required' in cmdParams[cmd]:
          msg += f'\n - Required: {"yes" if cmdParams[cmd]["required"] else "no"}'
        if 'default' in cmdParams[cmd]:
          msg += f'\n - Default: {cmdParams[cmd]["default"]}'
        if 'allowed' in cmdParams[cmd]:
          msg += f'\n - Allowed: `{"`, `".join(cmdParams[cmd]["allowed"])}`'
      return msg + ''
    else:
      return f'`{command}` is not a valid command.'