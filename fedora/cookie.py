import logging
import re

from maubot import MessageEvent
from maubot.handlers import command, event
from maubot_fedora_messages import GiveCookieV1
from mautrix.types import EventType
from urllib.parse import unquote

from .clients.bodhi import BodhiClient
from .constants import NL
from .db import UNIQUE_ERROR
from .exceptions import InfoGatherError, InvalidInput
from .fedmsg import publish
from .handler import Handler
from .utils import get_fasuser, get_fasuser_from_matrix_id, is_text_message

log = logging.getLogger(__name__)


COOKIE_TEXT_RE = re.compile(r"^([\w_.-]+)\+\+")
COOKIE_HTML_RE = re.compile(
    r"^<a href=['\"]?http[s]?://matrix.to/#/([^'\" >]+)['\" >][^>]*>[^<]+</a>:?\s?\+\+"
)
COOKIE_EMOJI = "🍪"


class CookieHandler(Handler):
    def __init__(self, plugin):
        super().__init__(plugin)
        self.bodhi = BodhiClient(plugin.config["bodhi_url"])

    # The event.on() decorator is not correctly typed and doesn't understand
    # this is a bound method.
    @event.on(EventType.ROOM_MESSAGE)  # type: ignore[arg-type]
    async def handle(self, evt: MessageEvent) -> None:
        if not is_text_message(evt.content):
            return
        if evt.sender == evt.client.mxid:
            # The bot sent this message
            return
        username = self._get_username(evt)
        if not username:
            return
        await evt.mark_read()
        try:
            to_user = await get_fasuser(username, evt, self.plugin.fasjsonclient)
            response = await self.give(evt.sender, to_user["username"])
        except (InfoGatherError, InvalidInput) as e:
            response = e.message
        await evt.respond(response)

    @event.on(EventType.REACTION)  # type: ignore[arg-type]
    async def handle_emoji(self, evt: MessageEvent) -> None:
        reaction = evt.content.relates_to
        emoji = reaction.key
        if emoji != COOKIE_EMOJI:
            return
        message_event = await self.plugin.client.get_event(evt.room_id, reaction.event_id)
        try:
            to_user = await get_fasuser_from_matrix_id(
                message_event.sender, self.plugin.fasjsonclient
            )
            response = await self.give(evt.sender, to_user["username"])
        except (InfoGatherError, InvalidInput) as e:
            response = e.message
        await self.plugin.client.send_notice(evt.room_id, text=response)

    def _get_username(self, evt: MessageEvent) -> str | None:
        if not is_text_message(evt.content) or evt.content.formatted_body is None:
            # No tags, use the text
            regex = COOKIE_TEXT_RE
            content = evt.content.body
        else:
            # User may have been tagged
            regex = COOKIE_HTML_RE
            content = evt.content.formatted_body
        match = regex.match(content)
        if not match:
            return None
        return match.group(1)

    async def _get_cookie_totals(self, username):
        dbq = "SELECT SUM(value) FROM cookies WHERE to_user = $1"
        total = await self.plugin.database.fetchval(dbq, username)
        by_release = {}

        dbq = (
            "SELECT release, SUM(value) AS count "
            "FROM cookies "
            "WHERE to_user = $1 "
            "GROUP BY release "
            "ORDER BY release"
        )
        release_totals = await self.plugin.database.fetch(dbq, username)
        for row in release_totals:
            by_release[row["release"]] = row["count"]

        return total, by_release

    async def give(self, sender: str, to_user: str) -> str:
        sender = unquote(sender)
        from_user = await get_fasuser_from_matrix_id(sender, self.plugin.fasjsonclient)
        from_user = from_user["username"]
        if from_user == to_user:
            raise InvalidInput("You can't give a cookie to yourself")
        current_release = await self.bodhi.get_current_release()
        current_release = str(current_release["version"])
        dbq = """
            INSERT INTO cookies (from_user, to_user, release)
            VALUES ($1, $2, $3)
        """
        try:
            await self.plugin.database.execute(
                dbq,
                from_user,
                to_user,
                current_release,
            )
        except UNIQUE_ERROR:
            return (
                f"{from_user} has already given cookies to {to_user} during the "
                f"F{current_release} timeframe"
            )
        total, by_release = await self._get_cookie_totals(to_user)
        fm = GiveCookieV1(
            body={
                "sender": from_user,
                "recipient": to_user,
                "total": total,
                "fedora_release": current_release,
                "count_by_release": by_release,
            }
        )
        await publish(fm)
        return (
            f"{from_user} gave a cookie to {to_user}. They now "
            f"have {total} cookie{'' if total==1 else 's'}, {by_release[current_release]} "
            f"of which {'was' if total==1 else 'were'} obtained "
            f"in the Fedora {current_release} release cycle"
        )

    @command.new(help="Commands for the cookie system")
    async def cookie(self, evt: MessageEvent) -> None:
        pass

    @cookie.subcommand(name="give", help="Give a cookie to another Fedora contributor")
    @command.argument("username", required=True)
    async def cookie_give(self, evt: MessageEvent, username: str) -> None:
        if not username:
            await evt.respond("username argument is required. e.g. `!cookie give mattdm`")
            return
        try:
            to_user = await get_fasuser(username, evt, self.plugin.fasjsonclient)
            response = await self.give(evt.sender, to_user["username"])
        except (InfoGatherError, InvalidInput) as e:
            response = e.message
        await evt.respond(response)

    @cookie.subcommand(name="count", help="Return the cookie count for a user")
    @command.argument("username", required=True)
    async def cookie_count(self, evt: MessageEvent, username: str) -> None:
        try:
            user = await get_fasuser(username or evt.sender, evt, self.plugin.fasjsonclient)
        except InfoGatherError as e:
            await evt.respond(e.message)
            return

        total, by_release = await self._get_cookie_totals(user["username"])

        if not total:
            await evt.respond(f"{user['username']} has no cookies")
            return

        message = f"{user['username']} has {total} cookies:{NL}"

        for release, count in by_release.items():
            message = message + f" * Fedora {release}: {count} cookies{NL}"

        await evt.respond(message)
