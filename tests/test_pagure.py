import httpx
import pytest


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
    respx_mock.get(f"http://pagure.example.com/api/0/{project}/issue/42").mock(
        return_value=httpx.Response(
            200,
            json={
                "title": "Dummy Issue",
                "full_url": f"http://pagure.example.com/{project}/issues/42",
            },
        )
    )
    await bot.send(f"!{command} 42")
    assert len(bot.sent) == 1
    expected_text = f"{project} #42 (http://pagure.example.com/{project}/issues/42): Dummy Issue"
    expected_html = (
        f'<p><a href="http://pagure.example.com/{project}/issues/42">'
        f"{project} #42</a>: Dummy Issue</p>\n"
    )
    assert bot.sent[0].content.body == expected_text
    assert bot.sent[0].content.formatted_body == expected_html


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
