import logging
import re
from datetime import datetime

from maubot import MessageEvent
from maubot.handlers import event
from mautrix.types import EventType, MessageType

from .clients.bodhi import BodhiClient
from .db import UNIQUE_ERROR
from .exceptions import InfoGatherError
from .handler import Handler
from .utils import get_fasuser

log = logging.getLogger(__name__)


COOKIE_TEXT_RE = re.compile(r"^([\w_.-]+)\+\+")
COOKIE_HTML_RE = re.compile(
    r"^<a href=['\"]?http[s]?://matrix.to/#/([^'\" >]+)['\" >][^>]*>[^<]+</a>:?\s?\+\+"
)


class CookieHandler(Handler):
    def __init__(self, plugin):
        super().__init__(plugin)
        self.bodhi = BodhiClient(plugin.config["bodhi_url"])

    @event.on(EventType.ROOM_MESSAGE)
    async def handle(self, evt: MessageEvent) -> None:
        if evt.content.msgtype not in [MessageType.TEXT, MessageType.NOTICE]:
            return
        if evt.sender == evt.client.mxid:
            # The bot sent this message
            return
        username = self._get_username(evt)
        if not username:
            return
        await evt.mark_read()
        try:
            await self.give(evt, username)
        except InfoGatherError as e:
            await evt.respond(e.message)

    def _get_username(self, evt: MessageEvent) -> str | None:
        if evt.content.formatted_body is None:
            # No tags, use the text
            regex = COOKIE_TEXT_RE
            content = evt.content.body
        else:
            # User may have been tagged
            regex = COOKIE_HTML_RE
            content = evt.content.formatted_body
        match = regex.match(content)
        if not match:
            return
        return match.group(1)

    async def give(self, evt: MessageEvent, username: str) -> None:
        from_user = await get_fasuser(evt.sender, evt, self.plugin.fasjsonclient)
        if from_user is None:
            raise InfoGatherError("Could not find your user in the Fedora Account system.")
        to_user = await get_fasuser(username, evt, self.plugin.fasjsonclient)
        if to_user is None:
            raise InfoGatherError(f"Could not find user {username} in the Fedora Account system.")
        current_release = await self.bodhi.get_current_release()
        current_release = str(current_release["version"])
        dbq = """
            INSERT INTO cookies (from_user, to_user, release, date)
            VALUES ($1, $2, $3, $4)
        """
        try:
            await self.plugin.database.execute(
                dbq,
                from_user["username"],
                to_user["username"],
                current_release,
                datetime.fromtimestamp(evt.timestamp / 1000),
            )
        except UNIQUE_ERROR:
            await evt.respond(
                f"You have already given cookies to {to_user['username']} during the "
                f"F{current_release} timeframe"
            )
            return
        dbq = "SELECT SUM(value) FROM cookies WHERE to_user = $1 AND release = $2"
        total = await self.plugin.database.fetchval(dbq, to_user["username"], current_release)
        await evt.respond(f"{to_user['username']} has {total} cookie(s)")
