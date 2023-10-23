import logging

from maubot import MessageEvent
from maubot.handlers import command

from .clients.fedorastatus import FedoraStatusClient
from .constants import NL
from .handler import Handler

log = logging.getLogger(__name__)


class InfraHandler(Handler):
    def __init__(self, plugin):
        super().__init__(plugin)
        self.fedorastatus_url = plugin.config["fedorastatus_url"]
        self.fedorastatus = FedoraStatusClient(self.fedorastatus_url)

    @command.new(help="Fedora Infrastructure commands")
    async def infra(self, evt: MessageEvent) -> None:
        pass

    @infra.subcommand(name="status", help="get a list of the ongoing and planned outages")
    async def infra_status(self, evt: MessageEvent) -> None:
        def format_title(outage):
            if outage.get("ticket"):
                return f"**[{outage.get('title')}]({outage.get('ticket')['url']})**"
            else:
                return f"**{outage.get('title')}**"

        ongoing = await self.fedorastatus.get_outages("ongoing")
        ongoing = ongoing.get("outages", [])

        planned = await self.fedorastatus.get_outages("planned")
        planned = planned.get("outages", [])

        message = f"I checked [Fedora Status]({self.fedorastatus_url}) and there are "
        if not ongoing and not planned:
            message = message + f"**no planned or ongoing outages on Fedora Infrastructure.**{NL}"
        else:
            message = message + (
                f"**{len(ongoing)} ongoing** and **{len(planned)} planned** "
                f"outages on Fedora Infrastructure.{NL}"
            )
            if ongoing:
                message = message + f"##### Ongoing{NL}"
                for outage in ongoing:
                    message = message + f" * {format_title(outage)}{NL}"
                    # TODO: Make these times relative (e.g. started 1 hour ago)
                    message = message + f"   Started at: {outage['startdate']}{NL}"
                    message = message + (
                        f"   Estimated to end: "
                        f"{outage['enddate'] if outage['enddate'] else 'Unknown'}{NL}"
                    )
            if planned:
                message = message + f"##### Planned{NL}"
                for outage in planned:
                    message = message + f" * {format_title(outage)}{NL}"
                    # TODO: Make these times relative (e.g. started 1 hour ago)
                    message = message + f"   Scheduled to start at: {outage['startdate']}{NL}"
                    message = message + (
                        f"   Scheduled to end at: "
                        f"{outage['enddate'] if outage['enddate'] else 'Unknown'}{NL}"
                    )

        await evt.respond(message)
