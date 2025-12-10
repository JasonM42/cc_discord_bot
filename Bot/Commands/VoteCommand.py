import discord
import asyncio
from typing import List, Dict

from Bot.UserYml import UserYml
from Bot.Commands.Command import Command
from envs import LOGGER

NUMBERS = [":one:", ":two:", ":three:", ":four:", ":five:", ":six:", ":seven:", ":eight:", ":nine:", ":keycap_ten:"]
UNICODE_NUMS = ["{}\N{COMBINING ENCLOSING KEYCAP}".format(num) for num in range(1, 10)]
UNICODE_YES_NO = [u"\u2705", u"\u274C"]
MIN_CHOICES = 1
MAX_CHOICES = 10

#  Potential support for up to 26 answer choices, but the unicode for the symbols seems kinda wonky, so not yet.
#  LETTERS = [f":regional_indicator_{letter}:" for letter in "abcdefghijklmnopqrstuvwxyz"]


class VoteCommand(Command):
    """
    Command to create a poll.
    Vote format `!cc vote <question> | <answer 1>, <answer 2>, <answer 3>`
    """
    ID = 'vote'  # type: str

    def __init__(self, client, child=False):
        super().__init__(client)
        self.cmd_dict = {}  # type: Dict[str, VoteCommand]

        # Prevent recursion in child object instances.
        if not child:
            subclasses = VoteCommand.__subclasses__()
            for cls in subclasses:
                self.cmd_dict[cls.ID] = cls(client)

    async def send_message(self, channel: discord.TextChannel, message: str, *args, duration=60):
        """

        :param channel:
        :param message:
        :param args:
        :param duration: How long to wait until declaring the vote winner. -1 if message is in error.
        :return:
        """
        msg = await channel.send(message)
        num_choices = args[0]
        emoji_list = args[1]
        # Check if valid vote called.
        if MIN_CHOICES < num_choices <= MAX_CHOICES and duration > 0:
            for i in range(num_choices):
                await msg.add_reaction(emoji_list[i])
            await asyncio.sleep(duration)
            vote_result, num_winner = await self.count_votes(msg)
            await channel.send(vote_result)
            return num_winner

    async def execute(self, message: discord.Message, vote_string=None):
        # Removes first two words ({ACTIVATION_PREFIX} vote)
        vote_string = ' '.join(message.content.split(' ')[2:])
        try:
            cmd_id = vote_string.split(' ')[0]  # Get just the first word Ex: mute or poll
            await self.cmd_dict[cmd_id].execute(message, vote_string)
        except KeyError:
            # If not a special type of vote, make a normal poll
            await self.cmd_dict['poll'].execute(message, vote_string)

    @staticmethod
    def interpret_time(duration: str) -> int:
        """
        Given a string of either numbers or text form of hours, seconds, etc. (ex: 1 hour, 5 minutes, 3 seconds)
        Convert all to an integer number of seconds.
        :param duration:
        :return: Integer number of seconds that the time given is.
        """
        duration = duration.strip().split(' ')

        # If only passed 1 number, interpret number as number of seconds
        if len(duration) == 1 and duration[0].isdigit():
            return int(duration[0])

        times = {
            "year": 31536000,
            "month": 2628288,
            "week": 604800,
            "day": 86400,
            "hour": 3600,
            "minute": 60,
            "second": 1
        }
        result = 0
        for i, interval in enumerate(duration):
            if not interval.isdigit():
                # De-pluralize, remove commas, etc.
                for time in times.keys():
                    if time in interval:
                        interval = time
                        break
                try:
                    result += int(duration[i - 1]) * times[interval]
                except KeyError:
                    pass

        return result if result != 0 else 60

    @staticmethod
    async def count_votes(message: discord.Message) -> (str, int):
        """
        Counts the reactions in the message and outputs a string proclaiming the emoji with the highest number of votes.
        :param message:
        :return:
        """
        msg_id = message.id
        updated_msg = await message.channel.fetch_message(msg_id)  # Need to check current vote count of the message
        reactions = updated_msg.reactions
        highest = [(None, 0)]
        num = 0
        for i, reaction in enumerate(reactions, 1):
            if reaction.count > highest[0][1]:
                highest = [(reaction.emoji, reaction.count)]
                num = i
            elif reaction.count == highest[0][1]:
                highest.append((reaction.emoji, reaction.count))

        if len(highest) == 1:
            return f"{highest[0][0]} wins with {highest[0][1] - 1} votes.", num
        else:
            result = "The result is a tie between "
            for i, tup in enumerate(highest, 1):
                if i == len(highest):
                    result += f"and {tup[0]} at {tup[1] - 1} votes."
                else:
                    result += f"{tup[0]}, "
            return result, 0


class VotePoll(VoteCommand):
    """

    """
    ID = 'poll'  # type: str

    def __init__(self, client, child=True):
        super().__init__(client, child=True)

    async def execute(self, message: discord.Message, vote_string=None):
        msg, n_ans, duration = self.set_vote(message, vote_string)
        num_winner = await self.send_message(message.channel, msg, n_ans, UNICODE_NUMS, duration=duration)

    @staticmethod
    def set_vote(message: discord.Message, vote_string: str) -> (str, int):
        vote_string = vote_string.split('|')
        question = vote_string[0].strip()
        answers = vote_string[1].strip().split(', ')
        try:
            duration = VoteCommand.interpret_time(vote_string[2].strip())
        except IndexError:
            duration = 60
        if question == '':
            return "You did not ask a question.", -1

        result = f"Question: **{question}**\n" \
                 f"Votes will be tallied in {duration} seconds.\n"
        num_answers = len(answers)
        if 1 < num_answers <= 10:
            LOGGER.info(f"{message.author} Created poll: {question} with answer choices {answers}, "
                        f"with duration {duration}")
            answers = zip(NUMBERS, answers)
        else:
            return "You may only have between 2 and 10 answer choices.", -1, -1
        result += "".join([f"{i} {ans}\n" for i, ans in answers])
        return result, num_answers, duration


class VoteMute(VoteCommand):
    """

    """
    ID = 'mute'  # type: str

    def __init__(self, client, child=True):
        super().__init__(client, child=True)

    async def execute(self, message: discord.Message, vote_string=None):
        msg, member, poll_duration, mute_duration = self.set_vote(message, vote_string)
        num_winner = await self.send_message(message.channel, msg, 2, UNICODE_YES_NO, duration=poll_duration)
        if num_winner == 1:
            await UserYml.mute(member, mute_duration)

    @staticmethod
    def set_vote(message: discord.Message, vote_string: str) -> (str, discord.Member, int, int):
        """
        Vote_string comes in form {prefix} vote mute {user} for <duration> | <poll duration>
        Durations are optional and the command may conclude at {prefix} vote mute {user}
        If durations are omitted in this way, default values (1 minute for both) will be used.
        :param message: The discord.Message object that the user sent to call the vote
        :param vote_string: The text string of the actual message minus the ACTIVATION_PREFIX and the word "vote"
        :return: What the bot will say in the chat channel.
        """
        if len(message.mentions) < 1:
            return "You did not properly select someone to be muted. " \
                   "Make sure you @mention them properly.", None, -1, -1
        elif len(message.mentions) > 1:
            return "You can only mute 1 person per vote", None, -1, -1
        if type(message.channel) != discord.TextChannel:
            return "This is not a valid command to run outside a server text channel.", None, -1, -1

        member = message.mentions[0]  # type: discord.Member
        mute_duration = 60
        poll_duration = 60
        if "for" in vote_string:
            durations = vote_string.split('for')[1]
            if "|" in vote_string:
                durations = durations.split('|')
                mute_duration = VoteCommand.interpret_time(durations[0])
                poll_duration = VoteCommand.interpret_time(durations[1])
            else:
                mute_duration = VoteCommand.interpret_time(durations)
        elif "|" in vote_string:
            poll_duration = VoteCommand.interpret_time(vote_string.split('|')[1])

        if poll_duration < 60:
            return "Poll duration must be at least 60 seconds.", None, -1, -1
        LOGGER.info(f"{message.author} voted to mute {member}")
        result = f"**Mute {member.display_name}?**\n" \
                 f"Poll will close in {poll_duration} seconds."

        return result, member, poll_duration, mute_duration


class VoteUnmute(VoteCommand):
    """

    """
    ID = 'unmute'  # type: str

    def __init__(self, client, child=True):
        super().__init__(client, child=True)

    async def execute(self, message: discord.Message, vote_string=None):
        msg, member = self.set_vote(message, vote_string)
        if member is not None:
            num_winner = await self.send_message(message.channel, msg, 2, UNICODE_YES_NO, duration=60)
            if num_winner == 1:
                await UserYml.unmute(member)

    @staticmethod
    def set_vote(message: discord.Message, vote_string: str) -> (str, discord.Member):
        if len(message.mentions) < 1:
            return "You did not properly select someone to be unmuted. " \
                   "Make sure you @mention them properly.", None
        elif len(message.mentions) > 1:
            return "You can only unmute 1 person per vote", None
        if type(message.channel) != discord.TextChannel:
            return "This is not a valid command to run outside a server text channel.", None

        member = message.mentions[0]  # type: discord.Member
        if not UserYml.get_user_obj(member).is_muted():
            return "This user is not muted.", None
        LOGGER.info(f"{message.author} voted to unmute {member}")
        result = f"**Unmute {member.display_name}?**"
        return result, member


class VoteBanish(VoteCommand):
    """

    """
    ID = 'banish'  # type: str

    def __init__(self, client, child=True):
        super().__init__(client, child=True)
        self.question = ""  # type: str
        self.answers = []  # type: List[str]

    def set_vote(self, message: discord.Message, vote_string: str) -> discord.Member:
        pass
