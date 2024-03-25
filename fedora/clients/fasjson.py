import logging

import httpx
from httpx_gssapi import HTTPSPNEGOAuth

from ..constants import MATRIX_USER_RE, NL
from ..exceptions import InfoGatherError

log = logging.getLogger(__name__)


class NoResult(Exception):
    def __init__(self, response):
        self.response = response


class FasjsonClient:
    def __init__(self, baseurl):
        self.baseurl = f"{baseurl}/v1/"

    async def _get(self, endpoint, **kwargs):
        kwargs["follow_redirects"] = True
        kwargs["auth"] = HTTPSPNEGOAuth()
        async with httpx.AsyncClient() as client:
            response = await client.get(self.baseurl + endpoint + "/", **kwargs)
            if response.status_code == 404:
                raise NoResult(response)
            if response.status_code >= 400:
                log.error(f"FASJSON response to {response.url}: {response.text}")
                raise InfoGatherError(
                    f"Sorry, could not get info from FASJSON (code {response.status_code})"
                )
            pass
        return response

    async def get_group_membership(self, groupname, membership_type="members", params=None):
        """looks up a group membership (members or sponsors) by the groupname"""
        try:
            response = await self._get(
                "/".join(["groups", groupname, membership_type]),
                params=params,
                headers={"X-Fields": "username,human_name,ircnicks"},
            )
        except NoResult as e:
            raise InfoGatherError(f"Sorry, but group '{groupname}' does not exist") from e
        return response.json().get("result")

    async def get_group(self, groupname, params=None):
        """looks up a group by the groupname"""
        try:
            response = await self._get("/".join(["groups", groupname]), params=params)
        except NoResult as e:
            raise InfoGatherError(f"Sorry, but group '{groupname}' does not exist") from e
        return response.json().get("result")

    async def get_user(self, username, params=None):
        """looks up a group by the groupname"""
        try:
            response = await self._get("/".join(["users", username]), params=params)
        except NoResult as e:
            raise InfoGatherError(
                f"Sorry, but Fedora Accounts user '{username}' does not exist"
            ) from e
        return response.json().get("result")

    async def search_users(self, params=None):
        """looks up a group by the groupname"""
        response = await self._get("/".join(["search", "users"]), params=params)
        return response.json().get("result")

    async def get_users_by_matrix_id(self, matrix_id: str) -> dict | str:
        """looks up a user by the matrix id"""

        # Fedora Accounts stores these strangly but this is to handle that
        try:
            matrix_username, matrix_server = MATRIX_USER_RE.findall(matrix_id)[0]
        except (ValueError, IndexError) as e:
            raise InfoGatherError(
                f"Sorry, {matrix_id} does not look like a valid matrix user ID "
                "(e.g. @username:homeserver.com )"
            ) from e

        # if given a fedora.im address -- just look up the username as a FAS name
        if matrix_server == "fedora.im":
            user = await self.get_user(matrix_username)
            return user

        searchterm = f"matrix://{matrix_server}/{matrix_username}"
        searchresult = await self.search_users(params={"ircnick__exact": searchterm})

        if len(searchresult) > 1:
            names = f"{NL}".join([name["username"] for name in searchresult])
            raise InfoGatherError(
                f"{len(searchresult)} Fedora Accounts users have the {matrix_id} "
                f"Matrix Account defined:{NL}"
                f"{names}"
            )
        elif len(searchresult) == 0:
            raise InfoGatherError(
                f"No Fedora Accounts users have the {matrix_id} Matrix Account defined"
            )

        return searchresult[0]
    
    async def get_user_groups(self, username, params=None):
        """
        Retrieves all groups a user belongs to using the Fasjson API.

        Args:
            username (str): Username of the user to query.
            params (dict, optional): Additional query parameters to include in the request.

        Returns:
            List[str] or None:
                - A list of group names the user belongs to (if found).
                - None (if the user is not found or there's an error).

        Raises:
            InfoGatherError: If there's an error fetching data from Fasjson or if the user is not found (404).
        """

        try:
            response = await self._get("/".join(["users", username, "groups"]), params=params)
            return response.json().get("groups")

        except NoResult as e:
            raise InfoGatherError(f"Sorry, but Fedora Accounts user '{username}' does not exist") from e
        except InfoGatherError as e:
            raise
