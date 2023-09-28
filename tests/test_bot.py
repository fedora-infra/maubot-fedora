async def test_version(bot, plugin):
    await bot.send("!version")
    assert len(bot.sent) == 1
    assert bot.sent[0].content.body == "maubot-fedora version 0.1.0"


async def test_help(bot, plugin):
    await bot.send("!help")
    assert len(bot.sent) == 1
    expected = (
        "● `!help [commandname]` - list commands\n"
        "● `!version ` - return information about this bot\n"
        "● `!epel <issue_id>` - Get a Summary of a ticket from the epel ticket tracker\n"
        "● `!fesco <issue_id>` - Get a Summary of a ticket from the fesco ticket tracker\n"
        "● `!fpc <issue_id>` - Get a Summary of a ticket from the packaging-committee "
        "ticket tracker\n"
        "● `!pagureissue <project> <issue_id>` - return a pagure issue\n"
        "● `!whoowns <package>` - Retrieve the owner of a given package\n"
        "● `!group  <subcommand> [...]` - Query information about Fedora Accounts groups\n"
        "● `!hello [username]` - Return brief information about a Fedora user.\n"
        "● `!localtime [username]` - Returns the current time of the user.\n"
        "● `!user [username]` - Return brief information about a Fedora user.\n"
        "● `!bug <bug_id>` - return a bugzilla bug\n"
        "● `!oncall  <subcommand> [...]` - oncall"
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
