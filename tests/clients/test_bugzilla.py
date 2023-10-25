import httpx
import pytest

from fedora.clients.bugzilla import BugzillaClient
from fedora.exceptions import InfoGatherError


async def test_get_bug(respx_mock):
    client = BugzillaClient("http://bugzilla.example.com")
    bugs = {"bugs": [{"id": "", "summary": "Dummy Issue"}]}
    respx_mock.get("http://bugzilla.example.com").mock(
        return_value=httpx.Response(
            200,
            json=bugs,
        )
    )
    current_release = await client.get_bug("1234")
    assert current_release == bugs


async def test_error_404(respx_mock):
    client = BugzillaClient("http://bugzilla.example.com")
    respx_mock.get("http://bugzilla.example.com").mock(
        return_value=httpx.Response(
            404,
            json={
                "code": 100,
                "documentation": "http://bugzilla.example.com",
                "error": True,
                "message": "'biscuits' is not a valid bug number nor an alias to a bug.",
            },
        )
    )
    with pytest.raises(
        InfoGatherError,
        match=(
            "Issue querying Bugzilla: 'biscuits' is not a valid bug number nor an alias to a bug."
        ),
    ):
        await client.get_bug("biscuits")


async def test_error_other(respx_mock):
    client = BugzillaClient("http://bugzilla.example.com")
    respx_mock.get("http://bugzilla.example.com").mock(
        return_value=httpx.Response(
            403,
        )
    )
    with pytest.raises(InfoGatherError, match="Issue querying Bugzilla: 403: Forbidden"):
        await client.get_bug("1234")
