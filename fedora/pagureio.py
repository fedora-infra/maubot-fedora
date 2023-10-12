from maubot import MessageEvent
from maubot.handlers import command

from .clients.pagure import PagureClient
from .exceptions import InfoGatherError
from .handler import Handler


class PagureIOHandler(Handler):
    def __init__(self, plugin):
        super().__init__(plugin)
        self.pagureioclient = PagureClient(self.plugin.config["pagureio_url"])

    async def _get_pagure_issue(self, evt: MessageEvent, project: str, issue_id: str) -> None:
        await evt.mark_read()
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

    @command.passive(r"^!(\S+)(?:\s+|$)(.*)")
    async def aliases(self, evt: MessageEvent, match) -> None:
        msg, cmd, arguments = match
        defined_aliases = self.plugin.config.get("pagureio_issue_aliases", {})
        if cmd in defined_aliases:
            await self._get_pagure_issue(evt, defined_aliases[cmd], arguments)
