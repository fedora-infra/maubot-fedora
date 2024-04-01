import re
from unittest import mock

import httpx
import pytest

from fedora.clients.fasjson import FasjsonClient
from fedora.exceptions import InfoGatherError


@pytest.mark.parametrize(
    "groupname,membership_type,expected_url",
    [
        ("sysadmin-main", "members", "groups/sysadmin-main/members"),
        ("sysadmin-main", "sponsors", "groups/sysadmin-main/sponsors"),
    ],
)
async def test_get_group_membership(monkeypatch, groupname, membership_type, expected_url):
    result = [{"username": "member1"}, {"username": "member2"}]
    client = FasjsonClient("http://fasjson.example.com")
    mock__get = mock.AsyncMock(
        return_value=httpx.Response(
            200,
            json={"result": result},
        )
    )
    monkeypatch.setattr(client, "_get", mock__get)

    response = await client.get_group_membership(groupname, membership_type)
    mock__get.assert_called_once_with(
        expected_url, params=None, headers={"X-Fields": "username,human_name,ircnicks"}
    )
    assert response == result


@pytest.mark.parametrize(
    "errorcode,expected_result",
    [
        (404, "Sorry, but group 'biscuits_group' does not exist"),
        (403, "Sorry, could not get info from FASJSON (code 403)"),
    ],
)
async def test_get_group_membership_errors(respx_mock, errorcode, expected_result):
    client = FasjsonClient("http://fasjson.example.com")
    respx_mock.get("http://fasjson.example.com").mock(
        return_value=httpx.Response(
            errorcode,
            json={"result": "biscuits"},
        )
    )
    with pytest.raises(InfoGatherError, match=(re.escape(expected_result))):
        await client.get_group_membership("biscuits_group", "members")


@pytest.mark.parametrize(
    "groupname,expected_url",
    [
        ("sysadmin-main", "groups/sysadmin-main"),
    ],
)
async def test_get_group(monkeypatch, groupname, expected_url):
    result = {
        "groupname": groupname,
        "description": "A test group",
    }
    client = FasjsonClient("http://fasjson.example.com")
    mock__get = mock.AsyncMock(
        return_value=httpx.Response(
            200,
            json={"result": result},
        )
    )
    monkeypatch.setattr(client, "_get", mock__get)

    response = await client.get_group(groupname)
    mock__get.assert_called_once_with(expected_url, params=None)
    assert response == result


@pytest.mark.parametrize(
    "errorcode,expected_result",
    [
        (404, "Sorry, but group 'biscuits_group' does not exist"),
        (403, "Sorry, could not get info from FASJSON (code 403)"),
    ],
)
async def test_get_group_errors(respx_mock, errorcode, expected_result):
    client = FasjsonClient("http://fasjson.example.com")
    respx_mock.get("http://fasjson.example.com").mock(
        return_value=httpx.Response(
            errorcode,
            json={"result": "biscuits"},
        )
    )
    with pytest.raises(InfoGatherError, match=(re.escape(expected_result))):
        await client.get_group("biscuits_group", "members")


@pytest.mark.parametrize(
    "username,expected_url",
    [
        ("biscuit_eater", "users/biscuit_eater"),
    ],
)
async def test_get_user(monkeypatch, username, expected_url):
    result = {
        "username": username,
    }
    client = FasjsonClient("http://fasjson.example.com")
    mock__get = mock.AsyncMock(
        return_value=httpx.Response(
            200,
            json={"result": result},
        )
    )
    monkeypatch.setattr(client, "_get", mock__get)

    response = await client.get_user(username)
    mock__get.assert_called_once_with(expected_url, params=None)
    assert response == result


@pytest.mark.parametrize(
    "errorcode,expected_result",
    [
        (404, "Sorry, but Fedora Accounts user 'biscuits_eater' does not exist"),
        (403, "Sorry, could not get info from FASJSON (code 403)"),
    ],
)
async def test_get_user_errors(respx_mock, errorcode, expected_result):
    client = FasjsonClient("http://fasjson.example.com")
    respx_mock.get("http://fasjson.example.com").mock(
        return_value=httpx.Response(
            errorcode,
            json={"result": "biscuits"},
        )
    )
    with pytest.raises(InfoGatherError, match=(re.escape(expected_result))):
        await client.get_user("biscuits_eater")


@pytest.mark.parametrize(
    "mxid", ["#scotchfinger:biscuits.test", "!icedvovo:biscuits.test", "timtam@biscuits.test"]
)
async def test_get_users_by_matrix_id_invalid_mxid(mxid):
    client = FasjsonClient("http://fasjson.example.com")
    with pytest.raises(
        InfoGatherError,
        match=(
            re.escape(
                f"Sorry, {mxid} does not look like a valid matrix user ID "
                "(e.g. @username:homeserver.com )"
            )
        ),
    ):
        await client.get_users_by_matrix_id(mxid)


async def test_get_users_by_matrix_id_multiple_users(monkeypatch):
    client = FasjsonClient("http://fasjson.example.com")
    mock_search_users = mock.AsyncMock(
        return_value=[{"username": "biscuit_eater"}, {"username": "cookie_eater"}]
    )
    monkeypatch.setattr(client, "search_users", mock_search_users)
    with pytest.raises(
        InfoGatherError,
        match=(
            re.escape(
                "2 Fedora Accounts users have the @cookie:biscuit.test Matrix Account "
                "defined:      \nbiscuit_eater      \ncookie_eater"
            )
        ),
    ):
        await client.get_users_by_matrix_id("@cookie:biscuit.test")


@pytest.mark.parametrize(
    "username,expected_url",
    [
        ("biscuit_eater", "users/biscuit_eater/groups"),
    ],
)
async def test_get_user_groups(monkeypatch, username, expected_url):
    result = ["group1", "group2"]
    client = FasjsonClient("http://fasjson.example.com")
    mock__get = mock.AsyncMock(
        return_value=httpx.Response(
            200,
            json={"groups": result},
        )
    )
    monkeypatch.setattr(client, "_get", mock__get)

    response = await client.get_user_groups(username)

    groups = result
    assert isinstance(response, list)
    assert all(group in result for group in groups)


@pytest.mark.parametrize(
    "errorcode,expected_result",
    [
        (404, "Sorry, but Fedora Accounts user 'biscuit_eater' does not exist"),
        (403, "Sorry, could not get info from FASJSON (code 403)"),
    ],
)
async def test_get_user_groups_errors(respx_mock, errorcode, expected_result):
    client = FasjsonClient("http://fasjson.example.com")
    respx_mock.get("http://fasjson.example.com").mock(
        return_value=httpx.Response(
            errorcode,
            json={"result": "biscuits"},
        )
    )
    with pytest.raises(InfoGatherError, match=(re.escape(expected_result))):
        await client.get_user_groups("biscuit_eater")
