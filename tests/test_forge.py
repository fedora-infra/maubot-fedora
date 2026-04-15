import datetime
from unittest import mock

import httpx
import pytest

import fedora


@pytest.mark.parametrize(
    "command,org,repo",
    [
        ("forge issue dummy-org dummy-repo", "dummy-org", "dummy-repo"),
        ("epel", "epel", "steering"),
    ],
)
async def test_forge_issue(bot, plugin, respx_mock, command, org, repo):
    user = {
        "html_url": "https://forge.fedoraproject.org/humaton",
        "full_name": "Tomáš Hrčka",
        "username": "humaton",
    }
    two_weeks_ago_ts = str(
        (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(weeks=-2)).isoformat()
    )
    one_week_ago_ts = str(
        (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(weeks=-1)).isoformat()
    )
    response = {
        "assignee": None,
        "closed_at": None,
        "comments": 0,
        "body": "Hi, \r\nafter the epel9 rwas created a",
        "created_at": two_weeks_ago_ts,
        "html_url": f"https://forge.fedoraproject.org/{org}/{repo}/issues/261",
        "id": 261,
        "updated_at": two_weeks_ago_ts,
        "milestone": None,
        "state": "open",
        "labels": [],
        "title": "When creating new epel release please include MDAPI",
        "user": user,
    }
    respx_mock.get(f"http://forge.example.com/api/v1/repos/{org}/{repo}/issues/42").mock(
        return_value=httpx.Response(
            200,
            json=response,
        )
    )
    await bot.send(f"!{command} 42")
    assert len(bot.sent) == 1
    assert bot.sent[0].content.body == (
        f"**{org}/{repo} #42** (https://forge.fedoraproject.org/{org}/{repo}/issues/261):"
        f"**When creating new epel release please include MDAPI**\n\n"
        f"● **Opened:** 2 weeks ago by humaton\n"
        f"● **Last Updated:** Never\n"
        f"● **Assignee:** Not Assigned"
    )
    assert bot.sent[0].content.formatted_body == (
        f'<p><a href="https://forge.fedoraproject.org/{org}/{repo}/issues/261">'
        f"<strong>{org}/{repo} #42</strong></a>:"
        f"<strong>When creating new epel release please include MDAPI</strong>"
        f"</p>\n<ul>\n"
        f"<li><strong>Opened:</strong> 2 weeks ago by humaton</li>\n"
        f"<li><strong>Last Updated:</strong> Never</li>\n"
        f"<li><strong>Assignee:</strong> Not Assigned</li>\n</ul>\n"
    )

    # test an issue that is closed and assigned
    response["closed_at"] = one_week_ago_ts
    response["state"] = "closed"
    response["updated_at"] = one_week_ago_ts
    response["assignee"] = user
    respx_mock.get(f"http://forge.example.com/api/v1/repos/{org}/{repo}/issues/42").mock(
        return_value=httpx.Response(
            200,
            json=response,
        )
    )
    await bot.send(f"!{command} 42")
    assert len(bot.sent) == 2
    assert bot.sent[1].content.body == (
        f"**{org}/{repo} #42** (https://forge.fedoraproject.org/{org}/{repo}/issues/261):"
        f"**When creating new epel release please include MDAPI**\n\n"
        f"● **Closed** a week ago\n"
        f"● **Opened:** 2 weeks ago by humaton\n"
        f"● **Last Updated:** a week ago\n"
        f"● **Assignee:** humaton"
    )
    assert bot.sent[1].content.formatted_body == (
        f'<p><a href="https://forge.fedoraproject.org/{org}/{repo}/issues/261">'
        f"<strong>{org}/{repo} #42</strong></a>:"
        f"<strong>When creating new epel release please include MDAPI</strong></p>\n"
        f"<ul>\n"
        f"<li><strong>Closed</strong> a week ago</li>\n"
        f"<li><strong>Opened:</strong> 2 weeks ago by humaton</li>\n"
        f"<li><strong>Last Updated:</strong> a week ago</li>\n"
        f"<li><strong>Assignee:</strong> humaton</li>\n</ul>\n"
    )


@pytest.mark.parametrize(
    "command,org,repo",
    [
        ("forge pr dummy-org dummy-repo", "dummy-org", "dummy-repo"),
        ("edpr", "epel", "docs"),
    ],
)
async def test_forge_pull_request(bot, plugin, respx_mock, command, org, repo):
    user = {
        "html_url": "https://forge.fedoraproject.org/humaton",
        "full_name": "Tomáš Hrčka",
        "username": "humaton",
    }
    two_weeks_ago_ts = str(
        (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(weeks=-2)).isoformat()
    )
    one_week_ago_ts = str(
        (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(weeks=-1)).isoformat()
    )
    response = {
        "assignee": None,
        "closed_at": None,
        "comments": 0,
        "body": "Hi, \r\nafter the epel9 rwas created a",
        "created_at": two_weeks_ago_ts,
        "html_url": f"https://forge.fedoraproject.org/{org}/{repo}/pulls/261",
        "id": 261,
        "updated_at": two_weeks_ago_ts,
        "milestone": None,
        "merged": False,
        "state": "open",
        "labels": [],
        "title": "When creating new epel release please include MDAPI",
        "user": user,
    }
    respx_mock.get(f"http://forge.example.com/api/v1/repos/{org}/{repo}/pulls/42").mock(
        return_value=httpx.Response(
            200,
            json=response,
        )
    )
    await bot.send(f"!{command} 42")
    assert len(bot.sent) == 1
    assert bot.sent[0].content.body == (
        f"**{org}/{repo} #42** (https://forge.fedoraproject.org/{org}/{repo}/pulls/261):"
        f"**When creating new epel release please include MDAPI**\n\n"
        f"● **Opened:** 2 weeks ago by humaton\n"
        f"● **Last Updated:** Never\n"
        f"● **Assignee:** Not Assigned"
    )
    assert bot.sent[0].content.formatted_body == (
        f'<p><a href="https://forge.fedoraproject.org/{org}/{repo}/pulls/261">'
        f"<strong>{org}/{repo} #42</strong></a>:"
        f"<strong>When creating new epel release please include MDAPI</strong>"
        f"</p>\n<ul>\n"
        f"<li><strong>Opened:</strong> 2 weeks ago by humaton</li>\n"
        f"<li><strong>Last Updated:</strong> Never</li>\n"
        f"<li><strong>Assignee:</strong> Not Assigned</li>\n</ul>\n"
    )

    # test a pull request that is closed and assigned
    response["closed_at"] = one_week_ago_ts
    response["state"] = "closed"
    response["updated_at"] = one_week_ago_ts
    response["assignee"] = user
    respx_mock.get(f"http://forge.example.com/api/v1/repos/{org}/{repo}/pulls/42").mock(
        return_value=httpx.Response(
            200,
            json=response,
        )
    )
    await bot.send(f"!{command} 42")
    assert len(bot.sent) == 2
    assert bot.sent[1].content.body == (
        f"**{org}/{repo} #42** (https://forge.fedoraproject.org/{org}/{repo}/pulls/261):"
        f"**When creating new epel release please include MDAPI**\n\n"
        f"● **Closed** a week ago\n"
        f"● **Opened:** 2 weeks ago by humaton\n"
        f"● **Last Updated:** a week ago\n"
        f"● **Assignee:** humaton"
    )
    assert bot.sent[1].content.formatted_body == (
        f'<p><a href="https://forge.fedoraproject.org/{org}/{repo}/pulls/261">'
        f"<strong>{org}/{repo} #42</strong></a>:"
        f"<strong>When creating new epel release please include MDAPI</strong></p>\n"
        f"<ul>\n"
        f"<li><strong>Closed</strong> a week ago</li>\n"
        f"<li><strong>Opened:</strong> 2 weeks ago by humaton</li>\n"
        f"<li><strong>Last Updated:</strong> a week ago</li>\n"
        f"<li><strong>Assignee:</strong> humaton</li>\n</ul>\n"
    )

    # test a pull request that is closed, merged and assigned
    response["merged"] = True
    response["merged_at"] = one_week_ago_ts
    response["merged_by"] = user
    respx_mock.get(f"http://forge.example.com/api/v1/repos/{org}/{repo}/pulls/42").mock(
        return_value=httpx.Response(
            200,
            json=response,
        )
    )
    await bot.send(f"!{command} 42")
    assert len(bot.sent) == 3
    assert bot.sent[2].content.body == (
        f"**{org}/{repo} #42** (https://forge.fedoraproject.org/{org}/{repo}/pulls/261):"
        f"**When creating new epel release please include MDAPI**\n\n"
        f"● **Merged** a week ago by humaton\n"
        f"● **Opened:** 2 weeks ago by humaton\n"
        f"● **Last Updated:** a week ago\n"
        f"● **Assignee:** humaton"
    )
    assert bot.sent[2].content.formatted_body == (
        f'<p><a href="https://forge.fedoraproject.org/{org}/{repo}/pulls/261">'
        f"<strong>{org}/{repo} #42</strong></a>:"
        f"<strong>When creating new epel release please include MDAPI</strong></p>\n"
        f"<ul>\n"
        f"<li><strong>Merged</strong> a week ago by humaton</li>\n"
        f"<li><strong>Opened:</strong> 2 weeks ago by humaton</li>\n"
        f"<li><strong>Last Updated:</strong> a week ago</li>\n"
        f"<li><strong>Assignee:</strong> humaton</li>\n</ul>\n"
    )


async def test_issue_notfound(bot, plugin, respx_mock):
    respx_mock.get(
        "http://forge.example.com/api/v1/repos/biscuits_namespace/biscuits_project/issues/44"
    ).mock(return_value=httpx.Response(404, json={"error": "Biscuits not Found Error"}))
    await bot.send("!forge issue biscuits_namespace biscuits_project 44")

    assert len(bot.sent) == 1
    assert bot.sent[0].content.body == "Issue querying Forgejo: Biscuits not Found Error"


async def test_pull_request_notfound(bot, plugin, respx_mock):
    respx_mock.get(
        "http://forge.example.com/api/v1/repos/biscuits_namespace/biscuits_project/pulls/44"
    ).mock(return_value=httpx.Response(404, json={"error": "Biscuits not Found Error"}))
    await bot.send("!forge pr biscuits_namespace biscuits_project 44")

    assert len(bot.sent) == 1
    assert bot.sent[0].content.body == "Issue querying Forgejo: Biscuits not Found Error"


@pytest.mark.parametrize(
    "command,result",
    [
        ("!forge", []),
        ("!forge asdasd", []),
        ("!forge issue", ["issue", "", "", ""]),
        ("!forge issue epel", ["issue", "epel", "", ""]),
        ("!forge issue epel steering", ["issue", "epel", "steering", ""]),
        ("!forge issue epel steering 1234", ["issue", "epel", "steering", "1234"]),
        ("!forge pr", ["pr", "", "", ""]),
        ("!forge pr epel", ["pr", "epel", "", ""]),
        ("!forge pr epel docs", ["pr", "epel", "docs", ""]),
        ("!forge pr epel docs 1234", ["pr", "epel", "docs", "1234"]),
        ("!epel", ["issue", "epel", "steering", ""]),
        ("!epel 1234", ["issue", "epel", "steering", "1234"]),
        ("!edpr", ["pr", "epel", "docs", ""]),
        ("!edpr 1234", ["pr", "epel", "docs", "1234"]),
        ("!epeld 1234", []),
        ("a!epeld 1234", []),
        ("!epel 1234 1234", ["issue", "epel", "steering", "1234 1234"]),
        ("!edpr 1234 1234", ["pr", "epel", "docs", "1234 1234"]),
        ("!cookies 1234", []),
        ("!tar 1234", []),
    ],
)
async def test_forge_regex(bot, plugin, monkeypatch, command, result):
    mocked_get_forge_issue = mock.AsyncMock()
    mocked_get_forge_pull_request = mock.AsyncMock()
    monkeypatch.setattr(fedora.forge.ForgeHandler, "_get_forge_issue", mocked_get_forge_issue)
    monkeypatch.setattr(
        fedora.forge.ForgeHandler, "_get_forge_pull_request", mocked_get_forge_pull_request
    )
    await bot.send(command)
    if result == []:
        mocked_get_forge_issue.assert_not_called()
        mocked_get_forge_pull_request.assert_not_called()
    elif result[0] == "issue":
        mocked_get_forge_pull_request.assert_not_called()
        mocked_get_forge_issue.assert_called_once()
        assert mocked_get_forge_issue.call_args[0][1] == result[1]
        assert mocked_get_forge_issue.call_args[0][2] == result[2]
        assert mocked_get_forge_issue.call_args[0][3] == result[3]
    elif result[0] == "pr":
        mocked_get_forge_issue.assert_not_called()
        mocked_get_forge_pull_request.assert_called_once()
        assert mocked_get_forge_pull_request.call_args[0][1] == result[1]
        assert mocked_get_forge_pull_request.call_args[0][2] == result[2]
        assert mocked_get_forge_pull_request.call_args[0][3] == result[3]
