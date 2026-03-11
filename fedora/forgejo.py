from datetime import datetime

import arrow
from maubot import MessageEvent
from maubot.handlers import command

from .clients.forgejo import ForgejoClient
from .constants import COMMAND_RE, NL
from .exceptions import InfoGatherError
from .handler import Handler


class ForgejoHandler(Handler):
    def __init__(self, plugin):
        super().__init__(plugin)
        self.forgejoclient = ForgejoClient(self.plugin.config["forgejo_url"])

    async def _get_forgejo_issue(
        self, evt: MessageEvent, namespace: str, project: str, issue_id: str
    ) -> None:
        await evt.mark_read()
        try:
            issue = await self.forgejoclient.get_issue(project, issue_id, namespace)
        except InfoGatherError as e:
            await evt.respond(e.message)
            return

        title = issue.get("title")
        html_url = issue.get("html_url")
        state = issue.get("state")
        closed_at = issue.get("closed_at")
        assignee = issue["assignee"].get("username") if issue.get("assignee") else None
        updated_at = issue.get("updated_at")
        created_at = issue.get("created_at")
        user = issue["user"].get("username") if issue.get("user") else None

        response_text = f"[**{namespace}/{project} #{issue_id}**]({html_url}):**{title}**{NL}"
        if state == "closed":
            response_text = response_text + (
                f"* **Closed** {arrow.get(datetime.fromisoformat(closed_at)).humanize()}{NL}"
            )
        response_text = (
            response_text
            + f"* **Opened:** {arrow.get(datetime.fromisoformat(created_at)).humanize()}"
            + f" by {user}{NL}"
        )

        if updated_at == created_at:
            updated_at = "Never"
        else:
            updated_at = arrow.get(datetime.fromisoformat(updated_at)).humanize()
        response_text = response_text + f"* **Last Updated:** {updated_at}{NL}"

        if not assignee:
            assignee = "Not Assigned"
        response_text = response_text + f"* **Assignee:** {assignee}{NL}"

        await evt.respond(
            response_text,
            allow_html=True,
        )

    @command.new(help="return a forgejo issue")
    @command.argument("namespace", required=True)
    @command.argument("project", required=True)
    @command.argument("issue_id", required=True)
    async def forgejoissue(
        self, evt: MessageEvent, namespace: str, project: str, issue_id: str
    ) -> None:
        """
        Show a summary of a Forgejo issue

        #### Arguments ####

        * `namespace`: a namespace in forgejo
        * `project`: a project in forgejo
        * `issue_id`: the issue number

        """
        await self._get_forgejo_issue(evt, namespace, project, issue_id)

    @command.passive(COMMAND_RE)
    async def aliases(self, evt: MessageEvent, match) -> None:
        _msg, cmd, arguments = match
        defined_aliases = self.plugin.config.get("forgejo_issue_aliases", {})
        if cmd in defined_aliases:
            await self._get_forgejo_issue(
                evt, defined_aliases[cmd]["namespace"], defined_aliases[cmd]["project"], arguments
            )
