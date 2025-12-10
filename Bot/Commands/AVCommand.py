import pickle
import os
import discord
from typing import Dict
from envs import ACTIVATION_PREFIX, WENRITH_UID, DARKFYRE_UID
from Bot.Commands.Command import Command


class AVCommand(Command):
    """
    Retrieve info for the Abomination Vaults
    """
    ID = 'av'  # type: str

    def __init__(self, client, child=False):
        super().__init__(client)
        self.cmd_dict: Dict[str, AVCommand] = {}

        # Prevent recursion in child object instances.
        if not child:
            subclasses = AVCommand.__subclasses__()
            for cls in subclasses:
                self.cmd_dict[cls.ID] = cls(client)

    async def execute(self, message: discord.Message):
        # Removes first two words ({ACTIVATION_PREFIX} vote)
        cmd_string = ' '.join(message.content.split(' ')[2:])
        try:
            cmd_id = cmd_string.split(' ')[0]  # Get just the first word Ex: grdn
            await self.cmd_dict[cmd_id].execute(message, cmd_string)
        except KeyError:
            # If not a special type of vote, make a normal poll
            await self.cmd_dict['help'].execute(message, cmd_string)

    async def send_message(self, channel, message: str, *args):
        await channel.send(message)

    async def send_to_wenrith(self, message, *args):
        await self.client.fetch_user(WENRITH_UID).send(message)


class GrdnData(AVCommand):
    """
    Class for returning any data GRDN might know
    """
    ID = 'grdn'

    def __init__(self, client, child=True):
        super().__init__(client, child=True)

    async def execute(self, message: discord.Message, cmd_string=None):
        # Splits command into ['grdn', '<cmd>', '<args>']
        split_cmd = cmd_string.split(' ')

        # Help text
        if len(split_cmd) == 1:
            await self.send_message(message.channel, "You may add data to GRDN via "
                                                     "`!cc av grdn add <data key> <data to add here>`\n"
                                                     "You may request data from GRDN via "
                                                     "`!cc av grdn retrieve <data key>`")

        if len(split_cmd) >= 3:
            if split_cmd[1] == "add":
                with open(os.path.join(os.path.dirname(__file__), '../data/grdn_data.pkl'), 'rb') as f:
                    data_dict = pickle.load(f)
                    data_dict[split_cmd[2]] = split_cmd[3:].join(' ')
                    with open(os.path.join(os.path.dirname(__file__), '../data/grdn_data.pkl'), 'wb') as g:
                        pickle.dump(data_dict, g)
            elif split_cmd[1] == "get":
                # If the user is not Wenrith or Me
                if message.author.id == int(WENRITH_UID) or message.author.id == int(DARKFYRE_UID):
                    try:
                        with open(os.path.join(os.path.dirname(__file__), '../data/grdn_data.pkl'), 'rb') as f:
                            data_dict = pickle.load(f)
                            await self.send_message(message.channel, f"{split_cmd[2]}: {data_dict[split_cmd[2]]}")
                    except KeyError:
                        await self.send_message(message.channel, "There is no data associated with this key")
                else:
                    await self.send_message(message.channel, "You cannot access this data.")
