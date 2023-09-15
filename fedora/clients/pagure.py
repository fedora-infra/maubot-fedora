import httpx

from ..exceptions import InfoGatherError


class PagureClient:
    def __init__(self, baseurl):
        self.baseurl = f"{baseurl}/api/0/"

    async def _get(self, endpoint, **kwargs):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.baseurl + endpoint, **kwargs)
        return response

    def _check_errors(self, response):
        if response.status_code == 404:
            raise InfoGatherError(f"Issue querying Pagure: {response.json().get('error')}")
        elif response.status_code != 200:
            raise InfoGatherError(
                f"Issue querying Pagure: {response.status_code}: {response.reason_phrase}"
            )

    async def get_issue(self, project, issue_id, namespace=None, params=None):
        response = await self._get(
            "/".join(filter(None, [namespace, project, "issue", issue_id])),
            params=params,
        )
        self._check_errors(response)
        return response.json()

    async def get_project(self, project, namespace=None, params=None):
        response = await self._get(
            "/".join(filter(None, [namespace, project])),
            params=params,
        )
        self._check_errors(response)
        return response.json()
