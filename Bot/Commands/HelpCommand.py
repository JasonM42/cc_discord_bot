import discord

from envs import ACTIVATION_PREFIX
from Bot.Commands.Command import Command


class HelpCommand(Command):
    """
    Help command to list available commands.
    """
    ID = 'help'  # type: str

    def __init__(self, client):
        super().__init__(client)
        self.command_dict = None

    async def execute(self, message: discord.Message):
        result_string = "Possible commands are listed below.\n" \
                        "For more information on each command please enter the command\n\n"
        for _id, cmd_doc in self.command_dict.items():
            result_string += cmd_doc + "\n"
        await self.send_message(message.channel, result_string)

    def set_help_dict(self, cmd_dict):
        self.command_dict = cmd_dict.copy()
        del self.command_dict['default']
        for _id, cmd in self.command_dict.items():
            self.command_dict[_id] = f"{ACTIVATION_PREFIX} " + cmd.ID + ": " + cmd.__doc__
