from typing import Literal

import httpx

from ..exceptions import InfoGatherError


class FedoraStatusClient:
    def __init__(self, baseurl):
        self.baseurl = baseurl

    async def _get(self, endpoint, **kwargs) -> httpx.Response:
        kwargs.setdefault("headers", {})["Content-Type"] = "application/json"
        async with httpx.AsyncClient() as client:
            response = await client.get(self.baseurl + endpoint, **kwargs)
        return response

    def _check_errors(self, response):
        if response.status_code != 200:
            raise InfoGatherError(
                f"Issue querying Fedora Status: {response.status_code}: {response.reason_phrase}"
            )

    async def get_outages(self, outagetype: Literal["ongoing", "planned", "resolved"]):
        outages = await self._get(
            f"/{outagetype}.json",
        )
        self._check_errors(outages)

        return outages.json()
