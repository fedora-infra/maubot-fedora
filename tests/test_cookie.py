import time
from datetime import datetime
from unittest import mock

import httpx
import pytest
from mautrix.types import (
    EventType,
    MessageEvent,
    ReactionEvent,
    ReactionEventContent,
    RelatesTo,
    TextMessageEventContent,
)

import fedora


def _mock_user(respx_mock, username):
    respx_mock.get(
        "http://fasjson.example.com/v1/search/users/",
        params={"ircnick__exact": f"matrix://example.com/{username}"},
    ).mock(
        return_value=httpx.Response(
            200,
            json={"result": [{"username": username}]},
        )
    )
    respx_mock.get(f"http://fasjson.example.com/v1/users/{username}/").mock(
        return_value=httpx.Response(
            200,
            json={"result": {"username": username}},
        )
    )


@pytest.mark.parametrize("give_command", ["foobar++", "!cookie give foobar"])
async def test_cookie_give(bot, plugin, respx_mock, give_command):
    _mock_user(respx_mock, "dummy")
    _mock_user(respx_mock, "foobar")
    respx_mock.get("http://bodhi.example.com/releases/", params={"state": "current"}).mock(
        return_value=httpx.Response(
            200,
            json={
                "releases": [
                    {
                        "name": "F38",
                        "long_name": "Fedora 38",
                        "version": "38",
                        "id_prefix": "FEDORA",
                        "eol": "2024-05-14",
                    },
                    {
                        "name": "F37",
                        "long_name": "Fedora 37",
                        "version": "37",
                        "id_prefix": "FEDORA",
                        "eol": "2023-11-14",
                    },
                    {
                        "name": "F38C",
                        "long_name": "Fedora 38 Containers",
                        "version": "38",
                        "id_prefix": "FEDORA-CONTAINER",
                        "eol": "2024-05-14",
                    },
                ],
                "page": 1,
                "pages": 1,
                "rows_per_page": 20,
                "total": 13,
            },
        )
    )
    await bot.send(give_command)
    assert len(bot.sent) == 1
    assert bot.sent[0].content.body == (
        "dummy gave a cookie to foobar. They now have 1 cookie(s), "
        "1 of which were obtained in the Fedora 38 release cycle"
    )


@pytest.mark.parametrize(
    "body,html,username",
    [
        ("foobar++", None, "foobar"),
        (
            "Foo Bar++",
            '<a href="https://matrix.to/#/@foobar:example.com">Foo Bar</a>++',
            "foobar",
        ),
        (
            "Foo Bar:++",
            '<a href="https://matrix.to/#/@foobar:example.com">Foo Bar</a>:++',
            "foobar",
        ),
        (
            "Foo Bar: ++",
            '<a href="https://matrix.to/#/@foobar:example.com">Foo Bar</a>: ++',
            "foobar",
        ),
        ("do a foobar++ now", None, None),
        ("foobar++ well done!", None, "foobar"),
    ],
)
async def test_cookie_parse(bot, plugin, monkeypatch, respx_mock, body, html, username):
    give = mock.AsyncMock()
    monkeypatch.setattr(fedora.cookie.CookieHandler, "give", give)
    _mock_user(respx_mock, "foobar")
    await bot.send(body, html=html)
    if username is None:
        give.assert_not_called()
    else:
        give.assert_called_once()
        assert give.call_args[0][1] == username


async def test_cookie_give_twice(bot, plugin, respx_mock, db):
    _mock_user(respx_mock, "dummy")
    _mock_user(respx_mock, "foobar")
    respx_mock.get("http://bodhi.example.com/releases/", params={"state": "current"}).mock(
        return_value=httpx.Response(
            200,
            json={
                "releases": [
                    {
                        "version": "38",
                        "id_prefix": "FEDORA",
                        "eol": "2024-05-14",
                    },
                ],
            },
        )
    )
    await db.execute(
        "INSERT INTO cookies (from_user, to_user, release) " "VALUES ('dummy', 'foobar', '38')"
    )
    await bot.send("foobar++")
    assert len(bot.sent) == 1
    assert (
        bot.sent[0].content.body
        == "dummy has already given cookies to foobar during the F38 timeframe"
    )


async def test_cookie_give_myself(bot, plugin, respx_mock, db):
    _mock_user(respx_mock, "dummy")
    respx_mock.get("http://bodhi.example.com/releases/", params={"state": "current"}).mock(
        return_value=httpx.Response(
            200,
            json={
                "releases": [
                    {
                        "version": "38",
                        "id_prefix": "FEDORA",
                        "eol": "2024-05-14",
                    },
                ],
            },
        )
    )

    await bot.send("dummy++")
    given = await db.fetchval("SELECT COUNT(*) FROM cookies WHERE to_user = 'dummy'")
    assert given == 0
    assert len(bot.sent) == 1
    assert bot.sent[0].content.body == "You can't give a cookie to yourself"


async def test_cookie_count(bot, plugin, respx_mock, db):
    _mock_user(respx_mock, "foobar")

    dbq = "INSERT INTO cookies (from_user, to_user, release, value, date) VALUES ($1,$2,$3,$4,$5)"
    await db.execute(dbq, "dummy", "foobar", 37, 1, datetime.now())
    await db.execute(dbq, "dummy2", "foobar", 37, 1, datetime.now())
    await db.execute(dbq, "dummy", "foobar", 36, 1, datetime.now())
    await db.execute(dbq, "dummy2", "foobar", 36, 2, datetime.now())

    await bot.send("!cookie count foobar")
    assert len(bot.sent) == 1
    assert bot.sent[0].content.body == (
        "foobar has 5 cookies:\n\n" "● Fedora 36: 3 cookies\n" "● Fedora 37: 2 cookies"
    )


@pytest.mark.parametrize("emoji", [fedora.cookie.COOKIE_EMOJI, "🚀"])
async def test_cookie_react(bot, plugin, respx_mock, emoji):
    _mock_user(respx_mock, "dummy")
    _mock_user(respx_mock, "foobar")
    respx_mock.get("http://bodhi.example.com/releases/", params={"state": "current"}).mock(
        return_value=httpx.Response(
            200,
            json={
                "releases": [
                    {
                        "name": "F38",
                        "long_name": "Fedora 38",
                        "version": "38",
                        "id_prefix": "FEDORA",
                        "eol": "2024-05-14",
                    },
                ],
                "page": 1,
                "pages": 1,
                "rows_per_page": 20,
                "total": 1,
            },
        )
    )
    orig_message = MessageEvent(
        type=EventType.Class.MESSAGE,
        room_id="dummy-room-id",
        event_id="dummy-event-id",
        timestamp=time.time(),
        sender="@foobar:example.com",
        content=TextMessageEventContent(),
    )
    bot.client.get_event = mock.AsyncMock(return_value=orig_message)
    event = ReactionEvent(
        type=EventType.REACTION,
        room_id="dummy-room-id",
        event_id="dummy-reaction-event-id",
        timestamp=time.time(),
        sender="@dummy:example.com",
        content=ReactionEventContent(relates_to=RelatesTo(event_id="dummy-event-id", key=emoji)),
    )
    is_cookie_emoji = emoji == fedora.cookie.COOKIE_EMOJI
    await bot.dispatch(EventType.REACTION, event)
    if is_cookie_emoji:
        assert len(bot.sent) == 1
        assert bot.sent[0].content.body == (
            "dummy gave a cookie to foobar. They now have 1 cookie(s), "
            "1 of which were obtained in the Fedora 38 release cycle"
        )
    else:
        assert len(bot.sent) == 0


async def test_cookie_react_myself(bot, plugin, respx_mock, db):
    _mock_user(respx_mock, "dummy")
    respx_mock.get("http://bodhi.example.com/releases/", params={"state": "current"}).mock(
        return_value=httpx.Response(
            200,
            json={
                "releases": [
                    {
                        "name": "F38",
                        "long_name": "Fedora 38",
                        "version": "38",
                        "id_prefix": "FEDORA",
                        "eol": "2024-05-14",
                    },
                ],
                "page": 1,
                "pages": 1,
                "rows_per_page": 20,
                "total": 1,
            },
        )
    )
    orig_message = MessageEvent(
        type=EventType.Class.MESSAGE,
        room_id="dummy-room-id",
        event_id="dummy-event-id",
        timestamp=time.time(),
        sender="@dummy:example.com",
        content=TextMessageEventContent(),
    )
    bot.client.get_event = mock.AsyncMock(return_value=orig_message)
    event = ReactionEvent(
        type=EventType.REACTION,
        room_id="dummy-room-id",
        event_id="dummy-reaction-event-id",
        timestamp=time.time(),
        sender="@dummy:example.com",
        content=ReactionEventContent(
            relates_to=RelatesTo(event_id="dummy-event-id", key=fedora.cookie.COOKIE_EMOJI)
        ),
    )
    await bot.dispatch(EventType.REACTION, event)
    given = await db.fetchval("SELECT COUNT(*) FROM cookies WHERE to_user = 'dummy'")
    assert given == 0
    assert len(bot.sent) == 1
    assert bot.sent[0].content.body == "You can't give a cookie to yourself"
