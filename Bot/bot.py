import os
import discord
import envs
import asyncio
from typing import Dict
from datetime import datetime, timedelta

from envs import CLIENT, LOGGER
from Bot.Commands.Command import Command
from Bot.UserYml import UserYml

# Required so that all other commands are correctly listed as subclasses of the Command class
# Might be worth rewriting to be dynamic
from Bot.Commands.DefaultCommand import DefaultCommand
from Bot.Commands.HelpCommand import HelpCommand
from Bot.Commands.VoteCommand import VoteCommand
from Bot.Commands.UsersCommand import UsersCommand
from Bot.Commands.AVCommand import AVCommand


def command_factory() -> Dict[str, Command]:
    """
    Gets all command types and returns them in a dict with their id as keys
    and the class instance itself as the value.
    :return:
    """

    subclasses = Command.__subclasses__()
    cmd_dict = {}
    for cls in subclasses:
        cmd_dict[cls.ID] = cls(CLIENT)
    cmd_dict['help'].set_help_dict(cmd_dict)
    return cmd_dict


async def message_handler(command_dict: Dict[str, Command], msg: discord.Message):
    word_list = msg.content.split()
    try:
        await command_dict[word_list[1]].execute(msg)
    except (KeyError, IndexError) as e:
        await command_dict['default'].execute(msg)
        LOGGER.error(e)


async def on_voice_join(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    user = UserYml.get_user_obj(member)  # type: UserYml
    if user.is_muted():  # Saved date-time of User is not DATETIME_DEFAULT
        if user.muted <= datetime.now():  # User is muted and should not be anymore
            await user.unmute(member)
        elif not after.mute:  # User file says they should be muted, but they actually aren't.
            secs = user.muted - datetime.now()  # type: timedelta
            await user.mute(member, secs.seconds)


async def on_voice_leave(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    pass


def load_bot(args):
    cmd_dict = command_factory()

    @CLIENT.event
    async def on_ready():
        print('Connected.')
        LOGGER.info(f'{envs.CLIENT.user} has connected to Discord!')
        for guild in CLIENT.guilds:
            UsersCommand.safe_reload(guild=guild)

    @CLIENT.event
    async def on_message(message):
        # Ignore messages sent by self
        if message.author == envs.CLIENT.user:
            return

        if message.content.startswith(envs.ACTIVATION_PREFIX):
            LOGGER.info(f'{message.content} received')
            if message.content.endswith(envs.ACTIVATION_PREFIX):
                await message.channel.send(f'For help, please type `{envs.ACTIVATION_PREFIX} help`')
                return
            await message_handler(cmd_dict, message)

    @CLIENT.event
    async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if before.channel is None and after.channel is not None:
            await on_voice_join(member, before, after)
        elif before.channel is not None and after.channel is None:
            await on_voice_leave(member, before, after)

    @CLIENT.event
    async def on_guild_join(guild: discord.Guild):
        await UsersCommand.reload(guild=guild)

    @CLIENT.event
    async def on_guild_remove(guild: discord.Guild):
        cur_path = os.path.dirname(__file__)
        file_path = os.path.relpath(f'.\\Guilds\\{guild.id}', cur_path)
        if os.path.exists(file_path):
            os.remove(file_path)

    @CLIENT.event
    async def on_member_join(member: discord.Member):
        await UsersCommand.add_user(member.guild, member)

    CLIENT.run(envs.TOKEN)
