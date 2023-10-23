import httpx

from ..exceptions import InfoGatherError


class BodhiClient:
    def __init__(self, baseurl):
        self.baseurl = baseurl

    async def _get(self, endpoint, **kwargs):
        kwargs.setdefault("headers", {})["Content-Type"] = "application/json"
        async with httpx.AsyncClient() as client:
            response = await client.get(self.baseurl + endpoint, **kwargs)
        return response

    def _check_errors(self, response):
        if response.status_code == 404:
            errors = response.json().get("errors")
            raise InfoGatherError(
                f"Issue querying Bodhi: {','.join([e.get('description') for e in errors])}"
            )
        elif response.status_code != 200:
            raise InfoGatherError(
                f"Issue querying Bodhi: {response.status_code}: {response.reason_phrase}"
            )

    async def get_current_release(self):
        response = await self._get(
            "/releases/",
            params={"state": "current"},
        )
        self._check_errors(response)
        fedora_releases = [r for r in response.json()["releases"] if r["id_prefix"] == "FEDORA"]
        fedora_releases.sort(key=lambda r: r["eol"])
        return fedora_releases[-1]
