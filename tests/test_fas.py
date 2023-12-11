from datetime import datetime, timezone
from unittest import mock

import httpx
import pytest
import pytz

import fedora


async def test_group_info(bot, plugin, respx_mock):
    respx_mock.get("http://fasjson.example.com/v1/groups/dummygroup/").mock(
        return_value=httpx.Response(
            200,
            json={
                "result": {
                    "groupname": "dummygroup",
                    "description": "A test group",
                    "irc": ["channel1", "channel2"],
                }
            },
        )
    )
    await bot.send("!group info dummygroup")
    assert len(bot.sent) == 1
    expected = (
        "**Group Name:** dummygroup\n "
        "**Description:** A test group\n "
        "**URL:** None,\n "
        "**Mailing List:** None\n "
        "**Chat:** `channel1` and `channel2`"
    )
    assert bot.sent[0].content.body == expected

    await bot.send("!group info")
    assert len(bot.sent) == 2
    assert (
        bot.sent[1].content.body == "groupname argument is required. e.g. `!group info designteam`"
    )


async def test_group_info_notagroup(bot, plugin, respx_mock):
    respx_mock.get("http://fasjson.example.com/v1/groups/notagroup/").mock(
        return_value=httpx.Response(
            404,
        )
    )
    await bot.send("!group info notagroup")
    assert len(bot.sent) == 1
    assert bot.sent[0].content.body == "Sorry, but group 'notagroup' does not exist"


@pytest.mark.parametrize("membership_type", ["members", "sponsors"])
@pytest.mark.parametrize("groupname", [None, "dummygroup"])
async def test_group_members(bot, plugin, respx_mock, membership_type, groupname, monkeypatch):
    respx_mock.get(f"http://fasjson.example.com/v1/groups/{groupname}/{membership_type}/").mock(
        return_value=httpx.Response(
            200, json={"result": [{"username": "member1"}, {"username": "member2"}]}
        ),
    )
    monkeypatch.setattr(bot.client, "get_joined_members", mock.AsyncMock(return_value=dict()))
    if groupname is None:
        await bot.send(f"!group {membership_type}")
        assert len(bot.sent) == 1
        assert (
            bot.sent[0].content.body
            == "groupname argument is required. e.g. `!group members designteam`"
        )
    else:
        await bot.send(f"!group {membership_type} {groupname}")
        assert len(bot.sent) == 1
        assert (
            bot.sent[0].content.body
            == f"{membership_type.title()} of {groupname}: member1, member2"
        )


async def test_group_members_notagroup(bot, plugin, respx_mock):
    respx_mock.get("http://fasjson.example.com/v1/groups/notagroup/members/").mock(
        return_value=httpx.Response(404),
    )
    await bot.send("!group members notagroup")
    assert len(bot.sent) == 1
    assert bot.sent[0].content.body == "Sorry, but group 'notagroup' does not exist"


async def test_group_members_massive_group(bot, plugin, respx_mock):
    respx_mock.get("http://fasjson.example.com/v1/groups/massivegroup/members/").mock(
        return_value=httpx.Response(
            200, json={"result": [{"username": f"member{n}"} for n in range(1, 300)]}
        ),
    )
    await bot.send("!group members massivegroup")
    assert len(bot.sent) == 1
    assert (
        bot.sent[0].content.body == "massivegroup has 299 members and thats too many to dump here"
    )


async def test_group_members_mentions(bot, plugin, respx_mock, monkeypatch):
    respx_mock.get("http://fasjson.example.com/v1/groups/dummygroup/members/").mock(
        return_value=httpx.Response(
            200,
            json={
                "result": [
                    {
                        "username": "member1",
                        "ircnicks": [],
                    },
                    {
                        "username": "member2",
                        "ircnicks": ["irc:/member2"],
                    },
                    {
                        "username": "member3",
                        "ircnicks": ["matrix:/member3"],
                        "human_name": "Member 3",
                    },
                    {
                        "username": "member4",
                        "ircnicks": ["matrix:/member4", "matrix:/member4bis"],
                        "human_name": "Member 4",
                    },
                    {
                        "username": "member5",
                        "ircnicks": ["matrix:/member5", "matrix:/member5bis"],
                        "human_name": "Member 5",
                    },
                ]
            },
        ),
    )
    monkeypatch.setattr(
        bot.client, "get_joined_members", mock.AsyncMock(return_value={"@member5:fedora.im": {}})
    )
    await bot.send("!group members dummygroup")
    assert len(bot.sent) == 1
    # member1: no ircnick → no mention
    # member2: no matrix id in ircnicks → no mention
    # member3: single matrix id → mention
    # member4: multiple matrix ids → mention list
    # member5: multiple matrix ids but only one is in the room → mention
    expected_body = (
        "Members of dummygroup: member1, member2, Member 3, "
        "member4 (@member4:fedora.im, @member4bis:fedora.im), "
        "Member 5"
    )
    expected_formatted_body = (
        "<p>Members of dummygroup: member1, member2, "
        '<a href="https://matrix.to/#/@member3:fedora.im">Member 3</a>, '
        'member4 (<a href="https://matrix.to/#/@member4:fedora.im">@member4:fedora.im</a>, '
        '<a href="https://matrix.to/#/@member4bis:fedora.im">@member4bis:fedora.im</a>), '
        '<a href="https://matrix.to/#/@member5:fedora.im">Member 5</a>'
        "</p>\n"
    )
    assert bot.sent[0].content.body == expected_body
    assert bot.sent[0].content.formatted_body == expected_formatted_body


@pytest.mark.parametrize("pronouns", [None, ["they / them", "mx"]])
@pytest.mark.parametrize("alias", [None, "hi", "hello", "hello2", "hellomynameis"])
async def test_user_hello(bot, plugin, respx_mock, monkeypatch, pronouns, alias):
    fasuser = {
        "username": "dummy",
        "human_name": "Dummy User",
        "pronouns": pronouns,
    }
    respx_mock.get("http://fasjson.example.com/v1/users/dummy/").mock(
        return_value=httpx.Response(
            200,
            json={"result": fasuser},
        )
    )
    respx_mock.get(
        "http://fasjson.example.com/v1/search/users/",
        params={"ircnick__exact": "matrix://example.com/dummy"},
    ).mock(return_value=httpx.Response(200, json={"result": [fasuser]}))

    monkeypatch.setattr(bot.client, "get_displayname", mock.AsyncMock(return_value="Dummy User"))

    if not alias:
        await bot.send("!user hello")
    else:
        await bot.send(f"!{alias}")
    assert len(bot.sent) == 1
    expected = "Dummy User: Dummy User (dummy)"
    expected_html = (
        '<p><a href="https://matrix.to/#/@dummy:example.com">Dummy User</a>: '
        "Dummy User (dummy)</p>\n"
    )
    if pronouns:
        pronouns_string = " or ".join(pronouns)
        expected = f"{expected} - {pronouns_string}"
        expected_html = (
            f'<p><a href="https://matrix.to/#/@dummy:example.com">Dummy User</a>: '
            f"Dummy User (dummy) - {pronouns_string}</p>\n"
        )
    assert bot.sent[0].content.body == expected
    assert bot.sent[0].content.formatted_body == expected_html


@pytest.mark.parametrize("command", ["hello", "info", "localtime"])
async def test_user_notfound(bot, plugin, respx_mock, command):
    respx_mock.get("http://fasjson.example.com/v1/users/dummy/").mock(
        return_value=httpx.Response(
            404,
        )
    )
    await bot.send(f"!user {command} dummy")

    assert len(bot.sent) == 1
    assert bot.sent[0].content.body == "Sorry, but Fedora Accounts user 'dummy' does not exist"


async def test_user_is_none(bot, plugin, monkeypatch):
    mock_get_fasuser = mock.AsyncMock(return_value=None)
    monkeypatch.setattr(fedora.fas, "get_fasuser", mock_get_fasuser)
    await bot.send("!user hello dummy")

    assert len(bot.sent) == 1
    assert bot.sent[0].content.body == "Cound not find this Fedora Account: dummy"


@pytest.mark.parametrize("alias", [None, "hi", "hello", "hello2", "hellomynameis"])
async def test_hello_with_username(bot, plugin, respx_mock, monkeypatch, alias):
    respx_mock.get("http://fasjson.example.com/v1/users/dummy2/").mock(
        return_value=httpx.Response(
            200,
            json={
                "result": {
                    "username": "dummy2",
                    "human_name": "Dummy User 2",
                }
            },
        )
    )
    # User hasn't set their matrix ID in FAS
    respx_mock.get(
        "http://fasjson.example.com/v1/search/users/",
        params={"ircnick__exact": "matrix://example.com/dummy"},
    ).mock(return_value=httpx.Response(200, json={"result": []}))
    monkeypatch.setattr(bot.client, "get_displayname", mock.AsyncMock(return_value="Dummy User"))
    if not alias:
        await bot.send("!user hello dummy2")
    else:
        await bot.send(f"!{alias} dummy2")
    assert len(bot.sent) == 1
    expected = "Dummy User: Dummy User 2 (dummy2)"
    expected_html = (
        '<p><a href="https://matrix.to/#/@dummy:example.com">'
        "Dummy User</a>: Dummy User 2 (dummy2)</p>\n"
    )
    assert bot.sent[0].content.body == expected
    assert bot.sent[0].content.formatted_body == expected_html


@pytest.mark.parametrize(
    "tz,response",
    [
        ("Europe/Paris", 'The current local time of "dummy" is: '),
        ("Cookieland/BiscuitTown", 'The timezone of "dummy" was unknown: "Cookieland/BiscuitTown"'),
        (None, 'User "dummy" doesn\'t share their timezone'),
    ],
)
@pytest.mark.parametrize("command", ["!user localtime dummy", "!localtime dummy"])
async def test_localtime(bot, plugin, respx_mock, monkeypatch, tz, response, command):
    respx_mock.get("http://fasjson.example.com/v1/users/dummy/").mock(
        return_value=httpx.Response(
            200,
            json={
                "result": {
                    "username": "dummy",
                    "timezone": tz,
                }
            },
        )
    )
    fake_now = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    datetime_mock = mock.MagicMock(wraps=datetime)
    datetime_mock.now.side_effect = fake_now.astimezone
    monkeypatch.setattr(fedora.fas, "datetime", datetime_mock)
    await bot.send(command)
    assert len(bot.sent) == 1
    if bot.sent[0].content.body.startswith('The current local time of "dummy" is: '):
        expected_time = fake_now.astimezone(pytz.timezone(tz))
        expected = f'{response}"{expected_time.strftime("%H:%M")}" (timezone: {tz})'
    else:
        expected = f"> <@dummy:example.com> {command}\n\n{response}"
    assert bot.sent[0].content.body == expected


@pytest.mark.parametrize("alias", [None, "fasinfo"])
async def test_user_info(bot, plugin, respx_mock, alias):
    respx_mock.get("http://fasjson.example.com/v1/users/dummy/").mock(
        return_value=httpx.Response(
            200,
            json={
                "result": {
                    "username": "dummy",
                    "human_name": "Dummy User",
                    "gpgkeyids": [],
                }
            },
        )
    )
    if not alias:
        await bot.send("!user info dummy")
    else:
        await bot.send(f"!{alias} dummy")
    assert len(bot.sent) == 1
    expected = (
        "User: dummy,\n "
        "Name: Dummy User,\n "
        "Pronouns: unset,\n "
        "Creation: None,\n "
        "Timezone: None,\n "
        "Locale: None,\n "
        "GPG Key IDs: None"
    )
    assert bot.sent[0].content.body == expected
