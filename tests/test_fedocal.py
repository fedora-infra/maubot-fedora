import httpx
from datetime import datetime, timedelta

async def test_fedocal_nextmeetings(bot, plugin, respx_mock, monkeypatch):   
    room = "#test:fedoraproject.org"
    
    future_date = datetime.now() + timedelta(days=9*365)
    
    meetings_data = [
        {"meeting_date": future_date.strftime("%Y-%m-%d"), "meeting_time_start": "09:00:00", "meeting_name": "Meeting 1", "meeting_location": "#test:fedoraproject.org"},
        {"meeting_date": future_date.strftime("%Y-%m-%d"), "meeting_time_start": "10:30:00", "meeting_name": "Meeting 2", "meeting_location": "#general:fedoraproject.org"},
    ]
    
    respx_mock.get(f"https://apps.fedoraproject.org/calendar/api/meetings").mock(
        return_value=httpx.Response(
            200,
            json={"meetings": meetings_data},
        )
    )
    
    await bot.send("!nextmeetings")
    assert len(bot.sent) == 1
    expected = (
        "The next meetings in FedoCal are:\n\n"
        "● Meeting 1 (starting in 8 years)\n"
        "● Meeting 2 (starting in 8 years)\n"
        "   There are no future meetings in FedoCal for this room (testroom)."
    )
    assert bot.sent[0].content.body == expected
