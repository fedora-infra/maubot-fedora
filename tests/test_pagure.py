import datetime
from unittest import mock

import httpx
import pytest

import fedora


@pytest.mark.parametrize(
    "command,project",
    [
        ("pagureissue dummy-project", "dummy-project"),
        ("fpc", "packaging-committee"),
        ("epel", "epel"),
        ("fesco", "fesco"),
    ],
)
async def test_pagureissue(bot, plugin, respx_mock, command, project):
    user = {
        "full_url": "https://pagure.io/user/humaton",
        "fullname": "Tomáš Hrčka",
        "name": "humaton",
        "url_path": "user/humaton",
    }
    two_weeks_ago_ts = int((datetime.datetime.utcnow() + datetime.timedelta(weeks=-2)).timestamp())
    one_week_ago_ts = int((datetime.datetime.utcnow() + datetime.timedelta(weeks=-1)).timestamp())
    response = {
        "assignee": None,
        "blocks": [],
        "close_status": None,
        "closed_at": None,
        "closed_by": None,
        "comments": [],
        "content": "Hi, \r\nafter the epel9 rwas created a",
        "custom_fields": [],
        "date_created": two_weeks_ago_ts,
        "depends": [],
        "full_url": f"https://pagure.io/{project}/issue/261",
        "id": 261,
        "last_updated": two_weeks_ago_ts,
        "milestone": None,
        "priority": None,
        "private": False,
        "related_prs": [],
        "status": "Open",
        "tags": [],
        "title": "When creating new epel release please include MDAPI",
        "user": user,
    }
    respx_mock.get(f"http://pagure.example.com/api/0/{project}/issue/42").mock(
        return_value=httpx.Response(
            200,
            json=response,
        )
    )
    await bot.send(f"!{command} 42")
    assert len(bot.sent) == 1
    assert bot.sent[0].content.body == (
        f"**{project} #42** (https://pagure.io/{project}/issue/261):"
        f"**When creating new epel release please include MDAPI**\n\n"
        f"● **Opened:** 2 weeks ago by humaton\n"
        f"● **Last Updated:** Never\n"
        f"● **Assignee:** Not Assigned"
    )
    assert bot.sent[0].content.formatted_body == (
        f'<p><a href="https://pagure.io/{project}/issue/261">'
        f"<strong>{project} #42</strong></a>:"
        f"<strong>When creating new epel release please include MDAPI</strong>"
        f"</p>\n<ul>\n"
        f"<li><strong>Opened:</strong> 2 weeks ago by humaton</li>\n"
        f"<li><strong>Last Updated:</strong> Never</li>\n"
        f"<li><strong>Assignee:</strong> Not Assigned</li>\n</ul>\n"
    )

    # test an issue that is closed and assigned
    response["closed_at"] = one_week_ago_ts
    response["closed_by"] = user
    response["close_status"] = "Closed"
    response["last_updated"] = one_week_ago_ts
    response["assignee"] = user
    respx_mock.get(f"http://pagure.example.com/api/0/{project}/issue/42").mock(
        return_value=httpx.Response(
            200,
            json=response,
        )
    )
    await bot.send(f"!{command} 42")
    assert len(bot.sent) == 2
    assert bot.sent[1].content.body == (
        f"**{project} #42** (https://pagure.io/{project}/issue/261):"
        f"**When creating new epel release please include MDAPI**\n\n"
        f"● **Open: Closed** a week ago by humaton\n"
        f"● **Opened:** 2 weeks ago by humaton\n"
        f"● **Last Updated:** a week ago\n"
        f"● **Assignee:** humaton"
    )
    assert bot.sent[1].content.formatted_body == (
        f'<p><a href="https://pagure.io/{project}/issue/261">'
        f"<strong>{project} #42</strong></a>:"
        f"<strong>When creating new epel release please include MDAPI</strong></p>\n"
        f"<ul>\n"
        f"<li><strong>Open: Closed</strong> a week ago by humaton</li>\n"
        f"<li><strong>Opened:</strong> 2 weeks ago by humaton</li>\n"
        f"<li><strong>Last Updated:</strong> a week ago</li>\n"
        f"<li><strong>Assignee:</strong> humaton</li>\n</ul>\n"
    )


async def test_issue_notfound(bot, plugin, respx_mock):
    respx_mock.get("http://pagure.example.com/api/0/biscuits_project/issue/44").mock(
        return_value=httpx.Response(404, json={"error": "Biscuits not Found Error"})
    )
    await bot.send("!pagureissue biscuits_project 44")

    assert len(bot.sent) == 1
    assert bot.sent[0].content.body == "Issue querying Pagure: Biscuits not Found Error"


@pytest.mark.parametrize(
    "command,result",
    [
        ("!fpc", ["packaging-committee", ""]),
        ("!fpc 1234", ["packaging-committee", "1234"]),
        ("!fpcd 1234", []),
        ("a!fpcd 1234", []),
        ("!fpc 1234 1234", ["packaging-committee", "1234 1234"]),
    ],
)
async def test_pagureissue_regex(bot, plugin, monkeypatch, command, result):
    mocked_get_pagure_issue = mock.AsyncMock()
    monkeypatch.setattr(
        fedora.pagureio.PagureIOHandler, "_get_pagure_issue", mocked_get_pagure_issue
    )
    await bot.send(command)
    if result == []:
        mocked_get_pagure_issue.assert_not_called()
    else:
        mocked_get_pagure_issue.assert_called_once()
        assert mocked_get_pagure_issue.call_args[0][1] == result[0]
        assert mocked_get_pagure_issue.call_args[0][2] == result[1]


async def test_whoowns(bot, plugin, respx_mock):
    respx_mock.get("http://src.example.com/api/0/rpms/dummy-package").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_users": {
                    "admin": ["admin-1", "admin-2"],
                    "owner": ["owner-1", "owner-2"],
                    "commit": ["committer-1", "committer-2"],
                },
            },
        )
    )
    await bot.send("!whoowns dummy-package")
    assert len(bot.sent) == 1
    expected_text = (
        "**owner:** owner-1, owner-2\n "
        "**admin:** admin-1, admin-2\n "
        "**commit:** committer-1, committer-2"
    )
    expected_html = (
        "<p><strong>owner:</strong> owner-1, owner-2<br />\n"
        "<strong>admin:</strong> admin-1, admin-2<br />\n"
        "<strong>commit:</strong> committer-1, committer-2</p>\n"
    )
    assert bot.sent[0].content.body == expected_text
    assert bot.sent[0].content.formatted_body == expected_html


@pytest.mark.parametrize("access_type", [None, "admin", "owner", "commit"])
async def test_whoowns_empty_users(bot, plugin, respx_mock, access_type):
    json_response = {
        "access_users": {
            "admin": [],
            "owner": [],
            "commit": [],
        }
    }

    if access_type:
        json_response["access_users"][access_type] = [f"{access_type}-1", f"{access_type}-2"]
    respx_mock.get("http://src.example.com/api/0/rpms/dummy-package").mock(
        return_value=httpx.Response(
            200,
            json=json_response,
        )
    )
    await bot.send("!whoowns dummy-package")
    if access_type:
        assert len(bot.sent) == 1
        expected_text = f"**{access_type}:** {access_type}-1, {access_type}-2"
        expected_html = f"<p><strong>{access_type}:</strong> {access_type}-1, {access_type}-2</p>\n"
        assert bot.sent[0].content.body == expected_text
        assert bot.sent[0].content.formatted_body == expected_html
    else:
        assert bot.sent[0].content.body == (
            "dummy-package has no owners, admins, or users with " "commit access"
        )
        assert len(bot.sent) == 1


async def test_whoowns_no_package_given(bot, plugin):
    await bot.send("!whoowns")
    assert len(bot.sent) == 1
    assert bot.sent[0].content.body == "package argument is required. e.g. `!whoowns kernel`"


async def test_whoowns_get_project_infogathererror(bot, plugin, respx_mock, monkeypatch):
    errormessage = "biscuits!"
    mock_get_project = mock.AsyncMock(side_effect=fedora.exceptions.InfoGatherError(errormessage))
    monkeypatch.setattr(fedora.distgit.PagureClient, "get_project", mock_get_project)
    respx_mock.get("http://src.example.com/api/0/rpms/dummy-package").mock(
        return_value=httpx.Response(
            200,
            json={},
        )
    )
    await bot.send("!whoowns kernel")

    assert len(bot.sent) == 1
    assert bot.sent[0].content.body == errormessage
