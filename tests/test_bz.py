import httpx


async def test_bug(bot, plugin, respx_mock):
    respx_mock.get("https://bugzilla.redhat.com/rest/bug/42").mock(
        return_value=httpx.Response(
            200,
            json={"bugs": [{"summary": "Dummy Issue"}]},
        )
    )
    await bot.send("!bug 42")
    assert len(bot.sent) == 1
    expected_text = "RHBZ#42 (https://bugzilla.redhat.com/42): Dummy Issue"
    expected_html = '<p><a href="https://bugzilla.redhat.com/42">' "RHBZ#42</a>: Dummy Issue</p>\n"
    assert bot.sent[0].content.body == expected_text
    assert bot.sent[0].content.formatted_body == expected_html


async def test_bug_no_id(bot, plugin):
    await bot.send("!bug")
    assert len(bot.sent) == 1
    expected_text = "bug_id argument is required. e.g. `!bug 1234567`"
    assert bot.sent[0].content.body == expected_text
