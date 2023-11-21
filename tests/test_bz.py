import httpx


async def test_bug(bot, plugin, respx_mock):
    respx_mock.get("https://bugzilla.redhat.com/rest/bug/42").mock(
        return_value=httpx.Response(
            200,
            json={"bugs": [{"component": ["Bugzilla General"], "summary": "Dummy Issue"}]},
        )
    )
    await bot.send("!bug 42")
    assert len(bot.sent) == 1
    expected_text = "RHBZ#42 (https://bugzilla.redhat.com/42): [Bugzilla General]: Dummy Issue"
    expected_html = (
        '<p><a href="https://bugzilla.redhat.com/42">'
        "RHBZ#42</a>: [Bugzilla General]: Dummy Issue</p>\n"
    )
    assert bot.sent[0].content.body == expected_text
    assert bot.sent[0].content.formatted_body == expected_html
