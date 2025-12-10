from __future__ import annotations
import os
import discord
import yaml
import asyncio
from datetime import datetime, timedelta
from envs import DATETIME_DEFAULT, LOGGER


class UserYml(yaml.YAMLObject):
    yaml_tag = u'!User'

    def __init__(self, name: str, uid: discord.User.id, muted=DATETIME_DEFAULT, deafened=DATETIME_DEFAULT):
        self.name = name
        self.uid = uid  # type: int
        self.muted = muted
        self.deafened = deafened

    def __repr__(self):
        return f"{self.__class__.__name__!s}(uid={self.uid!r}, muted={self.muted!r}, deafened={self.deafened!r})"

    def get_discord_member(self, guild: discord.Guild) -> discord.Member:
        return guild.get_member(self.uid)

    def is_muted(self):
        return self.muted != DATETIME_DEFAULT

    @classmethod
    async def mute(cls, member: discord.Member, secs: int):
        user = cls.get_user_obj(member)
        await user._mute(member, secs)

    async def _mute(self, member: discord.Member, secs: int):
        LOGGER.info(f"{member.display_name} was muted for {secs} seconds.")
        await self.connection_check(member.edit, mute=True)
        self.muted = datetime.now() + timedelta(seconds=secs)
        self.update_file(member.guild)

        await asyncio.sleep(secs)

        unmuted = await self.connection_check(member.edit, mute=False)
        if unmuted:  # Only update file if successful unmute. This lets the user be properly unmuted later.
            self.muted = DATETIME_DEFAULT
            self.update_file(member.guild)

    @classmethod
    async def unmute(cls, member: discord.Member):
        user = cls.get_user_obj(member)
        await user._unmute(member)

    async def _unmute(self, member: discord.Member):
        LOGGER.info(f"{member.display_name} was unmuted.")
        await self.connection_check(member.edit, mute=False)
        self.muted = DATETIME_DEFAULT
        self.update_file(member.guild)

    def update_file(self, guild: discord.Guild):

        guild_path = os.path.abspath(os.path.relpath(f'Bot\\Guilds\\{guild.id}'))
        user_path = os.path.join(guild_path, str(self.uid))
        with open(f'{user_path}.yml', "w") as user_file:
            user_file.write(yaml.dump(self))

    @staticmethod
    async def connection_check(async_func, *args, **kwargs) -> bool:
        try:
            await async_func(*args, **kwargs)
            return True
        except discord.HTTPException as e:
            LOGGER.info(e)
            return False

    @staticmethod
    def create_user_from_member(member: discord.Member):
        return UserYml(member.name, member.id)

    @staticmethod
    def get_user_file(guild: discord.Guild, member: discord.Member):
        dir_path = os.path.abspath(os.path.relpath(f'Bot\\Guilds\\{guild.id}\\{member.id}.yml'))
        return dir_path

    @classmethod
    def get_user_obj(cls, member: discord.Member) -> UserYml:
        with open(cls.get_user_file(member.guild, member)) as user_file:
            return yaml.load(user_file, Loader=yaml.Loader)
