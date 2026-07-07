from datetime import datetime

import arrow
from maubot import MessageEvent
from maubot.handlers import command

from .clients.forgejo import ForgejoClient
from .constants import COMMAND_RE, NL
from .exceptions import InfoGatherError
from .handler import Handler


class ForgeHandler(Handler):
    def __init__(self, plugin):
        super().__init__(plugin)
        self.forgejoclient = ForgejoClient(self.plugin.config["forge_url"])

    async def _get_forge_issue(self, evt: MessageEvent, org: str, repo: str, issue_id: str) -> None:
        await evt.mark_read()
        try:
            issue = await self.forgejoclient.get_issue(repo, issue_id, org)
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

        response_text = f"[**{org}/{repo} #{issue_id}**]({html_url}):**{title}**{NL}"
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

    async def _get_forge_pull_request(
        self, evt: MessageEvent, org: str, repo: str, pull_id: str
    ) -> None:
        await evt.mark_read()
        try:
            pull_request = await self.forgejoclient.get_pull_request(repo, pull_id, org)
        except InfoGatherError as e:
            await evt.respond(e.message)
            return

        title = pull_request.get("title")
        html_url = pull_request.get("html_url")
        state = pull_request.get("state")
        closed_at = pull_request.get("closed_at")
        merged = pull_request.get("merged")
        merged_at = pull_request.get("merged_at")
        merged_by = (
            pull_request["merged_by"].get("username") if pull_request.get("merged_by") else None
        )
        assignee = (
            pull_request["assignee"].get("username") if pull_request.get("assignee") else None
        )
        updated_at = pull_request.get("updated_at")
        created_at = pull_request.get("created_at")
        user = pull_request["user"].get("username") if pull_request.get("user") else None

        response_text = f"[**{org}/{repo} #{pull_id}**]({html_url}):**{title}**{NL}"
        if state == "closed":
            if merged:
                response_text = response_text + (
                    f"* **Merged**"
                    f" {arrow.get(datetime.fromisoformat(merged_at)).humanize()}"
                    f" by {merged_by}{NL}"
                )
            else:
                response_text = response_text + (
                    f"* **Closed**"
                    f" {arrow.get(datetime.fromisoformat(closed_at)).humanize()}{NL}"
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

    @command.new(help="Query information from Fedora Forge")
    async def forge(self):
        pass

    @forge.subcommand(help="return an issue from the forge")
    @command.argument("org", required=True)
    @command.argument("repo", required=True)
    @command.argument("issue_id", required=True)
    async def issue(self, evt: MessageEvent, org: str, repo: str, issue_id: str) -> None:
        """
        Show a summary of a Forge issue

        #### Arguments ####

        * `org`: an organization in the forge
        * `repo`: a repository in the organization
        * `issue_id`: the issue number

        """
        await self._get_forge_issue(evt, org, repo, issue_id)

    @forge.subcommand(name="pr", help="return a pull request from the forge")
    @command.argument("org", required=True)
    @command.argument("repo", required=True)
    @command.argument("pull_id", required=True)
    async def pull_request(self, evt: MessageEvent, org: str, repo: str, pull_id: str) -> None:
        """
        Show a summary of a Forge pull request

        #### Arguments ####

        * `org`: an organization in the forge
        * `repo`: a repository in the organization
        * `pull_id`: the pull request number

        """
        await self._get_forge_pull_request(evt, org, repo, pull_id)

    @command.passive(COMMAND_RE)
    async def aliases(self, evt: MessageEvent, match) -> None:
        _msg, cmd, arguments = match
        defined_aliases = self.plugin.config.get("forge_aliases", {})
        if (
            cmd in defined_aliases
            and isinstance(defined_aliases[cmd], list)
            and len(defined_aliases[cmd]) > 0
        ):
            if defined_aliases[cmd][0] == "issue":
                await self._get_forge_issue(
                    evt, defined_aliases[cmd][1], defined_aliases[cmd][2], arguments
                )
            elif defined_aliases[cmd][0] == "pr":
                await self._get_forge_pull_request(
                    evt, defined_aliases[cmd][1], defined_aliases[cmd][2], arguments
                )
