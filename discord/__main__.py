"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

import argparse
import sys
from pathlib import Path

import discord
import pkg_resources
import aiohttp
import platform


def show_version():
    """
    Prints a list of the current version of Python, discord.py and aiohttp.

    If
    discord.py is installed from pypi (not in editable mode), its version will
    also be shown along with that of the 
    discord.py pkg_resources if it is
    available (requires setuptools). The system information which consists of
    the system, 
    release and platform versions will also be displayed to show
    more info about where the bot is running on.

        :param sys: A module that
    gets passed in automatically by python for accessing information about
    things like what OS you are using etc..

        :type sys: ```module```
    :returns: None -- This function doesn't return anything it just prints to
    console though if you want to capture its output you could assign it to a
    variable but I would not recommend doing so as this function has no use for
    such an assignment other than displaying text on screen as opposed to
    storing something in memory like a string or number or any other data type
    because this function does nothing else except print stuff out anyway so
    why waste memory storing something that isn't useful? If I were going to
    give this function an output however I would give it some kind of message
    saying
    """
    entries = []

    entries.append("- Python v{0.major}.{0.minor}.{0.micro}-{0.releaselevel}".format(sys.version_info))
    version_info = discord.version_info
    entries.append("- discord.py v{0.major}.{0.minor}.{0.micro}-{0.releaselevel}".format(version_info))
    if version_info.releaselevel != "final":
        pkg = pkg_resources.get_distribution("discord.py")
        if pkg:
            entries.append(f"    - discord.py pkg_resources: v{pkg.version}")

    entries.append(f"- aiohttp v{aiohttp.__version__}")
    uname = platform.uname()
    entries.append("- system info: {0.system} {0.release} {0.version}".format(uname))
    print("\n".join(entries))


def core(parser, args):
    if args.version:
        show_version()


_bot_template = """#!/usr/bin/env python3

from discord.ext import commands
import discord
import config

class Bot(commands.{base}):
    def __init__(self, **kwargs):
        super().__init__(command_prefix=commands.when_mentioned_or('{prefix}'), **kwargs)
        for cog in config.cogs:
            try:
                self.load_extension(cog)
            except Exception as exc:
                print(f'Could not load extension {{cog}} due to {{exc.__class__.__name__}}: {{exc}}')

    async def on_ready(self):
        print(f'Logged on as {{self.user}} (ID: {{self.user.id}})')


bot = Bot()

# write general commands here

bot.run(config.token)
"""

_gitignore_template = """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Our configuration files
config.py
"""

_cog_template = '''from discord.ext import commands
import discord

class {name}(commands.Cog{attrs}):
    """The description for {name} goes here."""

    def __init__(self, bot):
        self.bot = bot
{extra}
def setup(bot):
    bot.add_cog({name}(bot))
'''

_cog_extras = """
    def cog_unload(self):
        # clean up logic goes here
        pass

    async def cog_check(self, ctx):
        # checks that apply to every command in here
        return True

    async def bot_check(self, ctx):
        # checks that apply to every command to the bot
        return True

    async def bot_check_once(self, ctx):
        # check that apply to every command but is guaranteed to be called only once
        return True

    async def cog_command_error(self, ctx, error):
        # error handling to every command in here
        pass

    async def cog_before_invoke(self, ctx):
        # called before a command is called here
        pass

    async def cog_after_invoke(self, ctx):
        # called after a command is called here
        pass

"""


# certain file names and directory names are forbidden
# see: https://msdn.microsoft.com/en-us/library/windows/desktop/aa365247%28v=vs.85%29.aspx
# although some of this doesn't apply to Linux, we might as well be consistent
_base_table = {
    "<": "-",
    ">": "-",
    ":": "-",
    '"': "-",
    # '/': '-', these are fine
    # '\\': '-',
    "|": "-",
    "?": "-",
    "*": "-",
}

# NUL (0) and 1-31 are disallowed
_base_table.update((chr(i), None) for i in range(32))

_translation_table = str.maketrans(_base_table)


def to_path(parser, name, *, replace_spaces=False):
    if isinstance(name, Path):
        return name

    if sys.platform == "win32":
        forbidden = (
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        )
        if len(name) <= 4 and name.upper() in forbidden:
            parser.error("invalid directory name given, use a different one")

    name = name.translate(_translation_table)
    if replace_spaces:
        name = name.replace(" ", "-")
    return Path(name)


def newbot(parser, args):
    """
    Creates a new bot directory with the given name.

    Args:
        parser
    (ArgumentParser): The argument parser used to add this subparser.
        args
    (Namespace): The arguments parsed by the argument parser.

    Returns:
    None: Nothing is returned, but an error may be raised if something goes
    wrong when creating the bot directory or files within it.

    Raises:
    OSError: An error occurred while making any necessary directories or files
    in this function's implementation, not necessarily due to user input. This
    exception is raised before any other possible exceptions from this function
    are raised, so that we can be sure that if there was an issue making our
    bot directory then no other file will be created either as a result of
    calling this function and thus leaving us with only one traceback instead
    of two for easier debugging later on when something inevitably goes wrong
    at some point in the future during runtime after deployment and we have no
    idea why/how it happened because nothing else raises errors like normal
    functions do... We hope... And I'm really sorry for writing such a long
    paragraph about how much I hate Python's exception handling system but yeah
    hopefully you get my point :P -Snowflakes#6835
    """
    new_directory = to_path(parser, args.directory) / to_path(parser, args.name)

    # as a note exist_ok for Path is a 3.5+ only feature
    # since we already checked above that we're >3.5
    try:
        new_directory.mkdir(exist_ok=True, parents=True)
    except OSError as exc:
        parser.error(f"could not create our bot directory ({exc})")

    cogs = new_directory / "cogs"

    try:
        cogs.mkdir(exist_ok=True)
        init = cogs / "__init__.py"
        init.touch()
    except OSError as exc:
        print(f"warning: could not create cogs directory ({exc})")

    try:
        with open(str(new_directory / "config.py"), "w", encoding="utf-8") as fp:
            fp.write('token = "place your token here"\ncogs = []\n')
    except OSError as exc:
        parser.error(f"could not create config file ({exc})")

    try:
        with open(str(new_directory / "bot.py"), "w", encoding="utf-8") as fp:
            base = "Bot" if not args.sharded else "AutoShardedBot"
            fp.write(_bot_template.format(base=base, prefix=args.prefix))
    except OSError as exc:
        parser.error(f"could not create bot file ({exc})")

    if not args.no_git:
        try:
            with open(str(new_directory / ".gitignore"), "w", encoding="utf-8") as fp:
                fp.write(_gitignore_template)
        except OSError as exc:
            print(f"warning: could not create .gitignore file ({exc})")

    print("successfully made bot at", new_directory)


def newcog(parser, args):
    """
    Creates a new cog with the given name.

    Args:
        parser (ArgumentParser):
    The argument parser for this function.
        args (Namespace): Parsed
    arguments for this function.

      Returns: None

      Raises: OSError if the cog
    directory could not be created or if the cog file could not be written to
    disk.
    """
    cog_dir = to_path(parser, args.directory)
    try:
        cog_dir.mkdir(exist_ok=True)
    except OSError as exc:
        print(f"warning: could not create cogs directory ({exc})")

    directory = cog_dir / to_path(parser, args.name)
    directory = directory.with_suffix(".py")
    try:
        with open(str(directory), "w", encoding="utf-8") as fp:
            attrs = ""
            extra = _cog_extras if args.full else ""
            if args.class_name:
                name = args.class_name
            else:
                name = str(directory.stem)
                if "-" in name or "_" in name:
                    translation = str.maketrans("-_", "  ")
                    name = name.translate(translation).title().replace(" ", "")
                else:
                    name = name.title()

            if args.display_name:
                attrs += f', name="{args.display_name}"'
            if args.hide_commands:
                attrs += ", command_attrs=dict(hidden=True)"
            fp.write(_cog_template.format(name=name, extra=extra, attrs=attrs))
    except OSError as exc:
        parser.error(f"could not create cog file ({exc})")
    else:
        print("successfully made cog at", directory)


def add_newbot_args(subparser):
    """
    Creates a command bot project quickly.

    :param name: the bot project name
    :type name: str, required
    :param directory: the directory to place it in
    (defaults to :code`Path.cwd()`), defaults to None if not specified or set
    explicitly as None  # noqarocde=no-nl-marker  # noqarocde=no-nl-marker  #
    noqarocde=no-nl-marker   # noqarocode=no_nl_marker   # nolint = max line
    length    nolint = max line length    nolint = max line length     nolint =
    max line length      linter disabled because of long lines generated by
    black autoformatter       linter disabled because of long lines generated
    by black autoformatter        linter disabled because of long lines
    generated by black autoformatter         linter disabled because of long
    lines generated by black autoformatter          linters are allowed to be
    longer than 79 characters for now           linters are allowed to be
    longer than 79 characters for now            linters are allowed to be
    longer than 79 characters for now             linters are allowed tp be
    longer
    """
    parser = subparser.add_parser("newbot", help="creates a command bot project quickly")
    parser.set_defaults(func=newbot)

    parser.add_argument("name", help="the bot project name")
    parser.add_argument("directory", help="the directory to place it in (default: .)", nargs="?", default=Path.cwd())
    parser.add_argument("--prefix", help="the bot prefix (default: $)", default="$", metavar="<prefix>")
    parser.add_argument("--sharded", help="whether to use AutoShardedBot", action="store_true")
    parser.add_argument("--no-git", help="do not create a .gitignore file", action="store_true", dest="no_git")


def add_newcog_args(subparser):
    """
    Creates a new cog template quickly.

    :param name: the cog name
    :type name:
    str
    """
    parser = subparser.add_parser("newcog", help="creates a new cog template quickly")
    parser.set_defaults(func=newcog)

    parser.add_argument("name", help="the cog name")
    parser.add_argument(
        "directory", help="the directory to place it in (default: cogs)", nargs="?", default=Path("cogs")
    )
    parser.add_argument("--class-name", help="the class name of the cog (default: <name>)", dest="class_name")
    parser.add_argument("--display-name", help="the cog name (default: <name>)")
    parser.add_argument("--hide-commands", help="whether to hide all commands in the cog", action="store_true")
    parser.add_argument("--full", help="add all special methods as well", action="store_true")


def parse_args():
    """
    Parses the command line arguments for the discord tool.

    :param parser: The
    argument parser to use
    :type parser: argparse.ArgumentParser
    :returns: A
    tuple containing the modified argument parser and a list of parsed
    arguments
    """
    parser = argparse.ArgumentParser(prog="discord", description="Tools for helping with discord.py")
    parser.add_argument("-v", "--version", action="store_true", help="shows the library version")
    parser.set_defaults(func=core)

    subparser = parser.add_subparsers(dest="subcommand", title="subcommands")
    add_newbot_args(subparser)
    add_newcog_args(subparser)
    return parser, parser.parse_args()


def main():
    parser, args = parse_args()
    args.func(parser, args)


if __name__ == "__main__":
    main()
