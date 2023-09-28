import httpx

from ..exceptions import InfoGatherError


class BugzillaClient:
    def __init__(self, baseurl):
        self.baseurl = f"{baseurl}/rest/"

    async def _get(self, endpoint, **kwargs):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.baseurl + endpoint, **kwargs)
        return response

    def _check_errors(self, response):
        if response.status_code == 404:
            raise InfoGatherError(f"Issue querying Bugzilla: {response.json().get('error')}")
        elif response.status_code != 200:
            raise InfoGatherError(
                f"Issue querying Bugzilla: {response.status_code}: {response.reason_phrase}"
            )

    async def get_bug(self, bug_id):
        response = await self._get("/".join(["bug", bug_id]))
        self._check_errors(response)
        return response.json()
