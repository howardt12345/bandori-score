
from discord.ext import commands
import sys

async def version(ctx: commands.Context, version: str, ping: bool):
  with open(f'{sys.path[0]} + /../versions/{version}.txt', 'r') as file:
    data = file.read()
  if ping:
    await ctx.send(f'@here {data}')
  else:
    await ctx.send(data)

async def announcements(ctx: commands.Context, ping: bool):
  with open(f'{sys.path[0]} + /../announcement.txt', 'r') as file:
    data = file.read()
  if ping:
    await ctx.send(f'@here Announcements:\n{data}')
  else:
    await ctx.send(f'Announcements:\n{data}')