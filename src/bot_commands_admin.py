
from discord.ext import commands

async def version(ctx: commands.Context, version: str, ping: bool):
  with open(f'versions/{version}.txt', 'r') as file:
    data = file.read()
  if ping:
    await ctx.send(f'@here {data}')
  else:
    await ctx.send(data)