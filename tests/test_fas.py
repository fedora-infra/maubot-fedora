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
        "**Chat:** None"
    )
    assert bot.sent[0].content.body == expected


@pytest.mark.parametrize("membership_type", ["members", "sponsors"])
async def test_group_members(bot, plugin, respx_mock, membership_type):
    respx_mock.get(f"http://fasjson.example.com/v1/groups/dummygroup/{membership_type}/").mock(
        return_value=httpx.Response(
            200, json={"result": [{"username": "member1"}, {"username": "member2"}]}
        ),
    )
    await bot.send(f"!group {membership_type} dummygroup")
    assert len(bot.sent) == 1
    assert bot.sent[0].content.body == f"{membership_type.title()} of dummygroup: member1, member2"


@pytest.mark.parametrize("pronouns", [None, ["they / them", "mx"]])
async def test_hello(bot, plugin, respx_mock, pronouns):
    respx_mock.get("http://fasjson.example.com/v1/users/dummy/").mock(
        return_value=httpx.Response(
            200,
            json={
                "result": {
                    "username": "dummy",
                    "human_name": "Dummy User",
                    "pronouns": pronouns,
                }
            },
        )
    )
    # User hasn't set their matrix ID in FAS
    respx_mock.get(
        "http://fasjson.example.com/v1/search/users/",
        params={"ircnick__exact": "matrix://example.com/dummy"},
    ).mock(return_value=httpx.Response(200, json={"result": []}))

    await bot.send("!hello")
    assert len(bot.sent) == 1
    expected = "Dummy User (dummy)"
    if pronouns:
        expected = f"{expected} - {' or '.join(pronouns)}"
    assert bot.sent[0].content.body == expected


async def test_hello_with_username(bot, plugin, respx_mock):
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

    await bot.send("!hello dummy2")
    assert len(bot.sent) == 1
    assert bot.sent[0].content.body == "Dummy User 2 (dummy2)"


async def test_localtime(bot, plugin, respx_mock, monkeypatch):
    respx_mock.get("http://fasjson.example.com/v1/users/dummy/").mock(
        return_value=httpx.Response(
            200,
            json={
                "result": {
                    "username": "dummy",
                    "timezone": "Europe/Paris",
                }
            },
        )
    )
    fake_now = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    datetime_mock = mock.MagicMock(wraps=datetime)
    datetime_mock.now.side_effect = fake_now.astimezone
    monkeypatch.setattr(fedora.fas, "datetime", datetime_mock)
    await bot.send("!localtime dummy")
    assert len(bot.sent) == 1
    expected_time = fake_now.astimezone(pytz.timezone("Europe/Paris"))
    expected = (
        f'The current local time of "dummy" is: "{expected_time.strftime("%H:%M")}" '
        "(timezone: Europe/Paris)"
    )
    assert bot.sent[0].content.body == expected


async def test_user_info(bot, plugin, respx_mock):
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
    await bot.send("!user dummy")
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
