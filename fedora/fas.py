import re
from datetime import datetime

import pytz
from maubot import MessageEvent
from maubot.handlers import command

from .clients.fasjson import FasjsonClient
from .constants import ALIASES, NL
from .exceptions import InfoGatherError


class FasHandler:
    def __init__(self, config):
        self.config = config
        self.fasjsonclient = FasjsonClient(self.config["fasjson_url"])

    async def _get_fasuser(self, username: str, evt: MessageEvent):
        async def _get_users_by_matrix_id(username: str) -> dict | str:
            """looks up a user by the matrix id"""

            # Fedora Accounts stores these strangly but this is to handle that
            try:
                matrix_username, matrix_server = re.findall(r"@(.*):(.*)", username)[0]
            except (ValueError, IndexError) as e:
                raise InfoGatherError(
                    f"Sorry, {username} does not look like a valid matrix user ID "
                    "(e.g. @username:homeserver.com )"
                ) from e

            # if given a fedora.im address -- just look up the username as a FAS name
            if matrix_server == "fedora.im":
                user = await self.fasjsonclient.get_user(matrix_username)
                return user

            searchterm = f"matrix://{matrix_server}/{matrix_username}"
            searchresult = await self.fasjsonclient.search_users(
                params={"ircnick__exact": searchterm}
            )

            if len(searchresult) > 1:
                names = f"{NL}".join([name["username"] for name in searchresult])
                raise InfoGatherError(
                    f"{len(searchresult)} Fedora Accounts users have the {username} "
                    f"Matrix Account defined:{NL}"
                    f"{names}"
                )
            elif len(searchresult) == 0:
                raise InfoGatherError(
                    f"No Fedora Accounts users have the {username} Matrix Account defined"
                )

            return searchresult[0]

        # if no username is supplied, we use the matrix id of the sender
        # (e.g. "@dudemcpants:fedora.im")
        if not username:
            username = evt.sender

        # check if the formatted message has mentions (ie the user has tab-completed on someones
        # name) in them
        if evt.content.formatted_body:
            # in element at least, when usernames are mentioned, they are formatted like:
            # <a href="https://matrix.to/#/@zodbot:fedora.im">zodbot</a>
            # here we check the formatted message and extract all the matrix user IDs
            u = re.findall(
                r'href=[\'"]?http[s]?://matrix.to/#/([^\'" >]+)',
                evt.content.formatted_body,
            )
            if len(u) > 1:
                raise InfoGatherError("Sorry, I can only look up one username at a time")
            elif len(u) == 1:
                mu = await _get_users_by_matrix_id(u[0])
                return mu

        usernames = username.split(" ")
        if len(usernames) > 1:
            raise InfoGatherError("Sorry, I can only look up one username at a time")

        # else check if the username given is a matrix id (@<username>:<server.com>)
        if re.search(r"@.*:.*", usernames[0]):
            musers = await _get_users_by_matrix_id(usernames[0])
            return musers

        # finally, assume we were given a FAS / Fedora Account ID and use that
        else:
            user = await self.fasjsonclient.get_user(usernames[0])
            return user

    @command.new(help="Query information about Fedora Accounts groups")
    async def group(self, evt: MessageEvent) -> None:
        """Query information about Fedora groups"""
        pass

    @group.subcommand(name="members", help="Return a list of members of the specified group")
    @command.argument("groupname", required=True)
    async def group_members(self, evt: MessageEvent, groupname: str) -> None:
        """
        Return a list of the members of the Fedora Accounts group

        ## Arguments ##
        `groupname`: (required) The name of the Fedora Accounts group
        """
        # required=True on subcommand arguments doenst seem to work
        # so we do it ourselves
        if not groupname:
            await evt.respond("groupname argument is required. e.g. `!group members designteam`")
            return

        try:
            members = await self.fasjsonclient.get_group_membership(
                groupname, membership_type="members"
            )
        except InfoGatherError as e:
            await evt.respond(e.message)
            return

        if len(members) > 200:
            await evt.respond(f"{groupname} has {len(members)} and thats too much to dump here")
            return

        await evt.respond(f"Members of {groupname}: {', '.join(m['username'] for m in members)}")

    @group.subcommand(name="sponsors", help="Return a list of owners of the specified group")
    @command.argument("groupname", required=True)
    async def group_sponsors(self, evt: MessageEvent, groupname: str) -> None:
        if not groupname:
            await evt.respond("groupname argument is required. e.g. `!group sponsors designteam`")
            return

        try:
            sponsors = await self.fasjsonclient.get_group_membership(
                groupname, membership_type="sponsors"
            )
        except InfoGatherError as e:
            await evt.respond(e.message)
            return

        await evt.respond(f"Sponsors of {groupname}: {', '.join(s['username'] for s in sponsors)}")

    @group.subcommand(name="info", help="Return a list of owners of the specified group")
    @command.argument("groupname", required=True)
    async def group_info(self, evt: MessageEvent, groupname: str) -> None:
        if not groupname:
            await evt.respond("groupname argument is required. e.g. `!group info designteam`")
            return

        try:
            group = await self.fasjsonclient.get_group(groupname)
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

    @command.new(help="Return brief information about a Fedora user.", aliases=ALIASES["hello"])
    @command.argument("username", pass_raw=True, required=False)
    async def hello(self, evt: MessageEvent, username: str) -> None:
        """
        Returns a short line of information about the user. If no username is provided, defaults to
        the sender of the message.

        #### Arguments ####

        * `username`: A Fedora Accounts username or a Matrix User ID
           (e.g. @username:fedora.im)

        """
        try:
            user = await self._get_fasuser(username, evt)
        except InfoGatherError as e:
            await evt.respond(e.message)
            return

        message = f"{user['human_name']} ({user['username']})"
        if pronouns := user.get("pronouns"):
            message += " - " + " or ".join(pronouns)
        await evt.respond(message)

    @command.new(help="Return brief information about a Fedora user.", aliases=ALIASES["user"])
    @command.argument("username", pass_raw=True, required=False)
    async def user(self, evt: MessageEvent, username: str) -> None:
        """
        Returns a information from Fedora Accounts about the user
        If no username is provided, defaults to the sender of the message.

        #### Arguments ####

        * `username`: A Fedora Accounts username or a Matrix User ID
           (e.g. @username:fedora.im)

        """
        try:
            user = await self._get_fasuser(username, evt)
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

    @command.new(help="Returns the current time of the user.")
    @command.argument("username", pass_raw=True, required=False)
    async def localtime(self, evt: MessageEvent, username: str) -> None:
        """
        Returns the current time of the user.
        The timezone is queried from FAS.

        #### Arguments ####

        * `username`: A Fedora Accounts username or a Matrix User ID
           (e.g. @username:fedora.im)

        """
        try:
            user = await self._get_fasuser(username, evt)
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
