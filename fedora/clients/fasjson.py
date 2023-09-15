import httpx
from httpx_gssapi import HTTPSPNEGOAuth

from ..exceptions import InfoGatherError


class FasjsonClient:
    def __init__(self, baseurl):
        self.baseurl = f'{baseurl}/v1/'

    async def _get(self, endpoint, **kwargs):
        kwargs['follow_redirects'] = True
        kwargs['auth'] = HTTPSPNEGOAuth()
        async with httpx.AsyncClient() as client:
            response = await client.get(self.baseurl+endpoint, **kwargs)
        return response

    async def get_group_membership(self, groupname, membership_type="members", params=None):
        """looks up a group membership (members or sponsors) by the groupname"""
        response = await self._get("/".join(['groups', groupname, membership_type]), params=params, headers={'X-Fields': 'username'})
        if response.status_code == 404:
            raise InfoGatherError(f"Sorry, but group '{groupname}' does not exist")
        return response.json().get('result')

    async def get_group(self, groupname, params=None):
        """looks up a group by the groupname"""
        response = await self._get("/".join(['groups', groupname]), params=params)
        if response.status_code == 404:
            raise InfoGatherError(f"Sorry, but group '{groupname}' does not exist")
        return response.json().get('result')
    
    async def get_user(self, username, params=None):
        """looks up a group by the groupname"""
        response = await self._get( "/".join(['users', username]),params=params)
        if response.status_code == 404:
            raise InfoGatherError(f"Sorry, but Fedora Accounts user '{username}' does not exist")
        return response.json().get('result')

    async def search_users(self, params=None):
        """looks up a group by the groupname"""
        response = await self._get( "/".join(['search', 'users']), params=params)
        return response.json().get('result')
