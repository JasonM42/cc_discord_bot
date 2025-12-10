
from argparse import ArgumentParser
from Bot.bot import load_bot


def arg_setup():
    """
    Defines optional arguments and their default values
    :return: argparse Namespace object
    """
    parser = ArgumentParser(prog="Crew Bot")

    parser.add_argument('-v', '--version', action='version', version='%(prog)s version 0.0.2')
    parser.add_argument('-c', '--custom', action='store_true', help="Activates custom mode for the bot to test "
                                                                    "new functions")

    return parser.parse_args()


def main(args):
    load_bot(args)


if __name__ == "__main__":
    args = arg_setup()
    main(args)