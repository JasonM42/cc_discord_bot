import discord
from envs import LOGGER


class Command(object):
    """
    Generic class for Commands
    """
    ID = None  # type: str

    def __init__(self, client: discord.Client):
        self.client = client

    async def send_message(self, channel: discord.TextChannel, message: str, *args):
        await channel.send(message)

    async def execute(self, message: discord.Message):
        await self.send_message(message.channel, "How did you even...?")
