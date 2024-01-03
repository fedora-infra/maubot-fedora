import httpx
import pytest
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_fedocal_next_meeting(bot, plugin, respx_mock):
    respx_mock.get("https://apps.fedoraproject.org/calendar/api/meetings?location=channel1@fedoraproject.org").mock(
        return_value=httpx.Response(
            200,
            json={"meetings": [{"meeting_date": "2023-11-01", "meeting_time_start": "09:00:00", "meeting_name": "Meeting 1"}]},
        )
    )
    await bot.send("!nextmeeting channel1")
    assert len(bot.sent) == 1
    expected_response = "Next Meeting in #channel1:"
    assert bot.sent[0].content.body == expected_response

@pytest.mark.asyncio
async def test_fedocal_next_meetings(bot, plugin, respx_mock):   
    test_date = datetime.now().date()
    test_date = test_date + timedelta(days=1)
    test_date = test_date.strftime("%Y-%m-%d")
    respx_mock.get("https://apps.fedoraproject.org/calendar/api/meetings?location=channel1@fedoraproject.org").mock(
        return_value=httpx.Response(
            200,
            json={"meetings": [{"meeting_date": test_date, "meeting_time_start": "09:00:00", "meeting_name": "Meeting 1"},
                               {"meeting_date": test_date, "meeting_time_start": "10:30:00", "meeting_name": "Meeting 2"}]},
        )
    )
    await bot.send("!nextmeetings channel1")
    assert len(bot.sent) == 1
    expected_header = "Next Meetings in #channel1:"
    assert bot.sent[0].content.body == expected_header
