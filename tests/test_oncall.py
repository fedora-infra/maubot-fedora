import httpx


async def test_oncall_empty(bot, plugin):
    await bot.send("!oncall")
    assert len(bot.sent) == 1
    expected = "No one from Fedora Infrastructure is currently on call"
    assert bot.sent[0].content.body == expected


async def test_oncall_add(bot, plugin, db, respx_mock):
    respx_mock.get("http://fasjson.example.com/v1/users/dummy/").mock(
        return_value=httpx.Response(
            200,
            json={
                "result": {
                    "username": "dummy",
                    "ircnicks": ["irc:///dummyirc", "matrix://example.com/dummymx"],
                }
            },
        )
    )
    await bot.send("!oncall add dummy", room_id="controlroom")
    assert len(bot.sent) == 1
    expected = "dummy has been added to the oncall list"
    assert bot.sent[0].content.body == expected
    current_value = await db.fetch("SELECT * FROM oncall")
    assert len(current_value) == 1
    assert current_value[0]["username"] == "dummy"
    assert current_value[0]["mxid"] == "@dummymx:example.com"


async def test_oncall_add_empty(bot, plugin, db, respx_mock):
    respx_mock.get("http://fasjson.example.com/v1/users/dummy/").mock(
        return_value=httpx.Response(
            200,
            json={
                "result": {
                    "username": "dummy",
                    "ircnicks": ["irc:///dummyirc", "matrix://example.com/dummy"],
                }
            },
        )
    )
    respx_mock.get(
        "http://fasjson.example.com/v1/search/users/",
        params={"ircnick__exact": "matrix://example.com/dummy"},
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "result": [
                    {
                        "username": "dummy",
                        "ircnicks": ["irc:///dummyirc", "matrix://example.com/dummy"],
                    }
                ]
            },
        )
    )
    await bot.send("!oncall add", room_id="controlroom")
    assert len(bot.sent) == 1
    expected = "dummy has been added to the oncall list"
    assert bot.sent[0].content.body == expected
    current_value = await db.fetch("SELECT * FROM oncall")
    assert len(current_value) == 1
    assert current_value[0]["username"] == "dummy"
    assert current_value[0]["mxid"] == "@dummy:example.com"


async def test_oncall_add_wrong_room(bot, plugin, db):
    await bot.send("!oncall add dummy")
    assert len(bot.sent) == 1
    expected = (
        "> <@dummy:example.com> !oncall add dummy\n\nSorry, adding to the oncall list can only "
        "be done from the controlroom"
    )
    assert bot.sent[0].content.body == expected
    current_value = await db.fetch("SELECT COUNT(*) FROM oncall")
    assert current_value[0][0] == 0


async def test_oncall_add_existing(bot, plugin, db, respx_mock):
    respx_mock.get("http://fasjson.example.com/v1/users/dummy/").mock(
        return_value=httpx.Response(
            200,
            json={
                "result": {
                    "username": "dummy",
                    "ircnicks": ["irc:///dummyirc", "matrix://example.com/dummymx"],
                }
            },
        )
    )
    await db.execute(
        "INSERT INTO oncall (username, mxid, timezone) "
        "VALUES ('dummy', '@dummy:example.com', 'UTC')"
    )
    await bot.send("!oncall add dummy", room_id="controlroom")
    assert len(bot.sent) == 1
    expected = "dummy is already on the oncall list"
    assert bot.sent[0].content.body == expected
    current_value = await db.fetch("SELECT * FROM oncall")
    assert len(current_value) == 1


async def test_oncall_remove(bot, plugin, db, respx_mock):
    respx_mock.get("http://fasjson.example.com/v1/users/dummy/").mock(
        return_value=httpx.Response(
            200,
            json={
                "result": {
                    "username": "dummy",
                    "ircnicks": ["irc:///dummyirc", "matrix://example.com/dummymx"],
                }
            },
        )
    )
    await db.execute(
        "INSERT INTO oncall (username, mxid, timezone) "
        "VALUES ('dummy', '@dummy:example.com', 'UTC')"
    )
    await bot.send("!oncall remove dummy", room_id="controlroom")
    assert len(bot.sent) == 1
    expected = (
        "> <@dummy:example.com> !oncall remove dummy\n\ndummy has been removed from the oncall list"
    )
    assert bot.sent[0].content.body == expected
    current_value = await db.fetch("SELECT * FROM oncall")
    assert len(current_value) == 0


async def test_oncall_remove_wrong_room(bot, plugin, db, respx_mock):
    await bot.send("!oncall remove dummy")
    assert len(bot.sent) == 1
    expected = (
        "> <@dummy:example.com> !oncall remove dummy\n\n"
        "Sorry, removing from the oncall list can only be done from the controlroom"
    )
    assert bot.sent[0].content.body == expected
    current_value = await db.fetch("SELECT * FROM oncall")
    assert len(current_value) == 0


async def test_oncall_remove_absent(bot, plugin, db, respx_mock):
    respx_mock.get("http://fasjson.example.com/v1/users/dummy/").mock(
        return_value=httpx.Response(
            200,
            json={
                "result": {
                    "username": "dummy",
                    "ircnicks": ["irc:///dummyirc", "matrix://example.com/dummymx"],
                }
            },
        )
    )
    await bot.send("!oncall remove dummy", room_id="controlroom")
    assert len(bot.sent) == 1
    expected = (
        "> <@dummy:example.com> !oncall remove dummy\n\ndummy is not currently on the oncall list"
    )
    assert bot.sent[0].content.body == expected
