from maubot import MessageEvent
from maubot.handlers import command

from .clients.pagure import PagureClient
from .exceptions import InfoGatherError


class PagureIOHandler:
    def __init__(self, config):
        self.config = config
        self.pagureioclient = PagureClient(self.config["pagureio_url"])

    async def _get_pagure_issue(self, evt: MessageEvent, project: str, issue_id: str) -> None:
        try:
            issue = await self.pagureioclient.get_issue(project, issue_id)
        except InfoGatherError as e:
            await evt.respond(e.message)
            return
        title = issue.get("title")
        full_url = issue.get("full_url")
        await evt.respond(f"[{project} #{issue_id}]({full_url}): {title}")

    @command.new(help="return a pagure issue")
    @command.argument("project", required=True)
    @command.argument("issue_id", required=True)
    async def pagureissue(self, evt: MessageEvent, project: str, issue_id: str) -> None:
        """
        Show a summary of a Pagure issue

        #### Arguments ####

        * `project`: a project in pagure.io
        * `issue_id`: the issue number

        """
        await self._get_pagure_issue(evt, project, issue_id)

    # these were done in supybot / limnoria with the alias plugin. need to find a better way to
    # do this so they can be defined, but for now, lets just define the commands here.
    @command.new(help="Get a Summary of a ticket from the packaging-committee ticket tracker")
    @command.argument("issue_id", required=True)
    async def fpc(self, evt: MessageEvent, issue_id: str) -> None:
        """
        Show a summary of an issue in the `packaging-committee` pagure.io project

        #### Arguments ####

        * `issue_id`: the issue number

        """
        await self._get_pagure_issue(evt, "packaging-committee", issue_id)

    # these were done in supybot / limnoria with the alias plugin. need to find a better way to
    # do this so they can be defined, but for now, lets just define the commands here.
    @command.new(help="Get a Summary of a ticket from the epel ticket tracker")
    @command.argument("issue_id", required=True)
    async def epel(self, evt: MessageEvent, issue_id: str) -> None:
        """
        Show a summary of an issue in the `epel` pagure.io project

        #### Arguments ####

        * `issue_id`: the issue number

        """
        await self._get_pagure_issue(evt, "epel", issue_id)

    # these were done in supybot / limnoria with the alias plugin. need to find a better way to
    # do this so they can be defined, but for now, lets just define the commands here.
    @command.new(help="Get a Summary of a ticket from the fesco ticket tracker")
    @command.argument("issue_id", required=True)
    async def fesco(self, evt: MessageEvent, issue_id: str) -> None:
        """
        Show a summary of an issue in the `fesco` pagure.io project

        #### Arguments ####

        * `issue_id`: the issue number

        """
        await self._get_pagure_issue(evt, "fesco", issue_id)
