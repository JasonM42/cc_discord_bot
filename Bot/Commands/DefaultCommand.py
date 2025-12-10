import discord

from envs import ACTIVATION_PREFIX
from Bot.Commands.Command import Command


class DefaultCommand(Command):
    """
    Fallback command for invalid commands
    """
    ID = 'default'  # type: str

    def __init__(self, client: discord.Client):
        super().__init__(client)

    async def execute(self, message: discord.Message):
        await self.send_message(message.channel, f"That is not a valid command. For a list of available commands "
                                                 f"use `{ACTIVATION_PREFIX} help`")
