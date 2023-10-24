import datetime
import logging

import pytz
from maubot import MessageEvent
from maubot.handlers import command

from .clients.fedorastatus import FedoraStatusClient
from .constants import COMMAND_RE, NL
from .db import UNIQUE_ERROR
from .exceptions import InfoGatherError
from .handler import Handler
from .utils import get_fasuser, get_rowcount, matrix_ids_from_ircnicks

log = logging.getLogger(__name__)


class InfraHandler(Handler):
    def __init__(self, plugin):
        super().__init__(plugin)
        self.fedorastatus_url = plugin.config["fedorastatus_url"]
        self.fedorastatus = FedoraStatusClient(self.fedorastatus_url)

    async def _get_oncall(self, evt: MessageEvent) -> None:
        await evt.mark_read()
        dbq = """
                SELECT * FROM oncall
            """
        oncall_sysadmins = await self.plugin.database.fetch(dbq)
        if oncall_sysadmins:
            output = f"The following people are oncall:{NL}"
            for sysadmin in oncall_sysadmins:
                timezone = sysadmin["timezone"]
                currenttime = datetime.datetime.now(pytz.timezone(timezone)).strftime("%H:%M")
                output = output + (
                    f"* { self._format_mxid(sysadmin['mxid'])} "
                    f"({sysadmin['username']}) Current Time for them: "
                    f"{currenttime} ({timezone}){NL}"
                )
            output = output + (
                "\nIf they do not respond, please "
                "[file a ticket](https://pagure.io/fedora-infrastructure/issues)"
            )
            await evt.respond(output, allow_html=True)
        else:
            await evt.respond("No one from Fedora Infrastructure is currently on call")

    def _format_mxid(self, mxid, name=None):
        return f'<a href="https://matrix.to/#/{mxid}">{name if name else mxid}</a>'

    @command.passive(COMMAND_RE)
    async def alias_oncall(self, evt: MessageEvent, match) -> None:
        msg, cmd, arguments = match
        if cmd != "oncall":
            return
        if arguments:
            await evt.respond(
                "`!oncall` is an alias to `!infra oncall list` please use "
                "the `!infra oncall` command for changing the oncall list"
            )
            return

        await self._get_oncall(evt)

    @command.new(help="Fedora Infrastructure commands")
    async def infra(self, evt: MessageEvent) -> None:
        pass

    @infra.subcommand(help="oncall")
    async def oncall(self, evt: MessageEvent) -> None:
        pass

    @oncall.subcommand(name="list", help="List the Fedora Infrastructure members currently on call")
    async def oncall_list(self, evt: MessageEvent) -> None:
        await self._get_oncall(evt)

    @oncall.subcommand(name="add", help="Add a user to the current oncall list")
    @command.argument("username", pass_raw=True, required=True)
    async def oncall_add(self, evt: MessageEvent, username: str) -> None:
        if evt.room_id != self.plugin.config["controlroom"]:
            await evt.reply(
                "Sorry, adding to the oncall list can only be done from the controlroom"
            )
            return
        await evt.mark_read()
        try:
            user = await get_fasuser(username or evt.sender, evt, self.plugin.fasjsonclient)
        except InfoGatherError as e:
            await evt.respond(e.message)
            return

        dbq = """
                INSERT INTO oncall (username, mxid, timezone) VALUES ($1, $2, $3)
            """
        fasusername = user.get("username")
        mxids = matrix_ids_from_ircnicks(user.get("ircnicks", []))
        if len(mxids) == 0:
            # user hasn't defined a Matrix account in FAS, just default to fedora.im
            mxid = f"@{fasusername}:fedora.im"
        else:
            # Just grab the first mxid in the users list on fas
            mxid = mxids[0]
        try:
            await self.plugin.database.execute(dbq, fasusername, mxid, user.get("timezone", "UTC"))
        except UNIQUE_ERROR:
            await evt.respond(f"{fasusername} is already on the oncall list")
            return
        await evt.respond(f"{fasusername} has been added to the oncall list")

    @oncall.subcommand(name="remove", help="Remove a user to the current oncall list")
    @command.argument("username", pass_raw=True, required=True)
    async def oncall_remove(self, evt: MessageEvent, username: str) -> None:
        if evt.room_id != self.plugin.config["controlroom"]:
            await evt.reply(
                "Sorry, removing from the oncall list can only be done from the controlroom"
            )
            return
        await evt.mark_read()
        try:
            user = await get_fasuser(username or evt.sender, evt, self.plugin.fasjsonclient)
        except InfoGatherError as e:
            await evt.respond(e.message)
            return

        dbq = """
                DELETE FROM oncall WHERE username = $1
              """
        result = await self.plugin.database.execute(dbq, user["username"])
        rowcount = get_rowcount(self.plugin.database, result)
        if rowcount == 0:
            await evt.reply(f"{user['username']} is not currently on the oncall list")
        elif rowcount == 1:
            await evt.reply(f"{user['username']} has been removed from the oncall list")
        else:
            await evt.reply(f"Unexpected response trying to remove user: {result}")

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
