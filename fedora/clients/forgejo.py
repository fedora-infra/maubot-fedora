import httpx

from ..exceptions import InfoGatherError


class ForgejoClient:
    def __init__(self, baseurl):
        self.baseurl = f"{baseurl}/api/v1/repos/"

    async def _get(self, endpoint, **kwargs):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.baseurl + endpoint, **kwargs)
        return response

    def _check_errors(self, response):
        if response.status_code == 404:
            raise InfoGatherError(f"Issue querying Forgejo: {response.json().get('error')}")
        elif response.status_code != 200:
            raise InfoGatherError(
                f"Issue querying Forgejo: {response.status_code}: {response.reason_phrase}"
            )

    async def get_issue(self, repo, issue_id, org, params=None):
        response = await self._get(
            "/".join(filter(None, [org, repo, "issues", issue_id])),
            params=params,
        )
        self._check_errors(response)
        return response.json()

    async def get_pull_request(self, repo, pull_id, org, params=None):
        response = await self._get(
            "/".join(filter(None, [org, repo, "pulls", pull_id])),
            params=params,
        )
        self._check_errors(response)
        return response.json()
