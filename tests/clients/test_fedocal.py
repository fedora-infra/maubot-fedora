from datetime import datetime, timedelta

import httpx

from fedora.clients.fedocal import FedocalClient


async def test_fedocal_client_sortfilter_meetings(respx_mock):
    client = FedocalClient()

    meetings_data = [
        {
            "meeting_date": "2032-11-01",
            "meeting_time_start": "09:00:00",
            "meeting_name": "Meeting 1",
        },
        {
            "meeting_date": "2032-11-02",
            "meeting_time_start": "10:30:00",
            "meeting_name": "Meeting 2",
        },
    ]

    respx_mock.get("https://apps.fedoraproject.org/calendar/api/meetings").mock(
        return_value=httpx.Response(
            200,
            json={"meetings": meetings_data},
        )
    )

    meetings = await client._sortfilter_meetings()

    assert meetings == [
        (
            datetime(2032, 11, 1, 9, 0, 0),
            {
                "meeting_date": "2032-11-01",
                "meeting_time_start": "09:00:00",
                "meeting_name": "Meeting 1",
            },
        ),
        (
            datetime(2032, 11, 2, 10, 30, 0),
            {
                "meeting_date": "2032-11-02",
                "meeting_time_start": "10:30:00",
                "meeting_name": "Meeting 2",
            },
        ),
    ]


async def test_fedocal_client_future_meetings(respx_mock):
    client = FedocalClient()

    future_date = datetime.now() + timedelta(days=9 * 365)

    meetings_data = [
        {
            "meeting_date": future_date.strftime("%Y-%m-%d"),
            "meeting_time_start": "09:00:00",
            "meeting_name": "Meeting 1",
            "meeting_location": "#test:fedoraproject.org",
        },
        {
            "meeting_date": future_date.strftime("%Y-%m-%d"),
            "meeting_time_start": "10:30:00",
            "meeting_name": "Meeting 2",
            "meeting_location": "#general:fedoraproject.org",
        },
    ]

    respx_mock.get("https://apps.fedoraproject.org/calendar/api/meetings").mock(
        return_value=httpx.Response(
            200,
            json={"meetings": meetings_data},
        )
    )

    response = await client.future_meetings()

    assert response == (
        "- Meeting 1 (starting in 8 years)      \n" "- Meeting 2 (starting in 8 years)      \n"
    )


async def test_fedocal_client_future_meetings_nomeetings(respx_mock):
    client = FedocalClient()

    meetings_data = []

    respx_mock.get("https://apps.fedoraproject.org/calendar/api/meetings").mock(
        return_value=httpx.Response(
            200,
            json={"meetings": meetings_data},
        )
    )

    response = await client.future_meetings()

    assert response == "There are no future meetings in FedoCal."


async def test_fedocal_client_next_room_meeting_hasmeeting(respx_mock):
    client = FedocalClient()
    room = "#test:fedoraproject.org"

    future_date = datetime.now() + timedelta(days=9 * 365)

    meetings_data = [
        {
            "meeting_date": future_date.strftime("%Y-%m-%d"),
            "meeting_time_start": "09:00:00",
            "meeting_name": "Meeting 1",
            "meeting_location": "#test:fedoraproject.org",
        },
        {
            "meeting_date": future_date.strftime("%Y-%m-%d"),
            "meeting_time_start": "10:30:00",
            "meeting_name": "Meeting 2",
            "meeting_location": "#general:fedoraproject.org",
        },
    ]

    respx_mock.get("https://apps.fedoraproject.org/calendar/api/meetings").mock(
        return_value=httpx.Response(
            200,
            json={"meetings": meetings_data},
        )
    )

    response = await client.next_room_meeting(room)

    assert response == (
        "The next meeting in this room (#test:fedoraproject.org) "
        "is: 'Meeting 1' (starting in 8 years)"
    )


async def test_fedocal_client_next_room_meeting_hasnomeeting(respx_mock):
    client = FedocalClient()
    room = "#test2:fedoraproject.org"

    future_date = datetime.now() + timedelta(days=9 * 365)

    meetings_data = [
        {
            "meeting_date": future_date.strftime("%Y-%m-%d"),
            "meeting_time_start": "09:00:00",
            "meeting_name": "Meeting 1",
            "meeting_location": "#test:fedoraproject.org",
        },
        {
            "meeting_date": future_date.strftime("%Y-%m-%d"),
            "meeting_time_start": "10:30:00",
            "meeting_name": "Meeting 2",
            "meeting_location": "#general:fedoraproject.org",
        },
    ]

    respx_mock.get("https://apps.fedoraproject.org/calendar/api/meetings").mock(
        return_value=httpx.Response(
            200,
            json={"meetings": meetings_data},
        )
    )

    response = await client.next_room_meeting(room)

    assert response == (
        "There are no future meetings in FedoCal " "for this room (#test2:fedoraproject.org)."
    )
