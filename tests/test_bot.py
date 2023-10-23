from pathlib import Path

from ruamel.yaml import YAML


async def test_version(bot, plugin):
    base_path = Path(__file__).parent.parent
    yaml = YAML()
    with open(base_path.joinpath("maubot.yaml")) as fh:
        metadata = yaml.load(fh.read())
    await bot.send("!version")
    assert len(bot.sent) == 1
    assert bot.sent[0].content.body == f"maubot-fedora version {metadata['version']}"


async def test_help(bot, plugin):
    await bot.send("!help")
    assert len(bot.sent) == 1
    expected = (
        "● `!help [commandname]` - list commands\n"
        "● `!version ` - return information about this bot\n"
        "● `!pagureissue <project> <issue_id>` - return a pagure issue\n"
        "● `!whoowns <package>` - Retrieve the owner of a given package\n"
        "● `!group  <subcommand> [...]` - Query information about Fedora Accounts groups\n"
        "● `!user  <subcommand> [...]` - Get information about Fedora Accounts users\n"
        "● `!infra  <subcommand> [...]` - Fedora Infrastructure commands\n"
        "● `!bug <bug_id>` - return a bugzilla bug\n"
        "● `!oncall  <subcommand> [...]` - oncall\n"
        "● `!cookie  <subcommand> [...]` - Commands for the cookie system"
    )
    assert bot.sent[0].content.body == expected


async def test_help_group(bot, plugin):
    await bot.send("!help group")
    assert len(bot.sent) == 1
    expected = (
        "**Usage:** !group <subcommand> [...]\n\n"
        "● members <groupname> - Return a list of members of the specified group\n"
        "● sponsors <groupname> - Return a list of owners of the specified group\n"
        "● info <groupname> - Return a list of owners of the specified group"
    )
    assert bot.sent[0].content.body == expected


async def test_help_cookie(bot, plugin):
    await bot.send("!help cookie")
    assert len(bot.sent) == 1
    expected = (
        "**Usage:** !cookie <subcommand> [...]\n\n"
        "● give <username> - Give a cookie to another Fedora contributor\n"
        "● count <username> - Return the cookie count for a user"
    )
    assert bot.sent[0].content.body == expected
