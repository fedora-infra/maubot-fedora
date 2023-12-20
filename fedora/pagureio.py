import arrow
from maubot import MessageEvent
from maubot.handlers import command

from .clients.pagure import PagureClient
from .constants import COMMAND_RE, NL
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
        status = issue.get("status")
        close_status = issue.get("close_status")
        closed_at = issue.get("closed_at")
        closed_by = issue.get("closed_by").get("name") if issue.get("closed_by") else None
        assignee = issue["assignee"].get("name") if issue.get("assignee") else None
        last_updated = issue.get("last_updated")
        date_created = issue.get("date_created")
        user = issue["user"].get("name") if issue.get("user") else None

        response_text = f"[**{project} #{issue_id}**]({full_url}):**{title}**{NL}"
        if close_status:
            response_text = response_text + (
                f"* **{status}: {close_status}** "
                f"{arrow.get(int(closed_at)).humanize()} by {closed_by}{NL}"
            )
        response_text = (
            response_text + f"* **Opened:** {arrow.get(int(date_created)).humanize()} by {user}{NL}"
        )

        if last_updated == date_created:
            last_updated = "Never"
        else:
            last_updated = arrow.get(int(last_updated)).humanize()
        response_text = response_text + f"* **Last Updated:** {last_updated}{NL}"

        if not assignee:
            assignee = "Not Assigned"
        response_text = response_text + f"* **Assignee:** {assignee}{NL}"

        await evt.respond(
            response_text,
            allow_html=True,
        )

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

    @command.passive(COMMAND_RE)
    async def aliases(self, evt: MessageEvent, match) -> None:
        msg, cmd, arguments = match
        defined_aliases = self.plugin.config.get("pagureio_issue_aliases", {})
        if cmd in defined_aliases:
            await self._get_pagure_issue(evt, defined_aliases[cmd], arguments)
