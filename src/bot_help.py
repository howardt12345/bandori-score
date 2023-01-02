from bot_consts import *

def getCommandHelp(command, prefix):
  if command == '':
    msg = 'Available commands: \n'
    for c in commandHelp:
      msg += f' - `{prefix}{c}` (aliases: `{"`, `".join(commandAliases[c])}`): {commandHelp[c]["description"]}\n'
    return msg + '\nUse `$help` command for more info on a command.'
  else:
    key = next((k for k in commandAliases if command in commandAliases[k]), None)
    
    if command in commandHelp or key in commandHelp:
      if key is not None:
        command = key
      msg = f'`{prefix}{"|".join([command] + commandAliases[command])}`\n\n{commandHelp[command]["help"]}'
      cmdParams = commandParams[command]
      if cmdParams and cmdParams != {}:
        msg += "\n\nArguments:"
        for cmd in cmdParams:
          msg += f'\n`{cmd}`: {cmdParams[cmd]["type"].__name__}'
          msg += f'\n   {cmdParams[cmd]["help"]}'
          if 'required' in cmdParams[cmd]:
            msg += f'\n - Required: {"yes" if cmdParams[cmd]["required"] else "no"}'
          if 'default' in cmdParams[cmd]:
            msg += f'\n - Default: {cmdParams[cmd]["default"]}'
          if 'allowed' in cmdParams[cmd]:
            msg += f'\n - Allowed: {", ".join(cmdParams[cmd]["allowed"])}'
      else :
        msg += "\n\nThis command has no arguments."
      return msg + ''
    else:
      return f'`{command}` is not a valid command.'