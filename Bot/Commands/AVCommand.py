import datetime
import pickle
import os
import discord
from asyncio import sleep
from typing import Dict

from Bot.GoogleDataRetrieval import download_pickle, upload_pickle
from envs import ACTIVATION_PREFIX, WENRITH_UID, DARKFYRE_UID
from Bot.Commands.Command import Command

GRDN_DATA_PATH = os.path.join(os.path.dirname(__file__), '../data/grdn_data.pkl')
KNOWN_DATA_KEY = "known_data"


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

    async def send_to_wenrith(self, message: str, *args):
        # Send a message to both me and wenrith. (I want to see the message to ensure it's working right)
        darkfyre = await self.client.fetch_user(int(DARKFYRE_UID))
        await darkfyre.send(message)

        wenrith = await self.client.fetch_user(int(WENRITH_UID))
        await wenrith.send(message)


# If the user is not Wenrith or Me
def restrict_cmd(func):
    async def wrapper(self, message, *args, **kwargs):
        if message.author.id == int(WENRITH_UID) or message.author.id == int(DARKFYRE_UID):
            return await func(self, message, *args, **kwargs)
        else:
            await self.send_message(message.channel, "You cannot access this data.")

    return wrapper


def upload_data(data_dict: Dict):
    with open(GRDN_DATA_PATH, 'wb') as f:
        pickle.dump(data_dict, f)
        f.flush()
        upload_pickle()


class GrdnData(AVCommand):
    """
    Class for returning any data GRDN might know
    """
    ID = 'grdn'

    def __init__(self, client, child=True):
        super().__init__(client, child=True)
        self.last_accessed = datetime.datetime.min

    async def execute(self, message: discord.Message, cmd_string=None):
        # Splits command into ['grdn', '<cmd>', '<args>']
        split_cmd = cmd_string.split(' ')

        # Help text
        if len(split_cmd) == 1:
            await self.send_help_msg(message)

        if len(split_cmd) >= 2:
            # Reduce how often we grab this data. If we've fetched it in the last hour, just use the local version.
            if self.last_accessed < datetime.datetime.now() - datetime.timedelta(hours=1):
                download_pickle()
                self.last_accessed = datetime.datetime.now()
            cmd = split_cmd[1]

            match cmd:
                case "help":
                    await self.send_help_msg(message)
                case "add":
                    await self.add_data(message, split_cmd)
                case "get":
                    await self.get_data(message, split_cmd)
                case "append":
                    await self.append_data(message, split_cmd)
                case "replace":
                    await self.replace_data(message, split_cmd)
                case "list":
                    if "-all" in split_cmd and message.author.id == int(DARKFYRE_UID):
                        await self.list_all_data(message)
                    elif "-h" in split_cmd and message.author.id == int(DARKFYRE_UID):
                        await self.list_hidden_data(message)
                    else:
                        await self.list_data(message)
                case "delete":
                    await self.delete_data(message, split_cmd)
                case "unlock":
                    await self.unlock_key(message, split_cmd)
                case "activate":
                    await self.activation_sequence(message)
                case _:
                    await self.send_message(message.channel, f"Command `{cmd}` is invalid."
                                                             f"Use `!cc av grdn help` to list commands.")

    async def send_help_msg(self, message):
        await self.send_message(message.channel, "You may add data to GRDN via "
                                                 "`!cc av grdn add <data key> <data to add here>`\n"
                                                 "You may request data from GRDN via "
                                                 "`!cc av grdn get <data key>`\n"
                                                 "You may append additional data for a specific key with "
                                                 "`!cc av grdn append <data key> <adtl. data>`\n"
                                                 "You may replace data for a specific key with "
                                                 "`!cc av grdn replace <data key> <new data>`\n"
                                                 "List known data keys with `!cc av grdn list`\n"
                                                 "Delete data associated with a key via "
                                                 "`!cc av grdn delete <data key>`")

    async def add_data(self, message, cmd_list):
        """
        Add data to GRDN
        Command goes `!cc av grdn add <key> <data>`
        Optionally to make the data hidden: `!cc av grdn add <key> -h <data>`
        :param message:
        :param cmd_list:
        :return:
        """
        with open(GRDN_DATA_PATH, 'rb') as f:
            data_dict = pickle.load(f)
            added_data = False
            key = cmd_list[2].lower()
            if key in data_dict:
                await self.send_message(message.channel,
                                        f"Data already logged for key {key}\n"
                                        f"Use the `update` command if you wish to update this data.")
            else:
                if cmd_list[3] == "-h":
                    data_dict['data'][key] = ' '.join(cmd_list[4:])
                else:
                    data_dict['data'][key] = ' '.join(cmd_list[3:])
                    data_dict[KNOWN_DATA_KEY].append(key)
                added_data = True

        if added_data:
            upload_data(data_dict)
            await self.send_message(message.channel, f"Data for `{key}` added.")

    @restrict_cmd
    async def get_data(self, message, cmd_list):
        """
        Get stored data. Data can remain hidden if there's anything typed a
        :param message:
        :param cmd_list:
        :return:
        """
        try:
            with open(GRDN_DATA_PATH, 'rb') as f:
                data_dict = pickle.load(f)
                key = cmd_list[2].lower()
                data = data_dict['data'][key]
                # If the key isn't "known" and we're not purposefully keeping the data hidden,
                # add it to the known data list
                if key not in data_dict[KNOWN_DATA_KEY] and "-h" not in cmd_list:
                    data_dict[KNOWN_DATA_KEY].append(key)
                    upload_data(data_dict)
                await self.send_message(message.channel, f"{data}")
        except KeyError:
            await self.send_message(message.channel, f"There is no data associated with `{key}`")

    @restrict_cmd
    async def list_data(self, message):
        try:
            with open(GRDN_DATA_PATH, 'rb') as f:
                data_dict = pickle.load(f)
                data_keys = data_dict[KNOWN_DATA_KEY]
                data_str = ", ".join([f"`{key}`" for key in data_keys])
                await self.send_message(message.channel, f"Known data keys: {data_str}")
        except KeyError:
            await self.send_message(message.channel, "Error, no knowledgebase.")

    async def list_all_data(self, message):
        try:
            with open(GRDN_DATA_PATH, 'rb') as f:
                data_dict = pickle.load(f)
                data_keys = data_dict['data'].keys()
                data_str = ", ".join([f"`{key}`" for key in data_keys])
                await self.send_message(message.channel, f"All data keys: {data_str}")
        except KeyError:
            await self.send_message(message.channel, "Error, no knowledgebase.")

    async def list_hidden_data(self, message):
        try:
            with open(GRDN_DATA_PATH, 'rb') as f:
                data_dict = pickle.load(f)
                all_data_keys = data_dict['data'].keys()
                known_data_keys = data_dict[KNOWN_DATA_KEY]
                data_keys = [key for key in all_data_keys if key not in known_data_keys]
                data_str = ", ".join([f"`{key}`" for key in data_keys])
                await self.send_message(message.channel, f"Unrevealed data keys: {data_str}")
        except KeyError:
            await self.send_message(message.channel, "Error, no knowledgebase.")

    @restrict_cmd
    async def append_data(self, message, cmd_list):
        try:
            with open(GRDN_DATA_PATH, 'rb') as f:
                data_dict = pickle.load(f)
                key = cmd_list[2].lower()
                data_dict[key] = data_dict['data'][cmd_list[2]] + " " + ' '.join(cmd_list[3:])
            upload_data(data_dict)
            await self.send_message(message.channel, f"Data for {key} updated")
        except KeyError:
            await self.send_message(message.channel, f"There is no data associated with `{key}`")

    @restrict_cmd
    async def replace_data(self, message, cmd_list):
        try:
            with open(GRDN_DATA_PATH, 'rb') as f:
                data_dict = pickle.load(f)
                key = cmd_list[2].lower()
                data_dict['data'][key] = ' '.join(cmd_list[3:])
            upload_data(data_dict)
            await self.send_message(message.channel, f"Data for {key} replaced")
        except KeyError:
            await self.send_message(message.channel, f"There is no data associated with `{key}`")

    @restrict_cmd
    async def delete_data(self, message, cmd_list):
        try:
            with open(GRDN_DATA_PATH, 'rb') as f:
                data_dict = pickle.load(f)
                key = cmd_list[2]
                data_dict[KNOWN_DATA_KEY].remove(key)
                del data_dict['data'][key]
            upload_data(data_dict)
            await self.send_message(message.channel, f"Data for {key} deleted")
        except KeyError:
            await self.send_message(message.channel, f"There is no data associated with `{key}`")

    async def unlock_key(self, message, cmd_list):
        if message.author.id == int(DARKFYRE_UID):
            try:
                with open(GRDN_DATA_PATH, 'rb') as f:
                    data_dict = pickle.load(f)
                    key = cmd_list[2].lower()
                    data = data_dict['data'][key]
                    if key not in data_dict[KNOWN_DATA_KEY]:
                        data_dict[KNOWN_DATA_KEY].append(key)
                        upload_data(data_dict)
                        await self.send_to_wenrith(f"Key {key} added to known data.")
                    await self.send_to_wenrith(f"`{key}`: {data}")
            except KeyError:
                await self.send_message(message.channel, f"Key `{key}` does not exist")

        else:
            await self.send_message(message.channel, "You cannot access this command.")

    async def activation_sequence(self, message):
        if message.author.id == int(DARKFYRE_UID):
            await self.send_to_wenrith("Gauntlight activation detected.")
            await sleep(5)
            await self.send_to_wenrith("Systems powering up")
            await sleep(0.5)
            await self.send_to_wenrith(".")
            await sleep(0.5)
            await self.send_to_wenrith(".")
            await sleep(0.5)
            await self.send_to_wenrith(".")
            await sleep(0.5)
            await self.send_to_wenrith(".")
            await sleep(0.5)
            await self.send_to_wenrith("Motor systems online.")
            await sleep(0.2)
            await self.send_to_wenrith("Running diagnostic.")
            await sleep(1)
            await self.send_to_wenrith(".")
            await sleep(0.5)
            await self.send_to_wenrith(".")
            await sleep(0.2)
            await self.send_to_wenrith("System degradation detected. Not all functions may be available.")
            await sleep(2)
            await self.send_to_wenrith(".")
            await sleep(0.5)
            await self.send_to_wenrith(".")
            await sleep(0.5)
            await self.send_to_wenrith(".")
            await sleep(0.2)
            await self.send_to_wenrith("Error: Cognition systems corrupted. Repairs initialized. This action will "
                                       "run in the background. Recommend re-visiting sites of importance.")
            await sleep(2)
            await self.send_to_wenrith(".")
            await sleep(0.5)
            await self.send_to_wenrith(".")
            await sleep(1)
            await self.send_to_wenrith("Diagnostic complete. Waking...")
            await sleep(2)
            await self.send_to_wenrith("**Directive**: Eliminate Belcorra Haruvex and any associates.")
