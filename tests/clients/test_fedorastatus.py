import httpx
import pytest
from pydantic import ValidationError

from fedora.clients.fedorastatus import FedoraStatusClient
from fedora.exceptions import InfoGatherError


async def test_get_outages(respx_mock):
    client = FedoraStatusClient("http://status.example.com")
    json_response = {
        "outages": [
            {
                "title": "Matrix / libera.chat IRC bridge unavailable",
                "ticket": {
                    "id": "11460",
                    "url": "https://pagure.io/fedora-infrastructure/issue/11460",
                },
                "startdate": "2023-08-06T12:00:00+0000",
                "enddate": None,
            }
        ]
    }
    respx_mock.get("http://status.example.com").mock(
        return_value=httpx.Response(
            200,
            json=json_response,
        )
    )
    response = await client.get_outages("ongoing")
    assert response == json_response


async def test_invalid_outage_type():
    client = FedoraStatusClient("http://status.example.com")
    with pytest.raises(ValidationError, match="Input should be 'ongoing', 'planned' or 'resolved'"):
        await client.get_outages("PANTS")


async def test_error_response(respx_mock):
    client = FedoraStatusClient("http://status.example.com")
    respx_mock.get("http://status.example.com").mock(return_value=httpx.Response(404))
    with pytest.raises(InfoGatherError, match="Issue querying Fedora Status: 404: Not Found"):
        await client.get_outages("ongoing")
