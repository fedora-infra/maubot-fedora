from unittest import mock

import httpx
import pytest

from fedora.clients.forgejo import ForgejoClient
from fedora.exceptions import InfoGatherError


@pytest.mark.parametrize(
    "namespace,project,issue_id,params,expected_url",
    [
        ("tin_of", "biscuits", "1234", None, "tin_of/biscuits/issues/1234"),
        ("tin_of", "biscuits", "1234", {"fakeparam": True}, "tin_of/biscuits/issues/1234"),
    ],
)
async def test_get_issue(monkeypatch, namespace, project, issue_id, params, expected_url):
    issue = {
        "title": "Dummy Issue",
        "html_url": f"http://forge.example.com/{expected_url}",
    }
    client = ForgejoClient("http://forge.example.com")
    mock__get = mock.AsyncMock(
        return_value=httpx.Response(
            200,
            json=issue,
        )
    )
    monkeypatch.setattr(client, "_get", mock__get)

    issue_response = await client.get_issue(project, issue_id, namespace, params=params)
    mock__get.assert_called_once_with(expected_url, params=params)
    assert issue_response == issue


@pytest.mark.parametrize(
    "errorcode,expected_result",
    [
        (404, "Issue querying Forgejo: Issue not found"),
        (403, "Issue querying Forgejo: 403: Forbidden"),
    ],
)
async def test_errors(respx_mock, errorcode, expected_result):
    client = ForgejoClient("http://forge.example.com")
    respx_mock.get("http://forge.example.com").mock(
        return_value=httpx.Response(
            errorcode,
            json={"error": "Issue not found", "error_code": "ENOISSUE"},
        )
    )
    with pytest.raises(InfoGatherError, match=(expected_result)):
        await client.get_issue("project_biscuits", "1234", "namespace_tin_can")
