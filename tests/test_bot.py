async def test_version(bot, plugin):
    await bot.send("!version")
    assert len(bot.sent) == 1
    assert bot.sent[0].content.body == "maubot-fedora version 0.2.0"


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
