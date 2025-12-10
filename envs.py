import os
import discord
import logging
import datetime
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
ACTIVATION_PREFIX = os.getenv('PREFIX')
RIOT_API_KEY = os.getenv('RIOT_API_KEY')

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.members = True
intents.guilds = True

CLIENT = discord.Client(intents=intents)  # type: discord.Client
LOGGER_FORMAT = '%(asctime)s:%(levelname)s:%(name)s: %(message)s'  # Message log format
logging.basicConfig(filename='discord_bot.log', level=logging.INFO, format=LOGGER_FORMAT)
LOGGER = logging.getLogger('discord')
DATETIME_DEFAULT = datetime.datetime(2020, 1, 1)

WENRITH_UID = os.getenv('WENRITH_UID')
DARKFYRE_UID = os.getenv('DARKFYRE_UID')
