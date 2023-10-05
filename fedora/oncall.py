import logging
from datetime import datetime
from sqlite3 import IntegrityError

import pytz
from asyncpg.exceptions import UniqueViolationError
from maubot import MessageEvent
from maubot.handlers import command

from .constants import NL
from .exceptions import InfoGatherError
from .handler import Handler
from .utils import get_fasuser, get_rowcount

log = logging.getLogger(__name__)


class OnCallHandler(Handler):
    def _format_mxid(self, mxid, name=None):
        return f'<a href="https://matrix.to/#/{mxid}">{name if name else mxid}</a>'

    def _mxids_from_ircnicks(self, ircnicks):
        mxids = []
        for nick in ircnicks:
            if nick.startswith("matrix://"):
                # should be "matrix://matrix.org/username"
                m = nick.replace("matrix://", "").split("/")
                # m should be ['matrix.org', "username"]
                mxids.append(f"@{m[1]}:{m[0]}")
            elif nick.startswith("matrix:/"):
                mxids.append(f"{nick.replace('matrix:/', '@')}:fedora.im")
        return mxids

    @command.new(help="oncall", require_subcommand=False)
    async def oncall(self, evt: MessageEvent) -> None:
        dbq = """
                SELECT * FROM oncall
            """
        oncall_sysadmins = await self.plugin.database.fetch(dbq)
        if oncall_sysadmins:
            output = f"The following people are oncall:{NL}"
            for sysadmin in oncall_sysadmins:
                timezone = sysadmin.get("timezone", "UTC")
                currenttime = datetime.now(pytz.timezone(timezone)).strftime("%H:%M")
                output = output + (
                    f"* { self._format_mxid(sysadmin.get('mxid'))} "
                    f"({sysadmin.get('username')}) Current Time for them: "
                    f"{currenttime} ({timezone}){NL}"
                )
            output = output + (
                "\nIf they do not respond, please "
                "[file a ticket](https://pagure.io/fedora-infrastructure/issues)"
            )
            await evt.respond(output, allow_html=True)
        else:
            await evt.respond("No one from Fedora Infrastructure is currently on call")

    @oncall.subcommand(name="add", help="Add a user to the current oncall list")
    @command.argument("username", pass_raw=True, required=True)
    async def oncall_add(self, evt: MessageEvent, username: str) -> None:
        if evt.room_id != self.plugin.config["controlroom"]:
            await evt.reply(
                "Sorry, adding to the oncall list can only be done from the controlroom"
            )
            return
        try:
            user = await get_fasuser(username, evt, self.plugin.fasjsonclient)
        except InfoGatherError as e:
            await evt.respond(e.message)
            return

        dbq = """
                INSERT INTO oncall (username, mxid, timezone) VALUES ($1, $2, $3)
            """
        fasusername = user.get("username")
        mxids = self._mxids_from_ircnicks(user.get("ircnicks", []))
        if len(mxids) == 0:
            # user hasn't defined a Matrix account in FAS, just default to fedora.im
            mxid = f"@{fasusername}:fedora.im"
        else:
            # Just grab the first mxid in the users list on fas
            mxid = mxids[0]
        try:
            await self.plugin.database.execute(dbq, fasusername, mxid, user.get("timezone", "UTC"))
        except (UniqueViolationError, IntegrityError):
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
        try:
            user = await get_fasuser(username, evt, self.plugin.fasjsonclient)
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
