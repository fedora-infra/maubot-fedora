import httpx
import pytest

OUTAGE_FULL = {
    "title": "thetitle",
    "ticket": {"id": "1", "url": "https://i.test/1"},
    "startdate": "2023-08-06T1:00:00+0000",
    "enddate": "2023-08-06T2:00:00+0000",
}
OUTAGE_NO_ENDDATE = {
    "title": "thetitle",
    "ticket": {"id": "1", "url": "https://i.test/1"},
    "startdate": "2023-08-06T1:00:00+0000",
    "enddate": None,
}
OUTAGE_NO_TICKET = {
    "title": "thetitle",
    "ticket": None,
    "startdate": "2023-08-06T1:00:00+0000",
    "enddate": "2023-08-06T2:00:00+0000",
}
OUTAGE_NO_ENDDATE_NO_TICKET = {
    "title": "thetitle",
    "ticket": None,
    "startdate": "2023-08-06T1:00:00+0000",
    "enddate": None,
}


@pytest.mark.parametrize(
    "outages",
    [
        (
            [OUTAGE_FULL, OUTAGE_NO_ENDDATE, OUTAGE_NO_ENDDATE_NO_TICKET, OUTAGE_NO_TICKET],
            [OUTAGE_FULL, OUTAGE_NO_ENDDATE, OUTAGE_NO_ENDDATE_NO_TICKET, OUTAGE_NO_TICKET],
            (
                "I checked Fedora Status (http://status.example.com) and there are "
                "**4 ongoing** and **4 planned** outages on Fedora Infrastructure.\n\n"
                "##### Ongoing\n"
                "● **thetitle (https://i.test/1)**\n"
                "   Started at: 2023-08-06T1:00:00+0000\n"
                "   Estimated to end: 2023-08-06T2:00:00+0000\n"
                "● **thetitle (https://i.test/1)**\n"
                "   Started at: 2023-08-06T1:00:00+0000\n"
                "   Estimated to end: Unknown\n"
                "● **thetitle**\n"
                "   Started at: 2023-08-06T1:00:00+0000\n"
                "   Estimated to end: Unknown\n"
                "● **thetitle**\n"
                "   Started at: 2023-08-06T1:00:00+0000\n"
                "   Estimated to end: 2023-08-06T2:00:00+0000\n"
                "##### Planned\n"
                "● **thetitle (https://i.test/1)**\n"
                "   Scheduled to start at: 2023-08-06T1:00:00+0000\n"
                "   Scheduled to end at: 2023-08-06T2:00:00+0000\n"
                "● **thetitle (https://i.test/1)**\n"
                "   Scheduled to start at: 2023-08-06T1:00:00+0000\n"
                "   Scheduled to end at: Unknown\n"
                "● **thetitle**\n"
                "   Scheduled to start at: 2023-08-06T1:00:00+0000\n"
                "   Scheduled to end at: Unknown\n"
                "● **thetitle**\n"
                "   Scheduled to start at: 2023-08-06T1:00:00+0000\n"
                "   Scheduled to end at: 2023-08-06T2:00:00+0000"
            ),
        ),
        (
            [OUTAGE_FULL, OUTAGE_NO_ENDDATE, OUTAGE_NO_ENDDATE_NO_TICKET, OUTAGE_NO_TICKET],
            [],
            (
                "I checked Fedora Status (http://status.example.com) and there are "
                "**4 ongoing** and **0 planned** outages on Fedora Infrastructure.\n\n"
                "##### Ongoing\n"
                "● **thetitle (https://i.test/1)**\n"
                "   Started at: 2023-08-06T1:00:00+0000\n"
                "   Estimated to end: 2023-08-06T2:00:00+0000\n"
                "● **thetitle (https://i.test/1)**\n"
                "   Started at: 2023-08-06T1:00:00+0000\n"
                "   Estimated to end: Unknown\n"
                "● **thetitle**\n"
                "   Started at: 2023-08-06T1:00:00+0000\n"
                "   Estimated to end: Unknown\n"
                "● **thetitle**\n"
                "   Started at: 2023-08-06T1:00:00+0000\n"
                "   Estimated to end: 2023-08-06T2:00:00+0000"
            ),
        ),
        (
            [],
            [OUTAGE_FULL, OUTAGE_NO_ENDDATE, OUTAGE_NO_ENDDATE_NO_TICKET, OUTAGE_NO_TICKET],
            (
                "I checked Fedora Status (http://status.example.com) and there are "
                "**0 ongoing** and **4 planned** outages on Fedora Infrastructure.\n\n"
                "##### Planned\n"
                "● **thetitle (https://i.test/1)**\n"
                "   Scheduled to start at: 2023-08-06T1:00:00+0000\n"
                "   Scheduled to end at: 2023-08-06T2:00:00+0000\n"
                "● **thetitle (https://i.test/1)**\n"
                "   Scheduled to start at: 2023-08-06T1:00:00+0000\n"
                "   Scheduled to end at: Unknown\n"
                "● **thetitle**\n"
                "   Scheduled to start at: 2023-08-06T1:00:00+0000\n"
                "   Scheduled to end at: Unknown\n"
                "● **thetitle**\n"
                "   Scheduled to start at: 2023-08-06T1:00:00+0000\n"
                "   Scheduled to end at: 2023-08-06T2:00:00+0000"
            ),
        ),
        (
            [],
            [],
            (
                "I checked Fedora Status (http://status.example.com) and there are "
                "**no planned or ongoing outages on Fedora Infrastructure.**"
            ),
        ),
    ],
)
async def test_infra_outages(bot, plugin, respx_mock, outages):
    ongoing_json_response = {"outages": outages[0]}
    respx_mock.get("http://status.example.com/ongoing.json").mock(
        return_value=httpx.Response(
            200,
            json=ongoing_json_response,
        )
    )

    planned_json_response = {"outages": outages[1]}
    respx_mock.get("http://status.example.com/planned.json").mock(
        return_value=httpx.Response(
            200,
            json=planned_json_response,
        )
    )
    await bot.send("!infra status")
    assert len(bot.sent) == 1
    print(repr(bot.sent[0].content.body))
    assert bot.sent[0].content.body == outages[2]
