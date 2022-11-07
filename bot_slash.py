# Bot with slash commands 

import os
from dotenv import load_dotenv

import interactions

import cv2
import numpy as np

from api import ScoreAPI

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = interactions.Client(token=TOKEN)
scoreAPI = ScoreAPI()

@bot.command(
    name="image_command",
    description="test command",
    options = [
        interactions.Option(
            name="image",
            description="Test image",
            type=interactions.OptionType.ATTACHMENT,
            required=True,
        ),
    ],
)
async def image_command(ctx: interactions.CommandContext, image: interactions.api.models.message.Attachment):
    image_stream = await image.download()
    img_buffer = image_stream.read()
    img = cv2.imdecode(np.frombuffer(img_buffer, np.uint8), cv2.IMREAD_COLOR)

    output = scoreAPI.basicOutput(img)
    await ctx.send(output)

bot.start()