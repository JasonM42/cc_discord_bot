import discord
import os
import yaml
from Bot.UserYml import UserYml
from typing import Union, List
from Bot.Commands.Command import Command


class UsersCommand(Command):
    """
    Command for fixing the guild's User file. Will unmute/undeafen all members.
    """
    ID = 'users'  # type: str

    def __init__(self, client):
        super().__init__(client)

    async def execute(self, message: discord.Message, guild=None):
        guild = guild if guild is not None else message.guild  # type: discord.Guild
        if 'reload' in message.content:
            if 'safe' in message.content:
                self.safe_reload(guild)
            else:
                self.reload(guild)

    @staticmethod
    def reload(guild):
        cur_path = os.path.dirname(os.path.dirname(__file__))
        guilds_path = os.path.join(cur_path, 'Guilds')
        try:
            os.mkdir(guilds_path)
        except FileExistsError:
            pass
        try:
            os.mkdir(os.path.join(guilds_path, str(guild.id)))
        except FileExistsError:
            pass
        guilds_path = os.path.join(guilds_path, f'{guild.id}')
        user_list = [UserYml.create_user_from_member(member) for member in guild.members]
        for user in user_list:
            file_path = os.path.join(guilds_path, f"{user.uid}.yml")
            with open(file_path, 'w+') as user_file:
                user_file.write(yaml.dump(user))

    @classmethod
    def safe_reload(cls, guild):
        """Reload done to make user files for anyone that joined while the bot was offline."""
        guild_path = os.path.abspath(os.path.relpath(f'Bot\\Guilds\\{guild.id}'))
        for member in guild.members:
            user_path = os.path.join(guild_path, f'{member.id}.yml')
            if not os.path.exists(user_path):
                cls.add_user(guild, member, user_path)

    @classmethod
    def add_user(cls, guild, member, user_path=None):
        if user_path is None:
            guild_path = os.path.abspath(os.path.relpath(f'Bot\\Guilds\\{guild.id}'))
            user_path = os.path.join(guild_path, f'{member.id}.yml')
        with open(user_path, "w") as user_file:
            user = UserYml.create_user_from_member(member)
            user_file.write(yaml.dump(user))

