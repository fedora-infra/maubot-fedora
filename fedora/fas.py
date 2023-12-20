import logging
from datetime import datetime

import pytz
from maubot import MessageEvent
from maubot.handlers import command

from .constants import NL
from .exceptions import InfoGatherError
from .handler import Handler
from .utils import get_fasuser, inline_reply, matrix_ids_from_ircnicks, tag_user

log = logging.getLogger(__name__)


class FasHandler(Handler):
    async def _get_mentions(self, users, evt: MessageEvent):
        room_members = set((await evt.client.get_joined_members(evt.room_id)).keys())
        mentions = []
        for user in sorted(users, key=lambda u: u["username"]):
            mxids = matrix_ids_from_ircnicks(user.get("ircnicks", []))
            if len(mxids) == 0:
                mention = user["username"]
            elif len(mxids) == 1:
                mention = tag_user(mxids[0], user.get("human_name", user["username"]))
            elif len(set(mxids).intersection(room_members)) == 1:
                mxid = next(iter(set(mxids).intersection(room_members)))
                mention = tag_user(mxid, user.get("human_name", user["username"]))
            else:
                mention = f"{user['username']} ({', '.join(tag_user(mxid) for mxid in mxids)})"
            mentions.append(mention)
        return mentions

    async def _list_members(self, evt: MessageEvent, groupname: str, membership_type: str) -> None:
        """
        Return a list of the members or sponsors of the Fedora Accounts group

        ## Arguments ##
        `groupname`: (required) The name of the Fedora Accounts group
        `membership_type`: (required) `members` or `sponsors`
        """
        if not groupname:
            await evt.respond("groupname argument is required. e.g. `!group members designteam`")
            return

        await evt.mark_read()

        try:
            users = await self.plugin.fasjsonclient.get_group_membership(
                groupname, membership_type=membership_type
            )
        except InfoGatherError as e:
            await evt.respond(e.message)
            return

        if len(users) > 200:
            await evt.respond(
                f"{groupname} has {len(users)} {membership_type} and thats too many to dump here"
            )
            return

        mentions = await self._get_mentions(users, evt)
        await evt.respond(f"{membership_type.title()} of {groupname}: {', '.join(mentions)}")

    @command.new(help="Query information about Fedora Accounts groups")
    async def group(self, evt: MessageEvent) -> None:
        """Query information about Fedora groups"""
        pass

    @group.subcommand(name="members", help="Return a list of members of the specified group")
    @command.argument("groupname", required=True)
    async def group_members(self, evt: MessageEvent, groupname: str) -> None:
        await self._list_members(evt, groupname, "members")

    @group.subcommand(name="sponsors", help="Return a list of owners of the specified group")
    @command.argument("groupname", required=True)
    async def group_sponsors(self, evt: MessageEvent, groupname: str) -> None:
        await self._list_members(evt, groupname, "sponsors")

    @group.subcommand(name="info", help="Return a list of owners of the specified group")
    @command.argument("groupname", required=True)
    async def group_info(self, evt: MessageEvent, groupname: str) -> None:
        if not groupname:
            await evt.respond("groupname argument is required. e.g. `!group info designteam`")
            return

        await evt.mark_read()
        try:
            group = await self.plugin.fasjsonclient.get_group(groupname)
        except InfoGatherError as e:
            await evt.respond(e.message)
            return

        chat_channels = f"`{'` and `'.join(c for c in group['irc'])}`" if "irc" in group else "None"
        await evt.respond(
            f"**Group Name:** {group.get('groupname')}{NL}"
            f"**Description:** {group.get('description')}{NL}"
            f"**URL:** {group.get('url')},{NL}"
            f"**Mailing List:** {group.get('mailing_list')}{NL}"
            f"**Chat:** {chat_channels}{NL}"
        )

    async def _user_hello(self, evt: MessageEvent, username: str | None) -> None:
        await evt.mark_read()
        try:
            user = await get_fasuser(username or evt.sender, evt, self.plugin.fasjsonclient)
        except InfoGatherError as e:
            await evt.respond(e.message)
            return
        if user is None:
            await evt.respond(f"Cound not find this Fedora Account: {username}")
            return

        message = f"{user['human_name']} ({user['username']})"
        if pronouns := user.get("pronouns"):
            message += " - " + " or ".join(pronouns)
        await inline_reply(evt, message)

    async def _user_info(self, evt: MessageEvent, username: str | None) -> None:
        await evt.mark_read()
        try:
            user = await get_fasuser(username or evt.sender, evt, self.plugin.fasjsonclient)
        except InfoGatherError as e:
            await evt.respond(e.message)
            return

        await evt.respond(
            f"User: {user.get('username')},{NL}"
            f"Name: {user.get('human_name')},{NL}"
            f"Pronouns: {' or '.join(user.get('pronouns') or ['unset'])},{NL}"
            f"Creation: {user.get('creation')},{NL}"
            f"Timezone: {user.get('timezone')},{NL}"
            f"Locale: {user.get('locale')},{NL}"
            f"GPG Key IDs: {' and '.join(k for k in user['gpgkeyids'] or ['None'])}{NL}"
        )

    async def _user_localtime(self, evt: MessageEvent, username: str | None) -> None:
        await evt.mark_read()
        try:
            user = await get_fasuser(username or evt.sender, evt, self.plugin.fasjsonclient)
        except InfoGatherError as e:
            await evt.respond(e.message)
            return

        timezone_name = user["timezone"]
        if timezone_name is None:
            await evt.reply('User "%s" doesn\'t share their timezone' % user.get("username"))
            return
        try:
            time = datetime.now(pytz.timezone(timezone_name))
        except Exception:
            await evt.reply(
                f'The timezone of "{user.get("username")}" was unknown: "{timezone_name}"'
            )
            return
        await evt.respond(
            f'The current local time of "{user.get("username")}" is: "{time.strftime("%H:%M")}" '
            f"(timezone: {timezone_name})"
        )

    @command.new(help="Get information about Fedora Accounts users")
    async def user(self, evt: MessageEvent) -> None:
        """Query information about Fedora groups"""
        pass

    @user.subcommand(name="hello", help="Return brief information about a Fedora user.")
    @command.argument("username", pass_raw=True, required=False)
    async def user_hello(self, evt: MessageEvent, username: str | None) -> None:
        """
        Returns a short line of information about the user. If no username is provided, defaults to
        the sender of the message.

        #### Arguments ####

        * `username`: A Fedora Accounts username or a Matrix User ID
           (e.g. @username:fedora.im)

        """
        await self._user_hello(evt, username)

    @user.subcommand(name="info", help="Return brief information about a Fedora user.")
    @command.argument("username", pass_raw=True, required=False)
    async def user_info(self, evt: MessageEvent, username: str | None) -> None:
        """
        Returns a information from Fedora Accounts about the user
        If no username is provided, defaults to the sender of the message.

        #### Arguments ####

        * `username`: A Fedora Accounts username or a Matrix User ID
           (e.g. @username:fedora.im)

        """
        await self._user_info(evt, username)

    @user.subcommand(name="localtime", help="Returns the current time of the user.")
    @command.argument("username", pass_raw=True, required=True)
    async def user_localtime(self, evt: MessageEvent, username: str | None) -> None:
        """
        Returns the current time of the user.
        The timezone is queried from FAS.

        #### Arguments ####

        * `username`: A Fedora Accounts username or a Matrix User ID
           (e.g. @username:fedora.im)

        """
        await self._user_localtime(evt, username)

    @command.passive(r"^!(hi|hello|hello2|hellomynameis|fasinfo|localtime)(?:\s+|$)(.*)")
    async def aliases(self, evt: MessageEvent, match) -> None:
        msg, cmd, arguments = match
        if cmd in ["hi", "hello", "hello2", "hellomynameis"]:
            await self._user_hello(evt, arguments)
        elif cmd in ["fasinfo"]:
            await self._user_info(evt, arguments)
        elif cmd in ["localtime"]:
            await self._user_localtime(evt, arguments)
        else:
            return  # pragma: no cover
