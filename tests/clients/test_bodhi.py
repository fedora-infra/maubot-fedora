import httpx
import pytest

from fedora.clients.bodhi import BodhiClient
from fedora.exceptions import InfoGatherError


async def test_get_current_release(respx_mock):
    client = BodhiClient("http://bodhi.example.com")
    respx_mock.get("http://bodhi.example.com").mock(
        return_value=httpx.Response(
            200,
            json={
                "releases": [
                    {
                        "name": "F38",
                        "long_name": "Fedora 38",
                        "version": "38",
                        "id_prefix": "FEDORA",
                        "eol": "2024-05-14",
                    },
                    {
                        "name": "F37",
                        "long_name": "Fedora 37",
                        "version": "37",
                        "id_prefix": "FEDORA",
                        "eol": "2023-11-14",
                    },
                    {
                        "name": "F38C",
                        "long_name": "Fedora 38 Containers",
                        "version": "38",
                        "id_prefix": "FEDORA-CONTAINER",
                        "eol": "2024-05-14",
                    },
                ],
                "page": 1,
                "pages": 1,
                "rows_per_page": 20,
                "total": 13,
            },
        )
    )
    expected = {
        "name": "F38",
        "long_name": "Fedora 38",
        "version": "38",
        "id_prefix": "FEDORA",
        "eol": "2024-05-14",
    }
    current_release = await client.get_current_release()
    assert current_release == expected


async def test_error_404(respx_mock):
    client = BodhiClient("http://bodhi.example.com")
    respx_mock.get("http://bodhi.example.com").mock(
        return_value=httpx.Response(
            404,
            json={
                "status": "error",
                "errors": [{"location": "body", "name": "name", "description": "No such release"}],
            },
        )
    )
    with pytest.raises(InfoGatherError, match="Issue querying Bodhi: No such release"):
        await client.get_current_release()


async def test_error_other(respx_mock):
    client = BodhiClient("http://bodhi.example.com")
    respx_mock.get("http://bodhi.example.com").mock(
        return_value=httpx.Response(
            403,
        )
    )
    with pytest.raises(InfoGatherError, match="Issue querying Bodhi: 403: Forbidden"):
        await client.get_current_release()
