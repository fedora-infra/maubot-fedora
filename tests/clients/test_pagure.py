from unittest import mock

import httpx
import pytest

from fedora.clients.pagure import PagureClient
from fedora.exceptions import InfoGatherError


@pytest.mark.parametrize(
    "project,issue_id,namespace,params,expected_url",
    [
        ("biscuits", "1234", None, None, "biscuits/issue/1234"),
        ("biscuits", "1234", "tin_of", None, "tin_of/biscuits/issue/1234"),
        ("biscuits", "1234", "tin_of", {"fakeparam": True}, "tin_of/biscuits/issue/1234"),
        ("biscuits", "1234", None, {"fakeparam": True}, "biscuits/issue/1234"),
    ],
)
async def test_get_issue(monkeypatch, project, issue_id, namespace, params, expected_url):
    issue = {
        "title": "Dummy Issue",
        "full_url": f"http://pagure.example.com/{expected_url}",
    }
    client = PagureClient("http://pagure.example.com")
    mock__get = mock.AsyncMock(
        return_value=httpx.Response(
            200,
            json=issue,
        )
    )
    monkeypatch.setattr(client, "_get", mock__get)

    issue_response = await client.get_issue(project, issue_id, namespace=namespace, params=params)
    mock__get.assert_called_once_with(expected_url, params=params)
    assert issue_response == issue


@pytest.mark.parametrize(
    "errorcode,expected_result",
    [
        (404, "Issue querying Pagure: Issue not found"),
        (403, "Issue querying Pagure: 403: Forbidden"),
    ],
)
async def test_errors(respx_mock, errorcode, expected_result):
    client = PagureClient("http://pagure.example.com")
    respx_mock.get("http://pagure.example.com").mock(
        return_value=httpx.Response(
            errorcode,
            json={"error": "Issue not found", "error_code": "ENOISSUE"},
        )
    )
    with pytest.raises(InfoGatherError, match=(expected_result)):
        await client.get_issue("project_biscuits", "1234")
