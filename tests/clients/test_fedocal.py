import httpx
import pytest
from datetime import datetime
from fedora.clients.fedocal import FedocalClient

# Mocking HTTP responses using respx
@pytest.mark.asyncio
async def test_fedocal_client_get_matrix_rooms(respx_mock):
    client = FedocalClient()
    locations = [
        "testmeeting1@fedoraproject.org",
        "testmeeting2@fedoraproject.org",
    ]
    respx_mock.get("https://apps.fedoraproject.org/calendar/api/locations/").mock(
        return_value=httpx.Response(
            200,
            json={"locations": locations},
        )
    )
    matrix_rooms = await client.get_matrix_rooms()
    assert matrix_rooms == locations

@pytest.mark.asyncio
async def test_fedocal_client_get_next_meetings(respx_mock):
    client = FedocalClient()
    room = "testmeeting1"
    meetings_data = [
        {"meeting_date": "2023-11-01", "meeting_time_start": "09:00:00", "meeting_name": "Meeting 1"},
        {"meeting_date": "2023-11-02", "meeting_time_start": "10:30:00", "meeting_name": "Meeting 2"},
    ]
    respx_mock.get(f"https://apps.fedoraproject.org/calendar/api/meetings?location={room}@fedoraproject.org").mock(
        return_value=httpx.Response(
            200,
            json={"meetings": meetings_data},
        )
    )
    meetings = await client.get_next_meetings(room)
    assert meetings == [
        (
            datetime(2023, 11, 1, 9, 0, 0),
            {"meeting_date": "2023-11-01", "meeting_time_start": "09:00:00", "meeting_name": "Meeting 1"},
        ),
        (
            datetime(2023, 11, 2, 10, 30, 0),
            {"meeting_date": "2023-11-02", "meeting_time_start": "10:30:00", "meeting_name": "Meeting 2"},
        ),
    ]
